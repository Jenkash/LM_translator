# worker.py
import threading
import queue
import time
import traceback

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
    task_queue.put(('clear',))
    threading.Thread(target=_process_capture, daemon=True).start()

def on_clear():
    task_queue.put(('clear',))

def _process_local(img):
    t0 = time.perf_counter()
    blocks = recognize(img)
    t1 = time.perf_counter()

    filtered = []
    for b in blocks:
        if b['conf'] < config.MIN_CONFIDENCE: continue
        text = b['text'].strip()
        if len(text) < config.MIN_TEXT_LEN: continue
        b['text'] = text
        filtered.append(b)

    texts = [b['text'] for b in filtered]
    translations = translate_batch(texts)
    t2 = time.perf_counter()

    final = []
    for b, tr in zip(filtered, translations):
        if tr and tr.strip().lower() != b['text'].strip().lower():
            b['translation'] = tr
            final.append(b)

    return final, (t1 - t0, t2 - t1), len(blocks)

def _process_vision(img):
    t0 = time.perf_counter()
    blocks = translate_screenshot(img)
    t1 = time.perf_counter()
    return blocks, (0.0, t1 - t0), len(blocks)

def _process_capture():
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

        task_queue.put(('show', final, monitor))
        
    except Exception as e:
        print("\n[ERROR in _process_capture]:")
        traceback.print_exc()

def pump_queue(root, overlay):
    try:
        while True:
            cmd, *args = task_queue.get_nowait()
            if cmd == 'clear':
                overlay.clear()
            elif cmd == 'show':
                blocks, monitor = args
                print(f"[DEBUG] Рисуем {len(blocks)} блоков на экране...")
                if blocks:
                    print(f"[DEBUG] Координаты первого блока: x1={blocks[0]['x1']}, y1={blocks[0]['y1']}")
                
                overlay.show_blocks(
                    blocks,
                    offset_x=monitor['left'],
                    offset_y=monitor['top'],
                )
    except queue.Empty:
        pass
    except Exception as e:
        print("\n[ERROR in pump_queue]:")
        traceback.print_exc()
        
    root.after(80, pump_queue, root, overlay)