"use strict";
document.addEventListener('DOMContentLoaded', () => {
    let transcription = document.getElementById("id_transcription");
    let translation = document.getElementById("id_translation");
    transcription.value = "{{ issue.suggested_cree }}"
    translation.value = "{{ issue.suggested_english }}"
})
