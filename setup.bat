@echo off

rem ensure pip is present
python3 -m ensurepip || echo Can't run ensurepip. It is now your responsibility to ensure that pip is present!!!

rem install setuptools
python3 -m pip install --user setuptools
python3 -m pip install --user setupext-janitor

rem install the 'kg' (and related) packages and dependencies.
python3 setup.py clean --all
python3 setup.py install || exit /b
python3 setup.py clean --all


rem also try installing for pypy3. (It should just skip if you don't have pypy3)
pypy3 --version >nul 2>&1 && (
    echo ATTEMPTING TO INSTALL ON pypy3
    pypy3 -m ensurepip
    pypy3 -m pip install --user setuptools
    pypy3 -m pip install --user setupext-janitor
    pypy3 setup.py clean --all
    pypy3 setup.py install || exit /b
    pypy3 setup.py clean --all
    echo INSTALLED ON pypy3
) || (
    echo NOT INSTALLING ON pypy3, pypy3 NOT FOUND.
)

echo DONE
