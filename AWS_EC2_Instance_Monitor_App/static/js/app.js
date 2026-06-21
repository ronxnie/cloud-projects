document.addEventListener("DOMContentLoaded", () => {
    if (window.anime) {
        anime({
            targets: ".page-enter",
            opacity: [0, 1],
            translateY: [10, 0],
            easing: "easeOutQuad",
            duration: 420
        });

        anime({
            targets: ".instance-row, .metric, .panel",
            opacity: [0, 1],
            translateY: [8, 0],
            delay: anime.stagger(35),
            easing: "easeOutQuad",
            duration: 360
        });
    }

    document.querySelectorAll("form[data-confirm]").forEach((form) => {
        form.addEventListener("submit", (event) => {
            const message = form.getAttribute("data-confirm");
            if (message && !window.confirm(message)) {
                event.preventDefault();
            }
        });
    });

    document.querySelectorAll(".action-pulse").forEach((button) => {
        button.addEventListener("mouseenter", () => {
            if (!window.anime) {
                return;
            }
            anime({
                targets: button,
                scale: [1, 1.03],
                duration: 160,
                easing: "easeOutQuad"
            });
        });

        button.addEventListener("mouseleave", () => {
            if (!window.anime) {
                return;
            }
            anime({
                targets: button,
                scale: 1,
                duration: 160,
                easing: "easeOutQuad"
            });
        });
    });
});
