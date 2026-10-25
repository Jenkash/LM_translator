# translator.py
import os
import time
import threading
import config

os.environ["ARGOS_DEVICE_TYPE"] = config.ARGOS_DEVICE_TYPE
os.environ["ARGOS_BATCH_SIZE"]  = str(config.ARGOS_BATCH_SIZE)

import argostranslate.package
import argostranslate.translate

if config.TRANSLATION_ENGINE == "google":
    from deep_translator import GoogleTranslator

_cache = {}
_google_failures = 0
_google_disabled = False
_google_blocked_until = 0.0


class RateLimiter:
    def __init__(self, max_calls, period):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        self.lock = threading.Lock()

    def wait(self):
        with self.lock:
            now = time.monotonic()
            self.calls = [t for t in self.calls if now - t < self.period]
            if len(self.calls) >= self.max_calls:
                sleep_for = self.period - (now - self.calls[0]) + 0.1
                if sleep_for > 0:
                    time.sleep(sleep_for)
                now = time.monotonic()
                self.calls = [t for t in self.calls if now - t < self.period]
            self.calls.append(now)


_google_limiter = RateLimiter(max_calls=config.GOOGLE_RPS_LIMIT, period=1.0)


# ---------- Argos ----------
def ensure_argos_package(from_code=config.FROM_LANG, to_code=config.TO_LANG):
    if config.TRANSLATION_ENGINE != "argos":
        return
    installed = argostranslate.package.get_installed_packages()
    if any(p.from_code == from_code and p.to_code == to_code
           for p in installed):
        return
    print(f"Скачиваю модель перевода {from_code}->{to_code}...")
    argostranslate.package.update_package_index()
    available = argostranslate.package.get_available_packages()
    pkg = next(p for p in available
               if p.from_code == from_code and p.to_code == to_code)
    argostranslate.package.install_from_path(pkg.download())


def _translate_argos(text):
    return argostranslate.translate.translate(
        text, config.FROM_LANG, config.TO_LANG
    )


# ---------- Google ----------
def _google_is_available():
    global _google_disabled, _google_blocked_until
    if _google_disabled:
        return False
    if time.monotonic() < _google_blocked_until:
        return False
    return True


def _translate_google_batch(texts):
    global _google_failures, _google_disabled, _google_blocked_until

    if not _google_is_available():
        raise RuntimeError("Google disabled")

    to_send = [t for t in texts if t and t not in _cache]
    if not to_send:
        return [_cache.get(t, "") for t in texts]

    translator = GoogleTranslator(
        source=config.FROM_LANG,
        target=config.TO_LANG,
    )

    last_err = None
    for attempt in range(2):
        _google_limiter.wait()
        try:
            results = translator.translate_batch(to_send)
            if not results or len(results) != len(to_send):
                raise RuntimeError(
                    f"Batch size mismatch: "
                    f"{len(results or [])} vs {len(to_send)}"
                )
            _google_failures = 0
            for src, tr in zip(to_send, results):
                _cache[src] = tr or ""
            return [_cache.get(t, "") for t in texts]
        except Exception as e:
            last_err = e
            _google_failures += 1
            print(f"Google batch error (attempt {attempt+1}): {e}")
            if "too many requests" in str(e).lower():
                _google_blocked_until = time.monotonic() + 600
                print("Google временно заблокирован на 10 минут")
                _google_failures += 5
                break
            if attempt == 0:
                time.sleep(2.0)

    if _google_failures >= 3:
        print("Google отключён после серии неудач")
        _google_disabled = True

    raise RuntimeError(f"Google translate failed: {last_err}")


def _translate_google(text):
    return _translate_google_batch([text])[0]


# ---------- Универсальный интерфейс ----------
def translate_text(text):
    if not text or not text.strip():
        return ""
    text = text.strip()
    if text in _cache:
        return _cache[text]

    try:
        if config.TRANSLATION_ENGINE == "google" and _google_is_available():
            result = _translate_google(text)
        else:
            result = _translate_argos(text)
    except Exception as e:
        print(f"Ошибка перевода ({config.TRANSLATION_ENGINE}):", e)
        return ""

    if result and result.strip():
        _cache[text] = result
    return result or ""


def translate_batch(texts):
    if config.TRANSLATION_ENGINE == "google" and _google_is_available():
        try:
            return _translate_google_batch(texts)
        except Exception as e:
            print("Batch Google failed, fallback to Argos:", e)
            return [_translate_argos(t) if t else "" for t in texts]
    return [_translate_argos(t) if t else "" for t in texts]