"use strict";

// referencing: https://blog.addpipe.com/using-recorder-js-to-capture-wav-audio-in-your-html5-web-site/

let stopButton = document.getElementById("stopButton");
let recordingsList = document.getElementById("recordingsList");
let recNewEntryButton = document.getElementById("recNewEntryButton");
lang = document.getElementById("language-span").dataset.lang

recordButton.addEventListener("click", startRecording)
stopButton.addEventListener("click", stopRecording)
recNewEntryButton.addEventListener("click", reloadPage)


function reloadPage() {
    window.location.reload(true);
}


function startRecording() {
    const constraints = {
        audio: true,
        video: false,
    }

    recordButton.disabled = true;
    stopButton.disabled = false;

    navigator.mediaDevices.getUserMedia(constraints).then(function (stream) {
        gumStream = stream;
        input = audioContext.createMediaStreamSource(stream);
        rec = new Recorder(input);
        rec.record()
        recordButton.innerHTML = "Recording...";
    }).catch(function (err) {
        recordButton.disabled = false;
        stopButton.disabled = true;
    });
}

function pauseRecording() {
    if (rec.recording) {
        rec.stop();
    } else {
        rec.record()
    }
}

function stopRecording() {
    recordButton.innerHTML = "Record";
    stopButton.disabled = true;
    recordButton.disabled = false;

    rec.stop();
    gumStream.getAudioTracks()[0].stop();
    rec.exportWAV(createDownloadLink);
}

function createDownloadLink(blob) {
    let url = URL.createObjectURL(blob);
    let au = document.createElement('audio');
    let li = document.createElement('li');
    au.controls = true;
    au.src = url;

    li.appendChild(au);

    let filename = new Date().toISOString();
    let upload = document.createElement('button');
    upload.href = '#';
    upload.classList.add("button");
    upload.classList.add("button--success");
    upload.classList.add("button--small");
    upload.innerHTML = "Save";
    upload.addEventListener("click", async function(event) {
        let fd = new FormData();
        fd.append("audio_data", blob, filename);
        let translation = document.getElementById("id_translation").value
        let transcription = document.getElementById("id_transcription").value
        fd.append("translation", translation)
        fd.append("transcription", transcription)
        const response = await fetch(`/${lang}/record_audio`, {
            method: 'POST',
            mode: 'same-origin',    // Do not send CSRF token to another domain.
            headers: {
                'X-CSRFToken': csrftoken
            },
            body: fd
        })

        if (response.status == 200) {
            upload.innerHTML = "Saved &#x2713;";
        }

    })

    li.appendChild(document.createTextNode(" "));
    li.appendChild(upload);

    recordingsList.appendChild(li);
}
