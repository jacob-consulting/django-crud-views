(function () {
if (globalThis.__cvFormsetInit) {
    globalThis.cv.initFormsets();
    return;
}
globalThis.__cvFormsetInit = true;
const controllers = new WeakMap();

/**
 * CVFSConst
 *
 * constants used:
 *
 *  - attributes
 *  - selectors
 *
 */
const CVFSConst = Object.freeze({
    // attributes used
    attr: {
        formset_prefix: "cv-data-formset-prefix",
        form_prefix: "cv-data-formset-form-prefix",
        formset_data: "cv-data-formset",
        form_data: "cv-data-formset-form",
    },
    // selectors
    sel: {
        content: "div.cv-formset-content",
        row: "div.cv-formset-row"
    },
    // events dispatched
    event: {
        row_added: "cv:formset:row-added"
    }
});

/**
 * XBase: jquery helper
 */
class XBase {
    constructor(ctl) {
        this.ctl = ctl;
    }

    /**
     *
     * @param msg
     */
    debug(msg) {
        console.log(msg, "|");
    }

    /**
     * get selection, raise if not found
     *
     * @param selector
     * @param msg
     * @returns {*}
     */
    sel(selector, msg) {
        let selection = $(this.form || this.ctl?.form || document.querySelector("form.cv-form") || document).find(selector),
            message = msg || `${selector} not found`;
        return this.assert_sel(selection, message);
    }

    exact(selector, attribute, value, at) {
        const selection = at ? at.find(selector) : this.sel(selector);
        return this.assert_sel(selection.filter((_, el) => el.getAttribute(attribute) === value), `${value} not found`);
    }

    /**
     * get selection at selection, raise if not found
     *
     * @param at
     * @param selector
     * @param msg
     * @returns {*}
     */
    sel_at(at, selector, msg) {
        let selection = at.find(selector),
            message = msg || `${selector} not found`;
        return this.assert_sel(selection, message);
    }

    /**
     * assert that selection has at least one element
     *
     * @param selection
     * @param msg
     * @returns {*}
     */
    assert_sel(selection, msg) {
        if (selection.length === 0) {
            throw new Error(msg);
        }
        return selection;
    }

    /**
     * assert that expr is defined
     *
     * @param expr
     * @param msg
     * @returns {*}
     */
    assert_def(expr, msg) {
        if (expr === undefined) {
            throw new Error(msg);
        }
        return expr;
    }

    highlight(element, cls) {
        element.addClass(cls);
        setTimeout(() => {
            element.removeClass(cls);
        }, 500);
    }

    highlight_delete(element) {
        this.highlight(element, "cv-highlight-delete");
    }

    highlight_order(element) {
        this.highlight(element, "cv-highlight-order");
    }

    highlight_add(element) {
        this.highlight(element, "cv-highlight-add");
    }
}

/**
 * XFormset: formset representation
 *
 * This is short lived, disposed after each usage.
 */
class XFormset extends XBase {

    constructor(ctl, prefix) {
        super(ctl);

        this.selection = this.exact(CVFSConst.sel.content, CVFSConst.attr.formset_prefix, prefix);
        this.json = this.selection.attr(CVFSConst.attr.formset_data);
        this.data = JSON.parse(this.json);

        // from data
        this.path = this.data.path
        this.key = this.data.key
        this.prefix = this.data.prefix
        this.prefix_key = this.data.prefix_key
        this.hierarchy = this.data.hierarchy
        this.parent_prefix = this.data.parent_prefix
        this.parent_prefix_key = this.data.parent_prefix_key
        this.can_delete = this.data.can_delete
        this.can_delete_extra = this.data.can_delete_extra
        this.can_order = this.data.can_order
        this.edit_only = this.data.edit_only
        this.fields = this.data.fields
        this.pk_field = this.data.pk_field

        // checks
        console.assert(this.prefix === prefix, "prefix mismatch");

        // calculated

        // primary key and index: the pk starts after a "-" (or at the start), so a greedy prefix
        // cannot swallow leading digits of a multi-digit pk ("12-0" is pk 12, not 2)
        let pk_index_reg = new RegExp(String.raw`^(?:(.*)-)?(None|${this.data.pk})-(\d+)$`),
            pk_index_match = this.prefix_key.match(pk_index_reg).slice(-2),
            pk_index = pk_index_match.slice(-2),
            pk = pk_index[0] === "None" ? null : pk_index[0],
            index = Number.parseInt(pk_index[1]);
        this.pk = pk;
        this.index = index;

        // rows
        this.rows = this.selection.find(CVFSConst.sel.row)
            .filter((_, el) => el.getAttribute(CVFSConst.attr.formset_prefix) === this.prefix);
    }

    new() {
        return new XFormset(this.ctl, this.prefix);
    }

    get_management_form_value(key) {
        let selection = this.exact("input", "name", `${this.prefix}-${key}`),
            value = selection.val();
        return Number.parseInt(value);
    }

    set_management_form_value(key, value) {
        let selection = this.exact("input", "name", `${this.prefix}-${key}`);
        selection.val(value).attr("value", value);
    }

    get_total_forms() {
        return this.get_management_form_value("TOTAL_FORMS");
    }

    get_initial_forms() {
        return this.get_management_form_value("INITIAL_FORMS");
    }

    get_min_num_forms() {
        return this.get_management_form_value("MIN_NUM_FORMS");
    }

    get_max_num_forms() {
        return this.get_management_form_value("MAX_NUM_FORMS");
    }

    set_total_forms(num_forms) {
        this.set_management_form_value("TOTAL_FORMS", num_forms);
    }

    increment_total_forms() {
        let total_forms = this.get_total_forms();
        this.set_total_forms(total_forms + 1);
    }

    /**
     * Reorder formset rows
     */
    reorder() {

        let empty_fields = this.fields,
            pk_name = this.pk_field,
            empty_fields_check = empty_fields.concat([pk_name]),  // check all fields and pk
            order_index = 1;

        // abort if formset is not ordered
        if (!this.can_order) {
            return;
        }

        // loop over all rows
        this.rows.each((rid, r) => {

            let row = $(r);

            const prefix = row.attr(CVFSConst.attr.form_prefix);
            const inputs = row.find("input, select, textarea");
            const field = name => inputs.toArray().find(el => el.name === `${prefix}-${name}`);

            // every row must carry its pk input
            this.assert_def(field(pk_name));

            let order = this.assert_def(field("ORDER")),
                // get delete input (maybe checkbox or hidden)
                del = this.can_delete ? this.assert_def(field("DELETE")) : null,
                // get empty fields defined by suffix in options.empty_fields
                fields = empty_fields_check.map(field).filter(Boolean),
                // are all fields empty?
                empty = fields.map((field) => {
                    if (field.type === "checkbox" || field.type === "radio") return !field.checked;
                    return field.value.trim() === "";
                }),
                all_empty = empty.every(Boolean),
                // is row deleted? (depends on input type)
                // DELETE may render as a hidden input (crud_views default, value "1"/"0")
                // or as Django's checkbox
                deleted = del ? (del.type === "checkbox" ? del.checked : del.value === "1") : false;

            // set order depending on visibility
            if (all_empty || deleted) {
                order.value = '';
            } else {
                order.value = order_index;
                order_index++;
            }

            this.debug("form", rid, fields, del, order, all_empty, deleted, order_index);
        });
    }
}

/**
 * XFor: form representation
 *
 * This is short-lived, disposed after each usage.
 */
class XForm extends XBase {

    constructor(ctl, prefix) {
        super(ctl);
        this.row = this.exact(CVFSConst.sel.row, CVFSConst.attr.form_prefix, prefix);
        this.json = this.row.attr(CVFSConst.attr.form_data);
        this.data = JSON.parse(this.json);

        // from data
        this.key = this.data.key;
        this.prefix = this.data.prefix;
        this.prefix_key = this.data.prefix_key;
        this.formset_prefix = this.data.formset_prefix;

        // checks
        console.assert(this.prefix === prefix, "prefix mismatch");

        // init formset
        this.formset = new XFormset(ctl, this.formset_prefix);

        // calculated
        this.rows_total = this.formset.rows.length;
        this.row_index = this.formset.rows.index(this.row);
        this.row_is_first = this.row_index === 0;
        this.row_is_last = this.row_index === this.rows_total - 1;
        this.row_next = this.row_is_last ? null : this.formset.rows.eq(this.row_index + 1);
        this.row_previous = this.row_is_first ? null : this.formset.rows.eq(this.row_index - 1);
        this.row_last = this.formset.rows.last();

        // get delete input
        this.delete_input = this.formset.can_delete ? this.exact("input", "name", `${this.prefix}-DELETE`, this.row) : null;

        this.debug("form", this);
    }

    new() {
        let form = new XForm(this.ctl, this.prefix);
        return form;
    }

    add() {
        if (this.formset.edit_only) return;
        this.debug("add");

        let data = {
            template: this.formset.hierarchy.join("|"),
            pk: this.formset.pk === null ? "None" : this.formset.pk,
            num: this.formset.get_total_forms(),
            formset_parent_prefix_key: this.formset.parent_prefix_key
        };

        $.ajax({
            url: this.formset.path,       // the URL to send the request to
            type: "get",                // HTTP method (GET, POST, etc.)
            data: data,
            success: (response) => {    // Callback on success
                // A response for replaced/closed modal content must not mutate
                // a detached form or dispatch events into a newer session.
                if (!this.row[0].isConnected) return;
                // insert row at right position
                let html = response.html,
                    rows = response.rows;
                if (this.row_is_last) {
                    this.row_last[0].insertAdjacentHTML("afterend", html);
                } else {
                    this.row_next[0].insertAdjacentHTML("beforebegin", html);
                }
                this.formset.increment_total_forms();
                this.reorder();
                this.ctl.add_form_control_for_new_rows(rows);
                this.dispatch_row_added(rows);

                // highlight created rows
                rows.forEach((row) => {
                    console.log("highlight", row);
                    let hl = this.exact(CVFSConst.sel.row, CVFSConst.attr.form_prefix, row).find("input");
                    this.highlight_add(hl);
                });


            },
            error: (xhr, status, error) => {    // Callback on error
                this.debug('Error:', error);
            }
        });
    }

    /**
     * Dispatch "cv:formset:row-added" on each inserted row so scripts can initialize
     * widgets inside it (the formset counterpart of "cv:modal:loaded").
     *
     * Rows of nested formsets that arrive inside a new parent row get no event of their
     * own: the parent's event target already contains them, and a listener running
     * init(event.target) twice on the same element would double-bind.
     *
     * @param rows form prefixes of the inserted rows, as returned by the server
     */
    dispatch_row_added(rows) {
        let elements = rows
            .map((prefix) => this.sel(CVFSConst.sel.row).toArray()
                .find(el => el.getAttribute(CVFSConst.attr.form_prefix) === prefix))
            .filter(Boolean);
        elements
            .filter((el) => !elements.some((other) => other !== el && other.contains(el)))
            .forEach((el) => {
                el.dispatchEvent(new CustomEvent(CVFSConst.event.row_added, {
                    bubbles: true,
                    detail: {prefix: el.getAttribute(CVFSConst.attr.form_prefix), rows: rows},
                }));
            });
    }

    /**
     * Reorder formset rows.
     * Note: we have to re-create the formset instance here after a modification.
     */
    reorder() {
        let new_form = this.new();
        new_form.formset.reorder();
    }

    /**
     * Get all input elements in form
     *
     * @returns {*}
     */
    get_inputs() {
        return this.row.find(".cv-formset-form").first().find("input");
    }

    up() {
        let sel_highlight = this.get_inputs();
        this.debug("up");
        if (this.row_is_first) {
            return;
        }
        this.row[0].parentNode.insertBefore(this.row[0], this.row_previous[0])
        this.reorder();
        this.highlight_order(sel_highlight);
    }

    down() {
        let sel_highlight = this.get_inputs();
        this.debug("down");
        if (this.row_is_last) {
            return;
        }
        this.row_next[0].parentNode.insertBefore(this.row_next[0], this.row[0])
        this.reorder();
        this.highlight_order(sel_highlight);
    }

    delete() {
        this.debug("delete");
        let deleted = this.get_delete(),
            sel_highlight = this.get_inputs();

        // delete is a toggle: a second click un-marks the row
        this.set_delete(!deleted);

        this.highlight_delete(sel_highlight);
    }

    get_delete() {
        return this.delete_input[0].type === "checkbox" ? this.delete_input[0].checked : this.delete_input.val() === "1";
    }

    set_delete(value) {
        let button = this.row.find("button.cv-form-ctrl-delete")
            .filter((_, el) => el.getAttribute(CVFSConst.attr.form_prefix) === this.prefix);
        // class strings come from the template (data attributes), never from literals here
        let normal = button.attr("data-cv-class");
        let danger = button.attr("data-cv-class-danger");
        if (normal !== undefined && danger !== undefined) {
            if (value) {
                button.removeClass(normal);
                button.addClass(danger);
            } else {
                button.removeClass(danger);
                button.addClass(normal);
            }
        }
        if (this.delete_input[0].type === "checkbox") this.delete_input.prop("checked", value);
        else this.delete_input.val(value ? "1" : "0").attr("value", value ? "1" : "0");
    }


}

/**
 * XFormsetControl: formset control instance
 */
class CrudViewsFormset extends XBase {

    static get const() {
        let form_control = "cv-form-ctrl-";
        return {
            form_control_up: `.${form_control}up`,
            form_control_down: `.${form_control}down`,
            form_control_add: `.${form_control}add`,
            form_control_delete: `.${form_control}delete`,
        };
    }

    constructor(form = document.querySelector("form.cv-form")) {
        super();
        if (!form) throw new Error("owning form not found");
        if (controllers.has(form)) return controllers.get(form);
        this.form = form;
        controllers.set(form, this);
        this.onClick = event => {
            const button = event.target.closest?.("button.cv-form-ctrl-add, button.cv-form-ctrl-delete, button.cv-form-ctrl-up, button.cv-form-ctrl-down");
            if (!button || button.form !== this.form || event.defaultPrevented) return;
            event.preventDefault();
            if (button.type !== "button" || button.matches(":disabled") || !button.isConnected) return;
            for (let node = button; node && node !== this.form; node = node.parentElement) {
                if (node.hidden || node.hasAttribute("inert") || node.getAttribute("aria-disabled") === "true" ||
                    node.getAttribute("aria-hidden") === "true" || getComputedStyle(node).display === "none") return;
            }
            try {
                const row = this.get_form_context($(button));
                const action = Object.keys(CrudViewsFormset.const).find(key =>
                    button.matches(CrudViewsFormset.const[key])).replace("form_control_", "");
                const flags = row.formset;
                if (action === "add" && flags.edit_only) return;
                if (action === "delete" && (!flags.can_delete ||
                    (!flags.can_delete_extra && row.row_index >= flags.get_initial_forms()))) return;
                if ((action === "up" || action === "down") && !flags.can_order) return;
                row[action]();
            } catch (error) {
                this.debug("error", error);
            }
        };
        this.onSubmit = event => {
            if (event.defaultPrevented) return;
            try {
                if (!this.reorder_formsets()) event.preventDefault();
            } catch (error) {
                console.error("crud_views formset.js: reorder failed", error);
                event.preventDefault();
            }
        };
        form.addEventListener("click", this.onClick);
        // The owning-form listener runs before modal.js's document serializer.
        form.addEventListener("submit", this.onSubmit);
    }

    get_form_context(element) {
        return new XForm(this, element.attr(CVFSConst.attr.form_prefix));
    }

    // Internal compatibility seam. Delegation already covers newly inserted
    // descendants, including nested formsets with no separate row-added event.
    add_form_control_for_new_rows(rows) {
        rows.forEach(prefix => {
            const row = this.exact(CVFSConst.sel.row, CVFSConst.attr.form_prefix, prefix);
            globalThis.cv.initFormsets(row[0]);
        });
    }

    reorder_formsets() {
        this.sel(CVFSConst.sel.content).each((index, content) => {
            const formset = new XFormset(this, $(content).attr(CVFSConst.attr.formset_prefix));
            // Task 06-02 aggregates failures rather than losing each() returns.
            try {
                formset.reorder();
            } catch (error) {
                this.debug("error", error);
                return false;
            }
        });
        return true;
    }

    dispose() {
        this.form.removeEventListener("click", this.onClick);
        this.form.removeEventListener("submit", this.onSubmit);
        controllers.delete(this.form);
    }
}

// Internal test seams; cv.initFormsets is the supported public entry point.
globalThis.cv = globalThis.cv || {};
Object.assign(globalThis.cv, {CVFSConst, XBase, XFormset, XForm, CrudViewsFormset});

let retried = false;
let reported = false;

function owningForms(root) {
    const owners = new Set();
    if (root.matches?.("form")) owners.add(root);
    const owner = root.form || root.closest?.("form");
    if (owner) owners.add(owner);
    root.querySelectorAll("form").forEach(form => owners.add(form));
    return owners;
}

function initFormsets(root = document) {
    const owners = [...owningForms(root)].filter(form => form.querySelector(CVFSConst.sel.content));
    if (!owners.length) return;
    if (!globalThis.$?.fn?.jquery) {
        if (document.readyState !== "complete" && !retried) {
            retried = true;
            globalThis.addEventListener("load", () => initFormsets(document), {once: true});
        } else if (!reported) {
            reported = true;
            console.error("crud_views formset.js: pages with formsets need jQuery; load it before DOMContentLoaded.");
        }
        return;
    }
    owners.forEach(form => {
        if (!controllers.has(form)) new CrudViewsFormset(form);
    });
}

globalThis.cv.initFormsets = initFormsets;
document.addEventListener("DOMContentLoaded", () => initFormsets());
if (document.readyState !== "loading") initFormsets();
document.addEventListener("cv:modal:loaded", event => initFormsets(event.target));
document.addEventListener(CVFSConst.event.row_added, event => initFormsets(event.target));
document.addEventListener("cv:modal:unload", event => {
    owningForms(event.target).forEach(form => controllers.get(form)?.dispose());
});
})();
