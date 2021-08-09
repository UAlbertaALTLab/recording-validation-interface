"use strict";

URL = window.URL;
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

    var constraints = {
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
    recordButton.disables = false;
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
    upload.innerHTML = "Upload";
    upload.addEventListener("click", function(event) {
        var xhr = new XMLHttpRequest();
        xhr.onload = function(e) {
            if (this.readyState === 4) {
                console.log("Server returned: ", e.target.responseText);
            }
        };
        var fd = new FormData();
        fd.append("audio_data", blob, filename);
        xhr.open("POST", "/static/upload.php", true);
        xhr.send(fd);
    })

    li.appendChild(document.createTextNode(" "));
    li.appendChild(upload);

    recordingsList.appendChild(li)
}
