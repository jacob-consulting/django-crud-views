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
        let selection = $(selector),
            message = msg || `${selector} not found`;
        return this.assert_sel(selection, message);
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

        this.selection = this.sel(`${CVFSConst.sel.content}[${CVFSConst.attr.formset_prefix}="${prefix}"]`, "formset not found");
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

        // primary key and index
        let pk_index_reg = new RegExp(String.raw`^(.*)(None|${this.data.pk})-(\d+)$`),
            pk_index_match = this.prefix_key.match(pk_index_reg).slice(-2),
            pk_index = pk_index_match.slice(-2),
            pk = pk_index[0] === "None" ? null : pk_index[0],
            index = Number.parseInt(pk_index[1]);
        this.pk = pk;
        this.index = index;

        // rows
        this.rows = this.selection.find(`${CVFSConst.sel.row}[${CVFSConst.attr.formset_prefix}=${this.prefix}]`);
    }

    new() {
        return new XFormset(this.ctl, this.prefix);
    }

    get_management_form_value(key) {
        let selector = `input[name="${this.prefix}-${key}"]`,
            selection = this.sel(selector),
            value = selection.attr('value');
        return Number.parseInt(value);
    }

    set_management_form_value(key, value) {
        let selector = `input[name="${this.prefix}-${key}"]`,
            selection = this.sel(selector);
        selection.attr('value', value);
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

            let inputs = row.find(`input[name^="${this.prefix}"]`, "no inputs found");

            // every row must carry its pk input
            this.assert_def(inputs.toArray().find((el) => el.name.endsWith(`-${pk_name}`)));

            let order = this.assert_def(inputs.toArray().find((el) => el.name.endsWith("-ORDER"))),
                // get delete input (maybe checkbox or hidden)
                del = this.assert_def(inputs.toArray().find((el) => el.name.endsWith("-DELETE"))),
                // get empty fields defined by suffix in options.empty_fields
                fields = inputs.toArray().filter((el) => {
                    let some = empty_fields_check.some((suffix) => {
                        return el.name.endsWith(`-${suffix}`);
                    });
                    return some;
                }),
                // are all fields empty?
                empty = fields.map((field) => {
                    if (field.type === "text" || field.type === "hidden") {
                        return field.value.trim() === "";
                    }
                    throw new Error("not implemented");
                }),
                all_empty = empty.every(Boolean),
                // is row deleted? (depends on input type)
                // DELETE may render as a hidden input (crud_views default, value "1"/"0")
                // or as Django's checkbox
                deleted = del.type === "checkbox" ? del.checked : del.value === "1";

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
        this.row = this.sel(`${CVFSConst.sel.row}[${CVFSConst.attr.form_prefix}="${prefix}"]`, "form not found");
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
        this.delete_input = this.formset.can_delete ? this.row.find(`input[name="${this.prefix}-DELETE"]`) : null;

        this.debug("form", this);
    }

    new() {
        let form = new XForm(this.ctl, this.prefix);
        return form;
    }

    add() {
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

                // highlight created rows
                rows.forEach((row) => {
                    console.log("highlight", row);
                    let hl = this.row.parent('div.cv-formset-content').find(`div.cv-formset-row[${CVFSConst.attr.form_prefix}="${row}"]`).find("input");
                    this.highlight_add(hl);
                });


            },
            error: (xhr, status, error) => {    // Callback on error
                this.debug('Error:', error);
            }
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

        // todo: toggle feature flag
        this.set_delete(!deleted);

        this.highlight_delete(sel_highlight);
    }

    get_delete() {
        return this.delete_input.attr("value") === "1";
    }

    set_delete(value) {
        let btn = this.row.find(`button.cv-form-ctrl-delete[${CVFSConst.attr.form_prefix}="${this.prefix}"]`);
        if (value) {
            btn.removeClass("btn-light");
            btn.addClass("btn-danger");
        } else {
            btn.removeClass("btn-danger");
            btn.addClass("btn-light");
        }
        this.delete_input.attr("value", value === true ? "1" : "0");
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

    constructor() {
        super();
        this.add_form_control_events();
        this.sel(`form.cv-form`).on("submit", (event) => {
            this.debug("submit");
            let reorder_success = null;
            try {
                reorder_success = this.reorder_formsets();
            } catch (error) {
                console.error("error", error.message);
                reorder_success = false;
            }
            if (!reorder_success) {
                event.preventDefault();
                return false;
            }
        });
    }

    /**
     * Get form context from element
     *
     * @param element
     * @returns {XForm}
     */
    get_form_context(element) {
        let form_prefix = element.attr(CVFSConst.attr.form_prefix),
            form = new XForm(this, form_prefix);
        return form;
    }

    /**
     * Attach form control events to new rows
     *
     * @param rows
     */
    add_form_control_for_new_rows(rows) {
        rows.forEach((prefix) => {
            let row_selection = this.sel(`${CVFSConst.sel.row}[${CVFSConst.attr.form_prefix}="${prefix}"]`, "row not found");
            this.add_form_control_events(row_selection);
        });
    }

    /**
     * Add form control events to
     * - selection
     * - or all form control elements
     *
     * @param selection
     */
    add_form_control_events(selection) {

        let is_global = selection === undefined,
            context = is_global ? null : this.get_form_context(selection),
            can_delete = context ? context.formset.can_delete : true,
            can_order = context ? context.formset.can_order : true,
            edit_only = context ? context.formset.edit_only : false,
            sel = is_global ? this.sel(`form.cv-form`) : selection,
            // On the global init pass `sel` spans every formset on the page, which may mix
            // orderable with non-orderable (or deletable with edit-only) formsets. A control
            // type can therefore be legitimately absent page-wide - e.g. a page whose only
            // formset is non-orderable has no up/down buttons. Look controls up WITHOUT
            // asserting in that case: binding a click handler to an empty jQuery set is a
            // harmless no-op, whereas the asserting sel_at would throw and abort the whole
            // controller, leaving even add/delete unbound. Per-row binding keeps the
            // asserting lookup since the row's own context guarantees the control exists.
            find = is_global ? (s) => sel.find(s) : (s, msg) => this.sel_at(sel, s, msg),
            del = can_delete ? find(CrudViewsFormset.const.form_control_delete, "delete not found") : null,
            add = edit_only === false ? find(CrudViewsFormset.const.form_control_add, "add not found") : null,
            up = can_order ? find(CrudViewsFormset.const.form_control_up, "up not found") : null,
            down = can_order ? find(CrudViewsFormset.const.form_control_down, "down not found") : null;

        if (del) {
            del.click((event) => {
                try {
                    let form = this.get_form_context($(event.currentTarget));
                    form.delete();
                } catch (error) {
                    this.debug("error", error);
                }
                event.preventDefault();
            });
        }

        if (add) {
            add.click((event) => {
                try {
                    let form = this.get_form_context($(event.currentTarget));
                    form.add();
                } catch (error) {
                    this.debug("error", error);
                }
                event.preventDefault();
            });
        }

        if (up) {
            up.click((event) => {
                try {
                    let form = this.get_form_context($(event.currentTarget));
                    form.up();
                } catch (error) {
                    this.debug("error", error);
                }
                event.preventDefault();
            });
        }

        if (down) {
            down.click((event) => {
                try {
                    let form = this.get_form_context($(event.currentTarget));
                    form.down();
                } catch (error) {
                    this.debug("error", error);
                }
                event.preventDefault();
            });
        }
    }

    /**
     * Reorder all formset
     */
    reorder_formsets() {
        this.debug("reorder_formsets");

        this.sel(`form.cv-form`).find(CVFSConst.sel.content).each((index, content) => {
            let formset = new XFormset(this, $(content).attr(CVFSConst.attr.formset_prefix));
            try {
                formset.reorder();
            } catch (error) {
                this.debug("error", error);
                return false;
            }
        });
        this.debug("reorder_formsets done");
        return true;
    }

}

// Test seam: expose the formset classes on a shared namespace. In the browser
// these are top-level lexical globals reachable by other classic scripts but
// not inspectable via globalThis; this adds namespaced access for the unit tests.
globalThis.cv = globalThis.cv || {};
Object.assign(globalThis.cv, {CVFSConst, XBase, XFormset, XForm, CrudViewsFormset});

$(function () {
    if (document.querySelector(".cv-formset-content")) {
        // the page's controller: its constructor binds all formset events
        globalThis.cv.formsetController = new CrudViewsFormset();
    }
});
