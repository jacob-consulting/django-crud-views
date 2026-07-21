export function modalSkeleton() {
    document.body.innerHTML = `
        <div id="cv-config" data-request-path="/books/" data-query-string="" data-csrf-token="test-token" hidden></div>
        <div class="modal fade" id="cv-modal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog" id="cv-modal-dialog">
                <div class="modal-content" id="cv-modal-content"></div>
            </div>
        </div>`;
}
