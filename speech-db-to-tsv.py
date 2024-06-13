import sqlite3
import csv

DB_FILE = "production/db-in-folder.sqlite3"
OUTPUT_TSV_FILE = "speech-db-entries.tsv"
LANGUAGE_ID = 1  # for Maskwacis


def recording_dict(db_row):
    return {
        "id": db_row[0],
        "compressed_audio": db_row[1],
        "timestamp": db_row[2],
        "quality": db_row[3],
        "comment": db_row[4],
        "phrase_id": db_row[5],
        "session_id": db_row[6],
        "speaker_id": db_row[7],
        "wrong_speaker": db_row[8],
        "is_user_submitted": db_row[9],
        "is_best": db_row[10],
        "was_user_submitted": db_row[11],
    }


def phrase_dict(db_row):
    return {
        "id": db_row[0],
        "field_transcription": db_row[1],
        "transcription": db_row[2].strip(),
        "translation": db_row[3].strip(),
        "kind": db_row[4].lower(),
        "validated": db_row[5],
        "status": db_row[6],
        "origin": db_row[7],
        "fuzzy_transcription": db_row[8],
        "date": db_row[9],
        "analysis": db_row[10],
        "modifier": db_row[11],
    }


def collect_recordings(id, cur):
    query = f"SELECT * from validation_recording WHERE phrase_id={str(id)}"
    return [recording_dict(x) for x in cur.execute(query).fetchall()]


def collect_speakers(iter):
    return "; ".join([rec["speaker_id"] for rec in iter])


def generate_phrase(db_row, cur):
    phrase = phrase_dict(db_row)
    recordings = collect_recordings(phrase["id"], cur)
    phrase["recordings"] = recordings
    phrase["speakers_in_recordings"] = collect_speakers(recordings)
    phrase["best_recording_tagged_with_speakers"] = collect_speakers(
        [rec for rec in recordings if rec["is_best"] > 0]
    )
    phrase["good_recording_tagged_with_speakers"] = collect_speakers(
        [rec for rec in recordings if rec["quality"].lower() == "good"]
    )
    phrase["bad_recording_tagged_with_speakers"] = collect_speakers(
        [rec for rec in recordings if rec["quality"].lower() == "bad"]
    )
    phrase["unknown_quality_recording_tagged_with_speakers"] = collect_speakers(
        [rec for rec in recordings if rec["quality"].lower() == "unknown"]
    )
    return phrase


# open connections to database.
con = sqlite3.connect(DB_FILE)
cur = con.cursor()
cur2 = con.cursor()

# collect all varied domains, mostly to check what kind of data is in it.  Does not need to be used later.
qualities = set(
    [
        entry[0]
        for entry in cur.execute(
            "SELECT DISTINCT quality from validation_recording"
        ).fetchall()
    ]
)
speakers = set(
    [
        entry[0]
        for entry in cur.execute(
            "SELECT DISTINCT speaker_id from validation_recording"
        ).fetchall()
    ]
)
kinds = set(
    [
        entry[0].lower()
        for entry in cur.execute(
            "SELECT DISTINCT kind from validation_phrase"
        ).fetchall()
    ]
)
origins = set(
    [
        entry[0]
        for entry in cur.execute(
            "SELECT DISTINCT origin from validation_phrase"
        ).fetchall()
    ]
)


res = cur.execute(f"SELECT * from validation_phrase WHERE language_id={LANGUAGE_ID}")

print("Collecting dataset...")
dataset = [generate_phrase(phrase, cur2) for phrase in res.fetchall()]
print("Filtering only entries with transcription and translation...")
filtered_dataset = list(
    filter(lambda phrase: phrase["transcription"] and phrase["translation"], dataset)
)
print("Done. Sorting by transcription...")

# sort dataset by transcription
filtered_dataset.sort(key=lambda entry: entry["transcription"])

print("Done. Writing tsv...")

with open(OUTPUT_TSV_FILE, "w", newline="") as tsvfile:
    fieldnames = list(dataset[0].keys())
    # Do NOT add the recordings list.  Just the extra generated information based on them.
    fieldnames.remove("recordings")
    writer = csv.DictWriter(
        tsvfile,
        delimiter="\t",
        lineterminator="\n",
        fieldnames=fieldnames,
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(filtered_dataset)

print("finished.")

print(
    f"There were {len(dataset)-len(filtered_dataset)} phrase entries not included because they lack transcription or translation."
)
