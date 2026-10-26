# main.py
import ctypes
import tkinter as tk
from tkinter import ttk

# Отключаем масштабирование Windows для нашей программы (КРИТИЧНО ДЛЯ НОУТБУКОВ)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2) # Для Windows 8.1+
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()      # Для старых Windows

import config
from setup_gui import SetupWindow
from overlay import OverlayManager
from hotkeys import start_hotkeys
from worker import on_capture, on_clear, pump_queue

def main():
    # 1. Показываем окно настроек
    root_setup = tk.Tk()
    setup = SetupWindow(root_setup)
    root_setup.mainloop()
    
    if not setup.saved:
        return

    # 2. Создаем главное окно (Пульт управления)
    root = tk.Tk()
    root.title("Переводчик активен")
    root.geometry("350x120")
    root.resizable(False, False)
    root.attributes('-topmost', True)

    lbl = ttk.Label(root, text="Переводчик запущен!\nF8 - Перевести\nF9 - Убрать окошки\nF10 или кнопка - Выход", justify="center", font=("Arial", 10))
    lbl.pack(pady=10)

    overlay = OverlayManager(root)

    def close_app():
        listener.stop()
        root.quit()
        root.destroy()

    btn_quit = ttk.Button(root, text="Завершить работу", command=close_app)
    btn_quit.pack()
    root.protocol("WM_DELETE_WINDOW", close_app)

    listener = start_hotkeys(on_capture, on_clear, close_app, root)
    root.after(80, pump_queue, root, overlay)

    print(f"Запущено. F8 - перевести, F9 - убрать, F10 - выход.")
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        close_app()

if __name__ == '__main__':
    main()