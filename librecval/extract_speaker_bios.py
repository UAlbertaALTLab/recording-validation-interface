import os
from hashlib import sha256
from tempfile import TemporaryDirectory

from django.core.files.base import ContentFile
from pydub import AudioSegment
from pympi.Elan import Eaf
from pathlib import Path

from librecval.transcode_recording import transcode_to_aac
from validation.models import Speaker


def compute_sha256hash(speaker, start, text):
    signature = f"speaker: {speaker}\n" f"timestamp: {start}\n" f"{text}"
    return sha256(signature.encode("UTF-8")).hexdigest()


def get_wav_file(bio_num, bio_wav_files):
    for f in bio_wav_files:
        if bio_num in str(f):
            return f
    raise Exception(
        f"cannot find bio num {bio_num} in all of these files: {bio_wav_files}"
    )


def extract_speaker_bios():
    path_to_eaf_files = Path(
        "/Users/jolenepoulin/Documents/recording-validation-interface/data/speakers/biographies"
    )
    assert path_to_eaf_files.is_dir()
    bio_files = list(path_to_eaf_files.glob("*.eaf"))

    bio_wav_files = list(path_to_eaf_files.glob("*.wav"))
    for file in bio_files:
        # extract recordings
        # extract annotations
        speaker, bio_num = get_speaker_and_bio_num(file)
        wav_file = get_wav_file(bio_num, bio_wav_files)

        print(speaker)
        print(file)
        # open the EAF
        eaf_file = Eaf(file)

        start, stop, text = get_bio_cree(eaf_file)
        save_audio(wav_file, start, stop, text, "crk", speaker)
        start, stop, text = get_bio_english(eaf_file)
        save_audio(wav_file, start, stop, text, "eng", speaker)


def get_bio_cree(eaf_file):
    cree_tier = "Cree (sentence)"
    return parse_eaf(eaf_file, cree_tier)


def get_bio_english(eaf_file):
    english_tier = "English (sentence)"
    return parse_eaf(eaf_file, english_tier)


def parse_eaf(eaf_file, tier_name):
    tiers = eaf_file.get_tier_names()
    start_times = []
    stop_times = []
    text = ""
    if tier_name in tiers:
        # Extract data for Cree phrases
        phrases = eaf_file.get_annotation_data_for_tier(tier_name)
        for phrase in phrases:
            start_times.append(phrase[0])
            stop_times.append(phrase[1])
            text += (
                eaf_file.get_annotation_data_at_time(tier_name, phrase[0] + 1)[0][2]
                + " "
            )

        start = start_times[0]
        stop = stop_times[-1]
        print("Start: ", start)
        print("Stop: ", stop)
        print("Text: ", text)

        if start and stop and text:
            return start, stop, text
    else:
        return 0, 0, ""


def save_audio(wav_file, start, stop, text, language, speaker):
    audio = AudioSegment.from_wav(wav_file)

    sound_bite = audio[start:stop].normalize(headroom=0.1)
    print(sound_bite)

    rec_id = compute_sha256hash(speaker, start, text)
    with TemporaryDirectory() as audio_dir:
        # recording_path = Path(f"/Users/jolenepoulin/Documents/recording-validation-interface/data/speakers/biographies/{rec_id}.m4a")
        recording_path = Path(audio_dir) / (rec_id + ".m4a")

        transcode_to_aac(
            sound_bite,
            recording_path,
            tags=dict(
                title=text,
                artist=speaker,
                language=language,
            ),
        )

        audio_data = recording_path.read_bytes()
        django_file = ContentFile(audio_data, name=recording_path.name)

        # get speaker using speaker name/code
        # add bio to speaker
        speaker = Speaker.objects.get(full_name=speaker)
        if language == "crk":
            speaker.crk_bio_audio = django_file
            speaker.crk_bio_text = text
        if language == "eng":
            speaker.eng_bio_audio = django_file
            speaker.eng_bio_text = text

        speaker.save()


def get_speaker_and_bio_num(file):
    print(file)
    sections = str(file).split("/")
    file_name = sections[-1]
    file_name = file_name.split(".")[0]
    print("FILE NAME: ", file_name)
    name = file_name[file_name.index("(") + 1 : file_name.index(")")]

    bio_number = file_name[3:5]
    print("NUMBER: ", bio_number)
    return name, bio_number


if __name__ == "__main__":
    extract_speaker_bios()
