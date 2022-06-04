#!/bin/bash

set -o nounset
set -o errexit

SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
REPO_ROOT="$(dirname "$SCRIPT_PATH")"
VENV_DIR="${REPO_ROOT}/.venv"
VENV_DATA="${REPO_ROOT}/venv"
REQUIREMENTS="${REPO_ROOT}/requirements.txt"

# if doesn't exist, or not a directory, or requirements newer...
if [ ! -e "${VENV_DIR}" ] \
    || [ ! -d "${VENV_DIR}" ] \
    || [ "${REQUIREMENTS}" -nt "${VENV_DIR}" ]
then
    # creating venv
    rm -rf "${VENV_DIR}"
    python3 -m venv "${VENV_DIR}"
    "${VENV_DIR}/bin/python3" -m pip install -r "${REQUIREMENTS}"
fi
