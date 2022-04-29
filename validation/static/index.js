"use strict";

// Vars for recording from an entry
let gumStream;      // stream from getUserMedia()
let rec;            // Recorder.js object
let input;          // MediaStreamAudioSourceNode
let recordButtons = document.getElementsByClassName(`recordButton`);
const audioContext = new AudioContext();
let lang;


document.addEventListener('DOMContentLoaded', () => {
    for (let judgement of ["yes", "no", "idk"]) {
        for (let button of document.querySelectorAll(`.translation-judgement-accuracy-${judgement}`)) {
            button.addEventListener("click", async (e) => {
                const phraseId = e.target.dataset.phraseId

                const response = await fetch(`/api/record_translation_judgement/${phraseId}`, {
                    method: 'POST',
                    mode: 'same-origin',    // Do not send CSRF token to another domain.
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken
                    },
                    body: JSON.stringify({judgement})
                })

                let r = await response.json()

                if (r.status != 'ok') {
                    return
                }

                const header = getElementByPhraseId("card__header", phraseId)
                const noButton = getElementByPhraseId("translation-judgement-accuracy-no", phraseId)
                const yesButton = getElementByPhraseId("translation-judgement-accuracy-yes", phraseId);
                const idkButton = getElementByPhraseId("translation-judgement-accuracy-idk", phraseId);

                if (judgement === 'yes') {
                    button.classList.replace("button--success", "button--success-solid")

                    noButton.classList.replace("button--fail-solid", "button--fail")
                    idkButton.classList.replace("button--neutral-solid", "button--neutral")

                    header.classList.remove("card__header--red")
                    header.classList.remove("card__header--grey")
                    header.classList.add("card__header--green")

                } else if (judgement === 'no') {
                    button.classList.replace("button--fail", "button--fail-solid")

                    yesButton.classList.replace("button--success-solid", "button--success")
                    idkButton.classList.replace("button--neutral-solid", "button--neutral")

                    header.classList.remove('card__header--green')
                    header.classList.remove("card__header--grey")
                    header.classList.add("card__header--red")

                } else if (judgement === "idk") {
                    button.classList.replace("button--neutral", "button--neutral-solid")

                    yesButton.classList.replace("button--success-solid", "button--success")
                    noButton.classList.replace("button--fail-solid", "button--fail")

                    header.classList.remove('card__header--green')
                    header.classList.remove("card__header--red")
                    header.classList.add("card__header--grey")

                }
            })
        }
    }

    for (let judgement of ["good", "bad"]) {
        for (let button of document.querySelectorAll(`.audio-quality-${judgement}`)) {
            button.addEventListener("click", async (e) => {
                const recordingId = e.target.dataset.recId

                const response = await fetch(`/api/record_audio_quality_judgement/${recordingId}`, {
                    method: 'POST',
                    mode: 'same-origin',    // Do not send CSRF token to another domain.
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken
                    },
                    body: JSON.stringify({judgement})
                })

                let r = await response.json();

                if (r.status !== 'ok') {
                    return
                }

                const goodButton = getElementByRecordingId("audio-quality-good", recordingId);
                const badButton = getElementByRecordingId("audio-quality-bad", recordingId);
                const wrongWordButton = getElementByRecordingId("wrong-word-button", recordingId);
                const wrongSpeakerButton = getElementByRecordingId("wrong-speaker-button", recordingId);

                wrongWordButton.classList.replace("button--neutral-solid", "button--neutral")
                wrongSpeakerButton.classList.replace("button--neutral-solid", "button--neutral")

                if (judgement === 'good') {
                    button.classList.replace("button--success", "button--success-solid")
                    badButton.classList.replace("button--fail-solid", "button--fail")
                } else if (judgement === 'bad') {
                    button.classList.replace("button--fail", "button--fail-solid")
                    goodButton.classList.replace("button--success-solid", "button--success")
                }
            })
        }
    }

    for (let button of document.querySelectorAll(`[data-cy="is-best"]`)) {
        button.addEventListener("click", async (e) => {
            const recordingId = e.target.dataset.recordingId;
            const phraseId = e.target.dataset.phraseIdBest;

            const response = await fetch(`/api/record_audio_is_best/${recordingId}`, {
                method: 'POST',
                mode: 'same-origin',    // Do not send CSRF token to another domain.
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({phraseId})
            });

            let r = await response.json();

            if (r.status !== 'ok') {
                return
            }

            // const bestElement = document.querySelector(`[data-recording-id='${recordingId}']`)
            const otherElements = document.querySelectorAll(`[data-phrase-id-best='${phraseId}']`)

            for (let el of otherElements) {
                el.innerHTML = "&#9734;";
            }

            if (r.set_solid) {
                e.target.innerHTML = "&#9733;";
            } else {
                e.target.innerHTML = "&#9734;";
            }
        })
    }

    for (let button of document.querySelectorAll(`[data-cy="approve-button"]`)) {
        button.addEventListener("click", async (e) => {
            const phraseId = e.target.dataset.phraseId;

            const response = await fetch(`/api/approve_user_phrase/${phraseId}`, {
                method: 'POST',
                mode: 'same-origin',    // Do not send CSRF token to another domain.
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({phraseId})
            });

            let r = await response.json();

            if (r.status !== 'ok') {
                return
            }
            e.target.innerHTML = "Approved"
        })
    }
})

function showWrongWordDiv(recordingId) {
    const wrongWordDiv = getElementByRecordingId("rec-wrong-word", recordingId);
    wrongWordDiv.classList.replace("menu__none", "menu__block");
}

function hideWrongWordDiv(recordingId) {
    const wrongWordDiv = getElementByRecordingId("rec-wrong-word", recordingId);
    wrongWordDiv.classList.replace("menu__block", "menu__none");
}

function getElementByPhraseId(className, phraseId) {
    const elements = document.getElementsByClassName(className);
    for (let e of elements) {
        if (e.dataset.phraseId === phraseId) {
            return e
        }
    }
}

function getElementByRecordingId(className, recordingId) {
    const elements = document.getElementsByClassName(className);
    for (let e of elements) {
        if (e.dataset.recId === recordingId) {
            return e
        }
    }
}
