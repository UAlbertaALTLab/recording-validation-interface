"use strict";

document.addEventListener("DOMContentLoaded", () => {
    for (let b of document.querySelectorAll('[data-cy="go-button-nav"]')) {
        b.addEventListener("click", (e) => {
            let pageNo = document.querySelector('[data-cy="page-num-input"]').value;
            if (!pageNo) {
                return;
            }

            let searchParams = new URLSearchParams(window.location.search);
            searchParams.set("page", pageNo)
            window.location.search = searchParams.toString();
        })
    }
})
