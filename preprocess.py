# preprocess.py
import cv2
import numpy as np
import config


def _upscale(img):
    if config.UPSCALE_FACTOR > 1:
        img = cv2.resize(
            img, None,
            fx=config.UPSCALE_FACTOR,
            fy=config.UPSCALE_FACTOR,
            interpolation=cv2.INTER_LANCZOS4,
        )
    return img


def _clahe(img, clip=None, tile=None):
    clip = clip or config.CLAHE_CLIP
    tile = tile or config.CLAHE_TILE
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=tile)
    l = clahe.apply(l)
    return cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2RGB)


def _adaptive(img):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    binv = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=config.ADAPTIVE_BLOCK,
        C=config.ADAPTIVE_C,
    )
    return cv2.cvtColor(binv, cv2.COLOR_GRAY2RGB)


def _invert(img):
    return cv2.bitwise_not(img)


def _sharpen(img):
    if not getattr(config, "ENABLE_SHARPEN", False):
        return img
    blur = cv2.GaussianBlur(img, (0, 0), 3)
    return cv2.addWeighted(
        img, 1 + config.SHARPEN_STRENGTH,
        blur, -config.SHARPEN_STRENGTH,
        0,
    )


def _make_variants(img):
    """Возвращает словарь: имя → обработанное RGB-изображение."""
    up = _upscale(img)
    base = _clahe(up) if config.USE_CLAHE else up
    base = _sharpen(base)

    variants = {'light': base}

    if config.PREPROCESS_MODE in ('dark', 'auto'):
        variants['dark'] = _clahe(_invert(up))

    if config.PREPROCESS_MODE in ('adaptive', 'auto'):
        variants['adaptive'] = _adaptive(up)

    if config.PREPROCESS_MODE == 'auto':
        variants['adaptive_inv'] = _adaptive(_invert(up))

    return variants


def get_variants(img):
    """
    Возвращает список (variant_name, processed_image, scale).
    """
    if not config.ENABLE_PREPROCESS:
        return [('none', img, 1.0)]

    variants = _make_variants(img)
    scale = float(config.UPSCALE_FACTOR) if config.UPSCALE_FACTOR > 1 else 1.0
    return [(name, im, scale) for name, im in variants.items()]


def preprocess(img):
    if not config.ENABLE_PREPROCESS:
        return img
    variants = _make_variants(img)
    mode = config.PREPROCESS_MODE
    if mode == 'auto':
        return variants['light']
    return variants.get(mode, variants['light'])