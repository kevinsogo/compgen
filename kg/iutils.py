from sys import stdout
import os.path
import pathlib


def set_handler(parser, default_file=stdout):
    def _set_handler(handler):
        parser.set_defaults(handler=handler, default_file=default_file)
        # return handler # Let's not return this, to ensure that they are not called.
    return _set_handler


def touch_container(file):
    ''' ensures that the folder containing "file" exists, possibly creating the nested directory path to it '''
    touch_dir(os.path.dirname(file))


def touch_dir(dirname):
    if not os.path.exists(dirname): print('Creating folder:', dirname)
    pathlib.Path(dirname).mkdir(parents=True, exist_ok=True)