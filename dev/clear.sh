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


echo "This script attempts to uninstall KompGen if you've installed it via setup.py install before."
echo "Run this with sudo"


rm toremove_*.txt || :

$pycommand setup.py clean --all
$pycommand setup.py install --force --record toremove_1.txt
$pycommand setup.py clean --all
$pycommand setup.py install --force --record toremove_2.txt --user
$pycommand setup.py clean --all


read -p "This will delete all files listed in the toremove_*.txt files (Read them just to be sure). Proceed [yes/NO]? " choice
case "$choice" in 
    [yY][eE][sS] ) 
    echo "Proceeding with deletion..."
    for x in $(sort toremove_*.txt | uniq); do
        rm $x || rm -r $x || echo "$x not found..."
    done
    echo "Finished deleting. You may still be able to import 'kg', but it will be empty."
    echo "If you want to remove it completely, delete the corresponding KompGen* folders"
    echo "in the site-packages or dist-packages of your Python3 installations. Due to the"
    echo "way this script works, there may be up to two such locations. For example, I"
    echo "found them in:"
    echo
    echo "    - /usr/local/lib/py*3.*/dist-packages/KompGen-*.egg"
    echo "    - ~/.local/lib/py*3.*/site-packages/KompGen-*.egg"
    echo
    echo "The exact location probably depends on where '$pycommand' is installed."
    ;;
  * )
    echo "Not deleting them. Uninstall incomplete."
    ;;
esac
