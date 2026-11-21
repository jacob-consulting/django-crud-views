"""Theme data prefixes through the real component rendering paths."""

from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID

import pytest
from django.template import Context, Template
from django.test import RequestFactory, override_settings
from django.utils.translation import override
from lxml import html

from crud_views_object_detail.lib.resolvers import ResolvedGroup, ResolvedProperty


def render_data_prefix_component(name, *, count=2, token="prefix-page"):
    """Fixed identities, English labels, stock icons and an explicit CSRF token."""
    context = {"csrf_token": "fixed-csrf-token", "request": RequestFactory().get("/prefix/?a=1&b=2")}
    if name.startswith("menu-"):
        context.update(
            group=SimpleNamespace(menu=[{"cv_label": "Read", "cv_url": "/read/", "cv_access": True}]),
            location=name.removeprefix("menu-"),
        )
        source = "{% load crud_views %}{% cv_actions_menu group location %}"
    elif name == "language":
        source = "{% load crud_views %}{% cv_language_selector %}"
    else:
        groups = [
            ResolvedGroup(title=title, id=key, properties=[ResolvedProperty("name", "Name", "<value> & text")])
            for title, key in [("First", "first"), ("Second", "second")][:count]
        ]
        context.update(groups=groups, layout=name, token=token)
        if name == "standalone":
            context["group"] = groups[0]
            source = '{% load crud_views_object_detail %}{% render_group group layout="accordion" %}'
        else:
            source = (
                "{% load crud_views_object_detail %}"
                "{% render_object_detail obj groups layout=layout component_id=token %}"
            )
    with (
        override("en"),
        override_settings(LANGUAGES=[("en", "English"), ("de", "German")][:count]),
        patch("crud_views_object_detail.lib.presentation.uuid4", return_value=UUID(int=391)),
    ):
        return Template(source).render(Context(context))


# Captured from 460af14c49df753680fd758bd5d6fed2c7ca3858 before template edits,
# with the fixed inputs above. Frozen for this phase: never normalize or regenerate
# on failure. Later authorized markup changes must explain each named byte delta.
_RAW_DEFAULT_COMPONENTS = {
    "menu-list": (
        "\n"
        "\n"
        '<div class="btn-group">\n'
        "    \n"
        "\n"
        '<button type="button" class="btn btn-outline-primary btn-xs dropdown-toggle cv-menu-toggle"\n'
        '        data-bs-toggle="dropdown" aria-expanded="false" aria-label="More actions"\n'
        '        data-bs-popper-config=\'{"strategy":"fixed"}\'>\n'
        '    <i class="fa-solid fa-ellipsis" aria-hidden="true"></i><span class="visually-hidden">More actions</span>\n'
        "</button>\n"
        "\n"
        '    <ul class="dropdown-menu dropdown-menu-end">\n'
        '        <li><a href="/read/"\n'
        '    class="dropdown-item"\n'
        "    \n"
        "    \n"
        "    \n"
        "    \n"
        '    cv-key=""><span class="cv-icon-fw" aria-hidden="true"></span> \n'
        "</a>\n"
        "\n"
        "</li>\n"
        "    </ul>\n"
        "</div>\n"
        "\n"
    ),
    "menu-context": (
        "\n"
        "\n"
        '<div class="btn-group">\n'
        "    \n"
        "\n"
        '<button type="button" class="btn btn-outline-primary btn-lg dropdown-toggle cv-menu-toggle"\n'
        '        data-bs-toggle="dropdown" aria-expanded="false" aria-label="More actions"\n'
        "        >\n"
        '    <i class="fa-solid fa-ellipsis" aria-hidden="true"></i><span class="visually-hidden">More actions</span>\n'
        "</button>\n"
        "\n"
        '    <ul class="dropdown-menu dropdown-menu-end">\n'
        '        <li><a href="/read/"\n'
        '    class="dropdown-item"\n'
        "    \n"
        "    \n"
        "    \n"
        "    \n"
        '    cv-key=""><span class="cv-icon-fw" aria-hidden="true"></span> \n'
        "</a>\n"
        "\n"
        "</li>\n"
        "    </ul>\n"
        "</div>\n"
        "\n"
    ),
    "menu-card": (
        "\n"
        "\n"
        '<div class="dropdown">\n'
        "    \n"
        "\n"
        '<button type="button" class="btn btn-secondary btn-sm dropdown-toggle cv-menu-toggle"\n'
        '        data-bs-toggle="dropdown" aria-expanded="false" aria-label="More actions"\n'
        "        >\n"
        '    <i class="fa-solid fa-ellipsis" aria-hidden="true"></i><span class="visually-hidden">More actions</span>\n'
        "</button>\n"
        "\n"
        '    <ul class="dropdown-menu dropdown-menu-end">\n'
        '        <li><a href="/read/"\n'
        '    class="dropdown-item"\n'
        "    \n"
        "    \n"
        "    \n"
        "    \n"
        '    cv-key=""><span class="cv-icon-fw" aria-hidden="true"></span> Read\n'
        "</a>\n"
        "\n"
        "</li>\n"
        "    </ul>\n"
        "</div>\n"
        "\n"
    ),
    "language": (
        "\n"
        "\n"
        "\n"
        '<div class="dropdown">\n'
        '  <button class="btn btn-outline-secondary dropdown-toggle" type="button"\n'
        '          data-bs-toggle="dropdown" aria-expanded="false">\n'
        '    <i class="fa-solid fa-language" aria-hidden="true"></i>\n'
        "    \n"
        "  </button>\n"
        '  <ul class="dropdown-menu dropdown-menu-end">\n'
        "    \n"
        "    <li>\n"
        '      <form action="/i18n/setlang/" method="post" class="m-0">\n'
        '        <input type="hidden" name="csrfmiddlewaretoken" value="fixed-csrf-token">\n'
        '        <input type="hidden" name="next" value="/prefix/?a=1&amp;b=2">\n'
        '        <input type="hidden" name="language" value="en">\n'
        '        <button type="submit" class="dropdown-item">\n'
        "          English\n"
        "        </button>\n"
        "      </form>\n"
        "    </li>\n"
        "    \n"
        "    <li>\n"
        '      <form action="/i18n/setlang/" method="post" class="m-0">\n'
        '        <input type="hidden" name="csrfmiddlewaretoken" value="fixed-csrf-token">\n'
        '        <input type="hidden" name="next" value="/prefix/?a=1&amp;b=2">\n'
        '        <input type="hidden" name="language" value="de">\n'
        '        <button type="submit" class="dropdown-item">\n'
        "          Deutsch\n"
        "        </button>\n"
        "      </form>\n"
        "    </li>\n"
        "    \n"
        "  </ul>\n"
        "</div>\n"
        "\n"
    ),
    "tabs-vertical": (
        "\n"
        '<div class="card" id="cvod-c11-prefix-page-root">\n'
        '    <div class="card-body">\n'
        '        <div class="row">\n'
        '            <div class="col-md-3">\n'
        '                <div class="nav flex-column nav-pills" id="cvod-c11-prefix-page-tabs"'
        ' role="tablist" aria-orientation="vertical" data-cv-od-tabs>\n'
        "                    \n"
        "                    \n"
        '                    <button class="nav-link active text-start"\n'
        '                            id="cvod-c11-prefix-page-s5-first-control"\n'
        '                            data-bs-toggle="pill"\n'
        '                            data-bs-target="#cvod-c11-prefix-page-s5-first-panel"\n'
        '                            type="button" role="tab"\n'
        '                            aria-controls="cvod-c11-prefix-page-s5-first-panel"\n'
        '                            tabindex="0"\n'
        '                            aria-selected="true">\n'
        "                        First\n"
        "                    </button>\n"
        "                    \n"
        "                    \n"
        '                    <button class="nav-link text-start"\n'
        '                            id="cvod-c11-prefix-page-s6-second-control"\n'
        '                            data-bs-toggle="pill"\n'
        '                            data-bs-target="#cvod-c11-prefix-page-s6-second-panel"\n'
        '                            type="button" role="tab"\n'
        '                            aria-controls="cvod-c11-prefix-page-s6-second-panel"\n'
        '                            tabindex="-1"\n'
        '                            aria-selected="false">\n'
        "                        Second\n"
        "                    </button>\n"
        "                    \n"
        "                </div>\n"
        "            </div>\n"
        '            <div class="col-md-9 border-start">\n'
        '                <div class="tab-content ps-md-4" id="cvod-c11-prefix-page-content">\n'
        "                    \n"
        "                    \n"
        '<div class="tab-pane fade active show"\n'
        '     id="cvod-c11-prefix-page-s5-first-panel"\n'
        '     role="tabpanel" tabindex="0"\n'
        '     aria-labelledby="cvod-c11-prefix-page-s5-first-control">\n'
        '    <h5 class="mb-1">First</h5>\n'
        "    \n"
        '    <dl class="row mb-0">\n'
        "        \n"
        "        \n"
        '<dt class="col-sm-4 text-body-secondary fw-medium">Name</dt>\n'
        '<dd class="col-sm-8">\n'
        "    &lt;value&gt; &amp; text\n"
        "    \n"
        "</dd>\n"
        "\n"
        "        \n"
        "    </dl>\n"
        "</div>\n"
        "\n"
        "                    \n"
        "                    \n"
        '<div class="tab-pane fade"\n'
        '     id="cvod-c11-prefix-page-s6-second-panel"\n'
        '     role="tabpanel" tabindex="0"\n'
        '     aria-labelledby="cvod-c11-prefix-page-s6-second-control">\n'
        '    <h5 class="mb-1">Second</h5>\n'
        "    \n"
        '    <dl class="row mb-0">\n'
        "        \n"
        "        \n"
        '<dt class="col-sm-4 text-body-secondary fw-medium">Name</dt>\n'
        '<dd class="col-sm-8">\n'
        "    &lt;value&gt; &amp; text\n"
        "    \n"
        "</dd>\n"
        "\n"
        "        \n"
        "    </dl>\n"
        "</div>\n"
        "\n"
        "                    \n"
        "                </div>\n"
        "            </div>\n"
        "        </div>\n"
        "    </div>\n"
        "</div>\n"
    ),
    "accordion": (
        "\n"
        '<div class="accordion" id="cvod-c11-prefix-page-root">\n'
        "\n"
        "\n"
        '<div class="accordion-item">\n'
        '    <h2 class="accordion-header">\n'
        "        \n"
        '        <button class="accordion-button" type="button"\n'
        '                id="cvod-c11-prefix-page-s5-first-control"\n'
        '                data-bs-toggle="collapse" data-bs-target="#cvod-c11-prefix-page-s5-first-panel"\n'
        '                aria-expanded="true"\n'
        '                aria-controls="cvod-c11-prefix-page-s5-first-panel">\n'
        "            \n"
        "            First\n"
        '            <span class="badge text-bg-secondary ms-2">1 properties</span>\n'
        "        </button>\n"
        "    </h2>\n"
        '    <div id="cvod-c11-prefix-page-s5-first-panel"\n'
        '         class="accordion-collapse collapse show"\n'
        '         aria-labelledby="cvod-c11-prefix-page-s5-first-control"\n'
        '         data-bs-parent="#cvod-c11-prefix-page-root">\n'
        '        <div class="accordion-body">\n'
        "            \n"
        '            <table class="table table-sm table-borderless mb-0">\n'
        '                <thead class="visually-hidden">\n'
        '                    <tr><th scope="col">Property</th><th scope="col">Value</th></tr>\n'
        "                </thead>\n"
        "                <tbody>\n"
        "                    \n"
        "                    \n"
        "<tr>\n"
        '    <th scope="row" class="text-body-secondary fw-medium" style="width: 30%;">Name</th>\n'
        "    <td>\n"
        "        &lt;value&gt; &amp; text\n"
        "        \n"
        "    </td>\n"
        "</tr>\n"
        "\n"
        "                    \n"
        "                </tbody>\n"
        "            </table>\n"
        "        </div>\n"
        "    </div>\n"
        "</div>\n"
        "\n"
        "\n"
        "\n"
        '<div class="accordion-item">\n'
        '    <h2 class="accordion-header">\n'
        "        \n"
        '        <button class="accordion-button collapsed" type="button"\n'
        '                id="cvod-c11-prefix-page-s6-second-control"\n'
        '                data-bs-toggle="collapse" data-bs-target="#cvod-c11-prefix-page-s6-second-panel"\n'
        '                aria-expanded="false"\n'
        '                aria-controls="cvod-c11-prefix-page-s6-second-panel">\n'
        "            \n"
        "            Second\n"
        '            <span class="badge text-bg-secondary ms-2">1 properties</span>\n'
        "        </button>\n"
        "    </h2>\n"
        '    <div id="cvod-c11-prefix-page-s6-second-panel"\n'
        '         class="accordion-collapse collapse"\n'
        '         aria-labelledby="cvod-c11-prefix-page-s6-second-control"\n'
        '         data-bs-parent="#cvod-c11-prefix-page-root">\n'
        '        <div class="accordion-body">\n'
        "            \n"
        '            <table class="table table-sm table-borderless mb-0">\n'
        '                <thead class="visually-hidden">\n'
        '                    <tr><th scope="col">Property</th><th scope="col">Value</th></tr>\n'
        "                </thead>\n"
        "                <tbody>\n"
        "                    \n"
        "                    \n"
        "<tr>\n"
        '    <th scope="row" class="text-body-secondary fw-medium" style="width: 30%;">Name</th>\n'
        "    <td>\n"
        "        &lt;value&gt; &amp; text\n"
        "        \n"
        "    </td>\n"
        "</tr>\n"
        "\n"
        "                    \n"
        "                </tbody>\n"
        "            </table>\n"
        "        </div>\n"
        "    </div>\n"
        "</div>\n"
        "\n"
        "\n"
        "</div>\n"
    ),
    "standalone": (
        "\n"
        '<div class="accordion-item">\n'
        '    <h2 class="accordion-header">\n'
        "        \n"
        '        <button class="accordion-button" type="button"\n'
        '                id="cvod-c33-g00000000000000000000000000000187-s5-first-control"\n'
        '                data-bs-toggle="collapse"'
        ' data-bs-target="#cvod-c33-g00000000000000000000000000000187-s5-first-panel"\n'
        '                aria-expanded="true"\n'
        '                aria-controls="cvod-c33-g00000000000000000000000000000187-s5-first-panel">\n'
        "            \n"
        "            First\n"
        '            <span class="badge text-bg-secondary ms-2">1 properties</span>\n'
        "        </button>\n"
        "    </h2>\n"
        '    <div id="cvod-c33-g00000000000000000000000000000187-s5-first-panel"\n'
        '         class="accordion-collapse collapse show"\n'
        '         aria-labelledby="cvod-c33-g00000000000000000000000000000187-s5-first-control"\n'
        "         >\n"
        '        <div class="accordion-body">\n'
        "            \n"
        '            <table class="table table-sm table-borderless mb-0">\n'
        '                <thead class="visually-hidden">\n'
        '                    <tr><th scope="col">Property</th><th scope="col">Value</th></tr>\n'
        "                </thead>\n"
        "                <tbody>\n"
        "                    \n"
        "                    \n"
        "<tr>\n"
        '    <th scope="row" class="text-body-secondary fw-medium" style="width: 30%;">Name</th>\n'
        "    <td>\n"
        "        &lt;value&gt; &amp; text\n"
        "        \n"
        "    </td>\n"
        "</tr>\n"
        "\n"
        "                    \n"
        "                </tbody>\n"
        "            </table>\n"
        "        </div>\n"
        "    </div>\n"
        "</div>\n"
    ),
}


@pytest.mark.parametrize("name", _RAW_DEFAULT_COMPONENTS)
def test_data_prefix_default_component_bytes(name):
    assert render_data_prefix_component(name) == _RAW_DEFAULT_COMPONENTS[name]
    assert render_data_prefix_component(name) == _RAW_DEFAULT_COMPONENTS[name]


def test_data_prefix_default_and_public_import():
    import crud_views.lib as public

    assert callable(getattr(public, "register_data_prefix", None)), "public prefix registration is missing"
    from crud_views.lib.data_prefix import get_data_prefix

    assert get_data_prefix() == "bs"


def test_data_prefix_registration_order(isolate_data_prefix):
    from crud_views.lib import register_data_prefix
    from crud_views.lib.data_prefix import get_data_prefix

    for prefix in ("coreui", "bs", "coreui", "coreui"):
        register_data_prefix(prefix)
        assert get_data_prefix() == prefix


@pytest.mark.parametrize("prefix", ["a", "bs", "coreui", "a1", "foo-bar2-baz", "a" * 1000])
def test_data_prefix_valid_values(prefix, isolate_data_prefix):
    from crud_views.lib import register_data_prefix
    from crud_views.lib.data_prefix import get_data_prefix

    register_data_prefix(prefix)
    assert get_data_prefix() == prefix


@pytest.mark.parametrize(
    "prefix",
    [
        "",
        "BS",
        "bS",
        "1a",
        "-a",
        "a--b",
        "a-",
        " a",
        "a ",
        "a\nb",
        "bs\n",
        "a\t",
        "a_b",
        "a.b",
        'a"',
        "a'",
        "a[b]",
        "<a>",
        "a/b",
        "a=b",
        "ä",
        "a\u0661",
        "\uff41",
        "a\x00",
        None,
        b"bs",
        1,
        1.5,
        True,
        False,
        [],
        {},
        (),
        set(),
    ],
)
def test_data_prefix_invalid_values_preserve_state(prefix, isolate_data_prefix):
    from crud_views.lib import register_data_prefix
    from crud_views.lib.data_prefix import get_data_prefix

    register_data_prefix("coreui")
    with pytest.raises(ValueError):
        register_data_prefix(prefix)
    assert get_data_prefix() == "coreui"


def test_data_prefix_tag_reads_late_registration(isolate_data_prefix):
    from crud_views.lib import register_data_prefix
    from crud_views.templatetags.crud_views import cv_data_prefix

    template = Template("{% load crud_views %}{% cv_data_prefix %}")
    for prefix in ("coreui", "bs"):
        register_data_prefix(prefix)
        assert type(cv_data_prefix()) is str
        assert template.render(Context()) == prefix


@pytest.mark.parametrize("location", ["list", "context", "card"])
def test_data_prefix_actions_menu(location, isolate_data_prefix):
    from crud_views.lib import register_data_prefix

    register_data_prefix("coreui")
    output = render_data_prefix_component(f"menu-{location}")
    assert output == _RAW_DEFAULT_COMPONENTS[f"menu-{location}"].replace("data-bs-", "data-coreui-")
    assert 'data-coreui-toggle="dropdown"' in output
    assert ("data-coreui-popper-config" in output) is (location == "list")
    assert "data-bs-" not in output


@pytest.mark.parametrize("name", _RAW_DEFAULT_COMPONENTS)
def test_data_prefix_component_attributes(name, isolate_data_prefix):
    from crud_views.lib import register_data_prefix

    register_data_prefix("coreui")
    output = render_data_prefix_component(name)
    assert output == _RAW_DEFAULT_COMPONENTS[name].replace("data-bs-", "data-coreui-")
    assert render_data_prefix_component(name) == output
    assert "data-bs-" not in output
    assert "data-coreui-toggle" in output


@pytest.mark.parametrize("prefix", ["bs", "coreui"])
@pytest.mark.parametrize("count", [0, 1, 2])
@pytest.mark.parametrize("layout", ["tabs-vertical", "accordion"])
def test_data_prefix_group_order_and_selection(prefix, count, layout, isolate_data_prefix):
    from crud_views.lib import register_data_prefix

    register_data_prefix(prefix)
    tree = html.fromstring(render_data_prefix_component(layout, count=count))
    controls = tree.cssselect(f"button[data-{prefix}-toggle]")
    assert len(controls) == count
    assert not tree.cssselect("value")
    if count:
        assert "<value> & text" in tree.text_content()
    for index, control in enumerate(controls):
        assert ("First", "Second")[index] in control.text_content()
        target = control.get(f"data-{prefix}-target")
        assert target == "#" + control.get("aria-controls")
        (panel,) = tree.xpath(".//*[@id=$id]", id=target[1:])
        assert panel.get("aria-labelledby") == control.get("id")
        assert ("show" in panel.classes) is (index == 0)
        if layout == "tabs-vertical":
            assert control.get("aria-selected") == ("true" if index == 0 else "false")
            assert control.get("tabindex") == ("0" if index == 0 else "-1")
            assert panel.get("tabindex") == "0"
            assert ("active" in control.classes) is (index == 0)
        else:
            assert control.get("aria-expanded") == ("true" if index == 0 else "false")
            assert ("collapsed" in control.classes) is (index != 0)
            assert panel.get(f"data-{prefix}-parent") == "#" + tree.get("id")


@pytest.mark.parametrize("prefix", ["bs", "coreui"])
def test_data_prefix_empty_and_standalone_components(prefix, isolate_data_prefix):
    from crud_views.lib import register_data_prefix

    register_data_prefix(prefix)
    for count in (0, 1):
        assert render_data_prefix_component("language", count=count).strip() == ""
    tree = html.fromstring(render_data_prefix_component("standalone"))
    (control,) = tree.cssselect(f"button[data-{prefix}-toggle]")
    (panel,) = tree.cssselect(".accordion-collapse")
    assert control.get("aria-expanded") == "true"
    assert control.get(f"data-{prefix}-target") == "#" + panel.get("id")
    assert panel.get("aria-labelledby") == control.get("id")
    assert not any(name.endswith("-parent") for name in panel.attrib)


def test_data_prefix_language_selection_and_transport(isolate_data_prefix):
    from crud_views.lib import register_data_prefix

    register_data_prefix("coreui")
    with override_settings(LANGUAGES=[("en", "English"), ("de", "German")]), override("de"):
        output = Template("{% load crud_views %}{% cv_language_selector %}").render(
            Context({"csrf_token": "fixed-csrf-token", "request": RequestFactory().get("/language/?x=1&y=2")})
        )
    tree = html.fromstring(output)
    (toggle,) = tree.cssselect("[data-coreui-toggle]")
    assert "Deutsch" in toggle.text_content()
    (selected,) = tree.cssselect("button.active")
    assert "Deutsch" in selected.text_content()
    for form in tree.cssselect("form"):
        assert form.get("method") == "post"
        assert form.get("action") == "/i18n/setlang/"
        assert form.cssselect('[name="csrfmiddlewaretoken"]')[0].get("value") == "fixed-csrf-token"
        assert form.cssselect('[name="next"]')[0].get("value") == "/language/?x=1&y=2"


def test_data_prefix_independent_and_nested_targets(isolate_data_prefix):
    from crud_views.lib import register_data_prefix
    from tests.test1.od.test_badge_semantics import template_settings

    register_data_prefix("coreui")
    nested = (
        "{% load crud_views_object_detail %}{% render_object_detail obj property_display=prop.value "
        'layout="tabs-vertical" component_id="inner" %}'
    )
    outer = [
        ResolvedGroup("Outer", id="outer", properties=[ResolvedProperty("child", "Child", [], template="nested.html")])
    ]
    outer[0].properties[0].value = [{"title": "Inner", "properties": []}]
    source = (
        '{% load crud_views_object_detail %}{% render_object_detail obj groups layout="tabs-vertical" '
        'component_id="outer" %}{% render_object_detail obj other layout="tabs-vertical" component_id="sibling" %}'
    )
    with override_settings(TEMPLATES=template_settings({"nested.html": nested})):
        output = Template(source).render(Context({"groups": outer, "other": [ResolvedGroup("Sibling")]}))
    tree = html.fragment_fromstring(output, create_parent="root")
    assert len(tree.cssselect("[data-cv-od-tabs]")) == 3
    controls = tree.cssselect("button[data-coreui-toggle]")
    assert len(controls) == 3
    ids = tree.xpath(".//@id")
    assert len(ids) == len(set(ids))
    for control in controls:
        (panel,) = tree.xpath(".//*[@id=$id]", id=control.get("data-coreui-target")[1:])
        assert panel.get("aria-labelledby") == control.get("id")
    assert "data-bs-" not in output
