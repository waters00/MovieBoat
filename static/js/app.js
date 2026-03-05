document.addEventListener(
    "error",
    (event) => {
        const target = event.target;
        if (!(target instanceof HTMLImageElement)) {
            return;
        }
        const fallback = target.dataset.fallback;
        if (!fallback) {
            return;
        }
        if (target.src !== fallback) {
            target.src = fallback;
        }
    },
    true
);
