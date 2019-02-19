#!/bin/bash

set -e

python3 setup.py clean --all
python3 setup.py install --force --record toremove.txt
python3 setup.py clean --all

read -p "This will delete all files listed in toremove.txt (Read it just to be sure). Proceed [yes/NO]? " choice
case "$choice" in 
    [yY][eE][sS] ) 
    echo "Proceeding with deletion"
    for x in $(cat toremove.txt); do
        rm $x || echo "$x not found..."
    done
    echo "Done."
    ;;
  * )
    echo "Not deleting them. Uninstall incomplete."
    ;;
esac

# also try installing for pypy3. (It should just skip if you don't have pypy3)
if [ -x "$(command -v pypy3)" ]; then
    echo "ATTEMPTING TO UNINSTALL ON pypy3 (sudo)"
    sudo pypy3 setup.py clean --all
    sudo pypy3 setup.py install --force --record toremove.txt
    sudo pypy3 setup.py clean --all

    read -p "This will delete all files listed in toremove.txt (Read it just to be sure). Proceed [yes/NO]? " choice
    case "$choice" in 
        [yY][eE][sS] ) 
        echo "Proceeding with deletion"
        for x in $(cat toremove.txt); do
            sudo rm $x || echo "$x not found..."
        done
        echo "Done."
        ;;
      * )
        echo "Not deleting them. Uninstall incomplete."
        ;;
    esac
fi
