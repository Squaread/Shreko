document.addEventListener("DOMContentLoaded", function () {
    const footerHTML = `
        <p>Shreko © 2026 — Todos os larps reservados.</p>
    `;
    document.querySelector(".footer").insertAdjacentHTML('beforeend', footerHTML);
});