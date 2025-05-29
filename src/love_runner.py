import os
import subprocess
import sys

def run_love_project(path):
    # Look for love.exe in the same directory as the executable
    exe_dir = os.path.dirname(sys.executable)
    love_exe = os.path.join(exe_dir, 'love.exe')
    if not os.path.exists(love_exe):
        # Fallback to system path
        love_exe = 'love'
    subprocess.Popen([love_exe, path]) 