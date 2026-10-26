# ocr.py
import numpy as np
import easyocr
import config
from preprocess import get_variants

_reader = None
_tess_ready = False

def get_reader():
    global _reader
    if _reader is None:
        # Берем язык игры из конфига. 
        # Если EasyOCR не знает такой язык, он выдаст ошибку при инициализации.
        source_lang = getattr(config, 'FROM_LANG', 'en')
        _reader = easyocr.Reader(
            [source_lang],
            gpu=config.USE_GPU,
            detect_network=config.DETECT_NETWORK,
            quantize=config.QUANTIZE,
        )
    return _reader

# ... (Остальной код ocr.py остается без изменений, можете скопировать его из вашего текущего файла) ...