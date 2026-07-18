document.addEventListener("DOMContentLoaded", () => {
    if (window.anime) {
        anime({
            targets: ".page-content",
            opacity: [0, 1],
            translateY: [10, 0],
            duration: 450,
            easing: "easeOutQuad"
        });

        anime({
            targets: ".metric-tile, .panel",
            opacity: [0, 1],
            translateY: [8, 0],
            delay: anime.stagger(45),
            duration: 420,
            easing: "easeOutQuad"
        });
    } else {
        document.querySelectorAll(".page-content").forEach((item) => {
            item.style.opacity = 1;
        });
    }

    const encryptionType = document.querySelector("#encryptionType");
    const kmsField = document.querySelector("#kmsField");
    const updateKmsVisibility = () => {
        if (!encryptionType || !kmsField) {
            return;
        }
        kmsField.classList.toggle("d-none", encryptionType.value !== "aws:kms");
    };

    updateKmsVisibility();
    encryptionType?.addEventListener("change", updateKmsVisibility);
});
