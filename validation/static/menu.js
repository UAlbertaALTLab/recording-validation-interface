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

function showEmptyRW(option) {
    document.cookie = "empty-rw=" + option + "; SameSite=Lax;"
    let menu = document.getElementById("options-menu");
    menu.classList.add("menu__none");
    menu.classList.remove("menu__block");
    location.reload();
}

function showSuggestions(option) {
    document.cookie = "suggestions=" + option + "; SameSite=Lax;"
    let menu = document.getElementById("options-menu");
    menu.classList.add("menu__none");
    menu.classList.remove("menu__block");
    location.reload();
}