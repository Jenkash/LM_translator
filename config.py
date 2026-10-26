# config.py
import os
import sys
import settings_manager

saved = settings_manager.load_settings() or {}

# 1. ОБЩИЕ НАСТРОЙКИ
GAME_MODE = saved.get("GAME_MODE", "arknights")
VISION_ENGINE = saved.get("VISION_ENGINE", "tokenharbor")

# 2. ЯЗЫКОВЫЕ НАСТРОЙКИ
FROM_LANG = saved.get("FROM_LANG", "en")
TO_LANG = saved.get("TO_LANG", "ru")
TARGET_LANG_NAME = saved.get("TARGET_LANG_NAME", "Russian")

# 3. НАСТРОЙКИ API
TOKENHARBOR_API_KEY  = saved.get("TOKENHARBOR_API_KEY", "")
TOKENHARBOR_BASE_URL = saved.get("TOKENHARBOR_BASE_URL", "https://tokenharbor.ai/v1")
TOKENHARBOR_MODEL    = saved.get("TOKENHARBOR_MODEL", "deepseek-v4.1-flash:free")

LMSTUDIO_BASE_URL = "http://localhost:1234/v1"
LMSTUDIO_API_KEY  = "lm-studio"
LMSTUDIO_MODEL    = saved.get("LMSTUDIO_MODEL", "minicpm-v-2_6")

VISION_MAX_TOKENS    = 4096
VISION_TEMPERATURE   = 0.0
VISION_MAX_WIDTH     = 1024
VISION_MAX_HEIGHT    = 576

# 4. ГОРЯЧИЕ КЛАВИШИ
HOTKEY_CAPTURE = "<f8>"
HOTKEY_CLEAR   = "<f9>"
HOTKEY_EXIT    = "<f10>" 

# None = весь экран (если GAME_MODE = "default")
CAPTURE_REGION = None

# ==========================================
# 5. НАСТРОЙКИ ОВЕРЛЕЯ (ОКОШЕК)
# ==========================================
OVERLAY_ALPHA     = 0.85
OVERLAY_BG        = "black"
OVERLAY_FG        = "white"
OVERLAY_FONT      = ("Arial", 12)

# ==========================================
# 6. ЛОКАЛЬНЫЙ OCR (Если VISION_ENGINE = "local")
# ==========================================
USE_GPU            = True
DETECT_NETWORK     = "craft"
QUANTIZE           = True
TEXT_THRESHOLD     = 0.6
LOW_TEXT           = 0.3
ADJUST_CONTRAST    = True
CONTRAST_THS       = 0.05
DECODER            = "greedy"
CANVAS_SIZE        = 1280
MAG_RATIO          = 1.0
BATCH_SIZE         = 8
MIN_CONFIDENCE     = 0.45
MIN_TEXT_LEN       = 4

# Предобработка
ENABLE_PREPROCESS  = True
PREPROCESS_MODE    = "light"
AUTO_PICK_BY_CONF  = False
UPSCALE_FACTOR     = 2
USE_CLAHE          = True
CLAHE_CLIP         = 2.5
CLAHE_TILE         = (8, 8)
USE_ADAPTIVE_THRESH = False
ADAPTIVE_BLOCK      = 15
ADAPTIVE_C          = 8
ENABLE_SHARPEN      = False
SHARPEN_STRENGTH    = 0.8

# Склейка блоков
LINE_Y_TOLERANCE   = 0.6
LINE_X_GAP_FACTOR  = 2.0
PARA_Y_GAP_FACTOR  = 0.5
PARA_X_OVERLAP     = 0.40

# Argos Translate
TRANSLATION_ENGINE = "argos"
ARGOS_DEVICE_TYPE  = "auto"
ARGOS_BATCH_SIZE   = 64
GOOGLE_RPS_LIMIT   = 4

# Tesseract (резерв)
USE_TESSERACT_FALLBACK   = False
TESSERACT_CONF_THRESHOLD = 0.65
TESSERACT_LANG           = "eng"
TESSERACT_CMD            = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Прочее
MODELS_DIR = "models"