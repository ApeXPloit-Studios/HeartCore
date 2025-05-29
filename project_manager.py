import os
import sys
import json

# Save projects.json in the same folder as the app executable
if getattr(sys, 'frozen', False):
    # Running as compiled exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running as script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECTS_FILE = os.path.join(BASE_DIR, "projects.json")

def load_projects():
    if not os.path.exists(PROJECTS_FILE):
        return []
    with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_projects(projects):
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(projects, f, indent=2)

def add_project(project):
    projects = load_projects()
    projects.append(project)
    save_projects(projects)

def remove_project(index):
    projects = load_projects()
    if 0 <= index < len(projects):
        projects.pop(index)
        save_projects(projects) 