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
                await response.json().then((r) => {
                    if (r['status'] === 'ok') {
                        if (judgement === 'yes') {
                            button.setAttribute("class", "button-success-solid translation-judgement-accuracy-yes")
                            

                        } else if (judgement === 'no') {
                            

                            button.setAttribute("class", "button-fail-solid translation-judgement-accuracy-no")
                        }
                    }
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
                            b.setAttribute("class", "button-fail translation-judgement-accuracy-no")
                        }
                    }

                    const headers = document.getElementsByClassName("card-top")
                    for (let h of headers) {
                        if (h.dataset.phraseId === phraseId) {
                            h.setAttribute("class", "card-top card-header-green")
                        }
                    }
                } else if (judgement === 'no') {
                    button.setAttribute("class", "button button--fail-solid translation-judgement-accuracy-no")
                    const yesButtons =  document.getElementsByClassName("translation-judgement-accuracy-yes");
                        for (let b of yesButtons) {
                            if (b.dataset.phraseId === phraseId) {
                                b.setAttribute("class", "button-success translation-judgement-accuracy-yes")
                            }
                        }

                            const headers = document.getElementsByClassName("card-top")
                        for (let h of headers) {
                            if (h.dataset.phraseId === phraseId) {
                                h.setAttribute("class", "card-top card-header-grey")
                            }
                        }
                    
                }
            })
        }
    }
})