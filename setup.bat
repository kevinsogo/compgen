@echo off

rem ensure pip is present
python3 -m ensurepip || echo Can't run ensurepip. It is now your responsibility to ensure that python3 -m pip is present!!! Try using get-pip.py

rem install setuptools, pip, and kg
python3 -m pip install --user --upgrade setuptools
python3 -m pip install --user --upgrade pip
python3 -m pip install --user . || exit /b

echo DONE
