
import wx

import ps2mc
import ps2save

from gui import utils


def get_dialog_units(win):
    return win.ConvertDialogToPixels((1, 1))[0]


class DirListControl(wx.ListCtrl):
    """Lists all the save files in a memory card image."""

    def __init__(self, parent, evt_focus, evt_select, config):
        self.config = config
        self.selected = set()
        self.evt_select = evt_select
        wx.ListCtrl.__init__(self, parent, wx.ID_ANY,
                             style=wx.LC_REPORT)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.evt_col_click)
        self.Bind(wx.EVT_LIST_ITEM_FOCUSED, evt_focus)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.evt_item_selected)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.evt_item_deselected)

    def _update_dirtable(self, mc, dir):
        self.dirtable = table = []
        enc = "unicode"
        if self.config.get_ascii():
            enc = "ascii"
        for ent in dir:
            if not ps2mc.mode_is_dir(ent[0]):
                continue
            dirname = "/" + ent[8].decode("ascii")
            s = mc.get_icon_sys(dirname)
            if s == None:
                continue
            a = ps2save.unpack_icon_sys(s)
            size = mc.dir_size(dirname)
            title = ps2save.icon_sys_title(a, encoding=enc)
            table.append((ent, s, size, title))

    def update_dirtable(self, mc):
        self.dirtable = []
        if mc == None:
            return
        dir = mc.dir_open("/")
        try:
            self._update_dirtable(mc, dir)
        finally:
            dir.close()

    def cmp_dir_name(self, i1, i2):
        return self.dirtable[i1][0][8] > self.dirtable[i2][0][8]

    def cmp_dir_title(self, i1, i2):
        return self.dirtable[i1][3] > self.dirtable[i2][3]

    def cmp_dir_size(self, i1, i2):
        return self.dirtable[i1][2] > self.dirtable[i2][2]

    def cmp_dir_modified(self, i1, i2):
        m1 = list(self.dirtable[i1][0][6])
        m2 = list(self.dirtable[i2][0][6])
        m1.reverse()
        m2.reverse()
        return m1 > m2

    def evt_col_click(self, event):
        col = event.Column
        if col == 0:
            cmp = self.cmp_dir_name
        elif col == 1:
            cmp = self.cmp_dir_size
        elif col == 2:
            cmp = self.cmp_dir_modified
        elif col == 3:
            cmp = self.cmp_dir_title
        self.SortItems(cmp)
        return

    def evt_item_selected(self, event):
        self.selected.add(event.GetData())
        self.evt_select(event)

    def evt_item_deselected(self, event):
        self.selected.discard(event.GetData())
        self.evt_select(event)

    def update(self, mc):
        """Update the ListCtrl according to the contents of the
           memory card image."""

        self.ClearAll()
        self.selected = set()
        self.InsertColumn(0, "Directory")
        self.InsertColumn(1, "Size")
        self.InsertColumn(2, "Modified")
        self.InsertColumn(3, "Description")
        li = self.GetColumn(1)
        li.SetAlign(wx.LIST_FORMAT_RIGHT)
        li.SetText("Size")
        self.SetColumn(1, li)

        self.update_dirtable(mc)

        empty = len(self.dirtable) == 0
        self.Enable(not empty)
        if empty:
            return

        for (i, a) in enumerate(self.dirtable):
            (ent, icon_sys, size, title) = a
            li = self.InsertItem(i, ent[8])
            self.SetItem(li, 1, "%dK" % (size // 1024))
            m = ent[6]
            m = ("%04d-%02d-%02d %02d:%02d"
                 % (m[5], m[4], m[3], m[2], m[1]))
            self.SetItem(li, 2, m)
            self.SetItem(li, 3, utils.single_title(title))
            self.SetItemData(li, i)

        du = get_dialog_units(self)
        for i in range(4):
            self.SetColumnWidth(i, wx.LIST_AUTOSIZE)
            self.SetColumnWidth(i, self.GetColumnWidth(i) + du)
        self.SortItems(self.cmp_dir_name)
