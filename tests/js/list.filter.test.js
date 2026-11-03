import $ from "jquery";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { loadScript, nav } from "./helpers/load.js";

// mode mirrors the server-rendered leaf (#262): "icon" a hidden label, "both" the icons plus a visible label
function fixture({ expanded = false, queryString = "", mode = "icon", label = "Filter" } = {}) {
    const text = mode === "icon" ? `<span class="visually-hidden">${label}</span>` : ` <span>${label}</span>`;
    document.body.innerHTML = `
        <div id="cv-config" data-request-path="/books/" data-query-string="${queryString}" data-csrf-token="test-token" hidden></div>
        <button type="button" id="cv-filter-toggle" aria-expanded="${expanded}" aria-controls="filter-collapse">
            <span data-cv-filter-icon="open"${expanded ? " hidden" : ""}><i class="x"></i></span>
            <span data-cv-filter-icon="close"${expanded ? "" : " hidden"}><i class="y"></i></span>
            ${text}
        </button>
        <button type="button" id="filter-button-reset"></button>
        <div id="filter-collapse"></div>`;
    vi.stubGlobal("cvGetConfig", () => ({ request: { path: "/books/", query_string: queryString }, csrfToken: "t" }));
    return {
        open: document.querySelector('[data-cv-filter-icon="open"]'),
        close: document.querySelector('[data-cv-filter-icon="close"]'),
        toggle: document.querySelector("#cv-filter-toggle"),
        label: document.querySelector("#cv-filter-toggle > span:not([data-cv-filter-icon])"),
    };
}

function hostFixture() {
    document.body.innerHTML = `
        <div id="cv-config" data-request-path="/books/" data-query-string="" data-csrf-token="test-token" hidden></div>
        <button type="button" id="cv-filter-toggle" aria-expanded="false" aria-controls="filter-collapse"
                class="btn icon-funnel" data-cv-filter-icon-open="icon-funnel" data-cv-filter-icon-close="icon icon-x">
            <span class="visually-hidden">Filter</span>
        </button>
        <div id="filter-collapse"></div>`;
    vi.stubGlobal("cvGetConfig", () => ({ request: { path: "/books/", query_string: "" }, csrfToken: "t" }));
    return { toggle: document.querySelector("#cv-filter-toggle") };
}

// The three server-rendered bodies of the filter leaf (#262). icon and both carry element icon wrappers or, with
// placement "host", the host classes plus their swap hooks; label carries no icon hook at all. The host open/close
// class strings share their "icon" token, the way a theme's "icon {name_class}" icon-host slot renders them.
const HOST = { open: "icon icon-funnel", close: "icon icon-x" };

function modeFixture({ mode = "label", placement = "element", expanded = false, label = "Filter" } = {}) {
    const host = placement === "host" && mode !== "label";
    const icons =
        mode === "label" || host
            ? ""
            : `<span data-cv-filter-icon="open"${expanded ? " hidden" : ""}><i class="x"></i></span>
               <span data-cv-filter-icon="close"${expanded ? "" : " hidden"}><i class="y"></i></span>`;
    const hostAttrs = host ? ` data-cv-filter-icon-open="${HOST.open}" data-cv-filter-icon-close="${HOST.close}"` : "";
    const classes = host ? `btn m-${mode} ${expanded ? HOST.close : HOST.open}` : `btn m-${mode}`;
    const text =
        mode === "icon" ? `<span class="visually-hidden">${label}</span>` : `${mode === "both" ? " " : ""}<span>${label}</span>`;
    document.body.innerHTML = `
        <div id="cv-config" data-request-path="/books/" data-query-string="" data-csrf-token="test-token" hidden></div>
        <button type="button" id="cv-filter-toggle" class="${classes}" aria-expanded="${expanded}"
                aria-controls="filter-collapse"${hostAttrs}>
            ${icons}
            ${text}
        </button>
        <div id="filter-collapse"></div>`;
    vi.stubGlobal("cvGetConfig", () => ({ request: { path: "/books/", query_string: "" }, csrfToken: "t" }));
    const toggle = document.querySelector("#cv-filter-toggle");
    return { toggle, label: visibleLabel(toggle), host };
}

// the visible label: a child span that is neither an icon wrapper nor the hidden label
function visibleLabel(toggle) {
    const labels = toggle.querySelectorAll(":scope > span:not([data-cv-filter-icon]):not(.visually-hidden)");
    expect(labels).toHaveLength(1);
    return labels[0];
}

// the icon state a fixture shows for one expansion state
function expectIcons(f, mode, expanded) {
    if (mode === "label") {
        expect(f.toggle.querySelectorAll("[data-cv-filter-icon], i")).toHaveLength(0);
        expect(f.toggle.hasAttribute("data-cv-filter-icon-open")).toBe(false);
        expect(f.toggle.className).toBe("btn m-label");
    } else if (f.host) {
        const active = (expanded ? HOST.close : HOST.open).split(" ");
        const inactive = expanded ? "icon-funnel" : "icon-x";
        expect([...f.toggle.classList]).toEqual(expect.arrayContaining(["btn", `m-${mode}`, ...active]));
        expect(f.toggle.classList.contains(inactive)).toBe(false);
    } else {
        const open = f.toggle.querySelector('[data-cv-filter-icon="open"]');
        const close = f.toggle.querySelector('[data-cv-filter-icon="close"]');
        expect([open.hidden, close.hidden]).toEqual([expanded, !expanded]);
        expect(f.toggle.className).toBe(`btn m-${mode}`);
    }
}

function expectPost(call, expanded) {
    expect(call).toEqual([
        "/books/",
        {
            method: "POST",
            headers: { "X-CSRFToken": "t", "Content-Type": "application/json; charset=utf-8" },
            body: JSON.stringify({ filter_expanded: expanded }),
        },
    ]);
}

function deferred() {
    let resolve, reject;
    const promise = new Promise((res, rej) => {
        resolve = res;
        reject = rej;
    });
    return { promise, resolve, reject };
}

const LAYOUTS = [
    ["label", "element"],
    ["both", "element"],
    ["both", "host"],
];

describe("list.filter.js", () => {
    let fetchMock;
    let toggle;

    beforeEach(() => {
        fetchMock = vi.fn(() => Promise.resolve({ ok: true }));
        vi.stubGlobal("fetch", fetchMock);
        toggle = vi.fn();
        window.cv = { ...window.cv, adapters: { collapse: { toggle } } };
        nav.href = "";
    });

    it("swaps the host icon classes on the button", async () => {
        const f = hostFixture();
        await loadScript("list.filter");
        f.toggle.click();
        expect(f.toggle.classList.contains("icon-funnel")).toBe(false);
        expect([...f.toggle.classList]).toEqual(expect.arrayContaining(["btn", "icon", "icon-x"]));
        f.toggle.click();
        expect(f.toggle.className).toBe("btn icon-funnel");
    });

    it("flips the hidden attribute on click without touching icon classes", async () => {
        const f = fixture();
        await loadScript("list.filter");
        f.toggle.click();
        expect(f.open.hidden).toBe(true);
        expect(f.close.hidden).toBe(false);
        expect(f.open.querySelector("i").className).toBe("x");
        f.toggle.click();
        expect(f.open.hidden).toBe(false);
        expect(f.close.hidden).toBe(true);
    });

    it("keeps the visible label of a both-mode toggle while its element icons flip", async () => {
        const f = fixture({ mode: "both" });
        await loadScript("list.filter");
        f.toggle.click();
        expect(f.toggle.getAttribute("aria-expanded")).toBe("true");
        expect([f.open.hidden, f.close.hidden]).toEqual([true, false]);
        expect(f.toggle.querySelector("#cv-filter-toggle > span:not([data-cv-filter-icon])")).toBe(f.label);
        expect(f.label.textContent).toBe("Filter");
        expect(fetchMock).toHaveBeenCalledWith("/books/", {
            method: "POST",
            headers: { "X-CSRFToken": "t", "Content-Type": "application/json; charset=utf-8" },
            body: JSON.stringify({ filter_expanded: true }),
        });
    });

    it("flips aria-expanded, posts the new state as JSON and toggles the panel", async () => {
        const f = fixture();
        await loadScript("list.filter");
        f.toggle.click();
        expect(f.toggle.getAttribute("aria-expanded")).toBe("true");
        expect(toggle).toHaveBeenCalledWith(document.getElementById("filter-collapse"));
        expect(fetchMock).toHaveBeenCalledWith("/books/", {
            method: "POST",
            headers: { "X-CSRFToken": "t", "Content-Type": "application/json; charset=utf-8" },
            body: JSON.stringify({ filter_expanded: true }),
        });
        f.toggle.click();
        expect(f.toggle.getAttribute("aria-expanded")).toBe("false");
        expect(fetchMock.mock.calls[1][1].body).toBe(JSON.stringify({ filter_expanded: false }));
    });

    it.each([
        ["open", "", true, false],
        ["closed", "display: none", false, true],
    ])("derives the state from the panel when the toggle has no aria-expanded (starts %s)", async (_n, style, startsOpen, expected) => {
        const f = fixture();
        f.toggle.removeAttribute("aria-expanded");
        document.getElementById("filter-collapse").setAttribute("style", style);
        await loadScript("list.filter");
        f.toggle.click();
        expect(startsOpen).toBe(!expected);
        expect(fetchMock.mock.calls[0][1].body).toBe(JSON.stringify({ filter_expanded: expected }));
        expect(f.toggle.getAttribute("aria-expanded")).toBe(String(expected));
    });

    it("changes nothing when the collapse adapter throws", async () => {
        vi.spyOn(console, "error").mockImplementation(() => {}); // jsdom reports listener errors here
        const swallow = (event) => event.preventDefault(); // ... and as a window "error" event
        window.addEventListener("error", swallow);
        toggle.mockImplementation(() => {
            throw new Error("no bootstrap");
        });
        const f = fixture();
        await loadScript("list.filter");
        f.toggle.click();
        window.removeEventListener("error", swallow);
        expect(f.toggle.getAttribute("aria-expanded")).toBe("false");
        expect(f.open.hidden).toBe(false);
        expect(fetchMock).not.toHaveBeenCalled();
    });

    it("changes nothing when the collapse adapter refuses the toggle (panel still animating)", async () => {
        toggle.mockImplementation(() => false);
        const f = fixture();
        await loadScript("list.filter");
        f.toggle.click();
        expect(toggle).toHaveBeenCalledTimes(1);
        expect(f.toggle.getAttribute("aria-expanded")).toBe("false");
        expect(f.open.hidden).toBe(false);
        expect(fetchMock).not.toHaveBeenCalled();
    });

    it("still toggles when the state POST fails", async () => {
        fetchMock.mockImplementation(() => Promise.reject(new Error("offline")));
        const f = fixture();
        await loadScript("list.filter");
        f.toggle.click();
        expect(toggle).toHaveBeenCalledTimes(1);
        expect(f.toggle.getAttribute("aria-expanded")).toBe("true");
        await new Promise((r) => setTimeout(r, 0)); // the rejection is handled, no unhandled error
    });

    it.each([
        ["sort=name&page=2", "/books/?sort=name&reset_filter=true"],
        ["", "/books/?reset_filter=true"],
        ["order=title&dir=desc&title=x", "/books/?order=title&dir=desc&reset_filter=true"],
        ["sort=a%26b", "/books/?sort=a%26b&reset_filter=true"],
    ])("reset navigates with %j", async (queryString, expected) => {
        fixture({ queryString });
        await loadScript("list.filter");
        document.getElementById("filter-button-reset").click();
        expect(nav.href).toBe(expected);
    });

    describe.each(LAYOUTS)("a %s-mode toggle with %s icons (#262)", (mode, placement) => {
        it.each([
            ["Filter", false],
            ["Filter", true],
            ["Ünïcødé ✓ 搜索", false],
            ["Ünïcødé ✓ 搜索", true],
        ])("keeps the label %j over two clicks (starts expanded: %s)", async (text, expanded) => {
            const f = modeFixture({ mode, placement, expanded, label: text });
            await loadScript("list.filter");
            for (const [click, state] of [
                [1, !expanded],
                [2, expanded],
            ]) {
                f.toggle.click();
                expect(toggle).toHaveBeenCalledTimes(click);
                expect(f.toggle.getAttribute("aria-expanded")).toBe(String(state));
                expect(visibleLabel(f.toggle)).toBe(f.label); // the same node, never re-rendered
                expect(f.label.textContent).toBe(text);
                expectIcons(f, mode, state);
                expect(fetchMock).toHaveBeenCalledTimes(click);
                expectPost(fetchMock.mock.calls[click - 1], state);
            }
        });

        it("collapses before it changes the DOM or persists", async () => {
            const f = modeFixture({ mode, placement });
            const seen = [];
            toggle.mockImplementation(() => {
                seen.push([f.toggle.getAttribute("aria-expanded"), f.toggle.className, fetchMock.mock.calls.length]);
                expectIcons(f, mode, false);
            });
            await loadScript("list.filter");
            const before = f.toggle.className;
            f.toggle.click();
            expect(seen).toEqual([["false", before, 0]]);
            expect(f.toggle.getAttribute("aria-expanded")).toBe("true");
        });

        it("never rolls back the latest state when persistence settles out of order", async () => {
            const requests = [deferred(), deferred()];
            fetchMock.mockImplementation(() => requests[fetchMock.mock.calls.length - 1].promise);
            const f = modeFixture({ mode, placement, label: "Ünïcødé ✓" });
            await loadScript("list.filter");
            f.toggle.click();
            f.toggle.click();
            expect(fetchMock.mock.calls.map((call) => call[1].body)).toEqual([
                JSON.stringify({ filter_expanded: true }),
                JSON.stringify({ filter_expanded: false }),
            ]);
            // the latest request fails first, then the earlier one succeeds late: neither may touch the DOM
            requests[1].reject(new Error("offline"));
            await new Promise((r) => setTimeout(r, 0));
            requests[0].resolve({ ok: true, json: () => Promise.resolve({ filter_expanded: true }) });
            await new Promise((r) => setTimeout(r, 0));
            expect(f.toggle.getAttribute("aria-expanded")).toBe("false");
            expectIcons(f, mode, false);
            expect(visibleLabel(f.toggle)).toBe(f.label);
            expect(f.label.textContent).toBe("Ünïcødé ✓");
            expect(fetchMock).toHaveBeenCalledTimes(2);
        });
    });

    it("changes nothing on a label-only toggle when the collapse adapter throws", async () => {
        vi.spyOn(console, "error").mockImplementation(() => {});
        const swallow = (event) => event.preventDefault();
        window.addEventListener("error", swallow);
        toggle.mockImplementation(() => {
            throw new Error("no bootstrap");
        });
        const f = modeFixture({ mode: "label" });
        await loadScript("list.filter");
        f.toggle.click();
        window.removeEventListener("error", swallow);
        expect(f.toggle.getAttribute("aria-expanded")).toBe("false");
        expectIcons(f, "label", false);
        expect(f.label.textContent).toBe("Filter");
        expect(fetchMock).not.toHaveBeenCalled();
    });

    it("changes nothing on a label-only toggle when the collapse adapter refuses the toggle", async () => {
        toggle.mockImplementation(() => false);
        const f = modeFixture({ mode: "label", expanded: true });
        await loadScript("list.filter");
        f.toggle.click();
        expect(toggle).toHaveBeenCalledTimes(1);
        expect(f.toggle.getAttribute("aria-expanded")).toBe("true");
        expect(f.label.textContent).toBe("Filter");
        expect(fetchMock).not.toHaveBeenCalled();
    });

    it("keeps a successful label-only toggle when the state POST fails", async () => {
        fetchMock.mockImplementation(() => Promise.reject(new Error("offline")));
        const f = modeFixture({ mode: "label" });
        await loadScript("list.filter");
        f.toggle.click();
        await new Promise((r) => setTimeout(r, 0));
        expect(f.toggle.getAttribute("aria-expanded")).toBe("true");
        expect(visibleLabel(f.toggle)).toBe(f.label);
        expect(f.label.textContent).toBe("Filter");
        expectPost(fetchMock.mock.calls[0], true);
    });

    it("loads harmlessly on a page without a toggle (no filter, or a pinned filter)", async () => {
        document.body.innerHTML = `<div id="filter-collapse" class="show"></div>`;
        await loadScript("list.filter");
        expect(document.getElementById("cv-filter-toggle")).toBeNull();
        expect(toggle).not.toHaveBeenCalled();
        expect(fetchMock).not.toHaveBeenCalled();
    });

    it("loads and works without jQuery", async () => {
        vi.stubGlobal("$", undefined);
        vi.stubGlobal("jQuery", undefined);
        try {
            const f = fixture();
            await loadScript("list.filter");
            f.toggle.click();
            expect(toggle).toHaveBeenCalledTimes(1);
        } finally {
            vi.stubGlobal("$", $);
            vi.stubGlobal("jQuery", $);
        }
    });
});
