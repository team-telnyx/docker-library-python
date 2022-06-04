#!/bin/bash

set -o nounset
set -o errexit
set -o xtrace

SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
REPO_ROOT="$(dirname "$SCRIPT_PATH")"
VENV_DIR="${REPO_ROOT}/.venv"

flock --exclusive --timeout 15 "${SCRIPT_PATH}/pyvenv-bootstrap.sh" -c "bash \"${SCRIPT_PATH}/pyvenv-bootstrap.sh\""

# "$VENV_DIR/bin/python3" -m invoke $@
"$VENV_DIR/bin/python3" -m doit $@
