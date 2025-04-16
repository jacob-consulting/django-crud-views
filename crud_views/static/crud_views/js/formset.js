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
            throw msg;
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
            throw msg;
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

        let me = this;

        me.selection = this.sel(`${CVFSConst.sel.content}[${CVFSConst.attr.formset_prefix}="${prefix}"]`, "formset not found");
        me.json = me.selection.attr(CVFSConst.attr.formset_data);
        me.data = JSON.parse(me.json);

        // from data
        me.path = me.data.path
        me.key = me.data.key
        me.prefix = me.data.prefix
        me.prefix_key = me.data.prefix_key
        me.hierarchy = me.data.hierarchy
        me.parent_prefix = me.data.parent_prefix
        me.parent_prefix_key = me.data.parent_prefix_key
        me.can_delete = me.data.can_delete
        me.can_delete_extra = me.data.can_delete_extra
        me.can_order = me.data.can_order
        me.edit_only = me.data.edit_only
        me.fields = me.data.fields
        me.pk_field = me.data.pk_field

        // checks
        console.assert(me.prefix === prefix, "prefix mismatch");

        // calculated

        // primary key and index
        let pk_index_reg = RegExp(`^(.*)(None|${me.data.pk})-(\\d+)$`),
            pk_index_match = me.prefix_key.match(pk_index_reg).slice(-2),
            pk_index = pk_index_match.slice(-2),
            pk = pk_index[0] === "None" ? null : pk_index[0],
            index = parseInt(pk_index[1]);
        me.pk = pk;
        me.index = index;

        // rows
        me.rows = me.selection.find(`${CVFSConst.sel.row}[${CVFSConst.attr.formset_prefix}=${me.prefix}]`);
    }

    new() {
        return new XFormset(this.ctl, this.prefix);
    }

    get_management_form_value(key) {
        let selector = `input[name="${this.prefix}-${key}"]`,
            selection = this.sel(selector),
            value = selection.attr('value');
        return parseInt(value);
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

        let me = this,
            empty_fields = me.fields,
            pk_name = me.pk_field,
            empty_fields_check = empty_fields.concat([pk_name]),  // check all fields and pk
            delete_checkbox = true,  // todo: from json
            order_index = 1;

        // abort if formset is not ordered
        if (!me.can_order) {
            return;
        }

        // loop over all rows
        me.rows.each(function (rid, r) {

            let row = $(this);

            let inputs = row.find(`input[name^="${me.prefix}"]`, "no inputs found"),
                pk = me.assert_def(inputs.toArray().find(function (el) {
                    return el.name.endsWith(`-${pk_name}`)
                })),
                order = me.assert_def(inputs.toArray().find(function (el) {
                    return el.name.endsWith("-ORDER")
                })),
                // get delete input (maybe checkbox or hidden)
                del = me.assert_def(inputs.toArray().find(function (el) {
                    return el.name.endsWith("-DELETE")
                })),
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
                    throw "not implemented";
                }),
                all_empty = empty.every((el) => el),
                // is row deleted? (depends on input type)
                deleted = delete_checkbox ? del.checked : del.value === "on";

            // set order depending on visibility
            if (all_empty || deleted) {
                order.value = '';
            } else {
                order.value = order_index;
                order_index++;
            }

            me.debug("form", rid, fields, del, order, all_empty, deleted, order_index);
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

        let me = this;

        me.row = this.sel(`${CVFSConst.sel.row}[${CVFSConst.attr.form_prefix}="${prefix}"]`, "form not found");
        me.json = me.row.attr(CVFSConst.attr.form_data);
        me.data = JSON.parse(me.json);

        // from data
        me.key = me.data.key;
        me.prefix = me.data.prefix;
        me.prefix_key = me.data.prefix_key;
        me.formset_prefix = me.data.formset_prefix;

        // checks
        console.assert(me.prefix === prefix, "prefix mismatch");

        // init formset
        me.formset = new XFormset(ctl, me.formset_prefix);

        // calculated
        me.rows_total = me.formset.rows.length;
        me.row_index = me.formset.rows.index(me.row);
        me.row_is_first = me.row_index === 0;
        me.row_is_last = me.row_index === me.rows_total - 1;
        me.row_next = me.row_is_last ? null : me.formset.rows.eq(me.row_index + 1);
        me.row_previous = me.row_is_first ? null : me.formset.rows.eq(me.row_index - 1);
        me.row_last = me.formset.rows.last();

        // get delete input
        me.delete_input = me.formset.can_delete ? me.row.find(`input[name="${me.prefix}-DELETE"]`) : null;

        me.debug("form", me);
    }

    new() {
        let form = new XForm(this.ctl, this.prefix);
        return form;
    }

    add() {
        this.debug("add");

        let me = this,
            data = {
                template: me.formset.hierarchy.join("|"),
                pk: me.formset.pk === null ? "None" : me.formset.pk,
                num: me.formset.get_total_forms(),
                formset_parent_prefix_key: me.formset.parent_prefix_key
            }

        $.ajax({
            url: me.formset.path,       // the URL to send the request to
            type: "get",                // HTTP method (GET, POST, etc.)
            data: data,
            success: function (response) {    // Callback on success
                // insert row at right position
                let html = response.html,
                    rows = response.rows;
                if (me.row_is_last) {
                    me.row_last[0].insertAdjacentHTML("afterend", html);
                } else {
                    me.row_next[0].insertAdjacentHTML("beforebegin", html);
                }
                me.formset.increment_total_forms();
                me.reorder();
                me.ctl.add_form_control_for_new_rows(rows);

                // highlight created rows
                rows.forEach(function (row, index) {
                    console.log("highlight", row);
                    let hl = me.row.parent('div.cv-formset-content').find(`div.cv-formset-row[${CVFSConst.attr.form_prefix}="${row}"]`).find("input");
                    me.highlight_add(hl);
                });


            },
            error: function (xhr, status, error) {    // Callback on error
                me.debug('Error:', error);
            }
        });
    }

    /**
     * Reorder formset rows.
     * Note: we have to re-create the formset instance here after a modification.
     */
    reorder() {
        let me = this,
            new_form = me.new();
        new_form.formset.reorder();
    }

    /**
     * Get all input elements in form
     *
     * @returns {*}
     */
    get_inputs() {
        let me = this;
        return me.row.find(".cv-formset-form").first().find("input");
    }

    up() {
        let me = this,
            sel_highlight = me.get_inputs();
        me.debug("up");
        if (me.row_is_first) {
            return;
        }
        me.row[0].parentNode.insertBefore(me.row[0], me.row_previous[0])
        me.reorder();
        me.highlight_order(sel_highlight);
    }

    down() {
        let me = this,
            sel_highlight = me.get_inputs();
        me.debug("down");
        if (me.row_is_last) {
            return;
        }
        me.row_next[0].parentNode.insertBefore(me.row_next[0], me.row[0])
        me.reorder();
        me.highlight_order(sel_highlight);
    }

    delete() {
        this.debug("delete");
        let me = this,
            deleted = me.get_delete(),
            sel_highlight = me.get_inputs();

        // todo: toggle feature flag
        me.set_delete(!deleted);

        me.highlight_delete(sel_highlight);
    }

    get_delete() {
        let me = this;
        return me.delete_input.attr("value") === "1";
        // return this.delete_input.attr("checked") === "checked";
    }

    set_delete(value) {
        let me = this,
            btn = me.row.find(`button.cv-form-ctrl-delete[${CVFSConst.attr.form_prefix}="${me.prefix}"]`);
        if (value) {
            btn.removeClass("btn-light");
            btn.addClass("btn-danger");
        } else {
            btn.removeClass("btn-danger");
            btn.addClass("btn-light");
        }
        //this.delete_input.attr("checked", value);
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

        let me = this;

        me.add_form_control_events();
        me.sel(`form.cv-form`).on("submit", function (event) {
            me.debug("submit");
            var reorder_success = null;
            try {
                reorder_success = me.reorder_formsets();
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
        let me = this;

        rows.forEach(function (prefix, index) {
            let row_selection = me.sel(`${CVFSConst.sel.row}[${CVFSConst.attr.form_prefix}="${prefix}"]`, "row not found");
            me.add_form_control_events(row_selection);
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

        var me = this,
            context = typeof selection === "undefined" ? null : me.get_form_context(selection),
            can_delete = context ? context.formset.can_delete : true,
            can_order = context ? context.formset.can_order : true,
            edit_only = context ? context.formset.edit_only : false,
            sel = typeof selection === "undefined" ? me.sel(`form.cv-form`) : selection,
            del = can_delete ? me.sel_at(sel, CrudViewsFormset.const.form_control_delete, "delete not found") : null,
            add = edit_only === false ? me.sel_at(sel, CrudViewsFormset.const.form_control_add, "add not found") : null,
            up = can_order ? me.sel_at(sel, CrudViewsFormset.const.form_control_up, "up not found") : null,
            down = can_order ? me.sel_at(sel, CrudViewsFormset.const.form_control_down, "down not found") : null;

        if (del) {
            del.click(function (event) {
                try {
                    let form = me.get_form_context($(this));
                    form.delete();
                } catch (error) {
                    me.debug("error", error);
                }
                event.preventDefault();
            });
        }

        if (add) {
            add.click(function (event) {
                try {
                    let form = me.get_form_context($(this));
                    form.add();
                } catch (error) {
                    me.debug("error", error);
                }
                event.preventDefault();
            });
        }

        if (up) {
            up.click(function (event) {
                try {
                    let form = me.get_form_context($(this));
                    form.up();
                } catch (error) {
                    me.debug("error", error);
                }
                event.preventDefault();
            });
        }

        if (down) {
            down.click(function (event) {
                try {
                    let form = me.get_form_context($(this));
                    form.down();
                } catch (error) {
                    me.debug("error", error);
                }
                event.preventDefault();
            });
        }
    }

    /**
     * Reorder all formset
     */
    reorder_formsets() {
        let me = this;

        me.debug("reorder_formsets");

        me.sel(`form.cv-form`).find(CVFSConst.sel.content).each(function (index, content) {
            let formset = new XFormset(me, $(content).attr(CVFSConst.attr.formset_prefix));
            try {
                formset.reorder();
            } catch (error) {
                me.debug("error", error);
                return false;
            }
        });
        me.debug("reorder_formsets done");
        return true;
    }

}

