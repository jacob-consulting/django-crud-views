function cv_list_action_form_submit(cv_oid) {
    let form_name = 'cv_form_' + cv_oid,
        form = $('#' + form_name);
    form.submit();
    return false;
}