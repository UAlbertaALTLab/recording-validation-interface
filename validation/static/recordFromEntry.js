"use strict";

// referencing: https://blog.addpipe.com/using-recorder-js-to-capture-wav-audio-in-your-html5-web-site/
try { lang = document.getElementById("language-span").dataset.lang; } catch { lang = ""; }

for (let recButton of recordButtons) {
    const phrase = recButton.dataset.phrase
    let stopButton = document.getElementById(`stopButton-${phrase}`);
    const transcription = document.getElementById(`transcription-span-${phrase}`).dataset.transcription
    const translation = document.getElementById(`translation-span-${phrase}`).dataset.translation
    recButton.addEventListener("click", (e) => {
        const constraints = {
            audio: true,
            video: false,
        }

        recButton.disabled = true;
        stopButton.disabled = false;

        navigator.mediaDevices.getUserMedia(constraints).then(function (stream) {
            gumStream = stream;
            input = audioContext.createMediaStreamSource(stream);
            rec = new Recorder(input);
            rec.record()
            recButton.innerHTML = "Recording...";
        }).catch(function (err) {
            recButton.disabled = false;
            stopButton.disabled = true;
        });
    });

    stopButton.addEventListener("click", (e) => {
        recButton.innerHTML = "Record";
        stopButton.disabled = true;
        recButton.disabled = false;

        rec.stop();
        gumStream.getAudioTracks()[0].stop();
        rec.exportWAV((blob) => {
            let url = URL.createObjectURL(blob);
            let au = document.createElement('audio');
            let li = document.createElement('li');
            au.controls = true;
            au.src = url;

            li.appendChild(au);

            let filename = new Date().toISOString();
            let upload = document.createElement('button');
            let location = window.location
            upload.href = '#';
            upload.classList.add("button");
            upload.classList.add("button--success");
            upload.classList.add("button--small");
            upload.innerHTML = "Save";
            upload.addEventListener("click", async function (event) {
                let fd = new FormData();
                fd.append("audio_data", blob, filename);
                fd.append("translation", translation)
                fd.append("transcription", transcription)
                fd.append("phrase", phrase)
                const response = await fetch(`/${lang}/record_audio_from_entry/${phrase}`, {
                    method: 'POST',
                    mode: 'same-origin',    // Do not send CSRF token to another domain.
                    headers: {
                        'X-CSRFToken': csrftoken
                    },
                    body: fd
                })

                if (parseInt(response.status) === 200) {
                    upload.innerHTML = "Saved &#x2713;";
                }

            })

            li.appendChild(document.createTextNode(" "));
            li.appendChild(upload);

            let recordingsList = document.getElementById(`recordingsList-${phrase}`);
            recordingsList.appendChild(li);
        });
    })
}
