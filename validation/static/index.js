"use strict";

//    translation-judgement-accuracy-yes
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

                if (judgement === 'yes') {
                    button.classList.add("button--success-solid")
                    button.classList.remove("button--success")
                    
                    const noButtons =  document.getElementsByClassName("translation-judgement-accuracy-no");
                    for (let b of noButtons) {
                        if (b.dataset.phraseId === phraseId) {
                            b.classList.remove('button--fail-solid')
                            b.classList.add('button--fail')
                        }
                    }

                    const headers = document.getElementsByClassName("card__header")
                    for (let h of headers) {
                        if (h.dataset.phraseId === phraseId) {
                            h.classList.remove("card__header--grey")
                            h.classList.add("card__header--green")
                        }
                    }

                } else if (judgement === 'no') {
                    button.classList.add("button--fail-solid")
                    button.classList.remove("button--fail")
                    const yesButtons =  document.getElementsByClassName("translation-judgement-accuracy-yes");
                    for (let b of yesButtons) {
                        if (b.dataset.phraseId === phraseId) {
                            b.classList.remove('button--success-solid')
                            b.classList.add('button--success')
                        }
                    }

                    const headers = document.getElementsByClassName("card__header")
                    for (let h of headers) {
                        if (h.dataset.phraseId === phraseId) {
                            h.classList.remove('card__header--green')
                            h.classList.add('card__header--grey')
                        }
                    }
                    
                } else if (judgement === "idk") {
                    const yesButtons =  document.getElementsByClassName("translation-judgement-accuracy-yes");
                    for (let b of yesButtons) {
                        if (b.dataset.phraseId === phraseId) {
                            b.classList.remove('button--success-solid')
                            b.classList.add('button--success')
                        }
                    }

                    const noButtons =  document.getElementsByClassName("translation-judgement-accuracy-no");
                    for (let b of noButtons) {
                        if (b.dataset.phraseId === phraseId) {
                            b.classList.remove('button--fail-solid')
                            b.classList.add('button--fail')
                        }
                    }

                    const headers = document.getElementsByClassName("card__header")
                    for (let h of headers) {
                        if (h.dataset.phraseId === phraseId) {
                            h.classList.remove('card__header--green')
                            h.classList.add('card__header--grey')
                        }
                    }

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
                    button.classList.remove('button--success')
                    button.classList.add('button--success-solid')

                    const badButtons =  document.getElementsByClassName("audio-quality-bad");
                    for (let b of badButtons) {
                        if (b.dataset.recId === recordingId) {
                            b.classList.remove('button--fail-solid')
                            b.classList.add('button--fail')
                        }
                    }
                } else if (judgement === 'bad') {
                    button.classList.remove('button--fail')
                    button.classList.add('button--fail-solid')

                    const goodButtons =  document.getElementsByClassName("audio-quality-good");
                    for (let b of goodButtons) {
                        if (b.dataset.recId === recordingId) {
                            b.classList.remove('button--success-solid')
                            b.classList.add('button--success')
                        }
                    }
                
                }
        })
    }
}
})