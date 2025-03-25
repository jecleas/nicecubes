function toggleBlock(element) {
    element.classList.toggle('active');
}

document.querySelectorAll('.action-button').forEach((button, index) => {
    button.addEventListener('click', () => {
        const trayId = `tray${index + 1}`;
        document.querySelectorAll(`#${trayId} .ice-cube`).forEach(cube => {
            cube.classList.remove('active');
        });
    });
});