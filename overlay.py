# overlay.py
import ctypes
import tkinter as tk
import config

GWL_EXSTYLE       = -20
WS_EX_LAYERED     = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW  = 0x00000080
WS_EX_NOACTIVATE  = 0x08000000

def make_click_through(window):
    window.update_idletasks()
    hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
    if hwnd == 0:
        hwnd = window.winfo_id()
    style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    ctypes.windll.user32.SetWindowLongW(
        hwnd, GWL_EXSTYLE,
        style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
    )

class OverlayManager:
    def __init__(self, root):
        self.root = root
        
        # Создаем ОДНО окно на весь экран при запуске
        self.win = tk.Toplevel(self.root)
        self.win.overrideredirect(True)
        self.win.attributes('-topmost', True)
        
        # Получаем размеры экрана
        screen_w = self.win.winfo_screenwidth()
        screen_h = self.win.winfo_screenheight()
        self.win.geometry(f"{screen_w}x{screen_h}+0+0")
        
        # Делаем окно "прозрачным" через магический цвет
        # Всё, что нарисовано этим цветом (magenta), станет прозрачным
        self.transparent_color = "#FF00FF"
        self.win.configure(bg=self.transparent_color)
        self.win.attributes('-transparentcolor', self.transparent_color)
        
        # Создаем холст для рисования
        self.canvas = tk.Canvas(
            self.win, 
            bg=self.transparent_color, 
            highlightthickness=0
        )
        self.canvas.pack(fill='both', expand=True)
        
        # Применяем клик-сквозь
        make_click_through(self.win)

    def clear(self):
        # Очищаем холст (удаляем все нарисованные окошки)
        self.canvas.delete("all")

    def show_blocks(self, blocks, offset_x, offset_y):
        self.clear()
        
        for b in blocks:
            # Вычисляем координаты с учетом смещения области захвата
            x1 = offset_x + int(b['x1'])
            y1 = offset_y + int(b['y1'])
            x2 = offset_x + int(b['x2'])
            y2 = offset_y + int(b['y2'])
            
            # Чуть-чуть поднимаем окошко вверх, чтобы оно ложилось ровно на текст
            y1 -= 5
            y2 -= 5
            
            # Делаем ширину и высоту адекватными
            ww = max(x2 - x1, 60)
            hh = max(y2 - y1, 24)
            
            # 1. Рисуем полупрозрачный черный фон
            # Tkinter Canvas не умеет в прозрачность отдельных фигур, 
            # поэтому мы просто рисуем черный прямоугольник.
            self.canvas.create_rectangle(
                x1, y1, x1 + ww, y1 + hh,
                fill=config.OVERLAY_BG, 
                outline=""
            )
            
            # 2. Рисуем текст перевода поверх прямоугольника
            self.canvas.create_text(
                x1 + 4, y1 + 2,
                text=b['translation'],
                fill=config.OVERLAY_FG,
                anchor='nw',
                width=ww - 8,  # Автоматический перенос строк
                font=config.OVERLAY_FONT
            )