"use strict";

//    translation-judgement-accuracy-yes
document.addEventListener('DOMContentLoaded', () => {
    console.log("hello")
    console.log(csrftoken)
    for (let judgement of ["yes", "no"]) {
        for (let button of document.querySelectorAll(`.translation-judgement-accuracy-${judgement}`)) {
            button.addEventListener("click", async (e) => {
                console.log("You clicked on", e)
                console.log(e.target.dataset.phraseId)
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
                    console.log(r['status'])
                    if (r['status'] === 'ok') {
                        if (judgement === 'yes') {
                            button.setAttribute("class", "button-success-solid translation-judgement-accuracy-yes")

                        } else if (judgement === 'no') {
                            button.setAttribute("class", "button-fail-solid translation-judgement-accuracy-yes")
                        }
                    }
                })
            })
        }
    }
})