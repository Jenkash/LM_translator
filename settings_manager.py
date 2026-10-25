# settings_manager.py
import json
import os
import sys

def get_settings_path():
    # Если запущено как .exe, сохраняем рядом с .exe
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "settings.json")

def load_settings():
    path = get_settings_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return None

def save_settings(settings):
    path = get_settings_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)