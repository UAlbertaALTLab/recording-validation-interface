"use strict";

document.addEventListener('DOMContentLoaded', () => {
    for (let button of document.querySelectorAll('[data-segment-name]')) {
        button.addEventListener("click", async (e) => {
            showDiv()
            const name = e.target.dataset.segmentName
            const translation = document.getElementById(name + '-translation').innerHTML;

            document.getElementById('id_cree').value = name;
            document.getElementById('id_translation').value = translation;
        })
    }

    for (let button of document.querySelectorAll('[data-cy="accept-button"], [data-cy="revert-button"]')) {
        button.addEventListener("click", async(e) => {
            showDiv()

            const transcription = e.target.dataset.transcription
            const translation = e.target.dataset.translation
            const analysis = e.target.dataset.analysis

            document.getElementById('id_cree').value = transcription;
            document.getElementById('id_translation').value = translation;
            document.getElementById('id_analysis').value = analysis;
        })
    }

    for (let button of document.querySelectorAll('[data-cy="cancel-button"]')) {
        button.addEventListener("click", async(e) => {
            document.getElementById('edit').style.display = "none";
        })
    }

    for (let button of document.querySelectorAll('[data-cy="back-button"]')) {
        button.addEventListener("click", async(e) => {
            window.history.back()
        })
    }
})


function showDiv() {
    document.getElementById('edit').style.display = "block";
    document.getElementById('id_cree').focus()
}
