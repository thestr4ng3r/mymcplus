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

import ctypes
uint8_t = ctypes.c_uint8
int16_t = ctypes.c_int16


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

        self.vertex_data = (int16_t * (3 * self.vertex_count))()
        self.normal_uv_data = (int16_t * (5 * self.vertex_count))()
        self.color_data = (uint8_t * (4 * self.vertex_count))()

        for i in range(self.vertex_count):
            offset = _icon_hdr_struct.size + i * stride
            d = data[offset:(offset + _vertex_coords_struct.size)]
            (self.vertex_data[i*3],
             self.vertex_data[i*3+1],
             self.vertex_data[i*3+2],
             _) = _vertex_coords_struct.unpack(d)

            offset += _vertex_coords_struct.size * self.animation_shapes
            d = data[offset:(offset + _normal_uv_color_struct.size)]
            (self.normal_uv_data[i*5],
             self.normal_uv_data[i*5+1],
             self.normal_uv_data[i*5+2],
             _,
             self.normal_uv_data[i*5+3],
             self.normal_uv_data[i*5+4],
             self.color_data[i*3],
             self.color_data[i*3+1],
             self.color_data[i*3+2],
             self.color_data[i*3+3]) = _normal_uv_color_struct.unpack(d)
