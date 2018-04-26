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

import wx
from wx import glcanvas

from ctypes import c_void_p

from OpenGL.GL import *

from .. import ps2icon
from .linalg import Matrix4x4, Vector3


lighting_none = {"lighting": False,
         "vertex_diffuse": False,
         "alt_lighting": False,
         "light_dirs": [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
         "light_colours": [[0, 0, 0, 0], [0, 0, 0, 0],
                   [0, 0, 0, 0]],
         "ambient": [0, 0, 0, 0]}

lighting_diffuse = {"lighting": False,
            "vertex_diffuse": True,
            "alt_lighting": False,
            "light_dirs": [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            "light_colours": [[0, 0, 0, 0], [0, 0, 0, 0],
                      [0, 0, 0, 0]],
            "ambient": [0, 0, 0, 0]}

lighting_icon = {"lighting": True,
         "vertex_diffuse": True,
         "alt_lighting": False,
         "light_dirs": [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
         "light_colours": [[0, 0, 0, 0], [0, 0, 0, 0],
                   [0, 0, 0, 0]],
         "ambient": [0, 0, 0, 0]}

lighting_alternate = {"lighting": True,
              "vertex_diffuse": True,
              "alt_lighting": True,
              "light_dirs": [[1, -1, 2, 0],
                     [-1, 1, -2, 0],
                     [0, 1, 0, 0]],
              "light_colours": [[1, 1, 1, 1],
                    [1, 1, 1, 1],
                    [0.7, 0.7, 0.7, 1]],
              "ambient": [0.5, 0.5, 0.5, 1]}

lighting_alternate2 = {"lighting": True,
               "vertex_diffuse": False,
               "alt_lighting": True,
               "light_dirs": [[1, -1, 2, 0],
                      [-1, 1, -2, 0],
                      [0, 4, 1, 0]],
               "light_colours": [[0.7, 0.7, 0.7, 1],
                     [0.7, 0.7, 0.7, 1],
                     [0.2, 0.2, 0.2, 1]],
               "ambient": [0.3, 0.3, 0.3, 1]}

camera_default = [0, 4, -8]
camera_high = [0, 7, -6]
camera_near = [0, 3, -6]
camera_flat = [0, 2, -7.5]


_glsl_vert = b"""
#version 150

uniform mat4 mvp_matrix_uni;

in vec3 vertex_attr;
in vec3 normal_attr;
in vec2 uv_attr;
in vec4 color_attr;

out vec4 color_var;

void main()
{
    vec3 pos = vertex_attr / 4096.0;
    color_var = color_attr;
    gl_Position = mvp_matrix_uni * vec4(pos, 1.0);
}
"""

_glsl_frag = b"""
#version 150

in vec4 color_var;

out vec4 color_out;

void main()
{
    color_out = color_var;
}
"""

_ATTRIB_VERTEX =    0
_ATTRIB_NORMAL =    1
_ATTRIB_UV =        2
_ATTRIB_COLOR =     3


class IconWindow(wx.Window):
    """Displays a save file's 3D icon."""

    ID_CMD_ANIMATE = 201
    ID_CMD_LIGHT_NONE = 202
    ID_CMD_LIGHT_ICON = 203
    ID_CMD_LIGHT_ALT1 = 204
    ID_CMD_LIGHT_ALT2 = 205
    ID_CMD_CAMERA_FLAT = 206
    ID_CMD_CAMERA_DEFAULT = 207
    ID_CMD_CAMERA_NEAR = 209
    ID_CMD_CAMERA_HIGH = 210

    light_options = {ID_CMD_LIGHT_NONE: lighting_none,
                     ID_CMD_LIGHT_ICON: lighting_icon,
                     ID_CMD_LIGHT_ALT1: lighting_alternate,
                     ID_CMD_LIGHT_ALT2: lighting_alternate2}

    camera_options = {ID_CMD_CAMERA_FLAT: camera_flat,
                      ID_CMD_CAMERA_DEFAULT: camera_default,
                      ID_CMD_CAMERA_NEAR: camera_near,
                      ID_CMD_CAMERA_HIGH: camera_high}

    def append_menu_options(self, win, menu):
        menu.AppendCheckItem(IconWindow.ID_CMD_ANIMATE, "Animate Icons")
        menu.AppendSeparator()
        menu.AppendRadioItem(IconWindow.ID_CMD_LIGHT_NONE, "Lighting Off")
        menu.AppendRadioItem(IconWindow.ID_CMD_LIGHT_ICON, "Icon Lighting")
        menu.AppendRadioItem(IconWindow.ID_CMD_LIGHT_ALT1, "Alternate Lighting")
        menu.AppendRadioItem(IconWindow.ID_CMD_LIGHT_ALT2, "Alternate Lighting 2")
        menu.AppendSeparator()
        menu.AppendRadioItem(IconWindow.ID_CMD_CAMERA_FLAT, "Camera Flat")
        menu.AppendRadioItem(IconWindow.ID_CMD_CAMERA_DEFAULT, "Camera Default")
        menu.AppendRadioItem(IconWindow.ID_CMD_CAMERA_NEAR, "Camera Near")
        menu.AppendRadioItem(IconWindow.ID_CMD_CAMERA_HIGH, "Camera High")

        win.Bind(wx.EVT_MENU, self.evt_menu_animate, id=IconWindow.ID_CMD_ANIMATE)
        win.Bind(wx.EVT_MENU, self.evt_menu_light, id=IconWindow.ID_CMD_LIGHT_NONE)
        win.Bind(wx.EVT_MENU, self.evt_menu_light, id=IconWindow.ID_CMD_LIGHT_ICON)
        win.Bind(wx.EVT_MENU, self.evt_menu_light, id=IconWindow.ID_CMD_LIGHT_ALT1)
        win.Bind(wx.EVT_MENU, self.evt_menu_light, id=IconWindow.ID_CMD_LIGHT_ALT2)

        win.Bind(wx.EVT_MENU, self.evt_menu_camera, id=IconWindow.ID_CMD_CAMERA_FLAT)
        win.Bind(wx.EVT_MENU, self.evt_menu_camera, id=IconWindow.ID_CMD_CAMERA_DEFAULT)
        win.Bind(wx.EVT_MENU, self.evt_menu_camera, id=IconWindow.ID_CMD_CAMERA_NEAR)
        win.Bind(wx.EVT_MENU, self.evt_menu_camera, id=IconWindow.ID_CMD_CAMERA_HIGH)

    def __init__(self, parent, focus):
        super().__init__(parent)
        self.failed = False

        attrib_list = [
            glcanvas.WX_GL_MAJOR_VERSION, 3,
            glcanvas.WX_GL_MINOR_VERSION, 2,
            glcanvas.WX_GL_CORE_PROFILE,
            glcanvas.WX_GL_RGBA,
            glcanvas.WX_GL_DOUBLEBUFFER,
            glcanvas.WX_GL_DEPTH_SIZE, 24,
            glcanvas.WX_GL_SAMPLES, 16
        ]

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.canvas = glcanvas.GLCanvas(self, attribList=attrib_list)
        self.context = glcanvas.GLContext(self.canvas)

        self._icon = None

        self._program = None
        self._vertex_vbo = None
        self._normal_uv_vbo = None
        self._color_vbo = None
        self._vao = None
        self._mvp_matrix_uni = -1
        self._gl_initialized = False

        self.canvas.Bind(wx.EVT_PAINT, self.paint)

        self.sizer.Add(self.canvas, wx.EXPAND, wx.EXPAND)
        self.SetSizer(self.sizer)

        #self.config = config = mymcsup.icon_config()
        #config.animate = True

        self.menu = wx.Menu()
        self.append_menu_options(self, self.menu)
        self.set_lighting(self.ID_CMD_LIGHT_ALT2)
        self.set_camera(self.ID_CMD_CAMERA_DEFAULT)

        self.Bind(wx.EVT_CONTEXT_MENU, self.evt_context_menu)


    def initialize_gl(self):
        self._gl_initialized = True

        shader_vert = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(shader_vert, [_glsl_vert])
        glCompileShader(shader_vert)

        shader_frag = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(shader_frag, [_glsl_frag])
        glCompileShader(shader_frag)

        self._program = glCreateProgram()

        glBindAttribLocation(self._program, _ATTRIB_VERTEX, "vertex_in")
        glBindAttribLocation(self._program, _ATTRIB_NORMAL, "normal_in")
        glBindAttribLocation(self._program, _ATTRIB_UV, "uv_in")
        glBindAttribLocation(self._program, _ATTRIB_COLOR, "color_in")

        glAttachShader(self._program, shader_vert)
        glAttachShader(self._program, shader_frag)
        glLinkProgram(self._program)

        log = glGetProgramInfoLog(self._program)
        if log:
            print("Failed to compile shader:")
            print(log.decode("utf-8"))
            self.failed = True
            return

        self._mvp_matrix_uni = glGetUniformLocation(self._program, "mvp_matrix_uni")

        self._vao = glGenVertexArrays(1)
        glBindVertexArray(self._vao)

        (self._vertex_vbo, self._normal_uv_vbo, self._color_vbo) = glGenBuffers(3)

        glBindBuffer(GL_ARRAY_BUFFER, self._vertex_vbo)
        glVertexAttribPointer(_ATTRIB_VERTEX, 3, GL_SHORT, GL_FALSE, 0, c_void_p(0))

        glBindBuffer(GL_ARRAY_BUFFER, self._normal_uv_vbo)
        glVertexAttribPointer(_ATTRIB_NORMAL, 3, GL_SHORT, GL_FALSE, 5*2, c_void_p(0))
        glVertexAttribPointer(_ATTRIB_UV, 2, GL_SHORT, GL_FALSE, 5*2, c_void_p(3*2))

        glBindBuffer(GL_ARRAY_BUFFER, self._color_vbo)
        glVertexAttribPointer(_ATTRIB_COLOR, 4, GL_UNSIGNED_BYTE, GL_TRUE, 0, c_void_p(0))

        glEnableVertexAttribArray(_ATTRIB_VERTEX)
        glEnableVertexAttribArray(_ATTRIB_NORMAL)
        glEnableVertexAttribArray(_ATTRIB_UV)
        glEnableVertexAttribArray(_ATTRIB_COLOR)


    def paint(self, _):
        self.context.SetCurrent(self.canvas)

        if not self._gl_initialized:
            self.initialize_gl()

        size = self.canvas.Size

        glViewport(0, 0, size.Width, size.Height)

        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if self._icon is not None:
            glUseProgram(self._program)

            modelview_matrix = Matrix4x4.look_at(Vector3(0.0, 2.5, 4.0), Vector3(0.0, 2.5, 0.0), Vector3(0.0, -1.0, 0.0))
            projection_matrix = Matrix4x4.perspective(80.0, float(size.Width) / float(size.Height), 0.1, 500.0)
            glUniformMatrix4fv(self._mvp_matrix_uni, 1, GL_FALSE, (projection_matrix * modelview_matrix).ctypes_array)

            glDisable(GL_CULL_FACE)

            glBindVertexArray(self._vao)
            glDrawArrays(GL_TRIANGLES, 0, self._icon.vertex_count)

        self.canvas.SwapBuffers()


    def update_menu(self, menu):
        """Update the content menu according to the current config."""

        menu.Check(IconWindow.ID_CMD_ANIMATE, False)#self.config.animate)
        menu.Check(self.lighting_id, True)
        menu.Check(self.camera_id, True)


    def load_icon(self, icon_sys_data, icon_data):
        """Pass the raw icon data to the support DLL for display."""

        if self.failed:
            return

        if icon_data is None:
            self._icon = None
        else:
            try:
                self._icon = ps2icon.Icon(icon_data)
                self._load_icon_gl()
            except ps2icon.Error as e:
                print("Failed to load icon.", e)
                self._icon = None

        self.canvas.Refresh(eraseBackground=False)


    def _load_icon_gl(self):
        glBindBuffer(GL_ARRAY_BUFFER, self._vertex_vbo)
        glBufferData(GL_ARRAY_BUFFER,
                     self._icon.vertex_count * 3 * 2,
                     self._icon.vertex_data,
                     GL_STATIC_DRAW)

        glBindBuffer(GL_ARRAY_BUFFER, self._normal_uv_vbo)
        glBufferData(GL_ARRAY_BUFFER,
                     self._icon.vertex_count * 5 * 2,
                     self._icon.normal_uv_data,
                     GL_STATIC_DRAW)

        glBindBuffer(GL_ARRAY_BUFFER, self._color_vbo)
        glBufferData(GL_ARRAY_BUFFER,
                     self._icon.vertex_count * 4,
                     self._icon.color_data,
                     GL_STATIC_DRAW)



    def _set_lighting(self, lighting, vertex_diffuse, alt_lighting, light_dirs, light_colours, ambient):
        #if self.failed:
        #    return
        #config = self.config
        #config.lighting = lighting
        #config.vertex_diffuse = vertex_diffuse
        #config.alt_lighting = alt_lighting
        #config.light_dirs = mkvec4arr3(light_dirs)
        #config.light_colours = mkvec4arr3(light_colours)
        #config.ambient = D3DXVECTOR4(*ambient)
        #if mymcsup.set_config(config) == -1:
        #    self.failed = True
        pass

    def set_lighting(self, id):
        self.lighting_id = id
        self._set_lighting(**self.light_options[id])

    def set_animate(self, animate):
        #if self.failed:
        #    return
        #self.config.animate = animate
        #if mymcsup.set_config(self.config) == -1:
        #    self.failed = True
        pass

    def _set_camera(self, camera):
        #if self.failed:
        #    return
        #self.config.camera = mymcsup.D3DXVECTOR3(*camera)
        #if mymcsup.set_config(self.config) == -1:
        #    self.failed = True
        pass

    def set_camera(self, id):
        self.camera_id = id
        self._set_camera(self.camera_options[id])

    def evt_context_menu(self, event):
        self.update_menu(self.menu)
        self.PopupMenu(self.menu)

    def evt_menu_animate(self, event):
        #self.set_animate(not self.config.animate)
        pass

    def evt_menu_light(self, event):
        self.set_lighting(event.GetId())

    def evt_menu_camera(self, event):
        self.set_camera(event.GetId())