"""Public link decisions from caller-owned objects, without a request or rendering view."""

from enum import Enum
from inspect import Parameter, signature
from pathlib import Path

import pytest

from crud_views.lib import link_access
from tests.test1 import test_link_access as private_link_tests
from tests.test1.app.models import Publisher
from tests.test1.test_ancestor_authorization import _user
from tests.test1.test_ancestor_docs import _fence

core_targets = private_link_tests.core_targets
data = private_link_tests.data

LINK_ACCESS_MD = Path(__file__).resolve().parents[2] / "docs" / "reference" / "link_access.md"


def test_public_signature_and_enum():
    check = getattr(link_access, "check_link_access", None)
    assert callable(check), "check_link_access must be importable from crud_views.lib.link_access"
    result_type = getattr(link_access, "LinkAccess", None)
    assert isinstance(result_type, type) and issubclass(result_type, Enum)
    assert [(p.name, p.kind, p.default) for p in signature(check).parameters.values()] == [
        ("target", Parameter.POSITIONAL_OR_KEYWORD, Parameter.empty),
        ("user", Parameter.POSITIONAL_OR_KEYWORD, Parameter.empty),
        ("obj", Parameter.KEYWORD_ONLY, None),
        ("known_ancestors", Parameter.KEYWORD_ONLY, ()),
    ]
    assert list(result_type.__members__) == ["ALLOWED", "DENIED_PERMISSION", "DENIED_STATE"]
    assert len(set(result_type)) == 3
    assert [bool(member) for member in result_type] == [True, False, False]
    for member in result_type:
        assert not isinstance(member, str)
        assert member != member.value


@pytest.mark.django_db
def test_public_object_tracer(core_targets, data):
    assert hasattr(link_access, "check_link_access"), "the documented public callable must exist"
    actor = _user("public_object_tracer", (Publisher, "view"))
    namespace = {"TargetView": core_targets.Detail, "user": actor, "book": data.book, "publisher": data.penguin}
    source = _fence(LINK_ACCESS_MD, "## Object target")
    exec(compile(source, f"{LINK_ACCESS_MD}:Object target", "exec"), namespace)
    assert namespace["result"] is link_access.LinkAccess.ALLOWED
