#
# This file is part of mymc+, based on mymc by Ross Ridge.
#
# mymc+ is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# mymc+ is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with mymc+.  If not, see <http://www.gnu.org/licenses/>.
#

"""A simple interface for working with various PS2 save file formats."""

import sys
import os
import binascii

from mymcplus.ps2mc_dir import *
from mymcplus.sjistab import shift_jis_normalize_table


from . import codebreaker, ems, max_drive, sharkport



class Error(Exception):
    """Base for all exceptions specific to this module."""
    pass


class Corrupt(Error):
    """Corrupt save file."""

    def __init__(self, msg, f = None):
        fn = None
        if f != None:
            fn = getattr(f, "name", None)
        self.filename = fn
        Error.__init__(self, "Corrupt save file: " + msg)


class Eof(Corrupt):
    """Save file is truncated."""

    def __init__(self, f = None):
        Corrupt.__init__(self, "Unexpected EOF", f)


class Subdir(Corrupt):
    def __init__(self, f = None):
        Corrupt.__init__(self, "Non-file in save file.", f)

#
# Table of graphically similar ASCII characters that can be used
# as substitutes for Unicode characters.
#
char_substs = {
    u'\u00a2': u"c",
    u'\u00b4': u"'",
    u'\u00d7': u"x",
    u'\u00f7': u"/",
    u'\u2010': u"-",
    u'\u2015': u"-",
    u'\u2018': u"'",
    u'\u2019': u"'",
    u'\u201c': u'"',
    u'\u201d': u'"',
    u'\u2032': u"'",
    u'\u2212': u"-",
    u'\u226a': u"<<",
    u'\u226b': u">>",
    u'\u2500': u"-",
    u'\u2501': u"-",
    u'\u2502': u"|",
    u'\u2503': u"|",
    u'\u250c': u"+",
    u'\u250f': u"+",
    u'\u2510': u"+",
    u'\u2513': u"+",
    u'\u2514': u"+",
    u'\u2517': u"+",
    u'\u2518': u"+",
    u'\u251b': u"+",
    u'\u251c': u"+",
    u'\u251d': u"+",
    u'\u2520': u"+",
    u'\u2523': u"+",
    u'\u2524': u"+",
    u'\u2525': u"+",
    u'\u2528': u"+",
    u'\u252b': u"+",
    u'\u252c': u"+",
    u'\u252f': u"+",
    u'\u2530': u"+",
    u'\u2533': u"+",
    u'\u2537': u"+",
    u'\u2538': u"+",
    u'\u253b': u"+",
    u'\u253c': u"+",
    u'\u253f': u"+",
    u'\u2542': u"+",
    u'\u254b': u"+",
    u'\u25a0': u"#",
    u'\u25a1': u"#",
    u'\u3001': u",",
    u'\u3002': u".",
    u'\u3003': u'"',
    u'\u3007': u'0',
    u'\u3008': u'<',
    u'\u3009': u'>',
    u'\u300a': u'<<',
    u'\u300b': u'>>',
    u'\u300a': u'<<',
    u'\u300b': u'>>',
    u'\u300c': u'[',
    u'\u300d': u']',
    u'\u300e': u'[',
    u'\u300f': u']',
    u'\u3010': u'[',
    u'\u3011': u']',
    u'\u3014': u'[',
    u'\u3015': u']',
    u'\u301c': u'~',
    u'\u30fc': u'-',
}



PS2SAVE_NPO_MAGIC = b"nPort"


def detect_file_type(f):
    """Detect the type of PS2 save file.

    The file-like object f should be positioned at the start of the file.
    """

    hdr = f.read(PS2MC_DIRENT_LENGTH * 3)
    if hdr[:12] == max_drive.PS2SAVE_MAX_MAGIC:
        return "max"
    if hdr[:17] == sharkport.PS2SAVE_SPS_MAGIC:
        return "sps"
    if hdr[:4] == codebreaker.PS2SAVE_CBS_MAGIC:
        return "cbs"
    if hdr[:5] == PS2SAVE_NPO_MAGIC:
        return "npo"
    #
    # EMS (.psu) save files don't have a magic number.  Check to
    # see if it looks enough like one.
    #
    if len(hdr) != PS2MC_DIRENT_LENGTH * 3:
        return None
    dirent = unpack_dirent(hdr[:PS2MC_DIRENT_LENGTH])
    dotent = unpack_dirent(hdr[PS2MC_DIRENT_LENGTH
                               : PS2MC_DIRENT_LENGTH * 2])
    dotdotent = unpack_dirent(hdr[PS2MC_DIRENT_LENGTH * 2:])
    if (mode_is_dir(dirent[0]) and mode_is_dir(dotent[0])
            and mode_is_dir(dotdotent[0]) and dirent[2] >= 2
            and dotent[8] == b"." and dotdotent[8] == b".."):
        return "psu"

    return None


def unpack_icon_sys(s):
    """Unpack an icon.sys file into a tuple."""

    # magic, title offset, ...
    # [14] title, normal icon, copy icon, del icon
    a = struct.unpack("<4s2xH4x"
                      "L" "16s16s16s16s" "16s16s16s" "16s16s16s" "16s"
                      "68s64s64s64s512x", s)
    a = list(a)
    for i in range(3, 7):
        a[i] = struct.unpack("<4L", a[i])
        a[i] = list(map(hex, a[i]))
    for i in range(7, 14):
        a[i] = struct.unpack("<4f", a[i])
    a[14] = zero_terminate(a[14])
    a[15] = zero_terminate(a[15])
    a[16] = zero_terminate(a[16])
    a[17] = zero_terminate(a[17])
    return a


def icon_sys_title(icon_sys, encoding=None):
    """Extract the two lines of the title stored in an icon.sys tuple."""

    offset = icon_sys[1]
    title = icon_sys[14]
    title2 = shift_jis_conv(title[offset:], encoding)
    title1 = shift_jis_conv(title[:offset], encoding)
    return (title1, title2)



#
# Set up tables of illegal and problematic characters in file names.
#
_bad_filename_chars = ("".join(map(chr, list(range(32))))
               + "".join(map(chr, list(range(127, 256)))))
_bad_filename_repl = "_" * len(_bad_filename_chars)

if os.name in ["nt", "os2", "ce"]:
    _bad_filename_chars += '<>:"/\\|'
    _bad_filename_repl +=  "()_'___"
    _bad_filename_chars2 = _bad_filename_chars + "?* "
    _bad_filename_repl2 = _bad_filename_repl +   "___"
else:
    _bad_filename_chars += "/"
    _bad_filename_repl += "_"
    _bad_filename_chars2 = _bad_filename_chars + "?*'&|:[<>] \\\""
    _bad_filename_repl2 = _bad_filename_repl +   "______(())___"

_filename_trans = str.maketrans(_bad_filename_chars, _bad_filename_repl)
_filename_trans2 = str.maketrans(_bad_filename_chars2, _bad_filename_repl2)


def fix_filename(filename):
    """Replace illegal or problematic characters from a filename."""
    return filename.translate(_filename_trans)


def make_longname(dirname, sf):
    """Return a string containing a verbose filename for a save file."""

    icon_sys = sf.get_icon_sys()
    title = ""
    if icon_sys is not None:
        title = icon_sys_title(icon_sys, "ascii")
        title = title[0] + " " + title[1]
        title = " ".join(title.split())
    crc = binascii.crc32(b"")
    for (ent, data) in sf:
        crc = binascii.crc32(data, crc)
    if len(dirname) >= 12 and (dirname[0:2] in ("BA", "BJ", "BE", "BK")):
        if dirname[2:6] == "DATA":
            title = ""
        else:
            #dirname = dirname[2:6] + dirname[7:12]
            dirname = dirname[2:12]

    return fix_filename("%s %s (%08X)" % (dirname, title, crc & 0xFFFFFFFF))



def shift_jis_conv(src, encoding = None):
    """Convert Shift-JIS strings to a graphically similar representation.

    If encoding is "unicode" then a Unicode string is returned, otherwise
    a string in the encoding specified is returned.  If necessary,
    graphically similar characters are used to replace characters not
    exactly    representable in the desired encoding.
    """
    
    if encoding == None:
        encoding = sys.getdefaultencoding()
    if encoding == "shift_jis":
        return src
    u = src.decode("shift_jis", "replace")
    if encoding == "unicode":
        return u
    a = []
    for uc in u:
        try:
            uc.encode(encoding)
            a.append(uc)
        except UnicodeError:
            for uc2 in shift_jis_normalize_table.get(uc, uc):
                a.append(char_substs.get(uc2, uc2))
    
    return "".join(a)




class ps2_save_file(object):
    """The state of a PlayStation 2 save file."""
    
    def __init__(self):
        self.file_ents = None
        self.file_data = None
        self.dirent = None
        self._defer_load_max_file = None

    def set_directory(self, ent, defer_file = None):
        self._defer_load_max_file = defer_file
        self._compressed = None
        self.file_ents = [None] * ent[2]
        self.file_data = [None] * ent[2]
        self.dirent = list(ent)

    def set_file(self, i, ent, data):
        self.file_ents[i] = ent
        self.file_data[i] = data

    def get_directory(self):
        return self.dirent

    def get_file(self, i):
        if self._defer_load_max_file is not None:
            f = self._defer_load_max_file
            self._defer_load_max_file = None
            max_drive.load2(self, f)
        return (self.file_ents[i], self.file_data[i])

    def __len__(self):
        return self.dirent[2]

    def __getitem__(self, index):
        return self.get_file(index)
    
    def get_icon_sys(self):
        for i in range(self.dirent[2]):
            (ent, data) = self.get_file(i)
            if ent[8].decode("ascii") == "icon.sys" and len(data) >= 964:
                return unpack_icon_sys(data[:964])
        return None

