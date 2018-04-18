# Source this before running flask run
RECVAL_SETTINGS="$(realpath "$(dirname "$0")")/local_settings.py"
export RECVAL_SETTINGS
