# overlay.py
import ctypes
import tkinter as tk
import config

GWL_EXSTYLE       = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW  = 0x00000080
WS_EX_NOACTIVATE  = 0x08000000

def make_click_through(window):
    window.update_idletasks()
    hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
    if hwnd == 0:
        hwnd = window.winfo_id()
    style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    new_style = style | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)

class OverlayManager:
    def __init__(self, root):
        self.root = root
        self.win = tk.Toplevel(self.root)
        self.win.overrideredirect(True)
        self.win.attributes('-topmost', True)
        
        screen_w = self.win.winfo_screenwidth()
        screen_h = self.win.winfo_screenheight()
        self.win.geometry(f"{screen_w}x{screen_h}+0+0")
        
        self.transparent_color = "#FF00FF"
        self.win.configure(bg=self.transparent_color)
        self.win.attributes('-transparentcolor', self.transparent_color)
        
        self.canvas = tk.Canvas(self.win, bg=self.transparent_color, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        make_click_through(self.win)
        self.win.update()
        
        # --- ОТЛАДКА: Рисуем тестовый красный квадрат при запуске ---
        self.canvas.create_rectangle(
            screen_w // 2 - 100, screen_h // 2 - 50, 
            screen_w // 2 + 100, screen_h // 2 + 50, 
            fill="red", outline="white", width=3
        )
        self.canvas.create_text(
            screen_w // 2, screen_h // 2, 
            text="ТЕСТ", fill="white", font=("Arial", 20, "bold")
        )

    def clear(self):
        self.canvas.delete("all")

    def show_blocks(self, blocks, offset_x, offset_y):
        self.clear()
        
        for b in blocks:
            x1 = offset_x + int(b['x1'])
            y1 = offset_y + int(b['y1'])
            x2 = offset_x + int(b['x2'])
            y2 = offset_y + int(b['y2'])
            
            y1 -= 5
            y2 -= 5
            
            ww = max(x2 - x1, 60)
            hh = max(y2 - y1, 24)
            
            self.canvas.create_rectangle(
                x1, y1, x1 + ww, y1 + hh,
                fill=config.OVERLAY_BG, outline=""
            )
            
            self.canvas.create_text(
                x1 + 4, y1 + 2,
                text=b['translation'],
                fill=config.OVERLAY_FG,
                anchor='nw',
                width=ww - 8,
                font=config.OVERLAY_FONT
            )
        
        self.canvas.update()