// Exceptions thrown inside a DOM event listener never reach the dispatcher: the
// browser (and jsdom) report them as an "error" event on window instead, so
// `expect(() => el.click()).not.toThrow()` cannot see them. Run the dispatch
// through this helper and assert that the returned list is empty.
export function listenerErrors(fn) {
    const errors = [];
    const onError = (event) => {
        errors.push(event.error ?? event.message);
        event.preventDefault();
    };
    window.addEventListener("error", onError);
    try {
        fn();
    } finally {
        window.removeEventListener("error", onError);
    }
    return errors;
}
