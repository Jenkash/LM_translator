# api_vision.py
import base64
import io
import json
import re
import cv2
from PIL import Image
from openai import OpenAI
import config
import settings_manager

_client = None

def _get_client():
    global _client
    if _client is None:
        # Читаем актуальные настройки с диска прямо сейчас
        s = settings_manager.load_settings() or {}
        engine = s.get("VISION_ENGINE", "tokenharbor")
        
        if engine == "lmstudio":
            _client = OpenAI(
                api_key="lm-studio",
                base_url=s.get("LMSTUDIO_BASE_URL", "http://localhost:1234/v1"),
                timeout=120.0,
            )
        else:
            api_key = s.get("TOKENHARBOR_API_KEY", "").strip()
            if not api_key:
                raise ValueError("API-ключ не указан в настройках! Закройте программу и запустите заново, чтобы ввести его.")
            
            _client = OpenAI(
                api_key=api_key,
                base_url=s.get("TOKENHARBOR_BASE_URL", "https://tokenharbor.ai/v1"), 
                timeout=120.0,
            )
    return _client

def _resize_if_needed(img_rgb):
    h, w = img_rgb.shape[:2]
    max_w, max_h = config.VISION_MAX_WIDTH, config.VISION_MAX_HEIGHT
    scale = min(1.0, max_w / w, max_h / h)
    if scale >= 1.0:
        return img_rgb, 1.0
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(img_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA), scale

def _encode_image(img_rgb) -> str:
    pil = Image.fromarray(img_rgb)
    buf = io.BytesIO()
    pil.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"

def _parse_blocks(raw_text, scale_back, orig_w, orig_h):
    if not raw_text:
        return []

    cleaned = re.sub(r"```(?:json)?\s*", "", raw_text)
    cleaned = cleaned.replace("```", "").strip()
    start, end = cleaned.find("["), cleaned.rfind("]")
    if start == -1 or end == -1:
        return []

    try:
        data = json.loads(cleaned[start:end + 1])
    except json.JSONDecodeError:
        return []

    result = []
    for it in data:
        bbox = it.get("bbox") or it.get("box")
        if not bbox or len(bbox) < 4:
            continue
        try:
            x1, y1, x2, y2 = [float(v) for v in bbox[:4]]
        except (TypeError, ValueError):
            continue

        # Защита: если модель вернула нормализованные координаты (от 0 до 1)
        if max(x1, y1, x2, y2) <= 1.0:
            x1, x2 = x1 * orig_w, x2 * orig_w
            y1, y2 = y1 * orig_h, y2 * orig_h
        else:
            x1, x2 = x1 * scale_back, x2 * scale_back
            y1, y2 = y1 * scale_back, y2 * scale_back

        x1, x2 = max(0, min(x1, orig_w)), max(0, min(x2, orig_w))
        y1, y2 = max(0, min(y1, orig_h)), max(0, min(y2, orig_h))

        text = (it.get("text") or "").strip()
        translation = (it.get("translation") or "").strip()
        
        if text and translation:
            result.append({
                "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                "text": text, "translation": translation, "conf": 1.0,
            })
    return result

def translate_screenshot(img_rgb):
    # Читаем настройки напрямую из файла для промпта
    s = settings_manager.load_settings() or {}
    target_lang = s.get("TARGET_LANG_NAME", "Russian")
    
    # Определяем имя модели
    if s.get("VISION_ENGINE") == "lmstudio":
        model_name = s.get("LMSTUDIO_MODEL", "minicpm-v-2_6")
    else:
        model_name = s.get("TOKENHARBOR_MODEL", "deepseek-v4.1-flash:free")

    orig_h, orig_w = img_rgb.shape[:2]
    resized, scale = _resize_if_needed(img_rgb)
    scale_back = 1.0 / scale if scale > 0 else 1.0
    
    send_w, send_h = resized.shape[1], resized.shape[0]
    b64_url = _encode_image(resized)

    prompt = f"""
Ты — OCR-переводчик игрового интерфейса.
Размер изображения: {send_w} x {send_h} пикселей.

Найди весь читаемый текст. Для каждого блока верни JSON:
- "bbox": [x1, y1, x2, y2] (в пикселях от 0 до {send_w} и от 0 до {send_h})
- "text": оригинал
- "translation": перевод на {target_lang}

ПРАВИЛА:
1. Каждый отдельный пункт меню, строка или независимое предложение — это ОТДЕЛЬНЫЙ блок.
2. НЕ объединяй в один блок разные пункты меню или далеко стоящие друг от друга предложения.
3. Если текст идет сплошным абзацем (как в книге), объединяй его в один блок.
4. Верни ТОЛЬКО JSON-массив без markdown.
5. Не пиши свои размышления.
/no_think
"""

    try:
        resp = _get_client().chat.completions.create(
            model=model_name,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": b64_url}},
                ],
            }],
            temperature=0.0,
            max_tokens=config.VISION_MAX_TOKENS,
            extra_body={"thinking": {"type": "disabled"}}
        )
    except Exception as e:
        print(f"[API ERROR] {e}")
        return []

    raw = resp.choices[0].message.content
    return _parse_blocks(raw, scale_back, orig_w, orig_h)