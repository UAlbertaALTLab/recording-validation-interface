from pympi.Elan import Eaf
from pathlib import Path


def extract_speaker_bios():
    path_to_eaf_files = Path("../data/speakers/biographies")
    assert path_to_eaf_files.is_dir()
    bio_files = list(path_to_eaf_files.glob("*.eaf"))
    for file in bio_files:
        # extract recordings
        # extract annotations
        print(file)
        # open the EAF
        eaf_file = Eaf(file)

        get_bio_cree(eaf_file)
        get_bio_english(eaf_file)


def get_bio_cree(eaf_file):
    cree_tier = "Cree (sentence)"
    parse_eaf(eaf_file, cree_tier)


def get_bio_english(eaf_file):
    english_tier = "English (sentence)"
    parse_eaf(eaf_file, english_tier)


def parse_eaf(eaf_file, tier_name):
    tiers = eaf_file.get_tier_names()
    if tier_name in tiers:
        # Extract data for Cree phrases
        phrases = eaf_file.get_annotation_data_for_tier(tier_name)
        for phrase in phrases:
            start = phrase[0]
            stop = phrase[1]
            translation = eaf_file.get_annotation_data_at_time(tier_name, start + 1)
            print("Start: ", start)
            print("Stop: ", stop)
            print("Translation: ", translation)


if __name__ == "__main__":
    extract_speaker_bios()
