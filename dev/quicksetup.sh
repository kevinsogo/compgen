#!/bin/bash

set -e

pycommand=$1

if [ -z "$pycommand" ]; then
    pycommand=python3
fi

echo "Installing using python command '$pycommand'"
echo

if [ ! -x "$(command -v $pycommand)" ]; then
    echo "Command '$pycommand' not found!"
    exit 1
fi


# install kg only
$pycommand -m pip install --user .

echo
activate-global-python-argcomplete --user && echo "AUTOCOMPLETE READY" || echo "Skipping autocomplete"
echo "DONE"
