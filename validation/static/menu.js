"use strict";

document.addEventListener("DOMContentLoaded", () => {
    for (let link of document.querySelectorAll('[data-cy="show-flex-button"]')) {
        link.addEventListener("click", () => {
            showCircumflex("on");
        })
    }

    for (let link of document.querySelectorAll('[data-cy="no-flex-button"]')) {
        link.addEventListener("click", () => {
            showCircumflex("off");
        })
    }
})


function showCircumflex(option) {
    document.cookie = "macron=" + option + "; SameSite=Lax;"
    let menu = document.getElementById("options-menu");
    menu.classList.add("menu__none");
    menu.classList.remove("menu__block");
    location.reload();
}
