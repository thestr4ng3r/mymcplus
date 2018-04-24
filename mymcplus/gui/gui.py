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

"""Graphical user-interface for mymcplus."""

import os
import sys
import struct
import io

# Work around a problem with mixing wx and py2exe
if os.name == "nt" and hasattr(sys, "setdefaultencoding"):
    sys.setdefaultencoding("mbcs")
import wx

from .. import ps2mc
from .. import ps2save
from .icon_window import IconWindow
from .dirlist_control import DirListControl
from . import utils


class GuiConfig(wx.Config):
    """A class for holding the persistant configuration state."""

    memcard_dir = "Memory Card Directory"
    savefile_dir = "Save File Directory"
    ascii = "ASCII Descriptions"
    
    def __init__(self):
        wx.Config.__init__(self, "mymcplus", "Ross Ridge",
                   style = wx.CONFIG_USE_LOCAL_FILE)

    def get_memcard_dir(self, default = None):
        return self.Read(GuiConfig.memcard_dir, default)

    def set_memcard_dir(self, value):
        return self.Write(GuiConfig.memcard_dir, value)

    def get_savefile_dir(self, default = None):
        return self.Read(GuiConfig.savefile_dir, default)

    def set_savefile_dir(self, value):
        return self.Write(GuiConfig.savefile_dir, value)

    def get_ascii(self, default = False):
        return bool(self.ReadInt(GuiConfig.ascii, int(bool(default))))

    def set_ascii(self, value):
        return self.WriteInt(GuiConfig.ascii, int(bool(value)))

def add_tool(toolbar, id, label, ico):
    tbsize = toolbar.GetToolBitmapSize()
    bmp = utils.get_icon_resource_bmp(ico, tbsize)
    return toolbar.AddTool(id, label, bmp, shortHelp = label)

class GuiFrame(wx.Frame):
    """The main top level window."""
    
    ID_CMD_EXIT = wx.ID_EXIT
    ID_CMD_OPEN = wx.ID_OPEN
    ID_CMD_EXPORT = 103
    ID_CMD_IMPORT = 104
    ID_CMD_DELETE = wx.ID_DELETE
    ID_CMD_ASCII = 106
    
    def message_box(self, message, caption = "mymcplus", style = wx.OK,
            x = -1, y = -1):
        return wx.MessageBox(message, caption, style, self, x, y)

    def error_box(self, msg):
        return self.message_box(msg, "Error", wx.OK | wx.ICON_ERROR)
        
    def mc_error(self, value, filename = None):
        """Display a message box for EnvironmentError exeception."""

        if filename == None:
            filename = getattr(value, "filename")
        if filename == None:
            filename = self.mcname
        if filename == None:
            filename = "???"
                    
        strerror = getattr(value, "strerror", None)
        if strerror == None:
            strerror = "unknown error"
            
        return self.error_box(filename + ": " + strerror)

    def __init__(self, parent, title, mcname = None):
        self.f = None
        self.mc = None
        self.mcname = None
        self.icon_win = None

        size = (750, 350)
        wx.Frame.__init__(self, parent, wx.ID_ANY, title, size = size)

        self.Bind(wx.EVT_CLOSE, self.evt_close)

        self.config = GuiConfig()
        self.title = title

        self.SetIcons(utils.get_icon_resource("mc4.ico"))
                
        self.Bind(wx.EVT_MENU, self.evt_cmd_exit, id=self.ID_CMD_EXIT)
        self.Bind(wx.EVT_MENU, self.evt_cmd_open, id=self.ID_CMD_OPEN)
        self.Bind(wx.EVT_MENU, self.evt_cmd_export, id=self.ID_CMD_EXPORT)
        self.Bind(wx.EVT_MENU, self.evt_cmd_import, id=self.ID_CMD_IMPORT)
        self.Bind(wx.EVT_MENU, self.evt_cmd_delete, id=self.ID_CMD_DELETE)
        self.Bind(wx.EVT_MENU, self.evt_cmd_ascii, id=self.ID_CMD_ASCII)
        
        filemenu = wx.Menu()
        filemenu.Append(self.ID_CMD_OPEN, "&Open...",
                "Opens an existing PS2 memory card image.")
        filemenu.AppendSeparator()
        self.export_menu_item = filemenu.Append(
            self.ID_CMD_EXPORT, "&Export...",
            "Export a save file from this image.")
        self.import_menu_item = filemenu.Append(
            self.ID_CMD_IMPORT, "&Import...",
            "Import a save file into this image.")
        self.delete_menu_item = filemenu.Append(
            self.ID_CMD_DELETE, "&Delete")
        filemenu.AppendSeparator()
        filemenu.Append(self.ID_CMD_EXIT, "E&xit")

        optionmenu = wx.Menu()
        self.ascii_menu_item = optionmenu.AppendCheckItem(
            self.ID_CMD_ASCII, "&ASCII Descriptions",
            "Show descriptions in ASCII instead of Shift-JIS")


        self.Bind(wx.EVT_MENU_OPEN, self.evt_menu_open)

        self.CreateToolBar(wx.TB_HORIZONTAL)
        self.toolbar = toolbar = self.GetToolBar()
        tbsize = (32, 32)
        toolbar.SetToolBitmapSize(tbsize)
        add_tool(toolbar, self.ID_CMD_OPEN, "Open", "mc2.ico")
        toolbar.AddSeparator()
        add_tool(toolbar, self.ID_CMD_IMPORT, "Import", "mc5b.ico")
        add_tool(toolbar, self.ID_CMD_EXPORT, "Export", "mc6a.ico")
        toolbar.Realize()

        self.statusbar = self.CreateStatusBar(2,
                              style = wx.STB_SIZEGRIP)
        self.statusbar.SetStatusWidths([-2, -1])
        
        panel = wx.Panel(self, wx.ID_ANY, (0, 0))

        self.dirlist = DirListControl(panel,
                                      self.evt_dirlist_item_focused,
                                      self.evt_dirlist_select,
                                      self.config)
        if mcname != None:
            self.open_mc(mcname)
        else:
            self.refresh()

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.dirlist, 2, wx.EXPAND)
        sizer.AddSpacer(5)

        icon_win = IconWindow(panel, self)
        if icon_win.failed:
            icon_win.Destroy()
            icon_win = None
        self.icon_win = icon_win
        
        if icon_win == None:
            self.info1 = None
            self.info2 = None
        else:
            self.icon_menu = icon_menu = wx.Menu()
            icon_win.append_menu_options(self, icon_menu)
            optionmenu.AppendSubMenu(icon_menu, "Icon Window")
            title_style =  wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE
            
            self.info1 = wx.StaticText(panel, -1, "",
                           style = title_style)
            self.info2 = wx.StaticText(panel, -1, "",
                           style = title_style)
            # self.info3 = wx.StaticText(panel, -1, "")

            info_sizer = wx.BoxSizer(wx.VERTICAL)
            info_sizer.Add(self.info1, 0, wx.EXPAND)
            info_sizer.Add(self.info2, 0, wx.EXPAND)
            # info_sizer.Add(self.info3, 0, wx.EXPAND)
            info_sizer.AddSpacer(5)
            info_sizer.Add(icon_win, 1, wx.EXPAND)

            sizer.Add(info_sizer, 1, wx.EXPAND | wx.ALL,
                  border = 5)

        menubar = wx.MenuBar()
        menubar.Append(filemenu, "&File")
        menubar.Append(optionmenu, "&Options")
        self.SetMenuBar(menubar)

        
        panel.SetSizer(sizer)
        panel.SetAutoLayout(True)
        sizer.Fit(panel)

        self.Show(True)

        if self.mc == None:
            self.evt_cmd_open()

    def _close_mc(self):
        if self.mc != None:
            try:
                self.mc.close()
            except EnvironmentError as value:
                self.mc_error(value)
            self.mc = None
        if self.f != None:
            try:
                self.f.close()
            except EnvironmentError as value:
                self.mc_error(value)
            self.f = None
        self.mcname = None
        
    def refresh(self):
        try:
            self.dirlist.update(self.mc)
        except EnvironmentError as value:
            self.mc_error(value)
            self._close_mc()
            self.dirlist.update(None)

        mc = self.mc
        
        self.toolbar.EnableTool(self.ID_CMD_IMPORT, mc != None)
        self.toolbar.EnableTool(self.ID_CMD_EXPORT, False)

        if mc == None:
            status = "No memory card image"
        else:
            free = mc.get_free_space() // 1024
            limit = mc.get_allocatable_space() // 1024
            status = "%dK of %dK free" % (free, limit)
        self.statusbar.SetStatusText(status, 1)

    def open_mc(self, filename):
        self._close_mc()
        self.statusbar.SetStatusText("", 1)
        if self.icon_win != None:
            self.icon_win.load_icon(None, None)
        
        f = None
        try:
            f = open(filename, "r+b")
            mc = ps2mc.ps2mc(f)
        except EnvironmentError as value:
            if f != None:
                f.close()
            self.mc_error(value, filename)
            self.SetTitle(self.title)
            self.refresh()
            return

        self.f = f
        self.mc = mc
        self.mcname = filename
        self.SetTitle(filename + " - " + self.title)
        self.refresh()

    def evt_menu_open(self, event):
        self.import_menu_item.Enable(self.mc != None)
        selected = self.mc != None and len(self.dirlist.selected) > 0
        self.export_menu_item.Enable(selected)
        self.delete_menu_item.Enable(selected)
        self.ascii_menu_item.Check(self.config.get_ascii())
        if self.icon_win != None:
            self.icon_win.update_menu(self.icon_menu)

    def evt_dirlist_item_focused(self, event):
        if self.icon_win == None:
            return
        
        mc = self.mc

        i = event.GetData()
        (ent, icon_sys, size, title) = self.dirlist.dirtable[i]
        self.info1.SetLabel(title[0])
        self.info2.SetLabel(title[1])

        a = ps2save.unpack_icon_sys(icon_sys)
        try:
            mc.chdir("/" + ent[8].decode("ascii"))
            f = mc.open(a[15].decode("ascii"), "rb")
            try: 
                icon = f.read()
            finally:
                f.close()
        except EnvironmentError as value:
            print("icon failed to load", value)
            self.icon_win.load_icon(None, None)
            return

        self.icon_win.load_icon(icon_sys, icon)

    def evt_dirlist_select(self, event):
        self.toolbar.EnableTool(self.ID_CMD_IMPORT, self.mc != None)
        self.toolbar.EnableTool(self.ID_CMD_EXPORT,
                    len(self.dirlist.selected) > 0)

    def evt_cmd_open(self, event = None):
        fn = wx.FileSelector("Open Memory Card Image",
                     self.config.get_memcard_dir(""),
                     "Mcd001.ps2", "ps2", "*.ps2",
                     wx.FD_FILE_MUST_EXIST | wx.FD_OPEN,
                     self)
        if fn == "":
            return
        self.open_mc(fn)
        if self.mc != None:
            dirname = os.path.dirname(fn)
            if os.path.isabs(dirname):
                self.config.set_memcard_dir(dirname)

    def evt_cmd_export(self, event):
        mc = self.mc
        if mc == None:
            return
        
        selected = self.dirlist.selected
        dirtable = self.dirlist.dirtable
        sfiles = []
        for i in selected:
            dirname = dirtable[i][0][8].decode("ascii")
            try:
                sf = mc.export_save_file("/" + dirname)
                longname = ps2save.make_longname(dirname, sf)
                sfiles.append((dirname, sf, longname))
            except EnvironmentError as value:
                self.mc_error(value. dirname)

        if len(sfiles) == 0:
            return
        
        dir = self.config.get_savefile_dir("")
        if len(selected) == 1:
            (dirname, sf, longname) = sfiles[0]
            fn = wx.FileSelector("Export " + dirname,
                         dir, longname, "psu",
                         "EMS save file (.psu)|*.psu"
                         "|MAXDrive save file (.max)"
                         "|*.max",
                         (wx.FD_OVERWRITE_PROMPT
                          | wx.FD_SAVE),
                         self)
            if fn == "":
                return
            try:
                f = open(fn, "wb")
                try:
                    if fn.endswith(".max"):
                        sf.save_max_drive(f)
                    else:
                        sf.save_ems(f)
                finally:
                    f.close()
            except EnvironmentError as value:
                self.mc_error(value, fn)
                return

            dir = os.path.dirname(fn)
            if os.path.isabs(dir):
                self.config.set_savefile_dir(dir)

            self.message_box("Exported " + fn + " successfully.")
            return
        
        dir = wx.DirSelector("Export Save Files", dir, parent = self)
        if dir == "":
            return
        count = 0
        for (dirname, sf, longname) in sfiles:
            fn = os.path.join(dir, longname) + ".psu"
            try:
                f = open(fn, "wb")
                sf.save_ems(f)
                f.close()
                count += 1
            except EnvironmentError as value:
                self.mc_error(value, fn)
        if count > 0:
            if os.path.isabs(dir):
                self.config.set_savefile_dir(dir)
            self.message_box("Exported %d file(s) successfully."
                     % count)
            

    def _do_import(self, fn):
        sf = ps2save.ps2_save_file()
        f = open(fn, "rb")
        try:
            ft = ps2save.detect_file_type(f)
            f.seek(0)
            if ft == "max":
                sf.load_max_drive(f)
            elif ft == "psu":
                sf.load_ems(f)
            elif ft == "cbs":
                sf.load_codebreaker(f)
            elif ft == "sps":
                sf.load_sharkport(f)
            elif ft == "npo":
                self.error_box(fn + ": nPort saves"
                           " are not supported.")
                return
            else:
                self.error_box(fn + ": Save file format not"
                           " recognized.")
                return
        finally:
            f.close()

        if not self.mc.import_save_file(sf, True):
            self.error_box(fn + ": Save file already present.")
        
    def evt_cmd_import(self, event):
        if self.mc == None:
            return
        
        dir = self.config.get_savefile_dir("")
        fd = wx.FileDialog(self, "Import Save File", dir,
                   wildcard = ("PS2 save files"
                           " (.cbs;.psu;.max;.sps;.xps)"
                           "|*.cbs;*.psu;*.max;*.sps;*.xps"
                           "|All files|*.*"),
                   style = (wx.FD_OPEN | wx.FD_MULTIPLE
                        | wx.FD_FILE_MUST_EXIST))
        if fd == None:
            return
        r = fd.ShowModal()
        if r == wx.ID_CANCEL:
            return

        success = None
        for fn in fd.GetPaths():
            try:
                self._do_import(fn)
                success = fn
            except EnvironmentError as value:
                self.mc_error(value, fn)

        if success != None:
            dir = os.path.dirname(success)
            if os.path.isabs(dir):
                self.config.set_savefile_dir(dir)
        self.refresh()

    def evt_cmd_delete(self, event):
        mc = self.mc
        if mc == None:
            return
        
        selected = self.dirlist.selected
        dirtable = self.dirlist.dirtable

        dirnames = [dirtable[i][0][8].decode("ascii")
                for i in selected]
        if len(selected) == 1:
            title = dirtable[list(selected)[0]][3]
            s = dirnames[0] + " (" + utils.single_title(title) + ")"
        else:
            s = ", ".join(dirnames)
            if len(s) > 200:
                s = s[:200] + "..."
        r = self.message_box("Are you sure you want to delete "
                     + s + "?",
                     "Delete Save File Confirmation",
                     wx.YES_NO)
        if r != wx.YES:
            return

        for dn in dirnames:
            try:
                mc.rmdir("/" + dn)
            except EnvironmentError as value:
                self.mc_error(value, dn)

        mc.check()
        self.refresh()

    def evt_cmd_ascii(self, event):
        self.config.set_ascii(not self.config.get_ascii())
        self.refresh()
        
    def evt_cmd_exit(self, event):
        self.Close(True)

    def evt_close(self, event):
        self._close_mc()
        self.Destroy()
        
def run(filename = None):
    """Display a GUI for working with memory card images."""

    wx_app = wx.App()
    frame = GuiFrame(None, "mymcplus", filename)
    return wx_app.MainLoop()
    
if __name__ == "__main__":
    import gc
    gc.set_debug(gc.DEBUG_LEAK)

    run("test.ps2")

    gc.collect()
    for o in gc.garbage:
        print()
        print(o)
        if type(o) == ps2mc.ps2mc_file:
            for m in dir(o):
                print(m, getattr(o, m))
