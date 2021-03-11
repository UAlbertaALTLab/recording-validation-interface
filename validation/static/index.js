"use strict";

//    translation-judgement-accuracy-yes
document.addEventListener('DOMContentLoaded', () => {
    for (let judgement of ["yes", "no"]) {
        for (let button of document.querySelectorAll(`.translation-judgement-accuracy-${judgement}`)) {
            button.addEventListener("click", async (e) => {
                const phraseId = e.target.dataset.phraseId

                const response = await fetch(`api/record_translation_judgement/${phraseId}`, {
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
                    button.setAttribute("class", "button button--fail-solid translation-judgement-accuracy-no")
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
                    
                }
            })
        }
    }
})