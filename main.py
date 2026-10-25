# main.py
import tkinter as tk
from tkinter import ttk
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
    
    # Делаем окно поверх других, но не забираем фокус у игры постоянно
    root.attributes('-topmost', True)

    lbl = ttk.Label(root, text="Переводчик запущен!\nF8 - Перевести\nF9 - Убрать окошки\nF10 или кнопка - Выход", justify="center", font=("Arial", 10))
    lbl.pack(pady=10)

    overlay = OverlayManager(root)

    # Функция корректного завершения
    def close_app():
        listener.stop()
        root.quit()
        root.destroy()

    # Кнопка выхода
    btn_quit = ttk.Button(root, text="Завершить работу", command=close_app)
    btn_quit.pack()
    
    # Перехват нажатия на крестик окна
    root.protocol("WM_DELETE_WINDOW", close_app)

    # 3. Запуск горячих клавиш (передаем close_app для F10)
    listener = start_hotkeys(on_capture, on_clear, close_app, root)
    
    # 4. Очередь оверлея
    root.after(80, pump_queue, root, overlay)

    print(f"Запущено. F8 - перевести, F9 - убрать, F10 - выход.")
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        close_app()

if __name__ == '__main__':
    main()