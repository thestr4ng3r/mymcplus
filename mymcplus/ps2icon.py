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

"""Interface for working with PS2 icons."""

import struct
from array import array


class Error(Exception):
    """Base for all exceptions specific to this module."""
    pass

class Corrupt(Error):
    """Corrupt save file."""

    def __init__(self, msg):
        super().__init__(self, "Corrupt icon: " + msg)


_PS2_ICON_MAGIC = 0x010000

_FIXED_POINT_FACTOR = 4096.0

_icon_hdr_struct = struct.Struct("<IIIII")

_vertex_coords_struct = struct.Struct("<hhhH")
_normal_uv_color_struct = struct.Struct("<hhhHhhBBBB")

def unpack_icon_hdr(s):
    return _icon_hdr_struct.unpack(s[:20])


def pack_icon_hdr(icon):
    return _icon_hdr_struct.pack(icon)


class Icon:
    def __init__(self, data):
        length = len(data)

        if length < _icon_hdr_struct.size:
            raise Corrupt("File too small.")

        (magic, self.animation_shapes, self.tex_type, _, self.vertex_count) = unpack_icon_hdr(data[:_icon_hdr_struct.size])

        if magic != _PS2_ICON_MAGIC:
            raise Corrupt("Invalid magic.")

        stride = _vertex_coords_struct.size * self.animation_shapes \
                 + _normal_uv_color_struct.size

        if length < _icon_hdr_struct.size + self.vertex_count * stride:
            raise Corrupt("File too small.")

        self.vertex_data = array("f")
        self.normal_uv_data = array("f")
        self.color_data = array("B")

        for i in range(self.vertex_count):
            offset = _icon_hdr_struct.size + i * stride
            d = data[offset:(offset + _vertex_coords_struct.size)]
            (x, y, z, _) = _vertex_coords_struct.unpack(d)

            offset += _vertex_coords_struct.size * self.animation_shapes
            d = data[offset:(offset + _normal_uv_color_struct.size)]
            (nx, ny, nz, _, u, v, r, g, b, a) = _normal_uv_color_struct.unpack(d)

            self.vertex_data.extend([x / _FIXED_POINT_FACTOR, y / _FIXED_POINT_FACTOR, z / _FIXED_POINT_FACTOR])
            self.normal_uv_data.extend([nx, ny, nz, u, v])
            self.color_data.extend([r, g, b, a])
