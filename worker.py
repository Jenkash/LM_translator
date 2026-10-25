# worker.py
import threading
import queue
import time

import config
from capture import capture_screen

# Условный импорт: выбираем движок в зависимости от настроек
if config.VISION_ENGINE in ("tokenharbor", "lmstudio"):
    from api_vision import translate_screenshot
else:
    from ocr import recognize
    from translator import translate_batch

task_queue = queue.Queue()


def on_capture():
    """Вызывается при нажатии горячей клавиши (F8)."""
    task_queue.put(('clear',))  # Сначала убираем старые оверлеи
    threading.Thread(target=_process_capture, daemon=True).start()


def on_clear():
    """Вызывается при нажатии клавиши очистки (F9)."""
    task_queue.put(('clear',))


def _process_local(img):
    """Локальный пайплайн: EasyOCR + Argos/Google."""
    t0 = time.perf_counter()

    blocks = recognize(img)
    t1 = time.perf_counter()

    filtered = []
    for b in blocks:
        if b['conf'] < config.MIN_CONFIDENCE:
            continue
        text = b['text'].strip()
        if len(text) < config.MIN_TEXT_LEN:
            continue
        b['text'] = text
        filtered.append(b)

    texts = [b['text'] for b in filtered]
    translations = translate_batch(texts)
    t2 = time.perf_counter()

    final = []
    for b, tr in zip(filtered, translations):
        # Если перевод пустой или совпадает с оригиналом — пропускаем
        if tr and tr.strip().lower() != b['text'].strip().lower():
            b['translation'] = tr
            final.append(b)

    return final, (t1 - t0, t2 - t1), len(blocks)


def _process_vision(img):
    """Облачный или локальный AI пайплайн: TokenHarbor или LM Studio."""
    t0 = time.perf_counter()
    # Функция translate_screenshot сама знает, к какому серверу обращаться,
    # благодаря настройкам в config.py
    blocks = translate_screenshot(img)
    t1 = time.perf_counter()
    return blocks, (0.0, t1 - t0), len(blocks)


def _process_capture():
    """Основная функция обработки кадра."""
    try:
        img, monitor = capture_screen()

        if config.VISION_ENGINE in ("tokenharbor", "lmstudio"):
            final, timings, total = _process_vision(img)
        else:
            final, timings, total = _process_local(img)

        print(f"[{config.VISION_ENGINE}] "
              f"ocr: {timings[0]:.2f}s  "
              f"translate: {timings[1]:.2f}s  "
              f"blocks: {len(final)}/{total}")

        # Отправляем результат в главный поток для отрисовки
        task_queue.put(('show', final, monitor))
        
    except Exception as e:
        print("Ошибка обработки кадра:", e)


def pump_queue(root, overlay):
    """
    Вызывается из главного потока Tkinter по таймеру.
    Забирает результаты из очереди и обновляет оверлеи.
    """
    try:
        while True:
            cmd, *args = task_queue.get_nowait()
            if cmd == 'clear':
                overlay.clear()
            elif cmd == 'show':
                blocks, monitor = args
                overlay.show_blocks(
                    blocks,
                    offset_x=monitor['left'],
                    offset_y=monitor['top'],
                )
    except queue.Empty:
        pass
    # Планируем следующий вызов через 80 мс
    root.after(80, pump_queue, root, overlay)