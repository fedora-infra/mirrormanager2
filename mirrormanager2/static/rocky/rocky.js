
let menuOpen = false;

const doMenuOpen = () => {
    menuOpen = !menuOpen;

    if (menuOpen) {
        document.getElementById('user-menu').classList.remove('hidden');
    } else {
        document.getElementById('user-menu').classList.add('hidden');
    }
}

document.getElementById('user-menu-button').onclick = doMenuOpen;

