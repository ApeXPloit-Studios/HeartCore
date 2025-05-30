import os
import sys
import shutil
import subprocess
import requests
import zipfile
from io import BytesIO

APP_NAME = "HeartCore"
ENTRY_POINT = "app.py"
ICON_PATH = "icon.ico"
REQUIREMENTS = "requirements.txt"

RUNTIMES_VERSION = "11.5"
PLATFORMS = {
    "windows": {
        "url": "https://github.com/love2d/love/releases/download/11.5/love-11.5-win64.zip",
        "extract": True
    },
    "macos": {
        "url": "https://github.com/love2d/love/releases/download/11.5/love-11.5-macos.zip",
        "extract": True
    },
    "linux": {
        "url": "https://github.com/love2d/love/releases/download/11.5/love-11.5-x86_64.AppImage",
        "extract": False
    }
}

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

# Install dependencies
print("Installing dependencies from requirements.txt ...")
subprocess.run([sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS], check=True)

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

# Create runtimes and libs inside DIST_PATH
RUNTIMES_PATH = os.path.join(DIST_PATH, "runtimes", RUNTIMES_VERSION)
if os.path.exists(os.path.join(DIST_PATH, "runtimes")):
    shutil.rmtree(os.path.join(DIST_PATH, "runtimes"))
os.makedirs(RUNTIMES_PATH, exist_ok=True)

for platform, info in PLATFORMS.items():
    plat_dir = os.path.join(RUNTIMES_PATH, platform)
    os.makedirs(plat_dir, exist_ok=True)
    print(f"Downloading Love2D 11.5 for {platform}...")
    r = requests.get(info["url"])
    if info["extract"]:
        with zipfile.ZipFile(BytesIO(r.content)) as z:
            if platform == "windows":
                # Extract love.exe and all .dll files
                for member in z.namelist():
                    if member.endswith("love.exe") or member.endswith(".dll"):
                        z.extract(member, plat_dir)
                        # Move to plat_dir root if in subfolder
                        src = os.path.join(plat_dir, member)
                        dst = os.path.join(plat_dir, os.path.basename(member))
                        shutil.move(src, dst)
                        # Remove now-empty subfolder
                        subfolder = os.path.join(plat_dir, os.path.dirname(member))
                        if os.path.isdir(subfolder) and not os.listdir(subfolder):
                            os.rmdir(subfolder)
            elif platform == "macos":
                # Extract the love.app folder
                for member in z.namelist():
                    if member.startswith("love.app/"):
                        z.extract(member, plat_dir)
    else:
        # Save AppImage directly
        appimage_path = os.path.join(plat_dir, "love-11.5-x86_64.AppImage")
        with open(appimage_path, "wb") as f:
            f.write(r.content)
        print(f"Saved AppImage to {appimage_path}")

# Optionally create an empty libs folder inside DIST_PATH
libs_path = os.path.join(DIST_PATH, "libs")
if os.path.exists(libs_path):
    shutil.rmtree(libs_path)
os.makedirs(libs_path, exist_ok=True)

print(f"\nLove2D runtimes for 11.5 have been set up in '{os.path.join(DIST_PATH, 'runtimes')}'.")
print(f"An empty 'libs' folder has also been created in '{DIST_PATH}'.")
print(f"\nBuild complete! Check the '{DIST_PATH}' folder for the executable and required folders.") 