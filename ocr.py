# ocr.py
import numpy as np
import easyocr

import config
from preprocess import get_variants

_reader = None
_tess_ready = False


# ---------- Инициализация ----------
def get_reader():
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(
            ['en'],
            gpu=config.USE_GPU,
            detect_network=config.DETECT_NETWORK,
            quantize=config.QUANTIZE,
        )
    return _reader


def warmup():
    dummy = np.zeros((64, 64, 3), dtype=np.uint8)
    get_reader().readtext(
        dummy,
        canvas_size=config.CANVAS_SIZE,
        mag_ratio=config.MAG_RATIO,
    )
    if config.USE_TESSERACT_FALLBACK:
        _init_tesseract()


# ---------- Детекция ----------
def _readtext(img):
    return get_reader().readtext(
        img,
        paragraph=False,
        text_threshold=config.TEXT_THRESHOLD,
        low_text=config.LOW_TEXT,
        adjust_contrast=config.ADJUST_CONTRAST,
        contrast_ths=config.CONTRAST_THS,
        decoder=config.DECODER,
        canvas_size=config.CANVAS_SIZE,
        mag_ratio=config.MAG_RATIO,
        batch_size=config.BATCH_SIZE,
    )


def _score_results(results):
    """Сумма уверенностей по блокам с conf > 0.3."""
    if not results:
        return 0.0
    return sum(float(r[2]) for r in results if float(r[2]) > 0.3)


def detect_text(img):
    """
    Возвращает (results, scale).
    В auto-режиме перебирает варианты предобработки и берёт лучший.
    """
    if not config.ENABLE_PREPROCESS:
        return _readtext(img), 1.0

    if config.PREPROCESS_MODE != 'auto' or not config.AUTO_PICK_BY_CONF:
        _name, variant_img, scale = get_variants(img)[0]
        return _readtext(variant_img), scale

    best_results = None
    best_score = -1.0
    best_scale = 1.0
    best_name = None

    for name, variant_img, scale in get_variants(img):
        try:
            results = _readtext(variant_img)
        except Exception as e:
            print(f"Variant '{name}' failed: {e}")
            continue
        score = _score_results(results)
        if score > best_score:
            best_score = score
            best_results = results
            best_scale = scale
            best_name = name

    if best_name:
        print(f"[ocr] выбрал вариант '{best_name}' "
              f"(score {best_score:.2f}, blocks {len(best_results or [])})")

    return best_results or [], best_scale


# ---------- Tesseract (опционально) ----------
def _init_tesseract():
    global _tess_ready
    if _tess_ready:
        return
    import pytesseract
    if config.TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD
    _tess_ready = True


def _tesseract_read(img_crop):
    import pytesseract
    _init_tesseract()
    try:
        return pytesseract.image_to_string(
            img_crop, lang=config.TESSERACT_LANG
        ).strip()
    except Exception as e:
        print("Tesseract error:", e)
        return ""


# ---------- Склейка блоков ----------
def merge_boxes(results):
    """
    1) слова → строки
    2) строки → абзацы
    """
    items = []
    for bbox, text, conf in results:
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        items.append({
            'x1': min(xs), 'y1': min(ys),
            'x2': max(xs), 'y2': max(ys),
            'text': text, 'conf': float(conf),
        })

    items.sort(key=lambda i: (i['y1'], i['x1']))
    lines = []

    for it in items:
        placed = False
        it_cy = (it['y1'] + it['y2']) / 2
        it_h = max(it['y2'] - it['y1'], 1)

        for line in lines:
            line_cy = (line['y1'] + line['y2']) / 2
            line_h = max(line['y2'] - line['y1'], 1)
            avg_h = (it_h + line_h) / 2

            if abs(it_cy - line_cy) > avg_h * config.LINE_Y_TOLERANCE:
                continue

            gap = it['x1'] - line['x2']
            max_gap = avg_h * config.LINE_X_GAP_FACTOR

            if -avg_h * 0.5 <= gap < max_gap:
                line['x2'] = max(line['x2'], it['x2'])
                line['y1'] = min(line['y1'], it['y1'])
                line['y2'] = max(line['y2'], it['y2'])
                line['text'] += ' ' + it['text']
                line['conf'] = min(line['conf'], it['conf'])
                placed = True
                break

        if not placed:
            lines.append(it.copy())

    lines.sort(key=lambda i: i['y1'])
    paragraphs = []

    for line in lines:
        placed = False
        line_h = max(line['y2'] - line['y1'], 1)
        line_w = line['x2'] - line['x1']

        for p in paragraphs:
            p_h = max(p['y2'] - p['y1'], 1)
            p_w = p['x2'] - p['x1']
            avg_h = (line_h + p_h) / 2

            v_gap = line['y1'] - p['y2']
            if v_gap < -avg_h * 0.5 or v_gap > avg_h * config.PARA_Y_GAP_FACTOR:
                continue

            overlap = min(line['x2'], p['x2']) - max(line['x1'], p['x1'])
            min_w = min(line_w, p_w)
            if min_w <= 0:
                continue
            if overlap < min_w * config.PARA_X_OVERLAP:
                continue

            p['text'] += ' ' + line['text']
            p['x1'] = min(p['x1'], line['x1'])
            p['x2'] = max(p['x2'], line['x2'])
            p['y2'] = max(p['y2'], line['y2'])
            p['conf'] = min(p['conf'], line['conf'])
            placed = True
            break

        if not placed:
            paragraphs.append(line.copy())

    return paragraphs


# ---------- Полный пайплайн ----------
def recognize(img_rgb):
    results, used_scale = detect_text(img_rgb)
    blocks = merge_boxes(results)

    if used_scale and used_scale != 1.0:
        for b in blocks:
            for k in ('x1', 'y1', 'x2', 'y2'):
                b[k] = b[k] / used_scale

    if config.USE_TESSERACT_FALLBACK:
        for b in blocks:
            if b['conf'] < config.TESSERACT_CONF_THRESHOLD:
                x1, y1 = int(b['x1']), int(b['y1'])
                x2, y2 = int(b['x2']), int(b['y2'])
                crop = img_rgb[max(y1, 0):y2, max(x1, 0):x2]
                if crop.size == 0:
                    continue
                text = _tesseract_read(crop)
                if text:
                    b['text'] = text
                    b['conf'] = max(b['conf'], 0.5)

    return blocks