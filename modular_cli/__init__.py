import os
import sys


def get_entry_point() -> str:
    return os.path.basename(sys.argv[0] if sys.argv else 'modular-cli')


ENTRY_POINT = get_entry_point()
