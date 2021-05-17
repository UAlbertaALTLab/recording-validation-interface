"use strict";

function getElementByPhraseId(className, phraseId) {
    const elements =  document.getElementsByClassName(className);
    for (let e of elements) {
        if (e.dataset.phraseId === phraseId) {
           return e
        }
    }
}

function getElementByRecordingId(className, recordingId) {
    const elements =  document.getElementsByClassName(className);
    for (let e of elements) {
        if (e.dataset.recId === recordingId) {
           return e
        }
    }
}
