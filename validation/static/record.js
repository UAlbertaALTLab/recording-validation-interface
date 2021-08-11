"use strict";

var gumStream;      // stream from getUserMedia()
var rec;            // Recorder.js object
var input;          // MediaStreamAudioSourceNode
var AudioContext = window.AudioContext;
var audioContext = new AudioContext;
var recordButton = document.getElementById("recordButton");
var stopButton = document.getElementById("stopButton");
var pauseButton = document.getElementById("pauseButton");
var recordingsList = document.getElementById("recordingsList");

recordButton.addEventListener("click", startRecording)
stopButton.addEventListener("click", stopRecording)
pauseButton.addEventListener("click", pauseRecording)


function startRecording() {
    console.log("recordButton pressed")

    const constraints = {
        audio: true,
        video: false,
    }

    recordButton.disabled = true;
    stopButton.disabled = false;
    pauseButton.disabled = false;

    navigator.mediaDevices.getUserMedia(constraints).then(function (stream) {
        console.log("getUserMedia() success, stream created, initializing Recorder.js");
        gumStream = stream;
        input = audioContext.createMediaStreamSource(stream);
        rec = new Recorder(input);
        rec.record()
        console.log("Recording started");
    }).catch(function (err) {
        recordButton.disabled = false;
        stopButton.disabled = true;
        pauseButton.disabled = true;
    });
}

function pauseRecording() {
    console.log("pauseButton clicked rec.recording=", rec.recording);
    if (rec.recording) {
        rec.stop();
        pauseButton.innerHTML = "Resume";
    } else {
        rec.record()
        pauseButton.innerHTML = "Pause";
    }
}

function stopRecording() {
    console.log("stopButton clicked");
    stopButton.disabled = true;
    recordButton.disabled = false;
    pauseButton.disabled = true;

    pauseButton.innerHTML = "Pause";
    rec.stop();
    gumStream.getAudioTracks()[0].stop();
    rec.exportWAV(createDownloadLink);
}

function createDownloadLink(blob) {
    var url = URL.createObjectURL(blob);
    var au = document.createElement('audio');
    var li = document.createElement('li');
    var link = document.createElement('a');
    au.controls = true;
    au.src = url;

    link.href = url;
    link.download = new Date().toISOString() + '.wav'
    link.innerHTML = link.download;

    li.appendChild(au);
    li.appendChild(link);

    var filename = new Date().toISOString();
    var upload = document.createElement('a');
    upload.href = '#';
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

        console.log(response)
    })

    li.appendChild(document.createTextNode(" "));
    li.appendChild(upload);

    recordingsList.appendChild(li)
}
