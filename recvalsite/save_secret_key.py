import sys
from pathlib import Path


def save_secret_key(key: str) -> str:
    """
    Saves the secret key to the .env file.
    """
    env_file_path = _get_env_file_path()

    print("Secret key does not exist; saving to", env_file_path, file=sys.stderr)
    with env_file_path.open("a", encoding="UTF-8") as env_file:
        env_file.write(f"SECRET_KEY={key}\n")

    return key


def _get_env_file_path() -> Path:
    """
    Return the path to the .env file at the root of the repository assuming this
    structure:

    ./
    ├── .env
    ├── Pipfile
    └── who/
        └── knows/
            └── save_secret_key.py

    """
    cur_dir = Path(__file__).parent
    while not (cur_dir / "Pipfile").is_file():
        if cur_dir.parent == cur_dir:
            raise Exception("Reached root without encountering Pipfile")
        cur_dir = cur_dir.parent

    return cur_dir / ".env"
