document.addEventListener("DOMContentLoaded", function () {
    const header = document.querySelector(".header");
    const logo = header.dataset.logo;

    const headerHTML = `
        <div class="logo">
            <img src="${logo}" alt="Shreko">
            <div>
                <h1>Shreko</h1>
            </div>
        </div>
    `;

    header.insertAdjacentHTML('beforeend', headerHTML);
});