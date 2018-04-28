
def zero_terminate(s):
    """Truncate a string at the first NUL ('\0') character, if any."""

    i = s.find(b'\0')
    if i == -1:
        return s
    return s[:i]