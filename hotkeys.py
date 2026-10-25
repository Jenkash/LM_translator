# hotkeys.py
from pynput import keyboard
import config

def start_hotkeys(on_capture, on_clear, on_exit, root_window):
    def safe_exit():
        # Tkinter нельзя закрывать напрямую из фонового потока, 
        # поэтому просим главный поток это сделать
        root_window.after(0, on_exit)

    listener = keyboard.GlobalHotKeys({
        config.HOTKEY_CAPTURE: on_capture,
        config.HOTKEY_CLEAR:   on_clear,
        config.HOTKEY_EXIT:    safe_exit,
    })
    listener.start()
    return listener