#!/usr/bin/env python3
"""
Uniquify video — FFmpeg. Called by worker only. Never exposed to client.
Usage: python3 uniquify_video.py <input> <output> <variant_index> <stealth 0|1> <light 0|1>
"""
import os
import sys
import json
import random
import string
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

def R(a, b): return random.uniform(a, b)
def RI(a, b): return random.randint(a, b)
def uid(): return "".join(random.choices(string.ascii_lowercase + string.digits, k=16))
def rdate(d=90): return datetime.now() - timedelta(days=RI(0, d), hours=RI(0, 23), minutes=RI(0, 59), seconds=RI(0, 59))
def ifmt(dt): return dt.strftime("%Y-%m-%dT%H:%M:%S.000000Z")

DEVICES = [
    {"make": "Apple", "model": "iPhone 16 Pro Max", "sw": "18.2"},
    {"make": "Samsung", "model": "SM-S928B", "sw": "S928BXXU3AXK1"},
    {"make": "Google", "model": "Pixel 9 Pro", "sw": "AP4A.250205.002"},
]

def vinfo(path):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", "-show_format", str(path)],
            capture_output=True, text=True, timeout=30,
        )
        d = json.loads(r.stdout)
        i = {"w": 1080, "h": 1920, "dur": 10, "audio": False}
        for s in d.get("streams", []):
            if s.get("codec_type") == "video":
                i["w"] = int(s.get("width", 1080))
                i["h"] = int(s.get("height", 1920))
                i["dur"] = float(s.get("duration", d.get("format", {}).get("duration", 10)))
            if s.get("codec_type") == "audio":
                i["audio"] = True
        return i
    except Exception:
        return {"w": 1080, "h": 1920, "dur": 10, "audio": True}

def proc_video(inp, out, vi, stealth=False, light=False):
    inp, out = Path(inp), Path(out)
    ff = "ffmpeg"
    dev = random.choice(DEVICES)
    dt = rdate()
    i = vinfo(inp)
    w, h, dur = i["w"], i["h"], i["dur"]
    st = stealth
    if light:
        sat_r, ct_r, br_r, gm_r = R(0.01, 0.03), R(0.01, 0.03), R(0.01, 0.02), R(0.01, 0.03)
        zoom_r, px_r, ns_v = R(1.01, 1.03), RI(1, 3), RI(1, 2)
        cut_r, hue_r, spd_r, blur_r = R(0.03, 0.06), R(0.5, 1.0), R(1.01, 1.02), R(0.1, 0.2)
        pitch_r, eq_r = R(0.5, 1.5), R(0.5, 1.5)
    else:
        sat_r, ct_r, br_r, gm_r = R(0.03, 0.06), R(0.02, 0.06), R(0.02, 0.04), R(0.02, 0.06)
        zoom_r = R(1.04, 1.08 if st else 1.07)
        px_r, ns_v = RI(4, 8), RI(2, 4)
        cut_r, hue_r = R(0.12, 0.25 if st else 0.20), R(1.5, 3.0 if st else 2.5)
        spd_r, blur_r = R(1.03, 1.04), R(0.15, 0.35)
        pitch_r, eq_r = R(2, 3), R(1, 3)
    p = {
        "sat": round(1.0 + random.choice([-1, 1]) * sat_r, 3),
        "ct": round(1.0 + random.choice([-1, 1]) * ct_r, 3),
        "br": round(random.choice([-1, 1]) * br_r, 3),
        "gm": round(1.0 + random.choice([-1, 1]) * gm_r, 3),
        "zoom": round(zoom_r, 3),
        "px_x": random.choice([-1, 1]) * px_r,
        "px_y": random.choice([-1, 1]) * px_r,
        "spd": round(spd_r, 3),
        "ns": ns_v,
        "cut_s": round(cut_r, 3),
        "cut_e": round(cut_r, 3),
        "wf_ms": RI(40, 80),
        "crf": RI(17, 20),
        "vbr": RI(5500, 7000),
        "ab": random.choice([192, 256, 320]),
        "fps": 30,
        "hue_shift": round(hue_r * random.choice([-1, 1]), 2),
        "blur_micro": round(blur_r, 2),
        "gop_interval": RI(24, 90),
        "pitch_shift": round(pitch_r * random.choice([-1, 1]), 1),
        "hp_freq": RI(20, 30),
        "lp_freq": RI(18000, 19000),
    }
    zw = int(w / p["zoom"])
    zh = int(h / p["zoom"])
    cx = max(0, min((w - zw) // 2 + p["px_x"], w - zw))
    cy = max(0, min((h - zh) // 2 + p["px_y"], h - zh))
    zw, zh = zw + (zw % 2), zh + (zh % 2)
    ss, t_dur = p["cut_s"], dur - p["cut_e"] - ss
    if t_dur < 0.5:
        ss, t_dur = 0, dur
    t_dur = max(t_dur, 0.5)
    vf = [
        f"setpts={round(1 / p['spd'], 6)}*PTS",
        f"eq=brightness={p['br']}:contrast={p['ct']}:saturation={p['sat']}:gamma={p['gm']}",
        f"hue=h={p['hue_shift']}",
        f"crop={zw}:{zh}:{cx}:{cy}",
        f"scale={w}:{h}:flags=lanczos",
        "unsharp=5:5:0.8:5:5:0.0",
        f"noise=alls={p['ns']}:allf=t",
        f"fps={p['fps']}",
    ]
    if p["blur_micro"] > 0.15:
        vf.append(f"gblur=sigma={p['blur_micro']}")
    af = [f"atempo={p['spd']}", f"adelay={p['wf_ms']}|{p['wf_ms']}"]
    sr = 44100
    new_sr = int(sr * (1 + p["pitch_shift"] / 100))
    af += [f"asetrate={new_sr}", f"aresample={sr}", f"highpass=f={p['hp_freq']}", f"lowpass=f={p['lp_freq']}"]
    meta = ["-map_metadata", "-1"] if stealth else [
        "-metadata", f"creation_time={ifmt(dt)}",
        "-metadata", f"make={dev['make']}", "-metadata", f"model={dev['model']}", "-metadata", f"software={dev['sw']}",
    ]
    cmd = [ff, "-y", "-ss", str(ss), "-i", str(inp), "-t", str(t_dur), "-vf", ",".join(vf)]
    if i["audio"]:
        cmd += ["-af", ",".join(af), "-c:a", "aac", "-b:a", f"{p['ab']}k"]
    else:
        cmd += ["-an"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", str(p["crf"]), "-g", str(p["gop_interval"]), "-movflags", "+faststart"]
    cmd += meta + [str(out)]
    subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if out.exists() and out.stat().st_size > 0:
        return True
    return False

if __name__ == "__main__":
    if len(sys.argv) < 6:
        sys.exit(1)
    inp, out = sys.argv[1], sys.argv[2]
    vi = int(sys.argv[3])
    stealth = sys.argv[4] == "1"
    light = sys.argv[5] == "1"
    ok = proc_video(inp, out, vi, stealth=stealth, light=light)
    sys.exit(0 if ok else 1)
