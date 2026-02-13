#!/usr/bin/env python3
"""
Uniquify image — Pillow. Called by worker only. Never exposed to client.
Usage: python3 uniquify_image.py <input> <output> <variant_index> <stealth 0|1> <light 0|1>
"""
import sys
import random
from pathlib import Path

try:
    from PIL import Image, ImageEnhance, ImageFilter
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

def R(a, b): return random.uniform(a, b)
def RI(a, b): return random.randint(a, b)

def proc_image(inp, out, vi, stealth=False, light=False):
    inp, out = Path(inp), Path(out)
    d_br = random.choice([-1, 1])
    d_ct = random.choice([-1, 1])
    d_sat = random.choice([-1, 1])
    d_sh = random.choice([-1, 1])
    if light:
        p = {
            "br": round(1.0 + d_br * R(0.01, 0.02), 4),
            "ct": round(1.0 + d_ct * R(0.01, 0.03), 4),
            "sat": round(1.0 + d_sat * R(0.01, 0.03), 4),
            "sh": round(1.0 + d_sh * R(0.02, 0.05), 4),
            "zoom": round(R(1.01, 1.03), 3),
            "px_x": random.choice([-1, 1]) * RI(1, 3),
            "px_y": random.choice([-1, 1]) * RI(1, 3),
            "ns": RI(1, 2),
            "q": RI(90, 96),
            "rot": round(random.choice([-1, 1]) * R(0.2, 0.5), 2),
        }
    else:
        p = {
            "br": round(1.0 + d_br * R(0.03, 0.06), 4),
            "ct": round(1.0 + d_ct * R(0.03, 0.07), 4),
            "sat": round(1.0 + d_sat * R(0.03, 0.07), 4),
            "sh": round(1.0 + d_sh * R(0.05, 0.15), 4),
            "zoom": round(R(1.03, 1.07), 3),
            "px_x": random.choice([-1, 1]) * RI(3, 8),
            "px_y": random.choice([-1, 1]) * RI(3, 8),
            "ns": RI(2, 4),
            "q": RI(88, 96),
            "rot": round(random.choice([-1, 1]) * R(0.5, 2.0), 2),
        }
    try:
        img = Image.open(inp)
        ow, oh = img.size
        if img.mode != "RGB":
            img = img.convert("RGB")
        img = img.rotate(p["rot"], resample=Image.BICUBIC, expand=False, fillcolor=(RI(0, 30), RI(0, 30), RI(0, 30)))
        zw = int(ow / p["zoom"])
        zh = int(oh / p["zoom"])
        cx = max(0, min((ow - zw) // 2 + p["px_x"], ow - zw - 1))
        cy = max(0, min((oh - zh) // 2 + p["px_y"], oh - zh - 1))
        img = img.crop((cx, cy, cx + zw, cy + zh))
        img = img.resize((ow, oh), Image.LANCZOS)
        img = ImageEnhance.Brightness(img).enhance(p["br"])
        img = ImageEnhance.Contrast(img).enhance(p["ct"])
        img = ImageEnhance.Color(img).enhance(p["sat"])
        img = ImageEnhance.Sharpness(img).enhance(p["sh"])
        if HAS_NUMPY:
            a = np.array(img, dtype=np.float32)
            a = np.clip(a + np.random.randint(-p["ns"], p["ns"] + 1, a.shape, dtype=np.int16).astype(np.float32), 0, 255)
            img = Image.fromarray(a.astype(np.uint8))
        ext = out.suffix.lower()
        if stealth:
            ext = random.choice([".jpg", ".png", ".webp"])
            out = out.with_suffix(ext)
        if ext in [".jpg", ".jpeg"]:
            img.save(str(out), "JPEG", quality=p["q"])
        elif ext == ".webp":
            img.save(str(out), "WEBP", quality=p["q"])
        else:
            img.save(str(out), "PNG")
        return out.exists() and out.stat().st_size > 0
    except Exception:
        return False

if __name__ == "__main__":
    if len(sys.argv) < 6:
        sys.exit(1)
    inp, out = sys.argv[1], sys.argv[2]
    vi = int(sys.argv[3])
    stealth = sys.argv[4] == "1"
    light = sys.argv[5] == "1"
    ok = proc_image(inp, out, vi, stealth=stealth, light=light)
    sys.exit(0 if ok else 1)
