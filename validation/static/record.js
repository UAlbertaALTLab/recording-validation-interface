"use strict";

let gumStream;      // stream from getUserMedia()
let rec;            // Recorder.js object
let input;          // MediaStreamAudioSourceNode
const AudioContext = window.AudioContext;
let audioContext = new AudioContext;
let recordButton = document.getElementById("recordButton");
let stopButton = document.getElementById("stopButton");
// TODO: do we want a pause button??
// let pauseButton = document.getElementById("pauseButton");
let recordingsList = document.getElementById("recordingsList");
let recNewEntryButton = document.getElementById("recNewEntryButton");

recordButton.addEventListener("click", startRecording)
stopButton.addEventListener("click", stopRecording)
// pauseButton.addEventListener("click", pauseRecording)
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
    // pauseButton.disabled = false;

    navigator.mediaDevices.getUserMedia(constraints).then(function (stream) {
        gumStream = stream;
        input = audioContext.createMediaStreamSource(stream);
        rec = new Recorder(input);
        rec.record()
        recordButton.innerHTML = "Recording...";
    }).catch(function (err) {
        recordButton.disabled = false;
        stopButton.disabled = true;
        // pauseButton.disabled = true;
    });
}

function pauseRecording() {
    if (rec.recording) {
        rec.stop();
        // pauseButton.innerHTML = "Resume";
    } else {
        rec.record()
        // pauseButton.innerHTML = "Pause";
    }
}

function stopRecording() {
    recordButton.innerHTML = "Record";
    stopButton.disabled = true;
    recordButton.disabled = false;
    // pauseButton.disabled = true;

    // pauseButton.innerHTML = "Pause";
    rec.stop();
    gumStream.getAudioTracks()[0].stop();
    rec.exportWAV(createDownloadLink);
}

function createDownloadLink(blob) {
    let url = URL.createObjectURL(blob);
    let au = document.createElement('audio');
    let li = document.createElement('li');
    // let dlButton = document.createElement('button');     // Button to download audio--not sure if we want this feature
    au.controls = true;
    au.src = url;

    // dlButton.classList.add("button");
    // dlButton.classList.add("button--success");
    // dlButton.classList.add("button--small");
    // dlButton.href = url;
    // dlButton.download = new Date().toISOString() + '.wav'
    // dlButton.innerHTML = "Download";

    li.appendChild(au);
    // li.appendChild(dlButton);

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
        const response = await fetch(`/secrets/record_audio`, {
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
