# setup_gui.py
import tkinter as tk
from tkinter import ttk, messagebox
import settings_manager

class SetupWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Настройки переводчика")
        self.root.geometry("480x520")
        self.root.resizable(False, False)
        self.saved = False
        
        self.settings = settings_manager.load_settings() or {
            "GAME_MODE": "arknights",
            "VISION_ENGINE": "tokenharbor",
            "TOKENHARBOR_API_KEY": "",
            "TOKENHARBOR_BASE_URL": "https://tokenharbor.ai/v1",
            "TOKENHARBOR_MODEL": "deepseek-v4.1-flash:free",
            "LMSTUDIO_MODEL": "minicpm-v-2_6"
        }
        
        self.build_ui()

    def build_ui(self):
        # 1. Выбор игры
        frame_game = ttk.LabelFrame(self.root, text="Режим захвата экрана")
        frame_game.pack(fill="x", padx=10, pady=5)
        
        self.var_game = tk.StringVar(value=self.settings.get("GAME_MODE", "arknights"))
        ttk.Radiobutton(frame_game, text="Arknights (только нижняя часть)", variable=self.var_game, value="arknights").pack(anchor="w", padx=5, pady=2)
        ttk.Radiobutton(frame_game, text="Полный экран (для любых других игр)", variable=self.var_game, value="default").pack(anchor="w", padx=5, pady=2)

        # 2. Выбор движка
        frame_engine = ttk.LabelFrame(self.root, text="Движок распознавания")
        frame_engine.pack(fill="x", padx=10, pady=5)
        
        self.var_engine = tk.StringVar(value=self.settings.get("VISION_ENGINE", "tokenharbor"))
        ttk.Radiobutton(frame_engine, text="Облачный API (TokenHarbor, OpenRouter и др.)", variable=self.var_engine, value="tokenharbor", command=self.update_fields).pack(anchor="w", padx=5, pady=2)
        ttk.Radiobutton(frame_engine, text="LM Studio (Локальный AI)", variable=self.var_engine, value="lmstudio", command=self.update_fields).pack(anchor="w", padx=5, pady=2)

        # 3. Поля API
        self.frame_api = ttk.LabelFrame(self.root, text="Настройки облачного API (OpenAI-совместимый)")
        self.frame_api.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(self.frame_api, text="Base URL:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.entry_url = ttk.Entry(self.frame_api, width=45)
        self.entry_url.grid(row=0, column=1, padx=5, pady=2)
        self.entry_url.insert(0, self.settings.get("TOKENHARBOR_BASE_URL", "https://tokenharbor.ai/v1"))

        ttk.Label(self.frame_api, text="API Ключ:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.entry_key = ttk.Entry(self.frame_api, width=45, show="*")
        self.entry_key.grid(row=1, column=1, padx=5, pady=2)
        self.entry_key.insert(0, self.settings.get("TOKENHARBOR_API_KEY", ""))

        ttk.Label(self.frame_api, text="Модель:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.entry_model = ttk.Entry(self.frame_api, width=45)
        self.entry_model.grid(row=2, column=1, padx=5, pady=2)
        self.entry_model.insert(0, self.settings.get("TOKENHARBOR_MODEL", "deepseek-v4.1-flash:free"))

        # 4. Кнопка старта
        self.btn_start = ttk.Button(self.root, text="Сохранить и запустить", command=self.start)
        self.btn_start.pack(pady=20)

        self.update_fields()

    def update_fields(self):
        if self.var_engine.get() == "tokenharbor":
            self.entry_url.config(state="normal")
            self.entry_key.config(state="normal")
            self.entry_model.config(state="normal")
        else:
            self.entry_url.config(state="disabled")
            self.entry_key.config(state="disabled")
            self.entry_model.config(state="disabled")

    def start(self):
        self.settings["GAME_MODE"] = self.var_game.get()
        self.settings["VISION_ENGINE"] = self.var_engine.get()
        self.settings["TOKENHARBOR_BASE_URL"] = self.entry_url.get().strip()
        self.settings["TOKENHARBOR_API_KEY"] = self.entry_key.get().strip()
        self.settings["TOKENHARBOR_MODEL"] = self.entry_model.get().strip()
        
        if self.settings["VISION_ENGINE"] == "tokenharbor" and not self.settings["TOKENHARBOR_API_KEY"]:
            messagebox.showerror("Ошибка", "Введите API-ключ!")
            return
            
        settings_manager.save_settings(self.settings)
        self.saved = True
        self.root.destroy()