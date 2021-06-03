"use strict";

document.addEventListener("DOMContentLoaded", () => {
    for (let button of document.querySelectorAll('[data-cy="wrong-word-button"]')) {
        button.addEventListener("click", async (e) => {
            const recordingId = e.target.dataset.recId;
            showWrongWordDiv(recordingId);
        })
    }

    for (let button of document.querySelectorAll('[data-cy="cancel-wrong-word-button"]')) {
        button.addEventListener("click", async (e) => {
            const recordingId = e.target.dataset.recId;
            hideWrongWordDiv(recordingId);
        })
    }
});


function showWrongWordDiv(recordingId) {
    const wrongWordDiv = getElementByRecordingId("rec-wrong-word", recordingId);
    wrongWordDiv.classList.replace("menu__none", "menu__block");
}

function hideWrongWordDiv(recordingId) {
    const wrongWordDiv = getElementByRecordingId("rec-wrong-word", recordingId);
    wrongWordDiv.classList.replace("menu__block", "menu__none");
}
