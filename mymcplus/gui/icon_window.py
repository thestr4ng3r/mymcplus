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

from .. import ps2icon
from ..save import ps2save
from .icon_renderer import IconRenderer
from .linalg import Vector3


lighting_none = IconRenderer.LightingConfig(
    light_dirs = ((0.0, 0.0, 0.0),
                  (0.0, 0.0, 0.0),
                  (0.0, 0.0, 0.0)),
    light_colors = ((0.0, 0.0, 0.0),
                    (0.0, 0.0, 0.0),
                    (0.0, 0.0, 0.0)),
    ambient_light_color = (1.0, 1.0, 1.0))

lighting_icon = None

lighting_alt1 = IconRenderer.LightingConfig(
    light_dirs = ((1.0, -1.0, 2.0),
                  (-1.0, 1.0, -2.0),
                  (0.0, 1.0, 0.0)),
    light_colors = ((1.0, 1.0, 1.0),
                    (1.0, 1.0, 1.0),
                    (0.7, 0.7, 0.7)),
    ambient_light_color = (0.5, 0.5, 0.5))

lighting_alt2 = IconRenderer.LightingConfig(
    light_dirs = ((1.0, -1.0, 2.0),
                  (-1.0, 1.0, -2.0),
                  (0.0, 4.0, 1.0)),
    light_colors = ((0.7, 0.7, 0.7),
                    (0.7, 0.7, 0.7),
                    (0.2, 0.2, 0.2)),
    ambient_light_color = (0.3, 0.3, 0.3))


camera_default = [0, 4, -8]
camera_high = [0, 7, -6]
camera_near = [0, 3, -6]
camera_flat = [0, 2, -7.5]


class IconWindow(wx.Window):
    """Displays a save file's 3D icon."""

    ID_CMD_ANIMATE = 201
    ID_CMD_LIGHT_NONE = 202
    ID_CMD_LIGHT_ICON = 203
    ID_CMD_LIGHT_ALT1 = 204
    ID_CMD_LIGHT_ALT2 = 205
    ID_CMD_CAMERA_RESET = 206

    light_options = {ID_CMD_LIGHT_NONE: lighting_none,
                     ID_CMD_LIGHT_ICON: lighting_icon,
                     ID_CMD_LIGHT_ALT1: lighting_alt1,
                     ID_CMD_LIGHT_ALT2: lighting_alt2}


    def append_menu_options(self, win, menu):
        menu.AppendCheckItem(IconWindow.ID_CMD_ANIMATE, "Animate Icons")
        menu.AppendSeparator()
        menu.AppendRadioItem(IconWindow.ID_CMD_LIGHT_NONE, "Lighting Off")
        menu.AppendRadioItem(IconWindow.ID_CMD_LIGHT_ICON, "Icon Lighting")
        menu.AppendRadioItem(IconWindow.ID_CMD_LIGHT_ALT1, "Alternate Lighting")
        menu.AppendRadioItem(IconWindow.ID_CMD_LIGHT_ALT2, "Alternate Lighting 2")
        menu.AppendSeparator()
        menu.Append(IconWindow.ID_CMD_CAMERA_RESET, "Reset Camera")

        win.Bind(wx.EVT_MENU, self.evt_menu_animate, id=IconWindow.ID_CMD_ANIMATE)
        win.Bind(wx.EVT_MENU, self.evt_menu_light, id=IconWindow.ID_CMD_LIGHT_NONE)
        win.Bind(wx.EVT_MENU, self.evt_menu_light, id=IconWindow.ID_CMD_LIGHT_ICON)
        win.Bind(wx.EVT_MENU, self.evt_menu_light, id=IconWindow.ID_CMD_LIGHT_ALT1)
        win.Bind(wx.EVT_MENU, self.evt_menu_light, id=IconWindow.ID_CMD_LIGHT_ALT2)

        win.Bind(wx.EVT_MENU, self.evt_menu_camera, id=IconWindow.ID_CMD_CAMERA_RESET)

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

        self._renderer = IconRenderer(self.context)

        self._icon = None
        self._icon_sys = None

        self.canvas.Bind(wx.EVT_PAINT, self.paint)

        self.sizer.Add(self.canvas, wx.EXPAND, wx.EXPAND)
        self.SetSizer(self.sizer)

        #self.config = config = mymcsup.icon_config()
        #config.animate = True

        self._camera_dragging_rotation = False
        self._camera_dragging_offset = False
        self._last_mouse_pos = None

        self.lighting_id = self.ID_CMD_LIGHT_ICON

        self.menu = wx.Menu()
        self.append_menu_options(self, self.menu)
        self.set_lighting(self.lighting_id)
        self.reset_camera()

        self.Bind(wx.EVT_CONTEXT_MENU, self.evt_context_menu)
        self.canvas.Bind(wx.EVT_LEFT_DOWN, self.evt_mouse_left_down)
        self.canvas.Bind(wx.EVT_LEFT_UP, self.evt_mouse_left_up)
        self.canvas.Bind(wx.EVT_MIDDLE_DOWN, self.evt_mouse_middle_down)
        self.canvas.Bind(wx.EVT_MIDDLE_UP, self.evt_mouse_middle_up)
        self.canvas.Bind(wx.EVT_MOTION, self.evt_mouse_motion)
        self.canvas.Bind(wx.EVT_MOUSEWHEEL, self.evt_mouse_wheel)


    def paint(self, _):
        self._renderer.paint(self.canvas)


    def update_menu(self, menu):
        """Update the content menu according to the current config."""

        menu.Check(IconWindow.ID_CMD_ANIMATE, False)#self.config.animate)
        menu.Check(self.lighting_id, True)


    def load_icon(self, icon_sys, icon_data):
        """Pass the raw icon data to the support DLL for display."""

        if self.failed:
            return

        if icon_data is None:
            self._icon = None
            self._icon_sys = None
        else:
            try:
                self._icon = ps2icon.Icon(icon_data)
                self._icon_sys = icon_sys
            except ps2icon.Error as e:
                print("Failed to load icon.", e)
                self._icon = None
                self._icon_sys = None

        self._renderer.set_icon(self._icon_sys, self._icon)
        self.canvas.Refresh(eraseBackground=False)


    def set_lighting(self, id):
        self.lighting_id = id
        self._renderer.lighting_config = self.light_options[id]
        self.canvas.Refresh(eraseBackground=False)


    def set_animate(self, animate):
        #if self.failed:
        #    return
        #self.config.animate = animate
        #if mymcsup.set_config(self.config) == -1:
        #    self.failed = True
        pass


    def reset_camera(self):
        self._renderer.camera_offset = Vector3(0.0, 2.5, 0.0)
        self._renderer.camera_rotation = (0.0, 0.0)
        self._renderer.camera_distance = 5.0
        self.canvas.Refresh(eraseBackground=False)


    def evt_mouse_left_down(self, event):
        self._camera_dragging_rotation = True
        self._last_mouse_pos = event.GetPosition()


    def evt_mouse_left_up(self, event):
        self._camera_dragging_rotation = False


    def evt_mouse_middle_down(self, event):
        self._camera_dragging_offset = True
        self._last_mouse_pos = event.GetPosition()

    def evt_mouse_middle_up(self, event):
        self._camera_dragging_offset = False


    def evt_mouse_motion(self, event):
        import math

        if self._camera_dragging_rotation:
            speed = (0.01, 0.01)

            delta = event.GetPosition()
            delta -= self._last_mouse_pos

            cam_rot = self._renderer.camera_rotation
            cam_rot = (
                cam_rot[0] - speed[0] * delta.x,
                max(-math.pi * 0.5 + 0.01,
                    min(math.pi * 0.5 - 0.01,
                        cam_rot[1] - speed[1] * delta.y))
            )
            self._renderer.camera_rotation = cam_rot
        elif self._camera_dragging_offset:
            speed = 0.01

            delta = event.GetPosition()
            delta -= self._last_mouse_pos

            (eye, center, up) = self._renderer.calculate_camera()
            dir = (center - eye).normalized
            right = up.cross(dir)
            up = dir.cross(right)

            offset = self._renderer.camera_offset
            offset = offset \
                     + right * (speed * delta.x) \
                     + up * (speed * delta.y)
            self._renderer.camera_offset = offset
        else:
            return

        self.canvas.Refresh(eraseBackground=False)
        self._last_mouse_pos = event.GetPosition()


    def evt_mouse_wheel(self, event):
        speed = 0.001
        rot = event.GetWheelRotation()
        self._renderer.camera_distance = max(0.1, self._renderer.camera_distance - rot * speed)
        self.canvas.Refresh(eraseBackground=False)


    def evt_context_menu(self, event):
        self.update_menu(self.menu)
        self.PopupMenu(self.menu)


    def evt_menu_animate(self, event):
        #self.set_animate(not self.config.animate)
        pass


    def evt_menu_light(self, event):
        self.set_lighting(event.GetId())


    def evt_menu_camera(self, event):
        self.reset_camera()
