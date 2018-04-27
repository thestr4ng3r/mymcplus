
import struct
from . import ps2save

def read_fixed(f, n):
    """Read a string of a fixed length from a file."""

    s = f.read(n)
    if len(s) != n:
        raise ps2save.Eof(f)
    return s


def read_long_string(f):
    """Read a string prefixed with a 32-bit length from a file."""

    length = struct.unpack("<L", read_fixed(f, 4))[0]
    return read_fixed(f, length)