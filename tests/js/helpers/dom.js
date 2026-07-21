export function modalSkeleton() {
    document.body.innerHTML = `
        <div id="cv-config" data-request-path="/books/" data-query-string="" data-csrf-token="test-token" hidden></div>
        <div class="modal fade" id="cv-modal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog" id="cv-modal-dialog">
                <div class="modal-content" id="cv-modal-content"></div>
            </div>
        </div>`;
}

// formsetFixture()/rowHtml() mirror:
//   src/crud_views/templates/crud_views/formsets/formset.html (+ control.html)
//   JSON: XFormSet.data / XForm.data in src/crud_views/lib/formsets/render_tree.py
// Keep in sync when those change.
const FORMSET_DEFAULTS = {
    key: "book",
    pk: "None",
    index: 0,
    rows: 2,
    canOrder: true,
    canDelete: true,
    editOnly: false,
    fields: ["name"],
    pkField: "id",
    rowValues: null,
    rowDeleted: [],
};

export function formsetPrefix(opts = {}) {
    const o = { ...FORMSET_DEFAULTS, ...opts };
    return `${o.key}-${o.pk}-${o.index}`;
}

export function rowHtml(i, opts = {}) {
    const o = { ...FORMSET_DEFAULTS, ...opts };
    const prefix = formsetPrefix(o);
    const formPrefix = `${prefix}-${i}`;
    const value = o.rowValues?.[i] ?? `row ${i}`;
    const deleted = o.rowDeleted.includes(i) ? "1" : "0";
    const formData = JSON.stringify({
        key: o.key,
        prefix: formPrefix,
        prefix_key: `${o.pk}-${o.index}-${i}`,
        formset_prefix: prefix,
        pk: o.pk,
    });
    const orderInput = o.canOrder
        ? `<input type="hidden" name="${formPrefix}-ORDER" value="${i + 1}">`
        : "";
    const deleteInput = o.canDelete
        ? `<input type="hidden" name="${formPrefix}-DELETE" value="${deleted}">`
        : "";
    const orderButtons = o.canOrder
        ? `<button type="button" class="btn btn-light cv-form-ctrl-up" cv-data-formset-form-prefix="${formPrefix}"></button>
           <button type="button" class="btn btn-light cv-form-ctrl-down" cv-data-formset-form-prefix="${formPrefix}"></button>`
        : "";
    const addButton = o.editOnly
        ? ""
        : `<button type="button" class="btn btn-light cv-form-ctrl-add" cv-data-formset-form-prefix="${formPrefix}"></button>`;
    const deleteButton = o.canDelete
        ? `<button type="button" class="btn btn-light cv-form-ctrl-delete" cv-data-formset-form-prefix="${formPrefix}"></button>`
        : "";
    return `
        <div class="cv-formset-row" cv-data-formset-form='${formData}'
             cv-data-formset-prefix="${prefix}" cv-data-formset-form-prefix="${formPrefix}">
            <div class="cv-formset-form">
                <input type="hidden" name="${formPrefix}-${o.pkField}" value="">
                <input type="text" name="${formPrefix}-${o.fields[0]}" value="${value}">
                ${orderInput}
                ${deleteInput}
                <div class="cv-form-ctrl">${orderButtons}${addButton}${deleteButton}</div>
            </div>
        </div>`;
}

export function formsetFixture(opts = {}) {
    const o = { ...FORMSET_DEFAULTS, ...opts };
    const prefix = formsetPrefix(o);
    const data = JSON.stringify({
        key: o.key,
        prefix,
        prefix_key: `${o.pk}-${o.index}`,
        hierarchy: [o.key],
        parent_prefix: "",
        parent_prefix_key: "",
        can_delete: o.canDelete,
        can_delete_extra: true,
        can_order: o.canOrder,
        edit_only: o.editOnly,
        path: "/formset-rows/",
        fields: o.fields,
        pk_field: o.pkField,
        pk: o.pk,
    });
    const rowsHtml = Array.from({ length: o.rows }, (_, i) => rowHtml(i, o)).join("");
    document.body.innerHTML = `
        <form class="cv-form">
            <fieldset class="cv-formset-fieldset" cv-data-formset-key="${o.key}" cv-data-formset-prefix="${prefix}">
                <div class="cv-formset-content" cv-data-formset='${data}' cv-data-formset-prefix="${prefix}">
                    <input type="hidden" name="${prefix}-TOTAL_FORMS" value="${o.rows}">
                    <input type="hidden" name="${prefix}-INITIAL_FORMS" value="${o.rows}">
                    <input type="hidden" name="${prefix}-MIN_NUM_FORMS" value="0">
                    <input type="hidden" name="${prefix}-MAX_NUM_FORMS" value="1000">
                    ${rowsHtml}
                </div>
            </fieldset>
        </form>`;
    return { prefix };
}
