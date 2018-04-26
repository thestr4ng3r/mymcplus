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
    """Corrupt icon file."""

    def __init__(self, msg):
        super().__init__(self, "Corrupt icon: " + msg)


_PS2_ICON_MAGIC = 0x010000

_FIXED_POINT_FACTOR = 4096.0


TEXTURE_WIDTH = 128
TEXTURE_HEIGHT = 128

_TEXTURE_SIZE = TEXTURE_WIDTH * TEXTURE_HEIGHT * 2

_icon_hdr_struct = struct.Struct("<IIIII")

_vertex_coords_struct = struct.Struct("<hhhH")
_normal_uv_color_struct = struct.Struct("<hhhHhhBBBB")

_anim_hdr_struct = struct.Struct("<IIfII")
_frame_data_struct = struct.Struct("<IIII")
_frame_key_struct = struct.Struct("<ff")

import ctypes
uint8_t = ctypes.c_uint8
int16_t = ctypes.c_int16


class Icon:
    class Frame:
        class Key:
            def __init__(self):
                self.time = 0.0
                self.value = 0.0
        def __init__(self):
            self.shape_id = 0
            self.keys = []


    def __init__(self, data):
        self.animation_shapes = 0
        self.tex_type = 0
        self.vertex_count = 0
        self.vertex_data = None
        self.normal_uv_data = None
        self.color_data = None
        self.frame_length = 0
        self.anim_speed = 0.0
        self.play_offset = 0
        self.frame_count = 0
        self.texture = None

        length = len(data)
        offset = 0

        offset = self.__load_header(data, length, offset)
        offset = self.__load_vertex_data(data, length, offset)
        offset = self.__load_animation_data(data, length, offset)
        offset = self.__load_texture(data, length, offset)

        if length > offset:
            print("Warning: Icon file larger than expected.")


    def __load_header(self, data, length, offset):
        if length < _icon_hdr_struct.size:
            raise Corrupt("File too small.")

        (magic,
         self.animation_shapes,
         self.tex_type,
         _,
         self.vertex_count) = _icon_hdr_struct.unpack_from(data, offset)

        if magic != _PS2_ICON_MAGIC:
            raise Corrupt("Invalid magic.")

        return offset + _icon_hdr_struct.size


    def __load_vertex_data(self, data, length, offset):
        stride = _vertex_coords_struct.size * self.animation_shapes \
                 + _normal_uv_color_struct.size

        if length < offset + self.vertex_count * stride:
            raise Corrupt("File too small.")

        self.vertex_data = (int16_t * (3 * self.vertex_count))()
        self.normal_uv_data = (int16_t * (5 * self.vertex_count))()
        self.color_data = (uint8_t * (4 * self.vertex_count))()

        for i in range(self.vertex_count):
            (self.vertex_data[i*3],
             self.vertex_data[i*3+1],
             self.vertex_data[i*3+2],
             _) = _vertex_coords_struct.unpack_from(data, offset)

            # TODO: read all shapes

            offset += _vertex_coords_struct.size * self.animation_shapes

            (self.normal_uv_data[i*5],
             self.normal_uv_data[i*5+1],
             self.normal_uv_data[i*5+2],
             _,
             self.normal_uv_data[i*5+3],
             self.normal_uv_data[i*5+4],
             self.color_data[i*4],
             self.color_data[i*4+1],
             self.color_data[i*4+2],
             self.color_data[i*4+3]) = _normal_uv_color_struct.unpack_from(data, offset)

            offset += _normal_uv_color_struct.size

        return offset


    def __load_animation_data(self, data, length, offset):
        if length < offset + _anim_hdr_struct.size:
            raise Corrupt("File too small.")

        (anim_id_tag,
         self.frame_length,
         self.anim_speed,
         self.play_offset,
         self.frame_count) = _anim_hdr_struct.unpack_from(data, offset)

        offset += _anim_hdr_struct.size

        if anim_id_tag != 0x01:
            raise Corrupt("Invalid ID tag in animation header: {:#x}".format(anim_id_tag))

        self.frames = []
        for i in range(self.frame_count):
            if length < offset + _frame_data_struct.size:
                raise Corrupt("File too small.")

            frame = self.Frame()
            (frame.shape_id,
             key_count,
             _,
             _) = _frame_data_struct.unpack_from(data, offset)

            key_count -= 1 # TODO: why? see https://github.com/ticky/ps2icon/blob/25f5daa4b4e8c77ef86f81470308cffd659228b5/ps2icon.c#L145

            offset += _frame_data_struct.size

            for k in range(key_count):
                if length < offset + _frame_key_struct.size:
                    raise Corrupt("File too small.")

                key = self.Frame.Key()
                (key.time,
                 key.value) = _frame_key_struct.unpack_from(data, offset)
                frame.keys.append(key)

                offset += _frame_key_struct.size

            self.frames.append(frame)

        return offset


    def __load_texture(self, data, length, offset):
        if self.tex_type == 0x7: # uncompressed
            if length < offset + _TEXTURE_SIZE:
                raise Corrupt("File too small.")

            self.texture = data[offset:(offset + _TEXTURE_SIZE)]
            offset += _TEXTURE_SIZE
        else:
            print("Warning: Loading uncompressed textures not supported yet.")

        return offset