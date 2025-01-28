function vs_list_action_form_submit(vs_oid) {
    let form_name = 'vs_form_' + vs_oid,
        form = $('#' + form_name);
    form.submit();
    return false;
}