function cvGetConfig() {
    var el = document.getElementById("cv-config");
    return {
        request: {
            path: el.dataset.requestPath,
            query_string: el.dataset.queryString,
        }
    };
}

$(document).ready(function () {
    // list action form submit via data-cv-action="submit-form"
    $(document).on("click", "[data-cv-action='submit-form']", function (e) {
        e.preventDefault();
        var targetId = $(this).attr("data-cv-target");
        $("#" + targetId).submit();
    });

    // cancel button navigation via data-cv-cancel-url
    $(document).on("click", "[data-cv-cancel-url]", function (e) {
        e.preventDefault();
        window.location.href = $(this).attr("data-cv-cancel-url");
    });
});
