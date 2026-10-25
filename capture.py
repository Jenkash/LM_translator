# capture.py
import mss
import numpy as np
import config

def capture_screen(region=None):
    """
    region: None — весь основной монитор (или CAPTURE_REGION),
            либо dict {'top','left','width','height'}.
    Возвращает (img_rgb, region_dict).
    """
    if region is None:
        region = config.CAPTURE_REGION

    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Данные о всем экране
        
        # Если выбран режим Arknights и не задана кастомная область
        if config.GAME_MODE == "arknights" and region is None:
            w = monitor["width"]
            h = monitor["height"]
            # Захватываем нижние 25% экрана, оставляя по 5% отступов по бокам
            region = {
                "top": monitor["top"] + int(h * 0.75),
                "left": monitor["left"] + int(w * 0.05),
                "width": int(w * 0.90),
                "height": int(h * 0.25)
            }
        elif region is None:
            # Обычный режим — весь экран
            region = monitor

        # Делаем скриншот нужной области
        shot = sct.grab(region)
        img = np.array(shot)[:, :, :3]     # BGRA -> BGR
        img = img[:, :, ::-1].copy()       # BGR -> RGB
        
        # Возвращаем картинку и координаты области захвата.
        # Благодаря этому оверлеи поймут, куда их ставить на экране.
        return img, region