"""Read-only deletion descriptions and explicit native write provenance.

Inspection deliberately doesn't use Django's Collector: collect() executes application
code. The write adapter below retains Django's SQL executor, but establishes protection
origin before calling executable extensions instead of guessing from a traceback.
"""

from collections import defaultdict
from dataclasses import dataclass
from inspect import signature
from itertools import chain
from typing import NamedTuple

from django.core.exceptions import ImproperlyConfigured
from django.db import connections
from django.db.models import ForeignKey, Model, OneToOneField
from django.db.models.deletion import (
    CASCADE,
    DO_NOTHING,
    PROTECT,
    RESTRICT,
    SET_NULL,
    Collector,
    ProtectedError,
    RestrictedError,
    get_candidate_relations_to_delete,
)


class RelatedObjects(NamedTuple):
    tree: list
    summary: dict[str, int]
    protected: list


@dataclass(frozen=True)
class DeletePreviewBoundary:
    kind: str
    model: type[Model]
    field_name: str | None
    using: str
    source_pks: tuple


@dataclass(frozen=True)
class DeletePreviewContribution:
    boundary: DeletePreviewBoundary
    deleted: tuple[Model, ...] = ()
    protected: tuple[Model, ...] = ()
    complete: bool = False


@dataclass(frozen=True)
class DeleteInspection:
    related: RelatedObjects
    boundaries: tuple[DeletePreviewBoundary, ...]

    @property
    def complete(self):
        return not self.boundaries


def _identity(obj, using):
    # A proxy and its concrete instance describe the same stored deletion row.
    return using, obj._meta.concrete_model, obj.pk


class _DeleteInspector:
    def __init__(self, target, using):
        self.target = target
        self.using = using
        self.rows = {}
        self.edges = defaultdict(list)
        self.visited = set()
        self.unknown = defaultdict(list)
        self.protected = {}
        self.restricted = {}

    def boundary(self, kind, source, field_name=None):
        pks = self.unknown[kind, source._meta.model, field_name]
        if source.pk not in pks:
            pks.append(source.pk)

    def add(self, obj, parent=None):
        key = _identity(obj, self.using)
        self.rows.setdefault(key, obj)
        if parent is not None and key not in self.edges[parent]:
            self.edges[parent].append(key)
        return key

    def visit(self, obj, *, collect_related=True, parent=None):
        key = self.add(obj, parent)
        mode = key, collect_related
        if mode in self.visited:
            return
        self.visited.add(mode)
        opts = obj._meta
        for field in opts.concrete_model._meta.parents.values():
            if field is None:
                continue
            if type(field) not in (ForeignKey, OneToOneField):
                self.boundary("on_delete", obj, field.name)
                continue
            values = field.get_local_related_value(obj)
            query = {remote.attname: value for (_, remote), value in zip(field.related_fields, values, strict=True)}
            ancestors = field.remote_field.model._base_manager.using(self.using).filter(**query)
            # A polymorphic parent manager otherwise upcasts this stored parent row
            # back to the child, conflating its identity and omitting its summary count.
            if hasattr(ancestors, "non_polymorphic"):
                ancestors = ancestors.non_polymorphic()
            for ancestor in ancestors:
                self.visit(ancestor, collect_related=False, parent=key)
        if not collect_related:
            return
        for relation in get_candidate_relations_to_delete(opts):
            field = relation.field
            if type(field) not in (ForeignKey, OneToOneField):
                self.boundary("on_delete", obj, getattr(field, "name", None))
                continue
            handler = field.remote_field.on_delete
            if handler is SET_NULL or handler is DO_NOTHING:
                continue
            if not any(handler is native for native in (CASCADE, PROTECT, RESTRICT)):
                self.boundary("on_delete", obj, field.name)
                continue
            values = field.get_foreign_related_value(obj)
            query = {local.attname: value for (local, _), value in zip(field.related_fields, values, strict=True)}
            for child in relation.related_model._base_manager.using(self.using).filter(**query):
                if handler is CASCADE:
                    self.visit(child, parent=key)
                elif handler is PROTECT:
                    self.protected.setdefault(_identity(child, self.using), child)
                else:
                    self.restricted.setdefault(_identity(child, self.using), child)
        for field in opts.private_fields:
            if hasattr(field, "bulk_related_objects"):
                self.boundary("private_relation", obj, getattr(field, "name", None))

    def inspect(self):
        target = self.target
        if getattr(target.delete, "__func__", None) is not Model.delete:
            self.boundary("model_delete", target)
        # Explicit using selects native same-PK semantics, including fresh join values.
        if target._state.db != self.using:
            target = type(target)._base_manager.using(self.using).get(pk=target.pk)
        self.visit(target)
        self.protected.update((key, obj) for key, obj in self.restricted.items() if key not in self.rows)
        expanded = set()

        def tree(key):
            result = [self.rows[key]]
            if key in expanded:
                return result
            expanded.add(key)
            children = [item for child in self.edges[key] for item in tree(child)]
            if children:
                result.append(children)
            return result

        summary = defaultdict(int)
        for obj in self.rows.values():
            if obj._meta.concrete_model is not target._meta.concrete_model:
                summary[obj._meta.verbose_name] += 1
        boundaries = tuple(
            DeletePreviewBoundary(kind, model, name, self.using, tuple(pks))
            for (kind, model, name), pks in self.unknown.items()
        )
        return DeleteInspection(
            RelatedObjects(tree(_identity(target, self.using)), dict(summary), list(self.protected.values())),
            boundaries,
        )


def inspect_deletion(target, *, using):
    return _DeleteInspector(target, using).inspect()


def merge_delete_preview(inspection, contributions, *, using):
    """Merge boundary-scoped, trusted descriptions before any permission projection."""
    boundaries = {boundary: boundary for boundary in inspection.boundaries}
    seen = set()
    unresolved = set(boundaries)
    related = inspection.related
    tree = list(related.tree)
    summary = dict(related.summary)

    def walk(items):
        for item in items:
            if isinstance(item, list):
                yield from walk(item)
            elif isinstance(item, Model):
                yield item

    deleted = {_identity(obj, using) for obj in walk(tree)}
    protected = {_identity(obj, using): obj for obj in related.protected}
    root_model = tree[0]._meta.concrete_model
    for contribution in contributions:
        if not isinstance(contribution, DeletePreviewContribution):
            raise ValueError("Delete preview providers must return DeletePreviewContribution records")
        boundary = contribution.boundary
        if not isinstance(boundary, DeletePreviewBoundary):
            raise ValueError("Delete preview contribution must reference a DeletePreviewBoundary descriptor")
        try:
            hash(boundary)
        except TypeError as error:
            raise ValueError("Delete preview boundary must have an immutable source_pks tuple") from error
        if boundary not in boundaries or boundary.using != using or boundary in seen:
            raise ValueError("Delete preview contribution references an unknown, stale or duplicate boundary")
        if type(contribution.complete) is not bool:
            raise ValueError("Delete preview contribution complete must be a boolean")
        if not isinstance(contribution.deleted, tuple) or not isinstance(contribution.protected, tuple):
            raise ValueError("Delete preview deleted and protected records must be tuples of model instances")
        seen.add(boundary)
        for records, is_deleted in ((contribution.deleted, True), (contribution.protected, False)):
            for obj in records:
                if not isinstance(obj, Model) or obj._state.adding or obj.pk is None or obj._state.db != using:
                    raise ValueError("Delete preview records must be saved model instances on the selected database")
                key = _identity(obj, using)
                if is_deleted and key not in deleted:
                    deleted.add(key)
                    if len(tree) == 1:
                        tree.append([])
                    else:
                        tree[1] = list(tree[1])
                    tree[1].append(obj)
                    if obj._meta.concrete_model is not root_model:
                        name = obj._meta.verbose_name
                        summary[name] = summary.get(name, 0) + 1
                elif not is_deleted:
                    protected.setdefault(key, obj)
        if contribution.complete:
            unresolved.remove(boundary)
    return DeleteInspection(
        RelatedObjects(tree, summary, list(protected.values())),
        tuple(boundary for boundary in inspection.boundaries if boundary in unresolved),
    )


class _NativeDeleteBlocked(Exception):
    """A native collection blocker observed before any executable deletion extension."""


class _DeleteCollector(Collector):
    """Adapted from Django 4.2/5.2/6.0 Collector.collect (Django Software Foundation, BSD).

    Keep upstream batching, deferral, dependency, fast-delete and RESTRICT closure
    behavior. Deliberate differences: identity dispatch, immediate PROTECT, sticky
    callback provenance and no ProtectedError aggregation. Collector.delete is inherited.
    Source: https://github.com/django/django/blob/stable/6.0.x/django/db/models/deletion.py
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_callback_entered = False

    def _blocked(self, error):
        if not self.custom_callback_entered:
            raise _NativeDeleteBlocked from error
        raise error

    def collect(
        self,
        objs,
        source=None,
        nullable=False,
        collect_related=True,
        source_attr=None,
        reverse_dependency=False,
        keep_parents=False,
        fail_on_restricted=True,
    ):
        if self.can_fast_delete(objs):
            self.fast_deletes.append(objs)
            return
        new_objs = self.add(objs, source, nullable, reverse_dependency=reverse_dependency)
        if not new_objs:
            return
        model = new_objs[0].__class__
        if not keep_parents:
            for ptr in model._meta.concrete_model._meta.parents.values():
                if ptr:
                    self.collect(
                        [getattr(obj, ptr.name) for obj in new_objs],
                        source=model,
                        source_attr=ptr.remote_field.related_name,
                        collect_related=False,
                        reverse_dependency=True,
                        fail_on_restricted=False,
                    )
        if not collect_related:
            return
        # Django 4.2 exposes get_parent_list(); 5.2/6.0 expose all_parents.
        parents = ()
        if keep_parents:
            parents = getattr(model._meta, "all_parents", None)
            if parents is None:
                parents = set(model._meta.get_parent_list())
        model_fast_deletes = defaultdict(list)
        for related in get_candidate_relations_to_delete(model._meta):
            if keep_parents and related.model._meta.concrete_model in parents:
                continue
            field = related.field
            handler = field.remote_field.on_delete
            if handler is DO_NOTHING:
                continue
            related_model = related.related_model
            if self.can_fast_delete(related_model, from_field=field):
                model_fast_deletes[related_model].append(field)
                continue
            for batch in self.get_del_batches(new_objs, [field]):
                sub_objs = self.related_objects(related_model, [field], batch)
                if not (sub_objs.query.select_related or self._has_signal_listeners(related_model)):
                    referenced_fields = set(
                        chain.from_iterable(
                            (remote.attname for remote in relation.field.foreign_related_fields)
                            for relation in get_candidate_relations_to_delete(related_model._meta)
                        )
                    )
                    sub_objs = sub_objs.only(*tuple(referenced_fields))
                # Query evaluation/converters are outside any exception translation.
                if handler is SET_NULL:
                    self.add_field_update(field, None, sub_objs)
                    continue
                if not (getattr(handler, "lazy_sub_objs", False) or sub_objs):
                    continue
                if handler is CASCADE:
                    self.collect(
                        sub_objs,
                        source=field.remote_field.model,
                        source_attr=field.name,
                        nullable=field.null,
                        fail_on_restricted=False,
                    )
                    if field.null and not connections[self.using].features.can_defer_constraint_checks:
                        self.add_field_update(field, None, sub_objs)
                elif handler is PROTECT:
                    self._blocked(ProtectedError("Deletion blocked by a native protected relationship", set(sub_objs)))
                elif handler is RESTRICT:
                    self.add_restricted_objects(field, sub_objs)
                    self.add_dependency(field.remote_field.model, field.model)
                else:
                    self.custom_callback_entered = True
                    handler(self, field, sub_objs, self.using)
        for related_model, related_fields in model_fast_deletes.items():
            for batch in self.get_del_batches(new_objs, related_fields):
                self.fast_deletes.append(self.related_objects(related_model, related_fields, batch))
        for field in model._meta.private_fields:
            if hasattr(field, "bulk_related_objects"):
                self.custom_callback_entered = True
                sub_objs = field.bulk_related_objects(new_objs, self.using)
                self.collect(sub_objs, source=model, nullable=True, fail_on_restricted=False)
        if fail_on_restricted:
            for related_model, instances in self.data.items():
                self.clear_restricted_objects_from_set(related_model, instances)
            for qs in self.fast_deletes:
                self.clear_restricted_objects_from_queryset(qs.model, qs)
            restricted = set(
                chain.from_iterable(
                    objects for fields in self.restricted_objects.values() for objects in fields.values()
                )
            )
            if restricted:
                self._blocked(RestrictedError("Deletion blocked by a native restricted relationship", restricted))


def _selected_native_target(target, *, using):
    """Read current join values without changing the authorized origin's state."""
    return type(target)._base_manager.using(using).get(pk=target.pk)


def execute_deletion(target, *, using):
    method = target.delete
    if getattr(method, "__func__", None) is not Model.delete:
        try:
            signature(method).bind(using=using)
        except (TypeError, ValueError) as error:
            raise ImproperlyConfigured(
                "Custom model delete must have an inspectable signature accepting delete(using=...). "
                "Provide a keyword using parameter or a forwarding **kwargs adapter."
            ) from error
        return method(using=using)
    # Django 5.2+ validates every composite-key component; 4.2 has scalar PKs.
    pk_is_set = target._is_pk_set() if hasattr(Model, "_is_pk_set") else target.pk is not None
    if not pk_is_set:
        raise ValueError(
            f"{target._meta.object_name} object can't be deleted because its {target._meta.pk.attname} "
            "attribute is set to None."
        )
    collector = _DeleteCollector(using=using, origin=target)
    collector.collect([_selected_native_target(target, using=using)])
    result = collector.delete()
    setattr(target, target._meta.pk.attname, None)
    return result
