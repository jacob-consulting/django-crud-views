$(document).ready(function () {

    // add event listener to the filter button
    $('#filter-button').click(function () {
        let expanded = $('#filter-button').attr('aria-expanded');
        $('#filter-form')[0].elements["filter_expanded"].value = expanded;
        setFilterExpanded(expanded);
    });

    // filter reset button: reset filter but keep sort
    $('#filter-button-reset').click(function () {
        let url = ViewSet.request.path,
            query_string = ViewSet.request.query_string,
            params = new URLSearchParams(query_string),
            reset_param = "reset_filter=true";
        if (params.has("sort")) {
            window.location.href = url + "?sort=" + params.get("sort") + "&" + reset_param;
        } else {
            window.location.href = url + "?" + reset_param;
        }
    });

    $("#cv-filter-toggle").click(function (event) {

        // toggle icon
        $(this).find('i').toggleClass(' fa-filter fa-filter-circle-xmark');

        // get vars
        let collapse = $('#filter-collapse'),
            visible = collapse.is(":visible"),
            form = $('#filter-form'),
            data = {
                filter_expanded: !visible,
            };

        console.log('visible', visible);

        $.post({
                url: ViewSet.request.path,
                headers: {"X-CSRFToken": csrftoken},
                contentType: "application/json; charset=utf-8",
                data: JSON.stringify(data),
            },
            function (data, status) {
                console.log("Data: " + data + "\nStatus: " + status);
            }
        );

        // console.log('cv_filter_toggle', isVisible, collapse, form);
        collapse.collapse("toggle");
        event.preventDefault();
    });
});
