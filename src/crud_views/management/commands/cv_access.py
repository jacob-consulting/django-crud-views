"""Format one shared access trace without evaluating authorization independently."""

import json
import re
from typing import ClassVar

from django.core.management import BaseCommand, CommandError
from django.core.management.color import supports_color
from django.utils.termcolors import make_style
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from crud_views.lib.access_trace import resolve_trace_user, trace_access


def _style(value, role, enabled):
    if not enabled:
        return value
    if role in {"skipped", "not_reached", "not_evaluated"}:
        # Django's palette does not expose dim; keep this one explicit wrapper.
        return "\x1b[2m" + value + "\x1b[0m"
    color = {
        "key": "cyan",
        "passed": "green",
        "allowed": "green",
        "denied": "red",
        "not_found": "red",
        "error": "yellow",
        "no_such_route": "yellow",
        "login_redirect": "yellow",
        "unavailable": "yellow",
    }.get(role)
    return make_style(fg=color)(value) if color else value


def _text(value):
    """Keep untrusted diagnostic values on one line without terminal controls."""
    return "".join(char if char.isprintable() else json.dumps(char)[1:-1] for char in str(value))


def _result_label(result):
    return {
        "allowed": _("Allowed"),
        "passed": _("Passed"),
        "denied": _("Denied"),
        "not_found": _("Not found"),
        "login_redirect": _("Login redirect"),
        "no_such_route": _("No such route"),
        "error": _("Error"),
        "skipped": _("Skipped"),
        "not_reached": _("Not reached"),
        "not_evaluated": _("Not evaluated"),
        "unavailable": _("Unavailable"),
    }.get(result, _text(result))


def _kind_label(kind):
    return {
        "route": _("Route"),
        "validation": _("Validation"),
        "actor_admission": _("Actor admission"),
        "ancestor_lookup": _("Ancestor lookup"),
        "ancestor_gate": _("Ancestor gate"),
        "own_permission": _("Own permission"),
        "object_lookup": _("Object lookup"),
        "object_grant": _("Object grant"),
        "list_filter": _("List filter"),
        "action_state": _("Action state"),
        "manage_gate": _("Manage gate"),
        "custom_gate": _("Custom gate"),
        "login_middleware": _("Login middleware"),
        "limitation": _("Limitation"),
    }.get(kind, _text(kind))


def _facts(row):
    parts = [_kind_label(row["kind"])]
    for key, label in (
        ("viewset", _("ViewSet")),
        ("key", _("Key")),
        ("permission", _("Permission")),
        ("group", _("Group")),
        ("provider", _("Provider")),
        ("source", _("Source")),
        ("how", _("How")),
    ):
        if row.get(key) is not None:
            parts.append(_("%(label)s: %(value)s") % {"label": label, "value": _text(row[key])})
    if row.get("object"):
        parts.append(_("Object: %(model)s %(pk)s") % {key: _text(value) for key, value in row["object"].items()})
    if row.get("message"):
        parts.append(_text(row["message"]))
    if row.get("exception"):
        parts.append(_("%(class)s: %(message)s") % {key: _text(value) for key, value in row["exception"].items()})
    if row.get("counts"):
        counts = row["counts"]
        if counts["total"] is None:
            parts.append(ngettext("%(count)s row", "%(count)s rows", counts["visible"]) % {"count": counts["visible"]})
        else:
            parts.append(_("sees %(visible)s of %(total)s objects") % counts)
    return "; ".join(parts)


def _format_text(trace, color=False):
    data = trace.to_dict()
    actor = data["user"]
    if actor.get("anonymous"):
        user = _("Anonymous user")
    else:
        user = _("%(username)s (pk %(pk)s, %(state)s)") % {
            "username": _text(actor.get("username")),
            "pk": _text(actor.get("pk")),
            "state": _("active") if actor.get("active") else _("inactive"),
        }
    lines = [
        _("Path: %(path)s") % {"path": _text(trace.path)},
        _("Route: %(route)s") % {"route": _text(trace.route)},
        _("View: %(view)s") % {"view": _text(trace.view)},
        _("User: %(user)s") % {"user": user},
        "",
        _("Plan:"),
    ]
    lines.extend("  " + _facts(row) for row in data["plan"])
    if not trace.plan:
        lines.append("  " + _("No planned gates."))
    lines.extend(["", _("Steps:")])
    for step in data["steps"]:
        lines.append(
            _("%(number)s. %(result)s — %(facts)s")
            % {
                "number": step["n"],
                "result": _style(_result_label(step["result"]), step["result"], color),
                "facts": _facts(step),
            }
        )
    lines.extend(["", _("Limitations:")])
    lines.extend("  " + _text(message) for message in trace.untraced)
    lines.append("")
    if trace.decided_by is not None:
        lines.append(
            _("%(outcome)s at step %(number)s.")
            % {
                "outcome": _style(_result_label(trace.outcome), trace.outcome, color),
                "number": trace.decided_by,
            }
        )
    else:
        lines.append(
            _("Outcome: %(outcome)s.")
            % {
                "outcome": _style(_result_label(trace.outcome), trace.outcome, color),
            }
        )
    if trace.outcome == "allowed":
        lines.append(_("This user may open the page; handler-phase checks are not evaluated."))
    return "\n".join(lines)


def _color_json(serialized):
    """Wrap complete serialized string tokens; never decode/re-encode their escapes."""
    key = None

    def color_token(match):
        nonlocal key
        token = match.group()
        if serialized[match.end() :].lstrip().startswith(":"):
            key = json.loads(token)
            return _style(token, "key", True)
        role = json.loads(token) if key in {"result", "outcome"} else None
        key = None
        return _style(token, role, True)

    return re.sub(r'"(?:\\.|[^"\\])*"', color_token, serialized)


def _format_json(trace, color=False):
    serialized = json.dumps(trace.to_dict(), ensure_ascii=True, indent=2)
    return _color_json(serialized) if color else serialized


class Command(BaseCommand):
    requires_system_checks: ClassVar[list] = []

    @property
    def help(self):
        # argparse needs a real string, translated when the parser is created.
        return _("Trace whether a user may open a project URL, without running its view handler.")

    def add_arguments(self, parser):
        parser.add_argument("path", help=_("Project path or full URL (only its path is used)."))
        parser.add_argument("user", nargs="?", help=_("Username or primary key; username matches take precedence."))
        parser.add_argument(
            "--anonymous", action="store_true", help=_("Trace the anonymous user instead of a named user.")
        )
        parser.add_argument("--as-json", action="store_true", help=_("Print one versioned JSON trace document."))

    def handle(self, *args, path, user=None, anonymous=False, as_json=False, **options):
        if anonymous == (user is not None):
            raise CommandError(_("Supply either a user or --anonymous, but not both."), returncode=2)
        actor = None if anonymous else resolve_trace_user(user)
        if not anonymous and actor is None:
            raise CommandError(_("Unknown user: %(user)s") % {"user": _text(user)}, returncode=2)
        trace = trace_access(path, actor)
        color = not options["no_color"] and (options["force_color"] or (self.stdout.isatty() and supports_color()))
        if trace.outcome == "no_such_route" and not as_json:
            self.stderr.write(_("No such CRUD view route: %(path)s") % {"path": _text(trace.path)})
        else:
            self.stdout.write(_format_json(trace, color) if as_json else _format_text(trace, color))
        code = {"allowed": 0, "denied": 1, "not_found": 1, "login_redirect": 1, "no_such_route": 2, "error": 2}[
            trace.outcome
        ]
        if code:
            raise SystemExit(code)
