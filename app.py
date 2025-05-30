import wx
import os
import shutil
import datetime
from project_manager import load_projects, save_projects
from love_runner import run_love_project
from PIL import Image
import yaml
import platform
import zipfile
import subprocess
import glob
import sys

LIBS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'libs')
RUNTIMES_PATH = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), 'runtimes')
CURRENT_OS = platform.system().lower()

def get_available_libs():
    """Get list of available libraries from the libs directory"""
    if not os.path.exists(LIBS_PATH):
        return []
    return [d for d in os.listdir(LIBS_PATH) 
            if os.path.isdir(os.path.join(LIBS_PATH, d))]

def get_lib_files(lib_name, target_os):
    """Get list of library files for a specific library and OS"""
    lib_path = os.path.join(LIBS_PATH, lib_name, target_os.lower())
    if not os.path.exists(lib_path):
        return []
    return [f for f in os.listdir(lib_path) 
            if os.path.isfile(os.path.join(lib_path, f))]

def get_available_runtimes():
    """Get list of available Love2D runtime versions"""
    if not os.path.exists(RUNTIMES_PATH):
        return []
    return [d for d in os.listdir(RUNTIMES_PATH) 
            if os.path.isdir(os.path.join(RUNTIMES_PATH, d))]

def get_available_platforms(version):
    """Get list of available platforms for a specific Love2D version"""
    version_path = os.path.join(RUNTIMES_PATH, version)
    if not os.path.exists(version_path):
        return []
    return [d for d in os.listdir(version_path) 
            if os.path.isdir(os.path.join(version_path, d))]

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
        self.export_btn = wx.Button(panel, label="Export")
        hbox_right.Add(self.edit_btn, 0, wx.RIGHT, 5)
        hbox_right.Add(self.run_btn, 0, wx.RIGHT, 5)
        hbox_right.Add(self.rename_btn, 0, wx.RIGHT, 5)
        hbox_right.Add(self.remove_btn, 0, wx.RIGHT, 5)
        hbox_right.Add(self.export_btn, 0)
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
        self.export_btn.Bind(wx.EVT_BUTTON, self.OnExport)

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
        dlg = ProjectDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetData()
            name = data['name']
            path = data['path']
            icon_path = data['icon']
            description = data['description']
            version = data['version']
            author = data['author']
            selected_libs = data.get('libs', [])
            love_version = data['love_version']
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
                'libs': selected_libs,  # Store just the library references
                'love_version': love_version  # Store the Love2D version
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
            project = self.projects[self.selected_index]
            dlg = ProjectDialog(self, project_path=project['path'], edit_mode=True)
            if dlg.ShowModal() == wx.ID_OK:
                data = dlg.GetData()
                proj_name = os.path.basename(project['path'])
                heartproj_path = os.path.join(project['path'], f"{proj_name}.heartproj")
                # Update .heartproj file
                class QuotedDumper(yaml.SafeDumper):
                    pass
                def quoted_presenter(dumper, data):
                    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')
                QuotedDumper.add_representer(str, quoted_presenter)
                meta = {
                    'name': data['name'],
                    'description': data['description'],
                    'version': data['version'],
                    'author': data['author'],
                    'libs': data.get('libs', []),
                    'love_version': data['love_version']
                }
                with open(heartproj_path, "w", encoding="utf-8") as f:
                    yaml.dump(meta, f, Dumper=QuotedDumper, default_flow_style=False, allow_unicode=True)
                self.RefreshList()
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

    def OnExport(self, event):
        if self.selected_index is None:
            wx.MessageBox("Please select a project to export.", "No Project Selected")
            return
        
        project = self.projects[self.selected_index]
        dlg = ExportDialog(self, project)
        if dlg.ShowModal() == wx.ID_OK:
            export_data = dlg.GetData()
            self.ExportProject(project, export_data)
        dlg.Destroy()

    def ExportProject(self, project, export_data):
        try:
            # Read project metadata to get Love2D version
            proj_name = os.path.basename(project['path'])
            heartproj_path = os.path.join(project['path'], f"{proj_name}.heartproj")
            if not os.path.exists(heartproj_path):
                raise Exception("Project metadata file (.heartproj) not found")
            
            with open(heartproj_path, 'r', encoding='utf-8') as f:
                project_data = yaml.safe_load(f)
                love_version = project_data.get('love_version')
                if not love_version:
                    raise Exception("Love2D version not specified in project metadata")
            
            # Create temp directory for build process
            temp_dir = os.path.join(export_data['output_dir'], 'temp_build')
            os.makedirs(temp_dir, exist_ok=True)
            
            try:
                # Create .love file
                love_path = os.path.join(temp_dir, f"{project['name']}.love")
                with zipfile.ZipFile(love_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(project['path']):
                        for file in files:
                            if file.endswith('.heartproj'):  # Skip project metadata
                                continue
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, project['path'])
                            zipf.write(file_path, arcname)

                # Platform-specific export
                platform = export_data['platform']
                runtime_dir = os.path.join(RUNTIMES_PATH, love_version, platform.lower())
                if not os.path.exists(runtime_dir):
                    wx.MessageBox(f"Warning: No runtime found for {platform} ({love_version}) in runtimes folder. Export will skip copying the runtime.", "Export Warning", wx.OK | wx.ICON_WARNING)
                    # Still copy .love and libs, but skip runtime
                    if platform == 'Windows':
                        # Only copy .love and libs
                        shutil.copy2(love_path, os.path.join(export_data['output_dir'], f"{project['name']}.love"))
                        self.copy_project_libs(project['path'], 'Windows', export_data['output_dir'])
                    elif platform == 'MacOS':
                        shutil.copy2(love_path, os.path.join(export_data['output_dir'], f"{project['name']}.love"))
                        self.copy_project_libs(project['path'], 'MacOS', export_data['output_dir'])
                    elif platform == 'Linux':
                        shutil.copy2(love_path, os.path.join(export_data['output_dir'], f"{project['name']}.love"))
                        self.copy_project_libs(project['path'], 'Linux', export_data['output_dir'])
                else:
                    if platform == 'Windows':
                        self.ExportWindows(project, export_data, love_path, temp_dir, love_version)
                    elif platform == 'MacOS':
                        self.ExportMacOS(project, export_data, love_path, temp_dir, love_version)
                    elif platform == 'Linux':
                        self.ExportLinux(project, export_data, love_path, temp_dir, love_version)
                wx.MessageBox(f"Project exported successfully to {export_data['output_dir']}", "Export Complete")
            finally:
                # Clean up temp directory
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
        except Exception as e:
            wx.MessageBox(f"Export failed: {str(e)}", "Export Error", wx.OK | wx.ICON_ERROR)

    def ExportWindows(self, project, export_data, love_path, temp_dir, love_version):
        # Get Love2D runtime from app directory
        runtime_dir = os.path.join(RUNTIMES_PATH, love_version, 'windows')
        if not os.path.exists(runtime_dir):
            raise Exception(f"Love2D runtime files not found for version {love_version} on Windows. Please ensure the runtime files are in the 'runtimes/{love_version}/windows' directory.")
        
        # Copy Love2D runtime files to temp directory
        for file in os.listdir(runtime_dir):
            src = os.path.join(runtime_dir, file)
            dst = os.path.join(temp_dir, file)
            if os.path.isfile(src):
                shutil.copy2(src, dst)

        # Create fused executable
        love_exe = os.path.join(temp_dir, "love.exe")
        output_exe = os.path.join(export_data['output_dir'], f"{project['name']}.exe")
        
        # Use PowerShell to combine files
        cmd = f'Get-Content "{love_exe}","{love_path}" -Encoding Byte | Set-Content "{output_exe}" -Encoding Byte'
        subprocess.run(['powershell', '-Command', cmd], check=True)

        # Copy required DLLs to output directory
        for dll in ['SDL2.dll', 'OpenAL32.dll', 'love.dll', 'lua51.dll', 'mpg123.dll', 'msvcp120.dll', 'msvcr120.dll']:
            src = os.path.join(temp_dir, dll)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(export_data['output_dir'], dll))

        # Copy project libraries
        self.copy_project_libs(project['path'], 'Windows', export_data['output_dir'])

    def ExportMacOS(self, project, export_data, love_path, temp_dir, love_version):
        # Get Love2D runtime from app directory
        runtime_dir = os.path.join(RUNTIMES_PATH, love_version, 'macos')
        if not os.path.exists(runtime_dir):
            raise Exception(f"Love2D runtime files not found for version {love_version} on MacOS. Please ensure the runtime files are in the 'runtimes/{love_version}/macos' directory.")
        
        # Create .app structure
        app_name = f"{project['name']}.app"
        app_path = os.path.join(export_data['output_dir'], app_name)
        contents_path = os.path.join(app_path, "Contents")
        resources_path = os.path.join(contents_path, "Resources")
        macos_path = os.path.join(contents_path, "MacOS")
        
        os.makedirs(resources_path, exist_ok=True)
        os.makedirs(macos_path, exist_ok=True)

        # Copy .love file
        shutil.copy2(love_path, os.path.join(resources_path, "game.love"))

        # Create Info.plist
        plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleIdentifier</key>
    <string>{export_data['bundle_id']}</string>
    <key>CFBundleName</key>
    <string>{project['name']}</string>
    <key>CFBundleDisplayName</key>
    <string>{project['name']}</string>
    <key>CFBundleVersion</key>
    <string>{export_data['version']}</string>
    <key>CFBundleShortVersionString</key>
    <string>{export_data['version']}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>LOVE</string>
    <key>CFBundleExecutable</key>
    <string>love</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>'''
        
        with open(os.path.join(contents_path, "Info.plist"), 'w') as f:
            f.write(plist_content)

        # Copy Love2D binary and libraries
        for file in os.listdir(runtime_dir):
            src = os.path.join(runtime_dir, file)
            if file == 'love':
                dst = os.path.join(macos_path, file)
            else:
                dst = os.path.join(resources_path, file)
            if os.path.isfile(src):
                shutil.copy2(src, dst)

        # Copy project libraries
        self.copy_project_libs(project['path'], 'MacOS', resources_path)

    def ExportLinux(self, project, export_data, love_path, temp_dir, love_version):
        # Get Love2D runtime from app directory
        runtime_dir = os.path.join(RUNTIMES_PATH, love_version, 'linux')
        if not os.path.exists(runtime_dir):
            raise Exception(f"Love2D runtime files not found for version {love_version} on Linux. Please ensure the runtime files are in the 'runtimes/{love_version}/linux' directory.")
        
        # Create AppDir structure
        appimage_dir = os.path.join(export_data['output_dir'], "AppDir")
        os.makedirs(appimage_dir, exist_ok=True)

        # Create .desktop file
        desktop_content = f'''[Desktop Entry]
Name={project['name']}
Exec=love %f
Type=Application
Categories=Game;
Comment={export_data.get('description', '')}
'''
        with open(os.path.join(appimage_dir, f"{project['name']}.desktop"), 'w') as f:
            f.write(desktop_content)

        # Copy .love file
        shutil.copy2(love_path, os.path.join(appimage_dir, "game.love"))

        # Copy Love2D runtime files
        for file in os.listdir(runtime_dir):
            src = os.path.join(runtime_dir, file)
            dst = os.path.join(appimage_dir, file)
            if os.path.isfile(src):
                shutil.copy2(src, dst)

        # Copy project libraries
        self.copy_project_libs(project['path'], 'Linux', appimage_dir)

        # Note: Full AppImage creation would require additional tools and configuration
        wx.MessageBox("Linux export created basic AppDir structure. Full AppImage creation requires additional setup.", 
                     "Linux Export", wx.OK | wx.ICON_INFORMATION)

    def copy_project_libs(self, project_path, target_os, dest_path):
        """Copy required libraries for the target OS to the destination folder"""
        # Read project metadata
        proj_name = os.path.basename(project_path)
        heartproj_path = os.path.join(project_path, f"{proj_name}.heartproj")
        if not os.path.exists(heartproj_path):
            return
        
        with open(heartproj_path, 'r', encoding='utf-8') as f:
            project_data = yaml.safe_load(f)
            libs = project_data.get('libs', [])
        
        if not libs:
            return
        
        # Copy each library's files
        for lib in libs:
            lib_files = get_lib_files(lib, target_os)
            for file in lib_files:
                src = os.path.join(LIBS_PATH, lib, target_os.lower(), file)
                if os.path.exists(src):
                    shutil.copy2(src, os.path.join(dest_path, file))

class ProjectDialog(wx.Dialog):
    def __init__(self, parent, project_path=None, edit_mode=False):
        super().__init__(parent, title="Create New Project" if not edit_mode else "Edit Project", size=(420, 500))
        self.project_path = project_path
        self.edit_mode = edit_mode
        self.InitUI()
        self.Center()

    def InitUI(self):
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

        # Love2D Version
        hbox_love_version = wx.BoxSizer(wx.HORIZONTAL)
        hbox_love_version.Add(wx.StaticText(panel, label="Love2D Version:"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 8)
        self.love_version_choice = wx.Choice(panel, choices=get_available_runtimes())
        if self.love_version_choice.GetCount() > 0:
            self.love_version_choice.SetSelection(0)
        hbox_love_version.Add(self.love_version_choice, 1)
        vbox.Add(hbox_love_version, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 8)

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
        else:
            vbox.Add(wx.StaticText(panel, label="No libraries found in libs folder."), 0, wx.LEFT|wx.RIGHT|wx.TOP, 8)

        # Buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(panel, wx.ID_OK, "OK")
        cancel_button = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        button_sizer.Add(ok_button, 0, wx.ALL, 5)
        button_sizer.Add(cancel_button, 0, wx.ALL, 5)
        vbox.Add(button_sizer, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        panel.SetSizer(vbox)
        main_sizer.Add(panel, 1, wx.EXPAND|wx.ALL, 0)
        self.SetSizer(main_sizer)

        if self.edit_mode:
            self.LoadProjectData()

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

    def LoadProjectData(self):
        if self.project_path:
            with open(os.path.join(self.project_path, f"{os.path.basename(self.project_path)}.heartproj"), 'r', encoding='utf-8') as f:
                project_data = yaml.safe_load(f)
                self.name_ctrl.SetValue(project_data['name'])
                self.path_ctrl.SetValue(self.project_path)
                self.love_version_choice.SetSelection(self.love_version_choice.FindString(project_data['love_version']))
                self.icon_ctrl.SetValue(project_data.get('icon', ''))
                self.desc_ctrl.SetValue(project_data.get('description', ''))
                self.version_ctrl.SetValue(project_data['version'])
                self.author_ctrl.SetValue(project_data['author'])
                for lib in project_data.get('libs', []):
                    for cb in self.lib_checkboxes:
                        if cb.GetLabel() == lib:
                            cb.SetValue(True)

    def GetData(self):
        libs = [cb.GetLabel() for cb in getattr(self, 'lib_checkboxes', []) if cb.GetValue()]
        return {
            'name': self.name_ctrl.GetValue(),
            'path': self.path_ctrl.GetValue(),
            'icon': self.icon_ctrl.GetValue(),
            'description': self.desc_ctrl.GetValue(),
            'version': self.version_ctrl.GetValue(),
            'author': self.author_ctrl.GetValue(),
            'libs': libs,
            'love_version': self.love_version_choice.GetString(self.love_version_choice.GetSelection())
        }

class ExportDialog(wx.Dialog):
    def __init__(self, parent, project):
        super().__init__(parent, title=f"Export {project['name']}", size=(400, 500))
        self.project = project
        self.InitUI()
        self.Center()

    def InitUI(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Platform selection
        platform_box = wx.StaticBox(panel, label="Target Platform")
        platform_sizer = wx.StaticBoxSizer(platform_box, wx.VERTICAL)
        self.platform_choice = wx.Choice(panel, choices=['Windows', 'MacOS', 'Linux'])
        platform_sizer.Add(self.platform_choice, 0, wx.EXPAND|wx.ALL, 5)
        vbox.Add(platform_sizer, 0, wx.EXPAND|wx.ALL, 5)

        # Runtime warning
        self.runtime_warning = wx.StaticText(panel, label="")
        self.runtime_warning.SetForegroundColour(wx.Colour(255, 140, 0))  # Orange
        vbox.Add(self.runtime_warning, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)

        # Output directory
        dir_box = wx.StaticBox(panel, label="Output Directory")
        dir_sizer = wx.StaticBoxSizer(dir_box, wx.VERTICAL)
        dir_hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.dir_ctrl = wx.TextCtrl(panel)
        browse_btn = wx.Button(panel, label="Browse")
        browse_btn.Bind(wx.EVT_BUTTON, self.OnBrowseDir)
        dir_hbox.Add(self.dir_ctrl, 1, wx.RIGHT, 5)
        dir_hbox.Add(browse_btn, 0)
        dir_sizer.Add(dir_hbox, 0, wx.EXPAND|wx.ALL, 5)
        vbox.Add(dir_sizer, 0, wx.EXPAND|wx.ALL, 5)

        # Bundle ID (for MacOS)
        self.bundle_id_ctrl = wx.TextCtrl(panel)
        self.bundle_id_ctrl.SetValue(f"com.{self.project['name'].lower()}")
        vbox.Add(wx.StaticText(panel, label="Bundle ID:"), 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        vbox.Add(self.bundle_id_ctrl, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)

        # Version
        self.version_ctrl = wx.TextCtrl(panel)
        self.version_ctrl.SetValue("1.0.0")
        vbox.Add(wx.StaticText(panel, label="Version:"), 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        vbox.Add(self.version_ctrl, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)

        # Description
        self.desc_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        vbox.Add(wx.StaticText(panel, label="Description:"), 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        vbox.Add(self.desc_ctrl, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)

        # Buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(panel, wx.ID_OK, "OK")
        cancel_button = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        button_sizer.Add(ok_button, 0, wx.ALL, 5)
        button_sizer.Add(cancel_button, 0, wx.ALL, 5)
        vbox.Add(button_sizer, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        panel.SetSizer(vbox)

        # Set default output directory
        default_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                 'exports', 
                                 self.project['name'],
                                 self.platform_choice.GetString(0).lower())
        self.dir_ctrl.SetValue(default_dir)

        # Bind events
        self.platform_choice.Bind(wx.EVT_CHOICE, self.OnPlatformChange)
        self.OnPlatformChange(None)  # Set initial warning

    def OnBrowseDir(self, event):
        dlg = wx.DirDialog(self, "Select Output Directory")
        if dlg.ShowModal() == wx.ID_OK:
            self.dir_ctrl.SetValue(dlg.GetPath())
        dlg.Destroy()

    def OnPlatformChange(self, event):
        platform = self.platform_choice.GetString(self.platform_choice.GetSelection()).lower()
        # Get Love2D version from project .heartproj
        love_version = None
        if hasattr(self, 'project') and self.project:
            proj_name = os.path.basename(self.project['path'])
            heartproj_path = os.path.join(self.project['path'], f"{proj_name}.heartproj")
            if os.path.exists(heartproj_path):
                with open(heartproj_path, 'r', encoding='utf-8') as f:
                    project_data = yaml.safe_load(f)
                    love_version = project_data.get('love_version')
        if not love_version:
            love_version = '11.5'  # fallback default
        runtime_dir = os.path.join(RUNTIMES_PATH, love_version, platform)
        if not os.path.exists(runtime_dir):
            self.runtime_warning.SetLabel(f"Warning: No runtime found for {platform} ({love_version}) in runtimes folder. Export will skip copying the runtime.")
        else:
            self.runtime_warning.SetLabel("")
        # Update default output directory
        default_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                 'exports', 
                                 self.project['name'],
                                 platform)
        self.dir_ctrl.SetValue(default_dir)

    def GetData(self):
        return {
            'platform': self.platform_choice.GetString(self.platform_choice.GetSelection()),
            'output_dir': self.dir_ctrl.GetValue(),
            'bundle_id': self.bundle_id_ctrl.GetValue(),
            'version': self.version_ctrl.GetValue(),
            'description': self.desc_ctrl.GetValue()
        }

def main():
    app = wx.App(False)
    ProjectManagerFrame()
    app.MainLoop()

if __name__ == "__main__":
    main() 