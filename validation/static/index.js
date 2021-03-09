"use strict";

//    translation-judgement-accuracy-yes
document.addEventListener('DOMContentLoaded', () => {
    for (let judgement of ["yes", "no"]) {
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

                if (judgement === 'yes') {
                    button.setAttribute("class", "button button--success-solid translation-judgement-accuracy-yes")
                } else if (judgement === 'no') {
                    button.setAttribute("class", "button button--fail-solid translation-judgement-accuracy-no")
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

                let r = await response.json()

                if (r.status != 'ok') {
                    return
                }

                if (judgement === 'good') {
                    button.setAttribute("class", "button button--success-solid audio-quality-good")
                } else if (judgement === 'bad') {
                    button.setAttribute("class", "button button--fail-solid audio-quality-bad")
                }
            })
        }
    }
})