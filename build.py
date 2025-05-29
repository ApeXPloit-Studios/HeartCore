import os
import sys
import shutil
import subprocess
import requests
import zipfile
from io import BytesIO

APP_NAME = "HeartCore"
ENTRY_POINT = os.path.join("src", "app.py")
ICON_PATH = os.path.join("src", "icon.ico")  # Optional: provide your own icon
REQUIREMENTS = "requirements.txt"

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
    # Copy libs folder
    libs_src = os.path.join(os.getcwd(), 'libs')
    libs_dst = os.path.join(DIST_PATH, 'libs')
    if os.path.exists(libs_src):
        print(f"Copying libraries from {libs_src} to {libs_dst} ...")
        shutil.copytree(libs_src, libs_dst)
    print(f"\nBuild complete! Check the '{DIST_PATH}' folder for the executable and love.exe.")
else:
    print(f"Build for {TARGET_OS} is not implemented yet.") 