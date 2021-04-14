"use strict";

function showMenu() {
    let menu = document.getElementById("options-menu");
    if (menu.classList.contains("menu__none")) {
        menu.classList.remove("menu__none");
        menu.classList.add("menu__block");
    } else {
        menu.classList.add("menu__none");
        menu.classList.remove("menu__block");
    }
}

function showMacron(option) {
    document.cookie = "macron=" + option + "; SameSite=Lax;"
    let menu = document.getElementById("options-menu");
    menu.classList.add("menu__none");
    menu.classList.remove("menu__block");
    location.reload();
}
