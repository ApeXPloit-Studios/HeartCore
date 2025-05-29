import os
import sys
import shutil
import subprocess
import requests
import zipfile
from io import BytesIO
import yaml

APP_NAME = "HeartCore"
ENTRY_POINT = "app.py"
ICON_PATH = "icon.ico"
REQUIREMENTS = "requirements.txt"

def get_project_libs(project_path):
    """Get list of libraries from project's .heartproj file"""
    proj_name = os.path.basename(project_path)
    heartproj_path = os.path.join(project_path, f"{proj_name}.heartproj")
    if not os.path.exists(heartproj_path):
        return []
    with open(heartproj_path, 'r', encoding='utf-8') as f:
        project_data = yaml.safe_load(f)
        return project_data.get('libs', [])

def copy_project_libs(project_path, target_os, dist_path):
    """Copy required libraries for the target OS to the dist folder"""
    libs = get_project_libs(project_path)
    if not libs:
        return
    
    # Create libs directory in dist
    libs_dst = os.path.join(dist_path, 'libs')
    os.makedirs(libs_dst, exist_ok=True)
    
    # Copy each library from the appropriate OS folder
    for lib in libs:
        src = os.path.join('libs', target_os.lower(), lib)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(libs_dst, lib))
            print(f"Copied library: {lib}")
        else:
            print(f"Warning: Library not found for {target_os}: {lib}")

# Install dependencies
print("Installing dependencies from requirements.txt ...")
subprocess.run([sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS], check=True)

# OS options
os_options = {
    '1': 'Windows',
    '2': 'Linux',
    '3': 'MacOS',
}

print("Select target OS:")
for k, v in os_options.items():
    print(f"  {k}. {v}")
os_choice = input("Enter number: ").strip()

if os_choice not in os_options:
    print("Invalid choice. Exiting.")
    sys.exit(1)

TARGET_OS = os_options[os_choice]
DIST_PATH = os.path.join("dist", TARGET_OS)

# Clean previous build
if os.path.exists(DIST_PATH):
    shutil.rmtree(DIST_PATH)

if TARGET_OS == 'Windows':
    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onefile",
        "--noconsole",
        "--distpath", DIST_PATH,
        ENTRY_POINT
    ]
    if os.path.exists(ICON_PATH):
        cmd.extend(["--icon", ICON_PATH])
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    
    # Download and extract LÖVE for Windows
    love_url = "https://github.com/love2d/love/releases/download/11.5/love-11.5-win64.zip"
    print(f"Downloading LÖVE for Windows from {love_url} ...")
    r = requests.get(love_url)
    with zipfile.ZipFile(BytesIO(r.content)) as z:
        for member in z.namelist():
            # Only extract love.exe and DLLs to the dist folder
            if member.endswith("love.exe") or member.endswith(".dll"):
                z.extract(member, DIST_PATH)
                # Move from subfolder to DIST_PATH root
                src = os.path.join(DIST_PATH, member)
                dst = os.path.join(DIST_PATH, os.path.basename(member))
                shutil.move(src, dst)
                # Remove now-empty subfolder
                subfolder = os.path.join(DIST_PATH, os.path.dirname(member))
                if os.path.isdir(subfolder) and not os.listdir(subfolder):
                    os.rmdir(subfolder)
    
    # Copy project libraries for the target OS
    copy_project_libs(os.getcwd(), TARGET_OS, DIST_PATH)
    
    print(f"\nBuild complete! Check the '{DIST_PATH}' folder for the executable and love.exe.")
else:
    print(f"Build for {TARGET_OS} is not implemented yet.") 