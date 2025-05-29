import wx
import os
import shutil
import datetime
from project_manager import load_projects, save_projects
from love_runner import run_love_project
from PIL import Image
import yaml

LIBS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'libs')

def get_available_libs():
    if not os.path.exists(LIBS_PATH):
        return []
    return [f for f in os.listdir(LIBS_PATH) if os.path.isfile(os.path.join(LIBS_PATH, f))]

class ProjectManagerFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="HeartCore - Love2D Project Manager", size=(800, 500))
        self.projects = load_projects()
        self.selected_index = None
        self.InitUI()
        self.Center()
        self.Show()

    def InitUI(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Top bar
        hbox_top = wx.BoxSizer(wx.HORIZONTAL)
        self.create_btn = wx.Button(panel, label="Create")
        self.import_btn = wx.Button(panel, label="Import")
        self.scan_btn = wx.Button(panel, label="Scan")
        self.search_ctrl = wx.SearchCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.search_ctrl.SetDescriptiveText("Filter Projects")
        hbox_top.Add(self.create_btn, 0, wx.RIGHT, 5)
        hbox_top.Add(self.import_btn, 0, wx.RIGHT, 5)
        hbox_top.Add(self.scan_btn, 0, wx.RIGHT, 5)
        hbox_top.Add(self.search_ctrl, 1)
        vbox.Add(hbox_top, 0, wx.EXPAND | wx.ALL, 8)

        # Project list
        self.project_list = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.project_list.InsertColumn(0, "Name", width=250)
        self.project_list.InsertColumn(1, "Path", width=350)
        self.project_list.InsertColumn(2, "Last Edited", width=150)
        vbox.Add(self.project_list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

        # Right-side buttons
        hbox_right = wx.BoxSizer(wx.HORIZONTAL)
        self.edit_btn = wx.Button(panel, label="Edit")
        self.run_btn = wx.Button(panel, label="Run")
        self.rename_btn = wx.Button(panel, label="Rename")
        self.remove_btn = wx.Button(panel, label="Remove")
        hbox_right.Add(self.edit_btn, 0, wx.RIGHT, 5)
        hbox_right.Add(self.run_btn, 0, wx.RIGHT, 5)
        hbox_right.Add(self.rename_btn, 0, wx.RIGHT, 5)
        hbox_right.Add(self.remove_btn, 0)
        vbox.Add(hbox_right, 0, wx.ALIGN_RIGHT | wx.ALL, 8)

        panel.SetSizer(vbox)

        # Bindings
        self.create_btn.Bind(wx.EVT_BUTTON, self.OnCreate)
        self.import_btn.Bind(wx.EVT_BUTTON, self.OnImport)
        self.scan_btn.Bind(wx.EVT_BUTTON, self.OnScan)
        self.search_ctrl.Bind(wx.EVT_TEXT, self.OnSearch)
        self.project_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelect)
        self.edit_btn.Bind(wx.EVT_BUTTON, self.OnEdit)
        self.run_btn.Bind(wx.EVT_BUTTON, self.OnRun)
        self.rename_btn.Bind(wx.EVT_BUTTON, self.OnRename)
        self.remove_btn.Bind(wx.EVT_BUTTON, self.OnRemove)

        self.RefreshList()

    def RefreshList(self, filter_text=""):
        self.project_list.DeleteAllItems()
        for idx, proj in enumerate(self.projects):
            if filter_text and filter_text.lower() not in proj["name"].lower():
                continue
            self.project_list.InsertItem(idx, proj["name"])
            self.project_list.SetItem(idx, 1, proj["path"])
            self.project_list.SetItem(idx, 2, proj.get("last_edited", ""))
        self.selected_index = None

    def OnCreate(self, event):
        dlg = CreateProjectDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetData()
            name = data['name']
            path = data['path']
            icon_path = data['icon']
            description = data['description']
            version = data['version']
            author = data['author']
            selected_libs = data.get('libs', [])
            proj_path = os.path.join(path, name)
            content_path = os.path.join(proj_path, 'content')
            os.makedirs(content_path, exist_ok=True)
            # Write main.lua
            with open(os.path.join(content_path, "main.lua"), "w", encoding="utf-8") as f:
                f.write("-- Love2D main.lua\nfunction love.draw() love.graphics.print('Hello World!', 400, 300) end")
            # Copy icon or use default
            if icon_path:
                shutil.copy(icon_path, os.path.join(proj_path, "icon.png"))
            else:
                # Write a placeholder icon.png (1x1 transparent PNG)
                Image.new('RGBA', (64, 64), (0,0,0,0)).save(os.path.join(proj_path, "icon.png"))
            # Copy selected libraries
            if selected_libs:
                for lib in selected_libs:
                    src = os.path.join(LIBS_PATH, lib)
                    dst = os.path.join(proj_path, lib)
                    shutil.copy(src, dst)
            # Write .heartproj file
            class QuotedDumper(yaml.SafeDumper):
                pass
            def quoted_presenter(dumper, data):
                return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')
            QuotedDumper.add_representer(str, quoted_presenter)
            meta = {
                'name': name,
                'description': description,
                'version': version,
                'author': author,
                'libs': selected_libs
            }
            with open(os.path.join(proj_path, f"{name}.heartproj"), "w", encoding="utf-8") as f:
                yaml.dump(meta, f, Dumper=QuotedDumper, default_flow_style=False, allow_unicode=True)
            project = {
                "name": name,
                "path": proj_path,
                "last_edited": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.projects.append(project)
            save_projects(self.projects)
            self.RefreshList()
        dlg.Destroy()

    def OnImport(self, event):
        path = wx.DirSelector("Select Existing Love2D Project Folder")
        if path:
            name = os.path.basename(path)
            project = {
                "name": name,
                "path": path,
                "last_edited": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.projects.append(project)
            save_projects(self.projects)
            self.RefreshList()

    def OnScan(self, event):
        root = wx.DirSelector("Select Folder to Scan for Projects")
        if root:
            for dirpath, dirnames, filenames in os.walk(root):
                if "main.lua" in filenames:
                    name = os.path.basename(dirpath)
                    if not any(p["path"] == dirpath for p in self.projects):
                        project = {
                            "name": name,
                            "path": dirpath,
                            "last_edited": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        self.projects.append(project)
            save_projects(self.projects)
            self.RefreshList()

    def OnSearch(self, event):
        self.RefreshList(self.search_ctrl.GetValue())

    def OnSelect(self, event):
        self.selected_index = event.GetIndex()

    def OnEdit(self, event):
        if self.selected_index is not None:
            path = self.projects[self.selected_index]["path"]
            os.startfile(path)

    def OnRun(self, event):
        if self.selected_index is not None:
            path = self.projects[self.selected_index]["path"]
            run_love_project(path)

    def OnRename(self, event):
        if self.selected_index is not None:
            dlg = wx.TextEntryDialog(self, "New Project Name:", "Rename Project")
            if dlg.ShowModal() == wx.ID_OK:
                new_name = dlg.GetValue()
                self.projects[self.selected_index]["name"] = new_name
                save_projects(self.projects)
                self.RefreshList()
            dlg.Destroy()

    def OnTags(self, event):
        wx.MessageBox("Tag management not implemented yet.", "Info")

    def OnRemove(self, event):
        if self.selected_index is not None:
            del self.projects[self.selected_index]
            save_projects(self.projects)
            self.RefreshList()

class CreateProjectDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Create New Project", size=(420, 500))
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        # Project Name
        hbox_name = wx.BoxSizer(wx.HORIZONTAL)
        hbox_name.Add(wx.StaticText(panel, label="Project Name:"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 8)
        self.name_ctrl = wx.TextCtrl(panel)
        hbox_name.Add(self.name_ctrl, 1)
        vbox.Add(hbox_name, 0, wx.EXPAND|wx.ALL, 8)
        # Project Path
        hbox_path = wx.BoxSizer(wx.HORIZONTAL)
        hbox_path.Add(wx.StaticText(panel, label="Project Path:"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 8)
        self.path_ctrl = wx.TextCtrl(panel)
        hbox_path.Add(self.path_ctrl, 1, wx.RIGHT, 4)
        browse_btn = wx.Button(panel, label="Browse")
        browse_btn.Bind(wx.EVT_BUTTON, self.OnBrowsePath)
        hbox_path.Add(browse_btn, 0)
        vbox.Add(hbox_path, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 8)
        # Icon
        hbox_icon = wx.BoxSizer(wx.HORIZONTAL)
        hbox_icon.Add(wx.StaticText(panel, label="Icon (optional):"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 8)
        self.icon_ctrl = wx.TextCtrl(panel)
        hbox_icon.Add(self.icon_ctrl, 1, wx.RIGHT, 4)
        icon_btn = wx.Button(panel, label="Browse")
        icon_btn.Bind(wx.EVT_BUTTON, self.OnBrowseIcon)
        hbox_icon.Add(icon_btn, 0)
        vbox.Add(hbox_icon, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 8)
        # Description
        vbox.Add(wx.StaticText(panel, label="Description (optional):"), 0, wx.LEFT|wx.RIGHT|wx.TOP, 8)
        self.desc_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        vbox.Add(self.desc_ctrl, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 8)
        # Version
        hbox_version = wx.BoxSizer(wx.HORIZONTAL)
        hbox_version.Add(wx.StaticText(panel, label="Version:"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 8)
        self.version_ctrl = wx.TextCtrl(panel, value="1.0.0")
        hbox_version.Add(self.version_ctrl, 1)
        vbox.Add(hbox_version, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 8)
        # Author
        hbox_author = wx.BoxSizer(wx.HORIZONTAL)
        hbox_author.Add(wx.StaticText(panel, label="Author:"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 8)
        self.author_ctrl = wx.TextCtrl(panel)
        hbox_author.Add(self.author_ctrl, 1)
        vbox.Add(hbox_author, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 8)
        # Library selection
        libs = get_available_libs()
        self.lib_checkboxes = []
        if libs:
            vbox.Add(wx.StaticText(panel, label="Include Libraries:"), 0, wx.LEFT|wx.RIGHT|wx.TOP, 8)
            for lib in libs:
                cb = wx.CheckBox(panel, label=lib)
                vbox.Add(cb, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 12)
                self.lib_checkboxes.append(cb)
        # Buttons
        btns = self.CreateSeparatedButtonSizer(wx.OK|wx.CANCEL)
        panel.SetSizer(vbox)
        main_sizer.Add(panel, 1, wx.EXPAND|wx.ALL, 0)
        main_sizer.Add(btns, 0, wx.ALIGN_CENTER|wx.ALL, 8)
        self.SetSizer(main_sizer)

    def OnBrowsePath(self, event):
        dlg = wx.DirDialog(self, "Select Project Folder")
        if dlg.ShowModal() == wx.ID_OK:
            self.path_ctrl.SetValue(dlg.GetPath())
        dlg.Destroy()

    def OnBrowseIcon(self, event):
        dlg = wx.FileDialog(self, "Select Icon", wildcard="PNG files (*.png)|*.png", style=wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.icon_ctrl.SetValue(dlg.GetPath())
        dlg.Destroy()

    def GetData(self):
        libs = [cb.GetLabel() for cb in getattr(self, 'lib_checkboxes', []) if cb.GetValue()]
        return {
            'name': self.name_ctrl.GetValue(),
            'path': self.path_ctrl.GetValue(),
            'icon': self.icon_ctrl.GetValue(),
            'description': self.desc_ctrl.GetValue(),
            'version': self.version_ctrl.GetValue(),
            'author': self.author_ctrl.GetValue(),
            'libs': libs
        }

def main():
    app = wx.App(False)
    ProjectManagerFrame()
    app.MainLoop()

if __name__ == "__main__":
    main() 