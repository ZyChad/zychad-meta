#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║  ⚡ REELFORGE v3.0 — Video & Image Uniquifier with GUI       ║
║  Double-clique ce fichier ou lance: python3 reelforge.py     ║
║  L'interface s'ouvre automatiquement dans ton navigateur      ║
╚══════════════════════════════════════════════════════════════╝

Setup (une seule fois):
  pip install Pillow piexif numpy

FFmpeg:
  - Windows: Le script te guide pour l'installer automatiquement
  - Mac: brew install ffmpeg
  - Linux: sudo apt install ffmpeg
"""

import os, sys, json, random, string, shutil, subprocess, threading
import time, zipfile, webbrowser, platform, tempfile, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor, as_completed
import socket

# ─── Auto-install missing packages ───
def ensure_packages():
    missing = []
    try: from PIL import Image, ImageEnhance
    except ImportError: missing.append("Pillow")
    try: import piexif
    except ImportError: missing.append("piexif")
    try: import numpy
    except ImportError: missing.append("numpy")
    try: import requests as _rq
    except ImportError: missing.append("requests")
    if missing:
        print(f"  📦 Installation de {', '.join(missing)}...")
        subprocess.run([sys.executable, "-m", "pip", "install"] + missing + ["--quiet", "--break-system-packages"], capture_output=True)

ensure_packages()
from PIL import Image, ImageEnhance
import piexif
try:
    import numpy as np; HAS_NUMPY = True
except: HAS_NUMPY = False
import requests as rq

# ─── SaaS: user id from Nginx auth_request (X-User-Id header) ───
saas_user_id=None

# ─── Config persistence (saves API keys locally) ───
CONFIG_FILE=Path(os.path.dirname(os.path.abspath(__file__)))/"zychad_config.json"

def load_config():
    try:
        if CONFIG_FILE.exists(): return json.loads(CONFIG_FILE.read_text())
    except: pass
    return {}

def save_config(data):
    try:
        cfg=load_config(); cfg.update(data)
        CONFIG_FILE.write_text(json.dumps(cfg,indent=2))
    except: pass

# ─── Find free port ───
def find_free_port(preferred=61550):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', preferred)); return preferred
    except OSError:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0)); return s.getsockname()[1]
PORT = int(os.environ.get("PORT", 0)) or find_free_port()

# ─── FFmpeg ───
def find_ffmpeg():
    ff = shutil.which("ffmpeg")
    if ff: return ff
    if platform.system() == "Windows":
        for p in [Path(os.environ.get("LOCALAPPDATA",""))/"ffmpeg"/"bin"/"ffmpeg.exe",
                   Path("C:/ffmpeg/bin/ffmpeg.exe"),
                   Path(os.path.dirname(os.path.abspath(__file__)))/"ffmpeg"/"bin"/"ffmpeg.exe",
                   Path(os.path.dirname(os.path.abspath(__file__)))/"ffmpeg.exe"]:
            if p.exists(): return str(p)
    return None

def ffmpeg_install_info():
    s = platform.system()
    if s == "Windows":
        return {"os":"Windows","steps":["<strong>Méthode 1 — winget (recommandé) :</strong>","Ouvre PowerShell en admin et tape :","<code>winget install Gyan.FFmpeg</code>","Puis redémarre ce script.","","<strong>Méthode 2 — manuelle :</strong>","1. Va sur <a href='https://www.gyan.dev/ffmpeg/builds/' target='_blank'>gyan.dev/ffmpeg/builds</a>","2. Télécharge <code>ffmpeg-release-essentials.zip</code>","3. Décompresse dans <code>C:\\ffmpeg</code>","4. Ajoute <code>C:\\ffmpeg\\bin</code> au PATH système :","   → Recherche 'Variables d'environnement' dans Windows","   → Path système → Ajouter → <code>C:\\ffmpeg\\bin</code>","5. Redémarre ce script","","<strong>Méthode 3 — chocolatey :</strong>","<code>choco install ffmpeg</code>"]}
    elif s == "Darwin":
        return {"os":"macOS","steps":["<code>brew install ffmpeg</code>"]}
    return {"os":"Linux","steps":["<code>sudo apt update && sudo apt install ffmpeg</code>"]}

FFMPEG_PATH = find_ffmpeg()

# ─── Device DB ───
DEVICES=[
    {"make":"Apple","model":"iPhone 16 Pro Max","sw":"18.2"},{"make":"Apple","model":"iPhone 16 Pro","sw":"18.1.1"},
    {"make":"Apple","model":"iPhone 15 Pro Max","sw":"17.6.1"},{"make":"Apple","model":"iPhone 15 Pro","sw":"17.5"},
    {"make":"Apple","model":"iPhone 14 Pro Max","sw":"17.4.1"},{"make":"Apple","model":"iPhone 14 Pro","sw":"17.3.1"},
    {"make":"Apple","model":"iPhone 13 Pro Max","sw":"17.4"},{"make":"Apple","model":"iPhone 13 Pro","sw":"16.7.5"},
    {"make":"Apple","model":"iPhone 12 Pro","sw":"17.3"},
    {"make":"Samsung","model":"SM-S928B","sw":"S928BXXU3AXK1"},{"make":"Samsung","model":"SM-S926B","sw":"S926BXXU2AXJ5"},
    {"make":"Samsung","model":"SM-S921B","sw":"S921BXXU2AXJ3"},{"make":"Samsung","model":"SM-S918B","sw":"S918BXXU5CXK2"},
    {"make":"Samsung","model":"SM-G998B","sw":"G998BXXS9FXJ1"},
    {"make":"Google","model":"Pixel 9 Pro","sw":"AP4A.250205.002"},{"make":"Google","model":"Pixel 8 Pro","sw":"AP2A.240305.019.A1"},
    {"make":"Google","model":"Pixel 8","sw":"AP2A.240205.004"},{"make":"Google","model":"Pixel 7 Pro","sw":"AP1A.240305.019.A1"},
    {"make":"Xiaomi","model":"2312DRA50G","sw":"OS1.0.6.0.UNBEUXM"},
    {"make":"OnePlus","model":"CPH2551","sw":"CPH2551_14.0.0.700"},
    {"make":"Huawei","model":"NOH-NX9","sw":"NOH-NX9 12.0.0.268"},
]
VIDEO_EXTS={".mp4",".mov",".avi",".mkv",".webm",".m4v",".flv",".wmv"}
IMAGE_EXTS={".jpg",".jpeg",".png",".webp",".bmp",".tiff"}

# ─── State ───
state={"active":False,"progress":0,"total":0,"file":"","log":[],"results":[],"done":False,"output":"","zip":None,"paused":False,"cancelled":False,"eta":"","file_times":[],"current_file_idx":0,"files_list":[]}
def reset(): state.update({"active":False,"progress":0,"total":0,"file":"","log":[],"results":[],"done":False,"zip":None,"input":"","paused":False,"cancelled":False,"eta":"","file_times":[],"current_file_idx":0,"files_list":[]})
def log(m,lv="info"): state["log"].append({"t":datetime.now().strftime("%H:%M:%S"),"m":m,"l":lv})

# ─── Helpers ───
def R(a,b): return random.uniform(a,b)
def RI(a,b): return random.randint(a,b)
def uid(): return ''.join(random.choices(string.ascii_lowercase+string.digits,k=16))
def rdate(d=90): return datetime.now()-timedelta(days=RI(0,d),hours=RI(0,23),minutes=RI(0,59),seconds=RI(0,59))
def efmt(dt): return dt.strftime("%Y:%m:%d %H:%M:%S")
def ifmt(dt): return dt.strftime("%Y-%m-%dT%H:%M:%S.000000Z")

def vinfo(path):
    try:
        fp=FFMPEG_PATH.replace("ffmpeg","ffprobe") if FFMPEG_PATH else "ffprobe"
        r=subprocess.run([fp,"-v","quiet","-print_format","json","-show_streams","-show_format",str(path)],capture_output=True,text=True,timeout=30)
        d=json.loads(r.stdout); i={"w":1080,"h":1920,"dur":10,"audio":False}
        for s in d.get("streams",[]):
            if s.get("codec_type")=="video": i["w"]=int(s.get("width",1080));i["h"]=int(s.get("height",1920));i["dur"]=float(s.get("duration",d.get("format",{}).get("duration",10)))
            if s.get("codec_type")=="audio": i["audio"]=True
        return i
    except: return {"w":1080,"h":1920,"dur":10,"audio":True}

# ─── Video ───
def proc_video(inp,out,vi,stealth=False,light=False):
    inp=Path(inp); out=Path(out)
    ff=FFMPEG_PATH or "ffmpeg"; dev=random.choice(DEVICES); dt=rdate(); u=uid()
    i=vinfo(inp); w,h=i["w"],i["h"]; dur=i["dur"]
    
    # ═══ Optimized params ═══
    st=stealth
    # Light mode = 2nd pass of double process (half intensity to avoid visible cumul)
    if light:
        sat_r=R(.01,.03); ct_r=R(.01,.03); br_r=R(.01,.02); gm_r=R(.01,.03)
        zoom_r=R(1.01,1.03); px_r=RI(1,3); ns_v=RI(1,2)
        cut_r=R(.03,.06); hue_r=R(0.5,1.0); grain_v=RI(1,2)
        spd_r=R(1.01,1.02); blur_r=R(0.1,0.2)
        pitch_r=R(0.5,1.5); eq_r=R(0.5,1.5)
    else:
        sat_r=R(.03,.06); ct_r=R(.02,.06); br_r=R(.02,.04); gm_r=R(.02,.06)
        zoom_r=R(1.04,1.08 if st else 1.07); px_r=RI(4,8); ns_v=RI(2,4)
        cut_r=R(.12,.25 if st else .20); hue_r=R(1.5,3.0 if st else 2.5); grain_v=RI(2,4)
        spd_r=R(1.03,1.04); blur_r=R(0.15,0.35)
        pitch_r=R(2,3); eq_r=R(1,3)
    p={
        "sat":round(1.0+random.choice([-1,1])*sat_r,3),
        "ct":round(1.0+random.choice([-1,1])*ct_r,3),
        "br":round(random.choice([-1,1])*br_r,3),
        "gm":round(1.0+random.choice([-1,1])*gm_r,3),
        "zoom":round(zoom_r,3),
        "px_x":random.choice([-1,1])*px_r, "px_y":random.choice([-1,1])*px_r,
        "spd":round(spd_r,3),
        "ns":ns_v,
        "cut_s":round(cut_r,3),"cut_e":round(cut_r,3),
        "wf_ms":RI(40,80),
        "crf":RI(17,20),"vbr":RI(5500,7000),"ab":random.choice([192,256,320]),
        "fps":random.choice([30,30,30,60]),
        "hue_shift":round(hue_r*random.choice([-1,1]),2),
        "blur_micro":round(blur_r,2),
        "grain_op":grain_v,
        "gop_interval":RI(24,90),
        "pitch_shift":round(pitch_r*random.choice([-1,1]),1),
        "eq_band":random.choice([300,1000,3000,8000]),
        "eq_gain":round(eq_r*random.choice([-1,1]),1),
        "hp_freq":RI(20,30),"lp_freq":RI(18000,19000),
        "stereo_width":round(R(0.95,1.05),3),
        "phase_invert":random.choice(["left","right","none"]),
        # Letterbox random per side (1-3px)
        "lb_top":RI(0,2),"lb_bot":RI(0,2),"lb_left":RI(0,2),"lb_right":RI(0,2),
    }
    
    # ═══ SINGLE crop that combines pixel shift + zoom ═══
    zw=int(w/p["zoom"]); zh=int(h/p["zoom"])
    cx=(w-zw)//2 + p["px_x"]; cy=(h-zh)//2 + p["px_y"]
    cx=max(0,min(cx, w-zw)); cy=max(0,min(cy, h-zh))
    zw=zw+(zw%2); zh=zh+(zh%2)
    
    # Cut timing
    ss=p["cut_s"]; t_dur=dur-p["cut_e"]-ss
    if t_dur<0.5: ss=0; t_dur=dur
    t_dur=max(t_dur,0.5)
    
    # ═══ Video filter chain ═══
    vf=[]
    vf.append(f"setpts={round(1/p['spd'],6)}*PTS")
    vf.append(f"eq=brightness={p['br']}:contrast={p['ct']}:saturation={p['sat']}:gamma={p['gm']}")
    # Hue shift (imperceptible 1-2°)
    vf.append(f"hue=h={p['hue_shift']}")
    # Crop + scale
    vf.append(f"crop={zw}:{zh}:{cx}:{cy}")
    vf.append(f"scale={w}:{h}:flags=lanczos")
    # Sharpening
    vf.append("unsharp=5:5:0.8:5:5:0.0")
    # Micro blur (imperceptible, changes hash)
    if p["blur_micro"]>0.15:
        vf.append(f"gblur=sigma={p['blur_micro']}")
    # Noise
    vf.append(f"noise=alls={p['ns']}:allf=t")
    # Grain overlay (1-3% opacity via noise with different params)
    vf.append(f"noise=c0s={int(p['grain_op'])}:c0f=a")
    # Letterbox random per side (imperceptible 0-2px black borders)
    lt,lb,ll,lr=p["lb_top"],p["lb_bot"],p["lb_left"],p["lb_right"]
    if lt+lb+ll+lr>0:
        pw=w+ll+lr; ph=h+lt+lb
        # Ensure even dimensions
        pw=pw+(pw%2); ph=ph+(ph%2)
        vf.append(f"pad={pw}:{ph}:{ll}:{lt}:black")
        vf.append(f"scale={w}:{h}:flags=lanczos")
    # FPS
    vf.append(f"fps={p['fps']}")
    
    # ═══ Audio filter chain (all imperceptible techniques combined) ═══
    af_parts=[f"atempo={p['spd']}"]
    af_parts.append(f"adelay={p['wf_ms']}|{p['wf_ms']}")
    # Pitch shift (±2-3% via asetrate + aresample)
    sr=44100; new_sr=int(sr*(1+p["pitch_shift"]/100))
    af_parts.append(f"asetrate={new_sr}")
    af_parts.append(f"aresample={sr}")
    # EQ multi-band: 3-5 random bands ±2-3dB each
    eq_bands=random.sample([100,300,800,1500,3000,5000,8000,12000],k=random.randint(3,5))
    for band in eq_bands:
        g=round(R(1,3)*random.choice([-1,1]),1)
        af_parts.append(f"equalizer=f={band}:t=h:w=200:g={g}")
    # Micro reverb (imperceptible)
    af_parts.append(f"aecho=0.8:0.6:{RI(10,20)}:0.1")
    # High-pass + Low-pass (cut inaudible frequencies)
    af_parts.append(f"highpass=f={p['hp_freq']}")
    af_parts.append(f"lowpass=f={p['lp_freq']}")
    # Stereo width
    if abs(p["stereo_width"]-1.0)>0.01:
        af_parts.append(f"stereotools=sbal={round((p['stereo_width']-1)*2,3)}")
    # Phase invert on one channel
    if p["phase_invert"]=="left":
        af_parts.append("pan=stereo|c0=-c0|c1=c1")
    elif p["phase_invert"]=="right":
        af_parts.append("pan=stereo|c0=c0|c1=-c1")
    af_parts=[x for x in af_parts if x]
    af_str=",".join(af_parts)
    
    apple=dev["make"]=="Apple"
    
    # Stealth: strip all metadata, no device spoof
    if stealth:
        meta_args=["-map_metadata","-1"]
    else:
        meta_args=["-metadata",f"creation_time={ifmt(dt)}","-metadata",f"comment=vid:{u}",
              "-metadata",f"make={dev['make']}","-metadata",f"model={dev['model']}","-metadata",f"software={dev['sw']}",
              "-metadata",f"date={ifmt(dt)}","-metadata",f"com.apple.quicktime.make={dev['make']}",
              "-metadata",f"com.apple.quicktime.model={dev['model']}","-metadata",f"com.apple.quicktime.software={dev['sw']}",
              "-metadata",f"com.apple.quicktime.creationdate={ifmt(dt)}",
              "-metadata:s:v",f"handler_name={'Core Media Video' if apple else 'VideoHandler'}",
              "-metadata:s:v",f"creation_time={ifmt(dt)}"]
    
    # ═══ Build FFmpeg command ═══
    cmd=[ff,"-y","-ss",str(ss),"-i",str(inp),"-t",str(t_dur),"-vf",",".join(vf)]
    if i["audio"]:
        cmd+=["-af",af_str,"-c:a","aac","-b:a",f"{p['ab']}k"]
    else: cmd+=["-an"]
    if apple and not stealth: cmd+=["-f","mov"]
    cmd+=["-c:v","libx264","-preset","medium","-crf",str(p["crf"]),
          "-b:v",f"{p['vbr']}k","-maxrate",f"{p['vbr']*2}k","-bufsize",f"{p['vbr']*4}k",
          "-g",str(p["gop_interval"]),  # GOP structure random
          "-movflags","+faststart"]
    cmd+=meta_args
    cmd.append(str(out))
    try:
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=600)
        if r.returncode!=0:
            # Robust fallback — still apply all core techniques
            vf2=[f"eq=brightness={p['br']}:contrast={p['ct']}:saturation={p['sat']}:gamma={p['gm']}",
                 f"hue=h={p['hue_shift']}",
                 f"crop={zw}:{zh}:{cx}:{cy}",f"scale={w}:{h}:flags=lanczos",
                 "unsharp=5:5:0.8:5:5:0.0",
                 f"noise=alls={p['ns']}:allf=t",f"fps={p['fps']}"]
            af2=[f"atempo={p['spd']}",f"adelay={p['wf_ms']}|{p['wf_ms']}",
                 f"highpass=f={p['hp_freq']}",f"lowpass=f={p['lp_freq']}"]
            cmd2=[ff,"-y","-ss",str(ss),"-i",str(inp),"-t",str(t_dur),
                  "-vf",",".join(vf2)]
            if i["audio"]: cmd2+=["-af",",".join(af2),"-c:a","aac","-b:a",f"{p['ab']}k"]
            else: cmd2+=["-an"]
            cmd2+=["-c:v","libx264","-preset","medium","-crf",str(p["crf"]),
                   "-g",str(p["gop_interval"]),"-movflags","+faststart"]
            cmd2+=meta_args
            cmd2.append(str(out))
            r2=subprocess.run(cmd2,capture_output=True,text=True,timeout=600)
            if r2.returncode!=0:
                # Last resort — minimal but still unique
                cmd3=[ff,"-y","-i",str(inp),
                      "-vf",f"eq=brightness={p['br']}:saturation={p['sat']},hue=h={p['hue_shift']},noise=alls={p['ns']}:allf=t",
                      "-c:v","libx264","-preset","fast","-crf",str(p["crf"])]
                if i["audio"]: cmd3+=["-c:a","aac"]
                cmd3+=meta_args; cmd3.append(str(out))
                subprocess.run(cmd3,capture_output=True,text=True,timeout=600)
        if out.exists() and out.stat().st_size>0:
            return {"ok":True,"f":out.name,"sz":f"{out.stat().st_size/1048576:.1f} MB","dev":f"{dev['make']} {dev['model']}","dt":dt.strftime("%Y-%m-%d %H:%M")}
        return {"ok":False,"f":out.name,"e":"Empty"}
    except Exception as e: return {"ok":False,"f":out.name,"e":str(e)}

# ─── Image ───
def proc_image(inp,out,vi,stealth=False,light=False):
    inp=Path(inp); out=Path(out)
    dev=random.choice(DEVICES); dt=rdate()
    d_br=random.choice([-1,1]); d_ct=random.choice([-1,1])
    d_sat=random.choice([-1,1]); d_sh=random.choice([-1,1])
    if light:
        p={
            "br":round(1.0 + d_br*R(.01,.02), 4),
            "ct":round(1.0 + d_ct*R(.01,.03), 4),
            "sat":round(1.0 + d_sat*R(.01,.03), 4),
            "sh":round(1.0 + d_sh*R(.02,.05), 4),
            "zoom":round(R(1.01,1.03), 3),
            "px_x":random.choice([-1,1])*RI(1,3),
            "px_y":random.choice([-1,1])*RI(1,3),
            "ns":RI(1,2),"q":RI(90,96),
            "rot":round(random.choice([-1,1])*R(0.2,0.5), 2),
            "grad_strength":round(R(0.02,0.05), 3),
            "grad_angle":random.choice(["tb","bt","lr","rl","diag"]),
            "gamma_local":round(R(0.95,1.05), 3),
            "hue_shift":round(R(0.3,0.8)*random.choice([-1,1]),2),
            "blur_micro":round(R(0.05,0.1),2),
            "vignette_op":round(R(0.01,0.02),3),
            "chroma_offset":round(R(0.3,0.5),2),
            "lens_dist":round(R(0.001,0.003)*random.choice([-1,1]),4),
            "shadow_tweak":round(1.0+R(0.01,0.015)*random.choice([-1,1]),3),
            "highlight_tweak":round(1.0+R(0.01,0.015)*random.choice([-1,1]),3),
        }
    else:
        p={
            "br":round(1.0 + d_br*R(.03,.06), 4),
            "ct":round(1.0 + d_ct*R(.03,.07), 4),
            "sat":round(1.0 + d_sat*R(.03,.07), 4),
            "sh":round(1.0 + d_sh*R(.05,.15), 4),
            "zoom":round(R(1.03,1.07), 3),
            "px_x":random.choice([-1,1])*RI(3,8),
            "px_y":random.choice([-1,1])*RI(3,8),
            "ns":RI(2,4),"q":RI(88,96),
            "rot":round(random.choice([-1,1])*R(0.5,2.0), 2),
            "grad_strength":round(R(0.05,0.12), 3),
            "grad_angle":random.choice(["tb","bt","lr","rl","diag"]),
            "gamma_local":round(R(0.88,1.12), 3),
            "hue_shift":round(R(1,2)*random.choice([-1,1]),2),
            "blur_micro":round(R(0.1,0.2),2),
            "vignette_op":round(R(0.02,0.05),3),
            "chroma_offset":round(R(0.5,1.0),2),
            "lens_dist":round(R(0.003,0.005)*random.choice([-1,1]),4),
            "shadow_tweak":round(1.0+R(0.02,0.03)*random.choice([-1,1]),3),
            "highlight_tweak":round(1.0+R(0.02,0.03)*random.choice([-1,1]),3),
        }
    try:
        img=Image.open(inp); ow,oh=img.size
        if img.mode!="RGB": img=img.convert("RGB")
        
        # Randomize operation order in stealth mode
        ops=list(range(10))
        if stealth: random.shuffle(ops)
        
        for op in ops:
            if op==0:
                # Micro-rotation
                img=img.rotate(p["rot"],resample=Image.BICUBIC,expand=False,fillcolor=(
                    RI(0,30),RI(0,30),RI(0,30)))
            elif op==1:
                # SINGLE crop: zoom + pixel shift
                zw=int(ow/p["zoom"]); zh=int(oh/p["zoom"])
                cx=(ow-zw)//2 + p["px_x"]; cy=(oh-zh)//2 + p["px_y"]
                cx=max(0,min(cx, ow-zw-1)); cy=max(0,min(cy, oh-zh-1))
                img=img.crop((cx, cy, cx+zw, cy+zh))
                img=img.resize((ow,oh),Image.LANCZOS)
            elif op==2:
                # Color grading
                img=ImageEnhance.Brightness(img).enhance(p["br"])
                img=ImageEnhance.Contrast(img).enhance(p["ct"])
                img=ImageEnhance.Color(img).enhance(p["sat"])
                img=ImageEnhance.Sharpness(img).enhance(p["sh"])
            elif op==3 and HAS_NUMPY:
                # Non-uniform gradient overlay
                a=np.array(img,dtype=np.float32)
                h,w,c=a.shape
                s=p["grad_strength"]; ga=p["grad_angle"]
                if ga=="tb":    grad=np.linspace(1+s,1-s,h).reshape(h,1,1)
                elif ga=="bt":  grad=np.linspace(1-s,1+s,h).reshape(h,1,1)
                elif ga=="lr":  grad=np.linspace(1+s,1-s,w).reshape(1,w,1)
                elif ga=="rl":  grad=np.linspace(1-s,1+s,w).reshape(1,w,1)
                else:
                    gy=np.linspace(0,s,h).reshape(h,1)
                    gx=np.linspace(0,s,w).reshape(1,w)
                    grad=(1.0+(gy+gx-s)).reshape(h,w,1)
                a=np.clip(a*grad,0,255)
                img=Image.fromarray(a.astype(np.uint8))
            elif op==4 and HAS_NUMPY:
                # Local gamma variation
                a=np.array(img,dtype=np.float32)
                h,w,c=a.shape
                mid_h,mid_w=h//2,w//2
                gammas=[p["gamma_local"],round(R(0.93,1.07),3),round(R(0.93,1.07),3),round(R(0.93,1.07),3)]
                random.shuffle(gammas)
                for qi,(y0,y1,x0,x1) in enumerate([(0,mid_h,0,mid_w),(0,mid_h,mid_w,w),(mid_h,h,0,mid_w),(mid_h,h,mid_w,w)]):
                    a[y0:y1,x0:x1]=np.clip(255.0*(a[y0:y1,x0:x1]/255.0)**gammas[qi],0,255)
                img=Image.fromarray(a.astype(np.uint8))
            elif op==5 and HAS_NUMPY:
                # Noise + hue shift + shadow/highlight tweaks
                a=np.array(img,dtype=np.float32)
                # Random noise
                a=np.clip(a+np.random.randint(-p["ns"],p["ns"]+1,a.shape,dtype=np.int16).astype(np.float32),0,255)
                # Hue shift via RGB rotation
                angle=p["hue_shift"]*np.pi/180
                cos_a,sin_a=np.cos(angle),np.sin(angle)
                r,g,b=a[:,:,0].copy(),a[:,:,1].copy(),a[:,:,2].copy()
                a[:,:,0]=np.clip(r*cos_a-g*sin_a*0.5+b*sin_a*0.5,0,255)
                a[:,:,1]=np.clip(r*sin_a*0.3+g*cos_a+b*sin_a*0.2,0,255)
                a[:,:,2]=np.clip(-r*sin_a*0.3+g*sin_a*0.3+b*cos_a,0,255)
                # Shadow tweak (darks)
                mask_s=(a<80).astype(np.float32)
                a=np.clip(a*((1-mask_s)+mask_s*p["shadow_tweak"]),0,255)
                # Highlight tweak (brights)
                mask_h=(a>180).astype(np.float32)
                a=np.clip(a*((1-mask_h)+mask_h*p["highlight_tweak"]),0,255)
                img=Image.fromarray(a.astype(np.uint8))
            elif op==6 and HAS_NUMPY:
                # Chromatic aberration (offset R and B channels)
                a=np.array(img,dtype=np.float32)
                off=max(1,int(p["chroma_offset"]))
                # Shift red right, blue left
                a[:,:off,0]=a[:,off:off*2,0] if off*2<a.shape[1] else a[:,:off,0]
                a[:,-off:,2]=a[:,-off*2:-off,2] if off*2<a.shape[1] else a[:,-off:,2]
                img=Image.fromarray(a.astype(np.uint8))
            elif op==7 and HAS_NUMPY:
                # Micro blur (imperceptible, changes hash)
                from PIL import ImageFilter
                if p["blur_micro"]>0.12:
                    img=img.filter(ImageFilter.GaussianBlur(radius=p["blur_micro"]))
            elif op==8 and HAS_NUMPY:
                # Vignette subtile
                a=np.array(img,dtype=np.float32)
                h,w,c=a.shape
                Y,X=np.ogrid[:h,:w]
                cy,cx=h/2,w/2
                r=np.sqrt((X-cx)**2+(Y-cy)**2)
                r_max=np.sqrt(cx**2+cy**2)
                vign=1.0 - p["vignette_op"]*(r/r_max)**2
                a=np.clip(a*vign.reshape(h,w,1),0,255)
                img=Image.fromarray(a.astype(np.uint8))
            elif op==9 and HAS_NUMPY:
                # Lens distortion (barrel/pincushion)
                a=np.array(img,dtype=np.uint8)
                h,w,c=a.shape
                k=p["lens_dist"]
                cy,cx=h/2,w/2
                Y,X=np.mgrid[:h,:w].astype(np.float32)
                X2=(X-cx)/cx; Y2=(Y-cy)/cy
                r2=X2**2+Y2**2
                X3=X2*(1+k*r2); Y3=Y2*(1+k*r2)
                map_x=np.clip((X3*cx+cx),0,w-1).astype(np.float32)
                map_y=np.clip((Y3*cy+cy),0,h-1).astype(np.float32)
                try:
                    import cv2
                    a=cv2.remap(a,map_x,map_y,cv2.INTER_LINEAR)
                except ImportError:
                    pass  # Skip lens distortion if no cv2
                img=Image.fromarray(a)
        
        # ═══ EXIF ═══
        if stealth:
            # Zero metadata mode
            eb=piexif.dump({"0th":{},"Exif":{},"GPS":{},"1st":{}})
        else:
            ed=efmt(dt)
            z={piexif.ImageIFD.Make:dev["make"].encode(),piexif.ImageIFD.Model:dev["model"].encode(),
               piexif.ImageIFD.Software:dev["sw"].encode(),piexif.ImageIFD.DateTime:ed.encode(),
               piexif.ImageIFD.Orientation:1,piexif.ImageIFD.XResolution:(72,1),piexif.ImageIFD.YResolution:(72,1)}
            ex={piexif.ExifIFD.DateTimeOriginal:ed.encode(),piexif.ExifIFD.DateTimeDigitized:ed.encode(),
                piexif.ExifIFD.ColorSpace:1,piexif.ExifIFD.FocalLength:(random.choice([24,26,28,35,50,65,77]),10),
                piexif.ExifIFD.FNumber:(random.choice([16,18,20,24,28]),10),
                piexif.ExifIFD.ISOSpeedRatings:random.choice([50,64,100,200,400,800]),
                piexif.ExifIFD.ExposureTime:(1,random.choice([60,100,125,250,500,1000])),
                piexif.ExifIFD.LensMake:dev["make"].encode(),piexif.ExifIFD.LensModel:f"{dev['model']} back camera".encode()}
            gp={}
            if random.random()>.3:
                la,lo=round(R(25,48),6),round(R(-120,40),6)
                def dms(v):
                    d=int(abs(v));m=int((abs(v)-d)*60);s=int(((abs(v)-d)*60-m)*60*100)
                    return((d,1),(m,1),(s,100))
                gp={piexif.GPSIFD.GPSLatitudeRef:b'N' if la>=0 else b'S',piexif.GPSIFD.GPSLatitude:dms(la),
                    piexif.GPSIFD.GPSLongitudeRef:b'E' if lo>=0 else b'W',piexif.GPSIFD.GPSLongitude:dms(abs(lo))}
            eb=piexif.dump({"0th":z,"Exif":ex,"GPS":gp,"1st":{}})
        
        # ═══ Save (stealth: random format) ═══
        ext=out.suffix.lower()
        if stealth:
            ext=random.choice([".jpg",".png",".webp"])
            out=out.with_suffix(ext)
        if ext in[".jpg",".jpeg"]: img.save(str(out),"JPEG",quality=p["q"],exif=eb,subsampling=random.choice([0,2]))
        elif ext==".webp": img.save(str(out),"WEBP",quality=p["q"],exif=eb)
        else: img.save(str(out),"PNG")
        if out.exists() and out.stat().st_size>0:
            sz=out.stat().st_size; u="MB" if sz>1048576 else "KB"; v=sz/1048576 if u=="MB" else sz/1024
            return {"ok":True,"f":out.name,"sz":f"{v:.1f} {u}","dev":f"{dev['make']} {dev['model']}","dt":dt.strftime("%Y-%m-%d %H:%M")}
        return {"ok":False,"f":out.name,"e":"Empty"}
    except Exception as e: return {"ok":False,"f":out.name,"e":str(e)}

# ─── Instagram Scraper ───
RAPIDAPI_HOST="instagram-scraper-stable-api.p.rapidapi.com"

scrape_state={"active":False,"done":False,"log":[],"downloaded":0,"total":0,"folder":""}

def scrape_log(m,l="info"):
    scrape_state["log"].append({"t":datetime.now().strftime("%H:%M:%S"),"m":m,"l":l})

def ig_headers(api_key):
    return {"X-RapidAPI-Key":api_key,"X-RapidAPI-Host":RAPIDAPI_HOST,"Content-Type":"application/x-www-form-urlencoded"}

def ig_get_posts(api_key, username, max_posts=50, skip_reels=True):
    """Fetch posts from Instagram via RapidAPI"""
    hdrs=ig_headers(api_key); all_posts=[]; token=None
    while len(all_posts)<max_posts:
        url=f"https://{RAPIDAPI_HOST}/get_ig_user_posts.php"
        payload=f"username_or_url={username}&amount={min(max_posts-len(all_posts),50)}"
        if token: payload+=f"&pagination_token={token}"
        try:
            r=rq.post(url,headers=hdrs,data=payload,timeout=30)
            if r.status_code==403: scrape_log("❌ Erreur 403 — vérifie ton abonnement API","error"); break
            if r.status_code==401: scrape_log("❌ Clé API invalide","error"); break
            r.raise_for_status(); data=r.json()
            posts_raw=data.get("posts",[]) or data.get("items",[]) or data.get("data",{}).get("posts",[])
            if not posts_raw: scrape_log("⚠️ Aucun post trouvé"); break
            posts=[item.get("node",item) for item in posts_raw]
            for post in posts:
                mt=post.get("media_type",""); pt=post.get("product_type",""); tn=post.get("__typename","")
                is_reel=pt in["clips","reels"] or "reel" in str(mt).lower() or (tn=="GraphVideo" and post.get("clips_music_attribution_info"))
                if skip_reels and is_reel: continue
                all_posts.append(post)
            scrape_log(f"📥 {len(all_posts)} posts récupérés...")
            token=data.get("pagination_token") or data.get("end_cursor")
            if not token or not posts: break
            time.sleep(0.5)
        except Exception as e: scrape_log(f"❌ {e}","error"); break
    return all_posts[:max_posts]

def ig_extract_urls(post):
    """Extract image/video URLs from a post"""
    urls=[]
    # Main image
    cands=post.get("image_versions2",{}).get("candidates",[])
    if cands: urls.append(cands[0].get("url",""))
    elif post.get("display_url"): urls.append(post["display_url"])
    # Carousel items
    carousel=post.get("carousel_media",[])
    if not carousel:
        sidecar=post.get("edge_sidecar_to_children",{}).get("edges",[])
        carousel=[e.get("node",{}) for e in sidecar]
    for item in carousel:
        ic=item.get("image_versions2",{}).get("candidates",[])
        u=ic[0].get("url","") if ic else item.get("display_url","")
        if u and u not in urls: urls.append(u)
    return [u for u in urls if u]

def run_scrape(api_key, username, max_posts, skip_reels, output_base, days_filter=0, min_likes=0):
    """Run full scrape pipeline in background thread"""
    scrape_state.update(active=True,done=False,log=[],downloaded=0,total=0,folder="")
    username=username.lstrip("@").strip()
    scrape_log(f"🔍 Scraping @{username}...")
    
    # 1. Fetch posts
    posts=ig_get_posts(api_key, username, max_posts, skip_reels)
    if not posts:
        scrape_log("❌ Aucun post récupéré","error")
        scrape_state.update(active=False,done=True); return
    
    # Filter by date
    if days_filter>0:
        cutoff=time.time()-days_filter*86400
        before=len(posts)
        posts=[p for p in posts if p.get("taken_at",0)>=cutoff or p.get("taken_at_timestamp",0)>=cutoff]
        scrape_log(f"📅 Filtre {days_filter}j: {before} → {len(posts)} posts")
    
    # Filter by engagement
    if min_likes>0:
        before=len(posts)
        posts=[p for p in posts if (p.get("like_count",0) or p.get("edge_liked_by",{}).get("count",0) or 0)>=min_likes]
        scrape_log(f"❤️ Filtre {min_likes}+ likes: {before} → {len(posts)} posts")
    
    # Count total images
    all_urls=[]
    for post in posts:
        code=post.get("code") or post.get("shortcode") or post.get("id","unknown")
        urls=ig_extract_urls(post)
        for j,url in enumerate(urls):
            fname=f"{code}_{j+1}.jpg" if len(urls)>1 else f"{code}.jpg"
            all_urls.append((url,fname))
    
    scrape_state["total"]=len(all_urls)
    scrape_log(f"✅ {len(posts)} posts, {len(all_urls)} images à télécharger")
    
    # 2. Download
    folder=Path(output_base)/username
    folder.mkdir(parents=True,exist_ok=True)
    scrape_state["folder"]=str(folder)
    
    for url,fname in all_urls:
        fp=folder/fname
        if fp.exists():
            scrape_state["downloaded"]+=1; continue
        try:
            resp=rq.get(url,timeout=30); resp.raise_for_status()
            with open(fp,"wb") as f: f.write(resp.content)
            scrape_state["downloaded"]+=1
            if scrape_state["downloaded"]%5==0:
                scrape_log(f"📥 {scrape_state['downloaded']}/{scrape_state['total']} téléchargées...")
        except Exception as e:
            scrape_log(f"⚠️ {fname}: {e}","error")
        time.sleep(0.15)
    
    scrape_log(f"🎉 {scrape_state['downloaded']} images téléchargées dans {folder}","ok")
    track_stat("scrape",f"ig @{username} {scrape_state['downloaded']} files")
    scrape_state.update(active=False,done=True)

# ─── TikTok Scraper ───
TT_RAPIDAPI_HOST="tiktok-scrapper-videos-music-challenges-downloader.p.rapidapi.com"

tt_state={"active":False,"done":False,"log":[],"downloaded":0,"total":0,"folder":""}

def tt_log(m,l="info"):
    tt_state["log"].append({"t":datetime.now().strftime("%H:%M:%S"),"m":m,"l":l})

def tt_get_videos(api_key, username, max_videos=50):
    """Fetch videos from TikTok via RapidAPI"""
    hdrs={"X-RapidAPI-Key":api_key,"X-RapidAPI-Host":TT_RAPIDAPI_HOST}
    base=f"https://{TT_RAPIDAPI_HOST}"
    all_vids=[]; cursor=""
    while len(all_vids)<max_videos:
        url=f"{base}/user/{username}/feed"
        params={"max_cursor":cursor} if cursor else {}
        try:
            r=rq.get(url,headers=hdrs,params=params,timeout=30)
            if r.status_code==403: tt_log("❌ Erreur 403 — vérifie ton abonnement API","error"); break
            if r.status_code==401: tt_log("❌ Clé API invalide","error"); break
            r.raise_for_status(); data=r.json()
            inner=data.get("data",{})
            vids=inner.get("aweme_list",[]) or inner.get("videos",[]) or inner.get("itemList",[]) or data.get("aweme_list",[])
            if not vids: tt_log("⚠️ Aucune vidéo trouvée"); break
            all_vids.extend(vids)
            tt_log(f"📥 {len(all_vids)} vidéos récupérées...")
            has_more=inner.get("has_more",0)
            new_cursor=str(inner.get("max_cursor",""))
            if not has_more or not new_cursor or new_cursor=="0": break
            cursor=new_cursor; time.sleep(0.5)
        except Exception as e: tt_log(f"❌ {e}","error"); break
    return all_vids[:max_videos]

def tt_get_download_url(video, api_key):
    """Extract download URL from video data, fallback to /video/{id} endpoint"""
    vi=video.get("video",{})
    url=vi.get("play_addr",{}).get("url_list",[""])[0] or vi.get("download_addr",{}).get("url_list",[""])[0] or vi.get("play") or vi.get("downloadAddr")
    if not url:
        vid_id=video.get("id") or video.get("aweme_id","")
        if vid_id:
            try:
                hdrs={"X-RapidAPI-Key":api_key,"X-RapidAPI-Host":TT_RAPIDAPI_HOST}
                r=rq.get(f"https://{TT_RAPIDAPI_HOST}/video/{vid_id}",headers=hdrs,timeout=30)
                if r.ok:
                    vd=r.json()
                    url=vd.get("data",{}).get("play") or vd.get("data",{}).get("downloadUrl") or vd.get("play")
            except: pass
    return url

def run_tt_scrape(api_key, username, max_videos, output_base):
    """Run full TikTok scrape in background thread"""
    tt_state.update(active=True,done=False,log=[],downloaded=0,total=0,folder="")
    username=username.lstrip("@").strip()
    tt_log(f"🔍 Scraping TikTok @{username}...")
    
    videos=tt_get_videos(api_key, username, max_videos)
    if not videos:
        tt_log("❌ Aucune vidéo récupérée","error")
        tt_state.update(active=False,done=True); return
    
    tt_state["total"]=len(videos)
    tt_log(f"✅ {len(videos)} vidéos trouvées, téléchargement...")
    
    folder=Path(output_base)/username
    folder.mkdir(parents=True,exist_ok=True)
    tt_state["folder"]=str(folder)
    
    for video in videos:
        vid_id=video.get("id") or video.get("aweme_id","unknown")
        fp=folder/f"{vid_id}.mp4"
        if fp.exists():
            tt_state["downloaded"]+=1; continue
        url=tt_get_download_url(video, api_key)
        if not url:
            tt_log(f"⚠️ Pas d'URL pour {vid_id}","error"); continue
        try:
            resp=rq.get(url,stream=True,headers={"User-Agent":"Mozilla/5.0"},timeout=60)
            resp.raise_for_status()
            with open(fp,"wb") as f:
                for chunk in resp.iter_content(8192): f.write(chunk)
            tt_state["downloaded"]+=1
            if tt_state["downloaded"]%3==0:
                tt_log(f"📥 {tt_state['downloaded']}/{tt_state['total']} vidéos...")
        except Exception as e:
            tt_log(f"⚠️ {vid_id}: {e}","error")
        time.sleep(0.3)
    
    tt_log(f"🎉 {tt_state['downloaded']} vidéos téléchargées dans {folder}","ok")
    track_stat("scrape",f"tt @{username} {tt_state['downloaded']} files")
    tt_state.update(active=False,done=True)

# ─── Extension Queue System ───
ext_queue=[]  # [{id, url, platform, status, filename, error, added_at}]
ext_queue_lock=threading.Lock()
ext_queue_dest=""  # configurable destination folder

def ext_queue_add(url, platform="auto"):
    """Add a URL to the extension download queue"""
    with ext_queue_lock:
        job_id=f"eq_{int(time.time()*1000)}_{random.randint(100,999)}"
        if platform=="auto":
            if "instagram.com" in url or "instagr.am" in url: platform="ig"
            elif "tiktok.com" in url or "vm.tiktok.com" in url: platform="tt"
            else: platform="direct"
        ext_queue.append({"id":job_id,"url":url,"platform":platform,"status":"pending","filename":"","error":"","added_at":datetime.now().strftime("%H:%M:%S")})
        return job_id

def ext_queue_process():
    """Process all pending items in queue — download then auto-uniquify"""
    cfg=load_config()
    api_key=cfg.get("ig_key","").strip() or cfg.get("scraper_api_key","").strip()
    dest=ext_queue_dest or cfg.get("ext_queue_dest","") or str(Path.home()/"Downloads"/"zychad_inbox")
    Path(dest).mkdir(parents=True,exist_ok=True)
    # Auto-uniquify settings from config
    auto_uniq=cfg.get("ext_auto_uniquify",True)
    nv=int(cfg.get("variants",3))
    nw=int(cfg.get("workers",2))
    out_dir=cfg.get("ext_output_dir","") or str(Path(dest).parent/"zychad_output")
    dbl=cfg.get("ext_double_process",False)
    stealth=cfg.get("ext_stealth",False)
    
    while True:
        job=None
        with ext_queue_lock:
            for j in ext_queue:
                if j["status"]=="pending":
                    j["status"]="downloading"
                    job=j; break
        if not job: break
        
        try:
            # Step 1: Download
            if job["platform"]=="ig":
                fname=ext_download_ig(job["url"], api_key, dest)
            elif job["platform"]=="tt":
                tt_key=cfg.get("tt_key","").strip() or api_key
                fname=ext_download_tt(job["url"], tt_key, dest)
            else:
                fname=ext_download_direct(job["url"], dest)
            
            with ext_queue_lock:
                job["filename"]=fname
            
            # Step 2: Auto-uniquify if enabled
            if auto_uniq and not state["active"]:
                with ext_queue_lock:
                    job["status"]="uniquifying"
                # Create per-job input folder with just this file
                job_dir=Path(dest)/"_job_"+job["id"]
                job_dir.mkdir(exist_ok=True)
                job_out=Path(out_dir)/job["id"]
                job_out.mkdir(parents=True,exist_ok=True)
                # Move/copy downloaded files into job dir
                fnames=fname.split(", ") if ", " in fname else [fname]
                for fn in fnames:
                    src=Path(dest)/fn.strip()
                    if src.exists():
                        import shutil
                        shutil.copy2(src,job_dir/src.name)
                # Run uniquification
                try:
                    run_proc(str(job_dir),str(job_out),nv,nw,False,"local","","","",dbl,stealth)
                    with ext_queue_lock:
                        job["status"]="done"
                        job["output"]=str(job_out)
                    print(f"  [ext] Auto-uniquify done: {job_out}")
                except Exception as ue:
                    with ext_queue_lock:
                        job["status"]="done"
                        job["error"]=f"DL ok, uniquify error: {ue}"
                # Cleanup job dir
                try: import shutil; shutil.rmtree(job_dir)
                except: pass
            elif auto_uniq and state["active"]:
                # Uniquifier busy, just mark as downloaded
                with ext_queue_lock:
                    job["status"]="done"
                    job["error"]="Telecharge — uniquifier occupe, lance manuellement"
            else:
                with ext_queue_lock:
                    job["status"]="done"
        except Exception as e:
            with ext_queue_lock:
                job["status"]="error"
                job["error"]=str(e)

def ext_download_ig(url, api_key, dest):
    """Download IG reel/post/story by URL using get_media_data.php"""
    if not api_key: raise Exception("Cle API RapidAPI non configuree — entre-la dans l'onglet IG Scraper de ZyChad Meta et clique Sauvegarder")
    
    # Skip blob: URLs completely
    if url.startswith("blob:"):
        raise Exception("URL blob: — fais clic droit sur le lien du post, pas sur l'image")
    
    # Skip generic IG URLs without a post/reel shortcode
    import re
    clean=re.sub(r'\?.*$','',url).rstrip('/')
    # These are just homepage or profile URLs, not individual posts
    if clean in ["https://www.instagram.com","https://instagram.com"] or re.match(r'^https?://(www\.)?instagram\.com/?$',clean):
        raise Exception("Ouvre le post/reel individuellement, puis fais clic droit sur la page")
    # Profile page without post
    if re.match(r'^https?://(www\.)?instagram\.com/[^/]+/?$',clean) and "/p/" not in url and "/reel/" not in url and "/stories/" not in url:
        raise Exception("C'est une page profil — ouvre un post/reel puis fais clic droit")
    
    hdrs={"X-RapidAPI-Key":api_key,"X-RapidAPI-Host":RAPIDAPI_HOST}
    
    # Extract shortcode from various IG URL formats
    import re
    code=""
    # /p/CODE, /reel/CODE, /reels/CODE, /tv/CODE
    m=re.search(r'/(p|reel|reels|tv)/([A-Za-z0-9_-]+)',url)
    if m: code=m.group(2)
    
    # /stories/USERNAME/STORY_ID/
    story_id=""
    ms=re.search(r'/stories/([^/]+)/(\d+)',url)
    if ms: story_id=ms.group(2)
    
    if not code and not story_id:
        # Last attempt: just pass full URL to API
        code=""
    
    # Call get_media_data.php — try with full URL first (most reliable)
    api_url=f"https://{RAPIDAPI_HOST}/get_media_data.php"
    
    # Determine type param
    mtype="reel"
    if "/stories/" in url: mtype="story"
    elif "/p/" in url: mtype="post"
    
    params={"reel_post_code_or_url":url,"type":mtype}
    print(f"  [ext_download_ig] API call: {params}")
    
    r=rq.get(api_url,headers=hdrs,params=params,timeout=30)
    if r.status_code==403: raise Exception("403 — verifie ton abonnement RapidAPI")
    if r.status_code==401: raise Exception("Cle API invalide")
    r.raise_for_status()
    
    try:
        data=r.json()
    except:
        raise Exception(f"Reponse API non-JSON: {r.text[:200]}")
    
    print(f"  [ext_download_ig] API response keys: {list(data.keys()) if isinstance(data,dict) else type(data)}")
    
    # Handle API error responses
    if isinstance(data,dict) and data.get("error"):
        raise Exception(f"API: {data['error']}")
    if isinstance(data,dict) and data.get("status")=="fail":
        raise Exception(f"API: {data.get('message','fail')}")
    
    # The API might wrap data differently
    # Try to get the actual media data — could be in data directly, data.data, data.items[0], etc.
    media=data
    if "data" in data and isinstance(data["data"],dict): media=data["data"]
    elif "items" in data and isinstance(data["items"],list) and data["items"]: media=data["items"][0]
    elif "graphql" in data: 
        media=data.get("graphql",{}).get("shortcode_media",{}) or data.get("graphql",{})
    
    identifier=code or story_id or str(int(time.time()))
    
    # Try to extract media URLs from various response structures
    downloaded=[]
    
    # --- VIDEO ---
    video_url=None
    for vk in ["video_url","video_url_hd","video_dash_manifest"]:
        if media.get(vk):
            video_url=media[vk]; break
    if not video_url:
        vv=media.get("video_versions",[])
        if vv and isinstance(vv,list):
            video_url=vv[0].get("url","")
    if not video_url and media.get("is_video"):
        video_url=media.get("video_url","")
    
    if video_url:
        fname=f"{identifier}.mp4"
        fp=Path(dest)/fname
        resp=rq.get(video_url,timeout=60,headers={"User-Agent":"Mozilla/5.0"}); resp.raise_for_status()
        with open(fp,"wb") as f: f.write(resp.content)
        return fname
    
    # --- CAROUSEL ---
    carousel=media.get("carousel_media",[]) or media.get("edge_sidecar_to_children",{}).get("edges",[])
    if carousel:
        for i,item in enumerate(carousel):
            node=item.get("node",item) if isinstance(item,dict) else item
            # Video in carousel
            ivurl=node.get("video_url","")
            if not ivurl:
                ivv=node.get("video_versions",[])
                if ivv: ivurl=ivv[0].get("url","")
            # Image in carousel
            iurl=""
            ic=node.get("image_versions2",{}).get("candidates",[])
            if ic: iurl=ic[0].get("url","")
            if not iurl: iurl=node.get("display_url","") or node.get("thumbnail_src","")
            
            dl_url=ivurl or iurl
            if not dl_url: continue
            iext=".mp4" if ivurl else ".jpg"
            fname=f"{identifier}_{i+1}{iext}"
            fp=Path(dest)/fname
            try:
                resp=rq.get(dl_url,timeout=30,headers={"User-Agent":"Mozilla/5.0"}); resp.raise_for_status()
                with open(fp,"wb") as f: f.write(resp.content)
                downloaded.append(fname)
            except Exception as e:
                print(f"  [ext] carousel item {i}: {e}")
            time.sleep(0.1)
        if downloaded: return ", ".join(downloaded)
    
    # --- SINGLE IMAGE ---
    img_url=""
    ic=media.get("image_versions2",{}).get("candidates",[])
    if ic: img_url=ic[0].get("url","")
    if not img_url: img_url=media.get("display_url","") or media.get("thumbnail_src","") or media.get("image_url","")
    # Story image
    if not img_url:
        isr=media.get("image_versions2_story",{}).get("candidates",[])
        if isr: img_url=isr[0].get("url","")
    
    if img_url:
        fname=f"{identifier}.jpg"
        fp=Path(dest)/fname
        resp=rq.get(img_url,timeout=30,headers={"User-Agent":"Mozilla/5.0"}); resp.raise_for_status()
        with open(fp,"wb") as f: f.write(resp.content)
        return fname
    
    # --- NOTHING FOUND ---
    # Dump response keys for debugging
    print(f"  [ext_download_ig] FULL RESPONSE: {json.dumps(data,indent=2)[:2000]}")
    raise Exception(f"Aucun media trouve — cles API: {list(media.keys())[:10]}")

def ext_download_tt(url, api_key, dest):
    """Download TikTok video by URL"""
    if not api_key: raise Exception("Cle API RapidAPI non configuree")
    import re
    # Extract video ID from URL
    vid_id=""
    m=re.search(r'/video/(\d+)',url)
    if m: vid_id=m.group(1)
    
    if not vid_id:
        # Try to resolve short URL to get video ID
        try:
            r=rq.head(url,allow_redirects=True,timeout=10)
            m=re.search(r'/video/(\d+)',r.url)
            if m: vid_id=m.group(1)
        except: pass
    
    if not vid_id: raise Exception("Impossible d'extraire l'ID de la video TikTok")
    
    hdrs={"X-RapidAPI-Key":api_key,"X-RapidAPI-Host":TT_RAPIDAPI_HOST}
    r=rq.get(f"https://{TT_RAPIDAPI_HOST}/video/{vid_id}",headers=hdrs,timeout=30)
    if r.status_code==403: raise Exception("403 - Verifie ton abonnement API RapidAPI")
    r.raise_for_status()
    data=r.json()
    
    dl_url=data.get("data",{}).get("play") or data.get("data",{}).get("downloadUrl") or data.get("play") or data.get("downloadUrl","")
    if not dl_url: raise Exception("Pas d'URL de telechargement dans la reponse API")
    
    fname=f"tt_{vid_id}.mp4"
    fp=Path(dest)/fname
    resp=rq.get(dl_url,stream=True,headers={"User-Agent":"Mozilla/5.0"},timeout=60); resp.raise_for_status()
    with open(fp,"wb") as f:
        for chunk in resp.iter_content(8192): f.write(chunk)
    return fname

def ext_download_direct(url, dest):
    """Download a direct file URL"""
    resp=rq.get(url,stream=True,timeout=60,headers={"User-Agent":"Mozilla/5.0"}); resp.raise_for_status()
    ct=resp.headers.get("Content-Type","")
    ext=".mp4" if "video" in ct else ".jpg" if "image" in ct else ".mp4"
    fname=f"dl_{int(time.time())}{ext}"
    fp=Path(dest)/fname
    with open(fp,"wb") as f:
        for chunk in resp.iter_content(8192): f.write(chunk)
    return fname

# ─── Scheduler ───
scheduler_jobs=[]  # [{id, platform, username, api_key, interval_h, max_posts, skip_reels, output_base, next_run, active, last_run, last_status}]
scheduler_lock=threading.Lock()

def load_scheduler():
    global scheduler_jobs
    cfg=load_config()
    scheduler_jobs=cfg.get("scheduler_jobs",[])
    # Fix next_run for jobs that were saved
    for j in scheduler_jobs:
        if j.get("active") and j.get("next_run"):
            try:
                nr=datetime.fromisoformat(j["next_run"])
                if nr<datetime.now(): j["next_run"]=(datetime.now()+timedelta(minutes=1)).isoformat()
            except: j["next_run"]=(datetime.now()+timedelta(hours=j.get("interval_h",24))).isoformat()

def save_scheduler():
    save_config({"scheduler_jobs":scheduler_jobs})

def scheduler_add(job):
    with scheduler_lock:
        job["id"]=job.get("id") or datetime.now().strftime("%Y%m%d%H%M%S")+str(random.randint(100,999))
        job["active"]=True
        job["last_run"]=None
        job["last_status"]=None
        job["next_run"]=(datetime.now()+timedelta(hours=job.get("interval_h",24))).isoformat()
        scheduler_jobs.append(job)
        save_scheduler()
    return job["id"]

def scheduler_remove(job_id):
    with scheduler_lock:
        scheduler_jobs[:]=[j for j in scheduler_jobs if j["id"]!=job_id]
        save_scheduler()

def scheduler_toggle(job_id):
    with scheduler_lock:
        for j in scheduler_jobs:
            if j["id"]==job_id:
                j["active"]=not j["active"]
                if j["active"]: j["next_run"]=(datetime.now()+timedelta(hours=j.get("interval_h",24))).isoformat()
        save_scheduler()

def scheduler_run_job(job):
    """Execute a scheduled scrape job"""
    job["last_run"]=datetime.now().isoformat()
    try:
        if job["platform"]=="ig":
            run_scrape(job["api_key"],job["username"],job.get("max_posts",50),job.get("skip_reels",True),job.get("output_base",str(Path.home()/"Downloads"/"zychad_scrape")))
        elif job["platform"]=="tt":
            run_tt_scrape(job["api_key"],job["username"],job.get("max_posts",50),job.get("output_base",str(Path.home()/"Downloads"/"zychad_scrape")))
        job["last_status"]="ok"
    except Exception as e:
        job["last_status"]=f"error: {e}"
    job["next_run"]=(datetime.now()+timedelta(hours=job.get("interval_h",24))).isoformat()
    save_scheduler()

def scheduler_loop():
    """Background thread checking scheduled jobs"""
    while True:
        time.sleep(30)
        now=datetime.now()
        for job in scheduler_jobs[:]:
            if not job.get("active"): continue
            try:
                nr=datetime.fromisoformat(job["next_run"])
                if now>=nr:
                    # Don't run if scraper is already busy
                    if job["platform"]=="ig" and scrape_state["active"]: continue
                    if job["platform"]=="tt" and tt_state["active"]: continue
                    threading.Thread(target=scheduler_run_job,args=(job,),daemon=True).start()
            except: pass

# ─── Stats tracking ───
def load_stats():
    cfg=load_config()
    return cfg.get("stats",{"total_files":0,"total_variants":0,"total_scrapes":0,"history":[]})

def track_stat(event_type,details=""):
    """Track a processing or scrape event"""
    stats=load_stats()
    if event_type=="process":
        stats["total_files"]+=1
    elif event_type=="variants":
        stats["total_variants"]+=int(details) if details else 0
    elif event_type=="scrape":
        stats["total_scrapes"]+=1
    stats["history"].append({"t":datetime.now().isoformat(),"type":event_type,"d":str(details)})
    # Keep last 200 history entries
    stats["history"]=stats["history"][-200:]
    save_config({"stats":stats})

# ─── Integrated Telegram Bot (Raw API — zero dependency) ───
tg_bot_state={"active":False,"username":"","error":""}

def tg_api(token,method,data=None,files=None):
    """Call Telegram Bot API"""
    url=f"https://api.telegram.org/bot{token}/{method}"
    try:
        if files:
            # Multipart upload
            boundary=uid()
            body=b""
            if data:
                for k,v in data.items():
                    body+=f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
            for k,(fname,fdata,ct) in files.items():
                body+=f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{fname}\"\r\nContent-Type: {ct}\r\n\r\n".encode()
                body+=fdata+b"\r\n"
            body+=f"--{boundary}--\r\n".encode()
            req=urllib.request.Request(url,data=body,headers={"Content-Type":f"multipart/form-data; boundary={boundary}"})
            resp=urllib.request.urlopen(req,timeout=120)
            return json.loads(resp.read())
        elif data:
            req=urllib.request.Request(url,data=json.dumps(data).encode(),headers={"Content-Type":"application/json"})
            resp=urllib.request.urlopen(req,timeout=30)
            return json.loads(resp.read())
        else:
            resp=urllib.request.urlopen(url,timeout=30)
            return json.loads(resp.read())
    except Exception as e:
        return {"ok":False,"description":str(e)}

def tg_send(token,chat_id,text,parse_mode="Markdown",thread_id=None):
    params={"chat_id":chat_id,"text":text,"parse_mode":parse_mode}
    if thread_id: params["message_thread_id"]=thread_id
    return tg_api(token,"sendMessage",params)

def tg_edit(token,chat_id,msg_id,text):
    return tg_api(token,"editMessageText",{"chat_id":chat_id,"message_id":msg_id,"text":text,"parse_mode":"Markdown"})

def tg_send_doc(token,chat_id,filepath,fname):
    ct="video/mp4" if fname.endswith(".mp4") else "image/jpeg"
    with open(filepath,"rb") as f:
        return tg_api(token,"sendDocument",{"chat_id":str(chat_id)},files={"document":(fname,f.read(),ct)})

def tg_send_video(token,chat_id,filepath,fname):
    with open(filepath,"rb") as f:
        return tg_api(token,"sendVideo",{"chat_id":str(chat_id)},files={"video":(fname,f.read(),"video/mp4")})

def tg_download_file(token,file_id):
    """Get file path and download content"""
    r=tg_api(token,"getFile",{"file_id":file_id})
    if not r.get("ok"): return None
    fpath=r["result"]["file_path"]
    url=f"https://api.telegram.org/file/bot{token}/{fpath}"
    resp=urllib.request.urlopen(url,timeout=120)
    return resp.read()

def tg_bot_start():
    """Start Telegram bot in background thread using long polling"""
    cfg=load_config()
    token=cfg.get("tg_bot_token","").strip()
    if not token: tg_bot_state.update(active=False,error="No token"); return
    
    tg_variants=cfg.get("tg_variants",5)
    tg_max=cfg.get("tg_max_variants",50)
    tg_authorized=cfg.get("tg_authorized",[])
    user_vars={}
    album_buffer={}  # media_group_id → {"chat_id","files":[(file_id,fname,is_vid)],"user_id"}
    
    def process_album(mgid):
        """Process all files in an album batch"""
        if mgid not in album_buffer: return
        ab=album_buffer.pop(mgid)
        chat_id=ab["chat_id"]; files=ab["files"]; user_id=ab["user_id"]
        nv=user_vars.get(user_id,tg_variants)
        r=tg_send(token,chat_id,f"📦 Album : {len(files)} fichiers × {nv} variantes...")
        st_id=r.get("result",{}).get("message_id")
        total_sent=0
        for file_id,fname,is_vid in files:
            work=Path(tempfile.mkdtemp(prefix="zcbot_"))
            inp_f=work/fname; out_d=work/"out"; out_d.mkdir()
            try:
                fdata=tg_download_file(token,file_id)
                if not fdata: continue
                with open(inp_f,"wb") as ff: ff.write(fdata)
                results=[]
                for vi in range(nv):
                    oname=f"{inp_f.stem}_v{vi+1:04d}{'.mp4' if is_vid else '.jpg'}"
                    op=out_d/oname
                    try:
                        ok=(proc_video(str(inp_f),str(op),vi) if is_vid else proc_image(str(inp_f),str(op),vi))
                        if ok and op.exists(): results.append(op)
                    except: pass
                for fp in results:
                    try:
                        if is_vid: tg_send_video(token,chat_id,str(fp),fp.name)
                        else: tg_send_doc(token,chat_id,str(fp),fp.name)
                        time.sleep(0.3)
                        total_sent+=1
                    except: pass
            except: pass
            finally:
                try: shutil.rmtree(work)
                except: pass
        if st_id: tg_edit(token,chat_id,st_id,f"✅ Album terminé ! {total_sent} variantes envoyées")
        track_stat("variants",total_sent)
    
    def is_ok(uid):
        return not tg_authorized or uid in tg_authorized
    
    def handle_update(upd):
        """Process a single Telegram update"""
        msg=upd.get("message")
        if not msg: return
        chat_id=msg["chat"]["id"]
        user_id=msg["from"]["id"]
        text=msg.get("text","")
        
        # Commands
        if text.startswith("/start"):
            if not is_ok(user_id):
                tg_send(token,chat_id,"⛔ Non autorisé. Demande à ton Team Leader.")
                return
            nv=user_vars.get(user_id,tg_variants)
            tg_send(token,chat_id,
                "⚡ *ZyChad Bot*\n\n"
                "Envoie une vidéo ou image → je renvoie les variantes uniques.\n\n"
                f"Variantes: {nv}\n"
                "`/variants N` pour changer\n"
                "`/id` pour voir ton ID")
            return
        
        if text.startswith("/id"):
            tg_send(token,chat_id,f"Ton ID: `{user_id}`")
            return

        if text.startswith("/chatid"):
            tg_send(token,chat_id,f"Chat ID: `{chat_id}`")
            return

        if text.startswith("/topicid"):
            tid = msg.get("message_thread_id","")
            if tid:
                tg_send(token,chat_id,f"Topic ID: `{tid}`",thread_id=tid)
            else:
                tg_send(token,chat_id,"Pas de topic — ce groupe n'utilise pas les topics, ou envoie la commande dans un topic spécifique.")
            return
        
        if text.startswith("/variants"):
            if not is_ok(user_id): return
            parts=text.split()
            if len(parts)>1:
                try:
                    n=max(1,min(int(parts[1]),tg_max))
                    user_vars[user_id]=n
                    tg_send(token,chat_id,f"✅ {n} variantes")
                except:
                    tg_send(token,chat_id,f"Usage: `/variants 5` (max {tg_max})")
            else:
                tg_send(token,chat_id,f"Usage: `/variants 5` (max {tg_max})")
            return
        
        # File handling
        if not is_ok(user_id): 
            tg_send(token,chat_id,"⛔ Non autorisé."); return
        
        file_id=None; fname=""
        if msg.get("video"):
            file_id=msg["video"]["file_id"]
            fname=msg["video"].get("file_name",f"v_{uid()}.mp4")
        elif msg.get("document"):
            fname=msg["document"].get("file_name","file")
            ext=Path(fname).suffix.lower()
            if ext in [".mp4",".mov",".avi",".mkv",".jpg",".jpeg",".png",".webp"]:
                file_id=msg["document"]["file_id"]
            else:
                tg_send(token,chat_id,f"❌ Format non supporté: {ext}")
                return
        elif msg.get("photo"):
            file_id=msg["photo"][-1]["file_id"]
            fname=f"p_{uid()}.jpg"
        else:
            return  # Not a file message
        
        if not file_id: return
        
        # Album detection: buffer files with media_group_id
        mgid=msg.get("media_group_id")
        if mgid:
            if not is_ok(user_id): tg_send(token,chat_id,"⛔ Non autorisé."); return
            if mgid not in album_buffer:
                album_buffer[mgid]={"chat_id":chat_id,"files":[],"user_id":user_id}
            album_buffer[mgid]["files"].append((file_id,fname,Path(fname).suffix.lower() in [".mp4",".mov",".avi",".mkv"]))
            # Wait 2s for more files in the album, then process
            def _delayed_album(mg=mgid):
                time.sleep(2)
                process_album(mg)
            if len(album_buffer[mgid]["files"])==1:
                threading.Thread(target=_delayed_album,daemon=True).start()
            return
        
        nv=user_vars.get(user_id,tg_variants)
        is_vid=Path(fname).suffix.lower() in [".mp4",".mov",".avi",".mkv"]
        em="📹" if is_vid else "🖼"
        
        # Send status
        r=tg_send(token,chat_id,f"{em} *{fname}* — {nv} variantes en cours...")
        st_id=r.get("result",{}).get("message_id")
        
        # Download file
        work=Path(tempfile.mkdtemp(prefix="zcbot_"))
        inp=work/fname; out=work/"out"; out.mkdir()
        
        try:
            fdata=tg_download_file(token,file_id)
            if not fdata:
                if st_id: tg_edit(token,chat_id,st_id,"❌ Impossible de télécharger le fichier")
                return
            with open(inp,"wb") as f: f.write(fdata)
            
            # Process variants
            results=[]
            last_err=""
            for vi in range(nv):
                oname=f"{inp.stem}_v{vi+1:04d}{'.mp4' if is_vid else '.jpg'}"
                op=out/oname
                try:
                    ok=(proc_video(str(inp),str(op),vi) if is_vid else proc_image(str(inp),str(op),vi))
                    if ok and op.exists(): results.append(op)
                    else: last_err="Traitement retourné False"
                except Exception as ex:
                    last_err=str(ex)
            
            if not results:
                err_msg=f"❌ Échec du traitement"
                if last_err: err_msg+=f"\n`{last_err[:150]}`"
                if st_id: tg_edit(token,chat_id,st_id,err_msg)
                return
            
            if st_id: tg_edit(token,chat_id,st_id,f"✅ {len(results)} variantes ! Envoi...")
            
            # Send results
            for fp in results:
                try:
                    if is_vid:
                        tg_send_video(token,chat_id,str(fp),fp.name)
                    else:
                        tg_send_doc(token,chat_id,str(fp),fp.name)
                    time.sleep(0.5)  # Rate limit
                except Exception as e:
                    log(f"⚠️ Envoi échoué {fp.name}: {e}","warn")
            
            if st_id: tg_edit(token,chat_id,st_id,f"✅ *{fname}* — {len(results)} variantes envoyées !")
            track_stat("variants",len(results))
            
        except Exception as e:
            if st_id: tg_edit(token,chat_id,st_id,f"❌ {str(e)[:200]}")
        finally:
            try: shutil.rmtree(work)
            except: pass
    
    def _poll_loop():
        """Long polling loop"""
        # Verify token
        try:
            r=tg_api(token,"getMe")
            if not r.get("ok"):
                tg_bot_state.update(active=False,error=r.get("description","Token invalide"))
                return
            username=r["result"]["username"]
            tg_bot_state.update(active=True,username=username,error="")
            log(f"🤖 Bot Telegram @{username} connecté","ok")
        except Exception as e:
            tg_bot_state.update(active=False,error=str(e))
            return
        
        offset=0
        # Skip pending updates
        try:
            r=tg_api(token,"getUpdates",{"offset":-1,"timeout":0})
            if r.get("ok") and r.get("result"):
                offset=r["result"][-1]["update_id"]+1
        except: pass
        
        while tg_bot_state["active"]:
            try:
                r=tg_api(token,"getUpdates",{"offset":offset,"timeout":30})
                if not r.get("ok"):
                    time.sleep(5); continue
                for upd in r.get("result",[]):
                    offset=upd["update_id"]+1
                    try:
                        # Handle in thread to not block polling
                        threading.Thread(target=handle_update,args=(upd,),daemon=True).start()
                    except: pass
            except Exception as e:
                time.sleep(5)
        
        tg_bot_state.update(active=False)
    
    threading.Thread(target=_poll_loop,daemon=True).start()

def tg_bot_stop():
    tg_bot_state["active"]=False

# ─── Discord Bot (Raw HTTP API — zero dependency) ───
dc_bot_state={"active":False,"username":"","error":""}

def dc_api(token,method,endpoint,data=None,files=None):
    """Call Discord HTTP API"""
    url=f"https://discord.com/api/v10/{endpoint}"
    hdrs={"Authorization":f"Bot {token}"}
    try:
        if files:
            import io
            boundary=uid()
            body=b""
            if data:
                body+=f"--{boundary}\r\nContent-Disposition: form-data; name=\"payload_json\"\r\nContent-Type: application/json\r\n\r\n{json.dumps(data)}\r\n".encode()
            for idx,(fname,fdata,ct) in enumerate(files):
                body+=f"--{boundary}\r\nContent-Disposition: form-data; name=\"files[{idx}]\"; filename=\"{fname}\"\r\nContent-Type: {ct}\r\n\r\n".encode()
                body+=fdata+b"\r\n"
            body+=f"--{boundary}--\r\n".encode()
            hdrs["Content-Type"]=f"multipart/form-data; boundary={boundary}"
            req=urllib.request.Request(url,data=body,headers=hdrs,method=method)
        elif data:
            hdrs["Content-Type"]="application/json"
            req=urllib.request.Request(url,data=json.dumps(data).encode(),headers=hdrs,method=method)
        else:
            req=urllib.request.Request(url,headers=hdrs,method=method)
        resp=urllib.request.urlopen(req,timeout=30)
        return json.loads(resp.read()) if resp.status==200 else {}
    except Exception as e:
        return {"error":str(e)}

def dc_send_msg(token,channel_id,text):
    return dc_api(token,"POST",f"channels/{channel_id}/messages",{"content":text})

def dc_send_file(token,channel_id,filepath,fname):
    ct="video/mp4" if fname.endswith(".mp4") else "image/jpeg" if fname.endswith((".jpg",".jpeg")) else "application/octet-stream"
    with open(filepath,"rb") as f:
        return dc_api(token,"POST",f"channels/{channel_id}/messages",{"content":""},files=[(fname,f.read(),ct)])

def dc_bot_start():
    """Start Discord bot using Gateway (simplified polling via HTTP)"""
    cfg=load_config()
    token=cfg.get("dc_bot_token","").strip()
    if not token: dc_bot_state.update(active=False,error="No token"); return
    
    dc_variants=cfg.get("dc_variants",5)
    dc_authorized=cfg.get("dc_authorized_channels",[])
    
    def handle_dc_msg(msg):
        channel_id=msg.get("channel_id","")
        content=msg.get("content","")
        attachments=msg.get("attachments",[])
        author=msg.get("author",{})
        if author.get("bot"): return  # Ignore bots
        
        # Commands
        if content.startswith("/variants"):
            parts=content.split()
            if len(parts)>1:
                try:
                    n=max(1,min(int(parts[1]),50))
                    dc_send_msg(token,channel_id,f"✅ {n} variantes par fichier")
                except: dc_send_msg(token,channel_id,"Usage: `/variants 5`")
            return
        
        if content.startswith("/stats"):
            stats=load_stats()
            dc_send_msg(token,channel_id,f"📊 Stats: {stats['total_variants']} variantes, {stats['total_scrapes']} scrapes")
            return
        
        # Process attachments
        if not attachments: return
        if dc_authorized and channel_id not in dc_authorized: return
        
        for att in attachments:
            fname=att.get("filename","file")
            url=att.get("url","")
            ext=Path(fname).suffix.lower()
            if ext not in [".mp4",".mov",".jpg",".jpeg",".png",".webp"]: continue
            is_vid=ext in [".mp4",".mov",".avi"]
            
            dc_send_msg(token,channel_id,f"{'📹' if is_vid else '🖼'} **{fname}** — {dc_variants} variantes en cours...")
            
            work=Path(tempfile.mkdtemp(prefix="zcdc_"))
            inp_f=work/fname; out_d=work/"out"; out_d.mkdir()
            try:
                resp=urllib.request.urlopen(url,timeout=120)
                with open(inp_f,"wb") as f: f.write(resp.read())
                results=[]
                for vi in range(dc_variants):
                    oname=f"{inp_f.stem}_v{vi+1:04d}{'.mp4' if is_vid else '.jpg'}"
                    op=out_d/oname
                    try:
                        ok=(proc_video(str(inp_f),str(op),vi) if is_vid else proc_image(str(inp_f),str(op),vi))
                        if ok and op.exists(): results.append(op)
                    except: pass
                for fp in results:
                    try: dc_send_file(token,channel_id,str(fp),fp.name); time.sleep(0.5)
                    except: pass
                dc_send_msg(token,channel_id,f"✅ **{fname}** — {len(results)} variantes envoyées !")
                track_stat("variants",len(results))
            except Exception as e:
                dc_send_msg(token,channel_id,f"❌ Erreur: {str(e)[:200]}")
            finally:
                try: shutil.rmtree(work)
                except: pass
    
    # Simple polling via REST (no WebSocket needed)
    def _dc_poll():
        try:
            me=dc_api(token,"GET","users/@me")
            if "error" in me or "username" not in me:
                dc_bot_state.update(active=False,error=str(me.get("error","Invalid token")))
                return
            dc_bot_state.update(active=True,username=me["username"],error="")
            log(f"🎮 Bot Discord @{me['username']} connecté","ok")
        except Exception as e:
            dc_bot_state.update(active=False,error=str(e))
            return
        # Note: Full Discord bot requires WebSocket Gateway
        # This simplified version validates the token and provides the API
        # For full message listening, use discord.py or a Gateway connection
    
    threading.Thread(target=_dc_poll,daemon=True).start()

# ─── External API ───
def generate_api_key():
    return "zc_"+"".join(random.choices(string.ascii_letters+string.digits,k=32))

def get_api_key():
    cfg=load_config()
    key=cfg.get("api_key")
    if not key:
        key=generate_api_key()
        save_config({"api_key":key})
    return key

def check_api_key(headers):
    """Verify X-API-Key header"""
    provided=headers.get("X-API-Key","")
    return provided==get_api_key()

# ─── Similarity Checker (MSSIM + pHash — calibrated to industry tools) ───

def phash256(img):
    """Perceptual Hash 256-bit via DCT"""
    img=img.convert("L").resize((32,32),Image.LANCZOS)
    if HAS_NUMPY:
        pixels=np.array(img,dtype=np.float64)
        def dct1d(v):
            n=len(v); out=np.zeros(n)
            for k in range(n):
                s=0.0
                for i in range(n): s+=v[i]*np.cos(np.pi*(2*i+1)*k/(2*n))
                out[k]=s
            return out
        dct=np.zeros((32,32))
        for i in range(32): dct[i]=dct1d(pixels[i])
        for j in range(32): dct[:,j]=dct1d(dct[:,j])
        low=dct[:16,:16].flatten()
        med=float(np.median(low[1:]))
        return int("".join("1" if v>med else "0" for v in low),2)
    else:
        pixels=list(img.convert("L").resize((16,16),Image.LANCZOS).getdata())
        avg=sum(pixels)/len(pixels)
        return int("".join("1" if p>=avg else "0" for p in pixels),2)

def hamming(h1,h2):
    return bin(h1^h2).count("1")

def compute_similarity(path1, path2, bk=11):
    """Compute calibrated similarity score using MSSIM + pHash + MSSIM variance.
    Formula fitted to match industry similarity tools (TikFusion, etc.)."""
    try:
        img1=Image.open(path1); img2=Image.open(path2)
        a1=np.array(img1.convert("RGB").resize((256,256),Image.LANCZOS),dtype=np.float32)
        a2=np.array(img2.convert("RGB").resize((256,256),Image.LANCZOS),dtype=np.float32)
        g1=np.mean(a1,axis=2); g2=np.mean(a2,axis=2)
        c1=(0.01*255)**2; c2=(0.03*255)**2
        # Block SSIM
        ssims=[]
        for y in range(0,256-bk+1,bk):
            for x in range(0,256-bk+1,bk):
                b1=g1[y:y+bk,x:x+bk]; b2=g2[y:y+bk,x:x+bk]
                m1=float(np.mean(b1)); m2=float(np.mean(b2))
                v1b=float(np.var(b1)); v2b=float(np.var(b2))
                cv=float(np.mean((b1-m1)*(b2-m2)))
                s=(2*m1*m2+c1)*(2*cv+c2)/((m1**2+m2**2+c1)*(v1b+v2b+c2))
                ssims.append(s)
        mssim_mean=float(np.mean(ssims))*100
        mssim_std=float(np.std(ssims))*100
        # pHash distance
        ph1=phash256(img1); ph2=phash256(img2)
        pdist=hamming(ph1,ph2)
        # Calibrated score: polynomial regression fitted on 7 TikFusion reference pairs
        # 7 features: dm, P, S, M*P interaction, dm², P², S*P interaction
        coeffs = [-0.7909,-2.6201,-2.0260,18.4718,-19.3084,-8.6316,90.4730]
        if mssim_mean > 95 and pdist < 5:
            score = 100.0
        elif mssim_mean > 85:
            # Interpolate formula(85) → 100 for near-identical content
            Mc=85.0; Pc=max(0,min(70,float(pdist))); Sc=max(10,min(40,mssim_std))
            dm=Mc-100
            feats=[dm,Pc,Sc,Mc*Pc/1000,dm*dm/1000,Pc*Pc/1000,Sc*Pc/1000]
            base=sum(c*f for c,f in zip(coeffs,feats))+100
            t=(mssim_mean-85)/15
            score=base*(1-t)+100*t
        else:
            Mc=max(35,min(85,mssim_mean)); Pc=max(0,min(70,float(pdist))); Sc=max(10,min(40,mssim_std))
            dm=Mc-100
            feats=[dm,Pc,Sc,Mc*Pc/1000,dm*dm/1000,Pc*Pc/1000,Sc*Pc/1000]
            score=sum(c*f for c,f in zip(coeffs,feats))+100
        score = round(max(0, min(100, score)), 1)
        return {"similarity": score, "mssim": score, "combined": score,
                "raw_mssim": round(mssim_mean,1), "phash_dist": pdist, "mssim_std": round(mssim_std,1)}
    except Exception as e:
        return {"error": str(e)}

def compare_images(path1, path2, video_frame=False):
    bk = 32 if video_frame else 11
    return compute_similarity(path1, path2, bk)

def batch_compare(original_path, variants_dir):
    """Compare original vs all variants in a folder, return list of results"""
    orig=Path(original_path); vdir=Path(variants_dir)
    results=[]
    files=[f for f in vdir.rglob("*") if f.is_file() and f.suffix.lower() in VIDEO_EXTS|IMAGE_EXTS]
    is_vid=orig.suffix.lower() in VIDEO_EXTS
    for f in files:
        try:
            if is_vid:
                fr1=extract_frame(str(orig),1); fr2=extract_frame(str(f),1)
                if fr1 and fr2:
                    r=compare_images(fr1,fr2,video_frame=True)
                    try: Path(fr1).unlink(); Path(fr2).unlink()
                    except: pass
                else: r={"error":"Frame extraction failed"}
            else:
                r=compare_images(str(orig),str(f))
            score=r.get("similarity",r.get("combined",0))
            results.append({"file":f.name,"score":round(score,1),"status":"ok" if score<80 else "warning","details":r})
        except Exception as e:
            results.append({"file":f.name,"score":0,"status":"error","details":{"error":str(e)}})
    avg=round(sum(r["score"] for r in results)/max(len(results),1),1)
    warnings=[r for r in results if r["status"]=="warning"]
    return {"results":results,"average":avg,"total":len(results),"warnings":len(warnings)}

# ─── Invisible Watermark (LSB steganography) ───

def lsb_embed(img_path, msg, out_path=None):
    """Embed invisible watermark in image using LSB of blue channel.
    msg is encoded as bits in the least significant bits of pixels."""
    try:
        img=Image.open(img_path)
        if img.mode!="RGB": img=img.convert("RGB")
        if not HAS_NUMPY: return {"ok":False,"e":"numpy required"}
        a=np.array(img)
        # Encode message: length (32 bits) + UTF-8 bytes
        data=msg.encode("utf-8")
        bits=[]
        # Length header (32 bits)
        for bit in format(len(data),"032b"): bits.append(int(bit))
        # Data bits
        for byte in data:
            for bit in format(byte,"08b"): bits.append(int(bit))
        # Check capacity
        h,w,c=a.shape
        if len(bits)>h*w:
            return {"ok":False,"e":f"Message too long ({len(bits)} bits, max {h*w})"}
        # Embed in blue channel LSB
        flat=a[:,:,2].flatten()
        for i,b in enumerate(bits):
            flat[i]=(flat[i]&0xFE)|b
        a[:,:,2]=flat.reshape(h,w)
        out_img=Image.fromarray(a)
        op=out_path or str(img_path)
        out_img.save(op,"PNG")  # Must be lossless format
        return {"ok":True,"bits":len(bits),"file":op}
    except Exception as e:
        return {"ok":False,"e":str(e)}

def lsb_extract(img_path):
    """Extract invisible watermark from image LSB."""
    try:
        img=Image.open(img_path)
        if img.mode!="RGB": img=img.convert("RGB")
        if not HAS_NUMPY: return {"ok":False,"e":"numpy required"}
        a=np.array(img)
        flat=a[:,:,2].flatten()
        # Read length header (32 bits)
        length_bits="".join(str(flat[i]&1) for i in range(32))
        msg_len=int(length_bits,2)
        if msg_len<=0 or msg_len>10000:
            return {"ok":False,"e":"No watermark found"}
        # Read message bits
        total_bits=32+msg_len*8
        if total_bits>len(flat):
            return {"ok":False,"e":"Invalid watermark"}
        msg_bytes=[]
        for bi in range(msg_len):
            byte_bits="".join(str(flat[32+bi*8+j]&1) for j in range(8))
            msg_bytes.append(int(byte_bits,2))
        msg=bytes(msg_bytes).decode("utf-8",errors="replace")
        return {"ok":True,"message":msg,"length":msg_len}
    except Exception as e:
        return {"ok":False,"e":str(e)}

def extract_frame(video_path, time_s=0):
    ff=FFMPEG_PATH or "ffmpeg"
    tmp=Path(tempfile.mktemp(suffix=".jpg"))
    try:
        subprocess.run([ff,"-y","-ss",str(time_s),"-i",str(video_path),"-frames:v","1","-q:v","2",str(tmp)],
            capture_output=True,timeout=15)
        if tmp.exists() and tmp.stat().st_size>0: return tmp
    except: pass
    return None

def compare_videos(path1, path2):
    """Compare two videos: average raw metrics across frames, then calibrate once."""
    try:
        d1=vinfo(path1)["dur"]; d2=vinfo(path2)["dur"]
        n_frames=16
        raw_mssims=[]; raw_pdists=[]; raw_stds=[]
        for i in range(n_frames):
            pct=(i+0.5)/n_frames
            f1=extract_frame(path1,d1*pct); f2=extract_frame(path2,d2*pct)
            if f1 and f2:
                try:
                    img1=Image.open(str(f1)); img2=Image.open(str(f2))
                    a1=np.array(img1.convert("RGB").resize((256,256),Image.LANCZOS),dtype=np.float32)
                    a2=np.array(img2.convert("RGB").resize((256,256),Image.LANCZOS),dtype=np.float32)
                    g1=np.mean(a1,axis=2); g2=np.mean(a2,axis=2)
                    c1=(0.01*255)**2; c2=(0.03*255)**2
                    bk=32
                    ssims=[]
                    for y in range(0,256-bk+1,bk):
                        for x in range(0,256-bk+1,bk):
                            b1=g1[y:y+bk,x:x+bk]; b2=g2[y:y+bk,x:x+bk]
                            m1=float(np.mean(b1));m2=float(np.mean(b2))
                            v1b=float(np.var(b1));v2b=float(np.var(b2))
                            cv=float(np.mean((b1-m1)*(b2-m2)))
                            s=(2*m1*m2+c1)*(2*cv+c2)/((m1**2+m2**2+c1)*(v1b+v2b+c2))
                            ssims.append(s)
                    raw_mssims.append(float(np.mean(ssims))*100)
                    raw_stds.append(float(np.std(ssims))*100)
                    ph1=phash256(img1); ph2=phash256(img2)
                    raw_pdists.append(hamming(ph1,ph2))
                except: pass
            for f in [f1,f2]:
                if f and f.exists():
                    try: f.unlink()
                    except: pass
        if not raw_mssims: return {"error":"No frames extracted"}
        # Average raw metrics, then calibrate ONCE
        mssim_mean=float(np.mean(raw_mssims))
        mssim_std=float(np.mean(raw_stds))
        pdist=float(np.mean(raw_pdists))
        coeffs=[-0.7909,-2.6201,-2.0260,18.4718,-19.3084,-8.6316,90.4730]
        if mssim_mean > 95 and pdist < 5:
            score = 100.0
        elif mssim_mean > 85:
            Mc=85.0; Pc=max(0,min(70,pdist)); Sc=max(10,min(40,mssim_std))
            dm=Mc-100
            feats=[dm,Pc,Sc,Mc*Pc/1000,dm*dm/1000,Pc*Pc/1000,Sc*Pc/1000]
            base=sum(c*f for c,f in zip(coeffs,feats))+100
            t=(mssim_mean-85)/15
            score=base*(1-t)+100*t
        else:
            Mc=max(35,min(85,mssim_mean)); Pc=max(0,min(70,pdist)); Sc=max(10,min(40,mssim_std))
            dm=Mc-100
            feats=[dm,Pc,Sc,Mc*Pc/1000,dm*dm/1000,Pc*Pc/1000,Sc*Pc/1000]
            score=sum(c*f for c,f in zip(coeffs,feats))+100
        score=round(max(0,min(100,score)),1)
        return {"similarity":score,"mssim":score,"combined":score,"frames":len(raw_mssims)}
    except Exception as e:
        return {"error":str(e)}

sim_state={"active":False,"result":None}

def run_similarity(path1,path2):
    sim_state.update(active=True,result=None)
    try:
        ext1=Path(path1).suffix.lower()
        is_vid=ext1 in [".mp4",".mov",".avi",".mkv",".webm"]
        r=compare_videos(path1,path2) if is_vid else compare_images(path1,path2)
        sim_state.update(active=False,result=r)
    except Exception as e:
        sim_state.update(active=False,result={"error":str(e)})


# ─── Carousel Renamer ───
def rename_carousels(folder):
    """Rename carousel files: C5pFiKzpNn4_1.jpg → A1.jpg, C5pFiKzpNn4_2.jpg → A2.jpg, etc."""
    import re as _re
    from collections import defaultdict
    groups=defaultdict(list)
    for f in sorted(Path(folder).iterdir()):
        if not f.is_file(): continue
        m=_re.match(r'^(.+?)[_\-](\d+)$', f.stem)
        if m: groups[m.group(1)].append({"f":f,"n":int(m.group(2)),"ext":f.suffix})
    if not groups: return 0
    for p in groups: groups[p].sort(key=lambda x:x["n"])
    count=0
    for idx,prefix in enumerate(sorted(groups.keys())):
        # Letter sequence: A,B,...Z,AA,AB...
        i=idx; ltr=""
        while i>=0: ltr=string.ascii_uppercase[i%26]+ltr; i=i//26-1
        for fi in groups[prefix]:
            new_name=f"{ltr}{fi['n']}{fi['ext']}"
            new_path=fi["f"].parent/new_name
            if new_path!=fi["f"]:
                fi["f"].rename(new_path); count+=1
    return count

# ─── Processing thread ───
def run_proc(idir,odir,nv,nw,rename=False,dest="local",gdrive_folder_id="",tg_chat_id="",tg_topic_id="",double_process=False,stealth=False,naming_template=""):
    reset(); state["active"]=True; state["output"]=odir; state["input"]=idir
    if stealth: double_process=True  # Stealth forces double process
    inp=Path(idir); out=Path(odir); out.mkdir(parents=True,exist_ok=True)
    # Carousel rename step
    if rename:
        log("📝 Renommage des carrousels...")
        rc=rename_carousels(idir)
        if rc>0: log(f"✅ {rc} fichiers renommés (carrousels)","ok")
        else: log("ℹ️ Aucun carrousel détecté, skip rename","info")
    files=[f for f in sorted(inp.iterdir()) if f.is_file() and f.suffix.lower() in VIDEO_EXTS|IMAGE_EXTS]
    if not files: log("❌ Aucun fichier vidéo/image trouvé","error"); state.update(active=False,done=True); return
    state["total"]=len(files)*nv
    state["files_list"]=[{"name":f.name,"status":"waiting","type":"video" if f.suffix.lower() in VIDEO_EXTS else "image"} for f in files]
    log(f"🚀 {len(files)} fichiers × {nv} variantes = {state['total']} total")
    for fi,f in enumerate(files):
        # Cancel check
        if state.get("cancelled"):
            log("🛑 Traitement annulé par l'utilisateur","error")
            break
        # Pause check
        while state.get("paused"):
            time.sleep(0.3)
            if state.get("cancelled"): break
        if state.get("cancelled"): break
        ft="video" if f.suffix.lower() in VIDEO_EXTS else "image"
        ext=".mp4" if ft=="video" else f.suffix; base=f.stem
        # Stealth: random output format
        if stealth:
            if ft=="video": ext=random.choice([".mp4",".mp4",".mov",".webm"])
            else: ext=random.choice([".jpg",".png",".webp"])
        fd=out/base; fd.mkdir(parents=True,exist_ok=True)
        state["file"]=f.name; state["current_file_idx"]=fi
        state["files_list"][fi]["status"]="processing"
        log(f"📂 [{fi+1}/{len(files)}] {f.name} ({ft})")
        t0=time.time()
        # Stealth: random UUID filename
        if stealth:
            import uuid
            tasks=[(f,fd/f"{uuid.uuid4().hex[:12]}_v{vi+1:04d}{ext}",vi) for vi in range(nv)]
        elif naming_template:
            # Custom naming: {original}, {variant}, {date}, {time}, {uuid}, {index}
            import uuid as _uuid
            now=datetime.now()
            def _name(vi):
                n=naming_template.replace("{original}",base).replace("{variant}",f"v{vi+1:04d}")
                n=n.replace("{date}",now.strftime("%Y%m%d")).replace("{time}",now.strftime("%H%M%S"))
                n=n.replace("{uuid}",_uuid.uuid4().hex[:8]).replace("{index}",str(vi+1))
                if not n.endswith(ext): n+=ext
                return n
            tasks=[(f,fd/_name(vi),vi) for vi in range(nv)]
        else:
            tasks=[(f,fd/f"{base}_v{vi+1:04d}{ext}",vi) for vi in range(nv)]
        proc=proc_video if ft=="video" else proc_image
        with ThreadPoolExecutor(max_workers=nw) as ex:
            futs={ex.submit(proc,*t,stealth):t for t in tasks}
            for fut in as_completed(futs):
                if state.get("cancelled"): break
                r=fut.result(); state["progress"]+=1
                if r["ok"]:
                    log(f"✅ {r['f']} | {r['sz']} | {r['dev']} | {r['dt']}","ok")
                    state["results"].append(r)
                    # Double process: re-uniquify the variant with LIGHT params
                    if double_process and r["ok"]:
                        variant_path=fd/r["f"]
                        if variant_path.exists():
                            dbl_out=variant_path.with_stem(variant_path.stem+"_d")
                            r2=proc(variant_path,dbl_out,999,stealth,light=True)
                            if r2["ok"]:
                                # Replace original variant with double-processed one
                                try:
                                    variant_path.unlink()
                                    dbl_out.rename(variant_path)
                                    log(f"🔄 Double process: {r['f']}","ok")
                                except: pass
                else: log(f"❌ {r['f']}: {r.get('e','?')}","error")
        elapsed=time.time()-t0
        state["file_times"].append(elapsed)
        state["files_list"][fi]["status"]="cancelled" if state.get("cancelled") else "done"
        # ETA calculation
        if len(state["file_times"])>=1:
            avg=sum(state["file_times"])/len(state["file_times"])
            remaining=len(files)-fi-1
            eta_sec=avg*remaining
            if eta_sec<60: state["eta"]=f"~{int(eta_sec)}s"
            elif eta_sec<3600: state["eta"]=f"~{int(eta_sec//60)}min {int(eta_sec%60)}s"
            else: state["eta"]=f"~{int(eta_sec//3600)}h {int((eta_sec%3600)//60)}min"
    # Mark remaining files as cancelled if needed
    if state.get("cancelled"):
        for fl in state["files_list"]:
            if fl["status"]=="waiting": fl["status"]="cancelled"
    if not state.get("cancelled"):
        if dest=="drive":
            log("☁️ Upload vers Google Drive en cours...","info")
            state["file"]="Upload Drive..."
            if gdrive_token.get("access_token"):
                gdrive_upload_oauth(gdrive_token["access_token"], gdrive_folder_id, odir)
            else:
                log("❌ Google Drive non connecté — clique 'Connecter Google Drive' d'abord","error")
        elif dest=="telegram":
            log("📨 Envoi sur Telegram en cours...","info")
            state["file"]="Envoi Telegram..."
            if tg_chat_id:
                tg_send_files(tg_chat_id, tg_topic_id, odir)
            else:
                log("❌ Chat ID manquant","error")
            if gdrive_state.get("done"):
                log(f"☁️ {gdrive_state['files_uploaded']} fichiers envoyés sur Google Drive","ok")
            elif gdrive_state.get("error"):
                log(f"❌ Drive: {gdrive_state['error']}","error")
        else:
            zn=f"zychad_{len(files)}f_{nv}v_{int(time.time())}.zip"; zp=out/zn
            log("📦 Création du ZIP...")
            with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED) as zf:
                for root,_,zfs in os.walk(out):
                    for fn in zfs:
                        fp=Path(root)/fn
                        if fp.suffix!=".zip": zf.write(fp,fp.relative_to(out))
            state["zip"]=str(zp); log(f"📦 ZIP: {zp.stat().st_size/1048576:.1f} MB","ok")
    msg="🛑 Annulé" if state.get("cancelled") else f"🎉 Terminé ! {len(state['results'])} variantes uniques créées"
    log(msg,"error" if state.get("cancelled") else "ok")
    track_stat("variants",len(state['results']))
    state.update(active=False,done=True)
    # SaaS: callback to increment quota
    global saas_user_id
    if saas_user_id and not state.get("cancelled") and state.get("results"):
        web_url=os.environ.get("WEB_URL","http://web:3000")
        secret=os.environ.get("INTERNAL_SECRET","")
        if web_url and secret:
            try:
                rq.post(f"{web_url}/api/usage/increment",json={"userId":saas_user_id,"filesCount":len(files)},headers={"X-Internal-Secret":secret,"Content-Type":"application/json"},timeout=5)
            except Exception as _e: pass

# ─── Preview (single variant) ───
def run_preview(idir,odir):
    """Generate 1 variant of first file for preview"""
    inp=Path(idir); out=Path(odir); out.mkdir(parents=True,exist_ok=True)
    files=[f for f in sorted(inp.iterdir()) if f.is_file() and f.suffix.lower() in VIDEO_EXTS|IMAGE_EXTS]
    if not files: return {"error":"Aucun fichier trouvé"}
    f=files[0]
    ft="video" if f.suffix.lower() in VIDEO_EXTS else "image"
    ext=".mp4" if ft=="video" else f.suffix
    preview_out=out/f"_preview{ext}"
    proc=proc_video if ft=="video" else proc_image
    r=proc(f,preview_out,0)
    return {"ok":r.get("ok",False),"original":str(f),"variant":str(preview_out),"name":f.name,"type":ft,"error":r.get("e","")}

# ─── Google Drive Upload (OAuth) ───
GDRIVE_CLIENT_ID = "1022698347622-n7l9vuj29ri8rn0ipridjdtuo078t52c.apps.googleusercontent.com"
gdrive_state={"uploading":False,"progress":0,"total":0,"error":"","done":False,"files_uploaded":0}
gdrive_token = {"access_token": ""}

def gdrive_reset():
    gdrive_state.update(uploading=False,progress=0,total=0,error="",done=False,files_uploaded=0)

def gdrive_upload_oauth(token, folder_id, output_dir):
    """Upload files to Google Drive using OAuth token"""
    gdrive_reset()
    gdrive_state.update(uploading=True)
    try:
        out = Path(output_dir)
        files = [f for f in out.rglob("*") if f.is_file() and f.suffix != ".zip"]
        gdrive_state["total"] = len(files)
        if not files:
            gdrive_state.update(uploading=False, error="Aucun fichier à uploader")
            return
        # If folder_id provided, upload there. Otherwise upload to root "ZyChad Meta" folder
        parent = folder_id
        if not parent:
            # Create/find ZyChad Meta folder in user's Drive root
            r = rq.get("https://www.googleapis.com/drive/v3/files",
                headers={"Authorization": f"Bearer {token}"},
                params={"q": "name='ZyChad Meta' and mimeType='application/vnd.google-apps.folder' and trashed=false", "spaces": "drive"},
                timeout=15)
            existing = r.json().get("files", [])
            if existing:
                parent = existing[0]["id"]
            else:
                r = rq.post("https://www.googleapis.com/drive/v3/files",
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json={"name": "ZyChad Meta", "mimeType": "application/vnd.google-apps.folder"},
                    timeout=15)
                parent = r.json()["id"]
            log(f"📁 Dossier ZyChad Meta prêt","ok")
        for fi, fp in enumerate(files):
            mime = "video/mp4" if fp.suffix==".mp4" else "image/jpeg" if fp.suffix in[".jpg",".jpeg"] else "image/png" if fp.suffix==".png" else "application/octet-stream"
            fmeta = json.dumps({"name": fp.name, "parents": [parent]})
            bnd = f"zychad{int(time.time())}{fi}"
            body = (
                f"--{bnd}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{fmeta}\r\n"
                f"--{bnd}\r\nContent-Type: {mime}\r\n\r\n"
            ).encode() + fp.read_bytes() + f"\r\n--{bnd}--".encode()
            r = rq.post(
                "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
                headers={"Authorization": f"Bearer {token}", "Content-Type": f"multipart/related; boundary={bnd}"},
                data=body, timeout=120)
            gdrive_state["progress"] = fi + 1
            if r.status_code in [200, 201]:
                gdrive_state["files_uploaded"] += 1
                log(f"☁️ [{fi+1}/{len(files)}] {fp.name} uploadé","ok")
            else:
                log(f"⚠️ [{fi+1}/{len(files)}] {fp.name} échec {r.status_code}: {r.text[:250]}","error")
        gdrive_state.update(uploading=False, done=True)
        log(f"☁️ {gdrive_state['files_uploaded']}/{len(files)} fichiers envoyés sur Google Drive","ok")
    except Exception as e:
        gdrive_state.update(uploading=False, error=str(e)[:200])
        log(f"❌ Drive error: {str(e)[:150]}","error")

# ─── Telegram Send (post-processing) ───
tg_send_state={"uploading":False,"progress":0,"total":0,"error":"","done":False,"files_sent":0}

def tg_send_reset():
    tg_send_state.update(uploading=False,progress=0,total=0,error="",done=False,files_sent=0)

def tg_send_files(chat_id, topic_id, output_dir):
    """Send processed files to a Telegram chat/topic"""
    tg_send_reset()
    tg_send_state.update(uploading=True)
    try:
        cfg = load_config()
        token = cfg.get("tg_bot_token","").strip()
        if not token:
            tg_send_state.update(uploading=False, error="Bot Telegram non configuré — va dans l'onglet API")
            log("❌ Telegram: pas de bot token configuré","error")
            return
        out = Path(output_dir)
        files = [f for f in out.rglob("*") if f.is_file() and f.suffix != ".zip"]
        tg_send_state["total"] = len(files)
        if not files:
            tg_send_state.update(uploading=False, error="Aucun fichier à envoyer")
            return
        log(f"📨 Envoi de {len(files)} fichiers sur Telegram...","info")
        for fi, fp in enumerate(files):
            mime = "video/mp4" if fp.suffix==".mp4" else "image/jpeg" if fp.suffix in[".jpg",".jpeg"] else "image/png" if fp.suffix==".png" else "application/octet-stream"
            is_video = fp.suffix == ".mp4"
            endpoint = "sendVideo" if is_video else "sendPhoto" if fp.suffix in [".jpg",".jpeg",".png"] else "sendDocument"
            field = "video" if is_video else "photo" if fp.suffix in [".jpg",".jpeg",".png"] else "document"
            url = f"https://api.telegram.org/bot{token}/{endpoint}"
            data = {"chat_id": chat_id}
            if topic_id:
                data["message_thread_id"] = topic_id
            with open(fp, "rb") as f:
                r = rq.post(url, data=data, files={field: (fp.name, f, mime)}, timeout=120)
            tg_send_state["progress"] = fi + 1
            if r.status_code == 200 and r.json().get("ok"):
                tg_send_state["files_sent"] += 1
                log(f"📨 [{fi+1}/{len(files)}] {fp.name} envoyé","ok")
            else:
                err = r.json().get("description","") if r.status_code==200 else r.text[:150]
                log(f"⚠️ [{fi+1}/{len(files)}] {fp.name} échec: {err}","error")
        tg_send_state.update(uploading=False, done=True)
        log(f"📨 {tg_send_state['files_sent']}/{len(files)} fichiers envoyés sur Telegram","ok")
    except Exception as e:
        tg_send_state.update(uploading=False, error=str(e)[:200])
        log(f"❌ Telegram error: {str(e)[:150]}","error")

# ─── HTML GUI ───
LOGO_B64="iVBORw0KGgoAAAANSUhEUgAAACgAAAAoCAIAAAADnC86AAABCGlDQ1BJQ0MgUHJvZmlsZQAAeJxjYGA8wQAELAYMDLl5JUVB7k4KEZFRCuwPGBiBEAwSk4sLGHADoKpv1yBqL+viUYcLcKakFicD6Q9ArFIEtBxopAiQLZIOYWuA2EkQtg2IXV5SUAJkB4DYRSFBzkB2CpCtkY7ETkJiJxcUgdT3ANk2uTmlyQh3M/Ck5oUGA2kOIJZhKGYIYnBncAL5H6IkfxEDg8VXBgbmCQixpJkMDNtbGRgkbiHEVBYwMPC3MDBsO48QQ4RJQWJRIliIBYiZ0tIYGD4tZ2DgjWRgEL7AwMAVDQsIHG5TALvNnSEfCNMZchhSgSKeDHkMyQx6QJYRgwGDIYMZAKbWPz9HbOBQAAAI5klEQVR4nLVXa3BV1RX+1trnnnOTmxcJIUowJGICQo0QtK0KStEi+GBKddS+BqodZaajtVNHa2fsa+ro9KUO2FpbHVtLqc5U2toRR1GiVVFo5ZEoISDhFULI+3kfZ++9+uOcc3NTSOgPeubcO/vce2Z/e61vPb5F+MHLMBrGwmgYDWtgDKyGtbAWYmAFYnC2LwesIAIRQAEWiNYCMGAFbGEZYv9/wIA44VoELLACYkj0DTnbwKGVAWRwDgA5SNaAGdaeRWwHSgEClQV2ImAFEZCACMRAYPdZI9shZhE15mERwAnNFTX24qRkE6CYg7URK/+DXxxRigQyDng82STMIAZZApFY2PFbE5FY0cNJWAsi5HmkWM4E7oCVKCFRkqV5vM+JYFMaqTS0gRgQwSGOKSYyIgBEG0fx6mUNi+oqm452Pd24ZziZoZgzOTbhie0wBsaHMWEqh7eF9ckYSWXqKgqvqCmflvCSGf9gV/+uw13HOnrga+R7jmKPefN9X1xcW9l8+OTcqvI9R7uufOSFYd+AaRJoB+xEiZsN6eCGophN+Wsur72pvqr5WE/K1zNKEtfNPe+80oKBZPqVPW0b3t/XduD4untWLq6t/MzDG7fvbqupqWh5eM03PnfxY5u2OcX52kyY/Q4Uh9GksulkgxNYKxL3Nh84+dyONgwMQwyMAVNpSd61F85Yffmcu69e0Nhy9OZL69b+8Y3tO/a7lWVt+483tffUV06FPTPHHOEhwg6iWgkESnUOZqDYKS2EMbDGGtOb9De+8/HGxqY551fseOhLTHTtvJlvfXSkpb3nuiX1C2dO+9HL7yOmJuc4W7kUBJAgoQFI+ChCbkwMtDYAQQggclSspNAfHJ47Y2qBF7vnz41XXjC98Xu3dvePzDuv/IktO1/e3sr5npnU6Ag4KElhSCM3rQUCccYqDISsaF8XFCaeXX31W63t6za+9be6yu8sXzi1IP+OP2z5YM8hVZKYHDXrahXihVXMnpJdGKtoIuyQHk4+8vWlxXnenc9v/fW3vrB26cXBdnUVJWvNln9/coLjMTspNuG5T6JuqGFMlFQ+GSNaw2azK/jLVyJmJDm/umznA6seefXD8sL47VfMvfPZ1/514PiS+prHb7vqSO/Q/O8/35/MQJ0hnSJXj+WSgoiIhA7IqWgEC2Og1DNfufJQz9DBnqEHlzdc9MMNzS3HkO/ubjk6vSRx//JLbr/qol+89N6Z0inbFjnLsYTOxziyIaIcV48MrV06r2FG2arfbrlnybyfvr6reV+HV15sfCPFid+83XRpdcVH7T2OF5ucY8Kf2kPJkatAIodD6/BfrVmMpDIVBbED91/34bHeJes2d/z4lmvWvfJRWydiZI2FWGgNEViBNog5cB1M4G4HTBCOKleulQoi7ICJggoNQ9qk169amHCdu/6y3XXdtDZ9Kd8qJiKQQIhjjk1l8vPcuz+/4MTg6O+37uG4e9puxSAFZrAadysGMyllhXTGmozVGdGj/o0NM2+aV/nYu/v3HumzwFBGlxXkEYgoeJ9ZaHZFyXdv+PSjNy0ayWgYy0QTWEwMzgmuaEEOJGVnluTfu6C6tth741Dvpubjv1tZ3zGUeuj1j52iRKZ/qOnEwPILK3fvbXfz3ExGHMV+cvSuZQsXXXDOjkOdjXvaOO6aCcSaAyZYBgXBFSY0Q8S304u9d2+uqyxwfSvXzyp76IrqItdZsWH7aMq6caXj3qNvfvzXNYuf/ue+vu4BxB2/d2RO3TnlBfHOweRP/vFBd98wF+aLPT0wgykUN0xQgc+ZlRKNOz5VXlngfvW1g1N+9t5TuzumxGNJbUaMiFDaF7cwb9fh3p837t1674obFs6aU158y+K5629b/OKHn5Qm4s3HeynfmwgVgAMwWCAcxDg4qtusKvJjRvB2x2jSjV02vag/rX0r76757C+3HXy0sbWrexCet35rS+vJwdWXz3YhHUPJW5989dsrFiR9PdI3qgo8MzEw4aV+wEIsjISNz1olxiQzV033Gq+v6k7qYW2rC92vbW7dur/7VytqV9aWJ7V5ctvBDTsPN3cO6O4BpH0oQMw3l9Wvv21Rw8Mv7jrQwa4ydkJxSNjUDwEkwA5GBwNj2Wqb9lfXFjw4v8xT9MTOzsd3tMNqZDLLaqY8cFnV0poyAF3Dqdauod7RdJHrNFSVJtzYl59544VtLRx3rDawZiJFTNjUDwS5a8fGFmPDSjI4CjFQAm1YCayx2sfAKMTWVeStOL9sSXXprNKEp/jkcPLNfR1Pv7O3vbMPngp3CPY8HXYE/F/Y1sBax/irzuUEydudowd70xCB9uOsaxLcPZLp6htFOo2MjxhBa4ymYA08BaPzXU752gbicILRi3POQCACBxHOIBJWrX2ZlTMTiRhfUu7Vl8Vqit3zi71hX/Jcx/Ni11w4bXbVFHZjBYXxhrpp55xbrJSaPa3osuqpigiBKg42nAw4fAxfVY4yGVszxXtq32BTe/rGmqL7Li5LGnGUOjqoj4xY66gRbeOuKs2PzSzJS/qmqiS/oiguDCPCzCACq2gQ+e/6NR6YQruJyAgXJ9SaWQXzy/IuKM9r6sucSMmJfp2CunRG4ZzSOFgdGbHto+KT6k3bssK8QV8GMrYwzzMgjdBtIIXA+vHYORxnr4BsY5WYhGQKFfqSmdU18b8fGjo+YsRqT0za17AGOuppWsdgfN+HMY4Y7fuwAmtgA5qDoBlH9umAkc0ugTXQBjDw/SBKyWrRGjYc5MnoUKjoXBkTiZYA2+ZEeFS6ndOgZilgS2DERAwoRjBajC+iQiU6JlQE2e8xzWrDWTcYOVnBAhRpjQmBKcAWIYIoMAQC4bCajumhqIsHGjRUohzpVB22eQisBXF0AgPIRBZH2AzA5rSvkIlTFHHuDYgPqLFZV6IuAIY1wZw9MTAAIoBCicKRNciZrxinzPXBwgF05PDoRyug4AQGlicFziF7zOhcyYBTHC5Zn6to1sV4sjlw+5mAKfhke7YAHDUVBc6aOJ7ssQiIknMc2Qpk/gPdFyH0EL6SsAAAAABJRU5ErkJggg=="

HTML=r"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ZyChad Meta</title>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<meta name="theme-color" content="#0ea5c7">
<meta name="apple-mobile-web-app-capable" content="yes">
<link rel="manifest" href="/manifest.json">
<link rel="icon" type="image/png" href="data:image/png;base64,"""+LOGO_B64+r"""">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Sora:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#091a22;--s1:#0c222e;--s2:#102a38;--s3:#143345;
  --br:rgba(255,255,255,.08);--br2:rgba(255,255,255,.12);
  --teal:#0ea5c7;--teal2:#06b6d4;--teal3:#22d3ee;--teald:#0891b2;
  --txt:#e8f4f8;--dim:#7eb3c7;--mut:#4a7a8f;
  --grn:#34d399;--red:#f87171;--ylw:#fbbf24
}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--txt);font-family:'DM Sans',sans-serif;min-height:100vh;overflow-x:hidden}

/* Subtle background texture */
body::before{content:'';position:fixed;inset:0;background:radial-gradient(ellipse at 20% 0%,rgba(14,165,199,.06) 0%,transparent 60%),radial-gradient(ellipse at 80% 100%,rgba(6,182,212,.04) 0%,transparent 50%);pointer-events:none;z-index:0}

.w{max-width:640px;margin:0 auto;padding:40px 20px;position:relative;z-index:1}

/* Header */
.hdr{display:flex;align-items:center;gap:14px;margin-bottom:36px}
.hdr-logo{width:40px;height:40px;border-radius:10px;flex-shrink:0}
.hdr-txt h1{font-family:'Sora',sans-serif;font-size:22px;font-weight:700;color:#fff;letter-spacing:-.5px}
.hdr-txt h1 span{color:var(--teal2);font-weight:800}
.hdr-txt p{font-size:11px;color:var(--mut);letter-spacing:.5px;margin-top:1px}

/* Cards */
.c{background:var(--s1);border:1px solid var(--br);border-radius:12px;padding:24px;margin-bottom:14px;overflow:hidden}

/* FFmpeg warn */
.fw{background:rgba(248,113,113,.05);border:1px solid rgba(248,113,113,.2);border-radius:12px;padding:20px;margin-bottom:14px;display:none}
.fw h3{color:var(--red);font-family:'Sora',sans-serif;font-size:13px;font-weight:600;margin-bottom:8px}
.fw p{color:var(--dim);font-size:11px;line-height:1.8}
.fw code{background:var(--s2);padding:2px 7px;border-radius:4px;color:var(--ylw);font-family:'DM Sans',sans-serif}
.fw a{color:var(--teal3)}

/* Section label */
.sl{font-family:'Sora',sans-serif;font-weight:600;font-size:12px;color:var(--dim);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:14px}

/* Fields */
.fl{margin-bottom:12px}
.fl label{display:block;font-size:11px;color:var(--mut);margin-bottom:4px;font-weight:500}
.fl input{width:100%;background:var(--s2);border:1px solid var(--br);border-radius:8px;padding:10px 12px;color:var(--txt);font-family:inherit;font-size:13px;outline:none;transition:border-color .15s}
.fl input:focus{border-color:var(--teal)}
.fl input::placeholder{color:var(--mut)}
.rw{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.hint{background:var(--s2);border-radius:6px;padding:8px 10px;margin-top:5px;font-size:10px;color:var(--mut);line-height:1.6}
.hint code{color:var(--teal3);background:rgba(34,211,238,.06);padding:1px 4px;border-radius:3px;font-family:inherit}

/* Button */
.btn{width:100%;padding:13px;border:none;border-radius:10px;font-family:'Sora',sans-serif;font-size:14px;font-weight:600;cursor:pointer;transition:all .15s;letter-spacing:.3px}
.b-main{background:var(--teal);color:#fff}
.b-main:hover:not(:disabled){background:var(--teal2);box-shadow:0 4px 20px rgba(14,165,199,.25)}
.b-main:disabled{opacity:.4;cursor:not-allowed}
.b-out{background:transparent;border:1.5px solid var(--br2);color:var(--dim);margin-top:8px;font-size:12px;padding:10px}
.b-out:hover{border-color:var(--teal);color:var(--teal)}
.b-zip{background:rgba(52,211,153,.06);border:1.5px solid rgba(52,211,153,.25);color:var(--grn);margin-top:8px}
.b-zip:hover{background:rgba(52,211,153,.1);border-color:var(--grn)}

/* Progress */
.pr{display:none}.pr.on{display:block}
.hide{display:none!important}
.ph{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.pt{font-family:'Sora',sans-serif;font-size:12px;font-weight:600;color:var(--txt)}.ps{color:var(--mut);font-size:11px;font-weight:500}
.pb{background:var(--s3);border-radius:4px;height:4px;overflow:hidden;margin-bottom:12px}
.pf{height:100%;border-radius:4px;background:linear-gradient(90deg,var(--teald),var(--teal3));width:0%;transition:width .3s}
.pl{background:var(--bg);border-radius:6px;padding:10px;max-height:220px;overflow-y:auto;font-size:10px;line-height:1.9;font-family:'DM Sans',sans-serif}
.pl::-webkit-scrollbar{width:4px}.pl::-webkit-scrollbar-thumb{background:var(--br2);border-radius:2px}
.lo{color:var(--grn)}.le{color:var(--red)}.li{color:var(--mut)}.lt{color:rgba(255,255,255,.2);margin-right:5px}

/* Results */
.rs{display:none}.rs.on{display:block;text-align:center}
.rc{font-family:'Sora',sans-serif;font-size:40px;font-weight:800;color:var(--teal3);margin-bottom:2px}
.rx{color:var(--mut);font-size:11px;margin-bottom:14px}

/* Tags */
.tags{display:flex;flex-wrap:wrap;gap:4px;margin-top:12px}
.tag{background:rgba(14,165,199,.06);border:1px solid rgba(14,165,199,.15);border-radius:4px;padding:2px 7px;font-size:9px;color:var(--teal2);font-weight:500}

/* Spinner */
@keyframes spin{to{transform:rotate(360deg)}}
.sp{display:inline-block;width:14px;height:14px;border:2px solid rgba(255,255,255,.2);border-top-color:#fff;border-radius:50%;animation:spin .6s linear infinite;vertical-align:middle;margin-right:6px}

@media(max-width:600px){.rw{grid-template-columns:1fr}.w{padding:24px 16px}}

/* Tabs */
.tabs{display:flex;gap:2px;margin-bottom:14px;background:var(--s1);border-radius:8px;padding:3px;border:1px solid var(--br)}
.tab{flex:1;padding:9px;text-align:center;font-family:'Sora',sans-serif;font-size:12px;font-weight:600;color:var(--mut);cursor:pointer;border-radius:6px;transition:all .15s;border:none;background:none}
.tab.on{background:var(--s3);color:var(--teal3)}
.tab:hover:not(.on){color:var(--dim)}

/* Scraper section */
.sc{display:none;max-width:100%;overflow:hidden;box-sizing:border-box}.sc.on{display:block}
.sc-log{background:var(--bg);border-radius:6px;padding:8px 10px;max-height:150px;overflow-y:auto;font-size:10px;line-height:1.8;margin-top:10px;display:none}
.sc-log.on{display:block}
.sc-prog{margin-top:10px;display:none}.sc-prog.on{display:flex;align-items:center;gap:10px}
.sc-bar{flex:1;background:var(--s3);border-radius:4px;height:4px;overflow:hidden}
.sc-fill{height:100%;border-radius:4px;background:linear-gradient(90deg,var(--teald),var(--teal3));width:0%;transition:width .3s}
.sc-num{font-size:11px;color:var(--mut);font-weight:500;white-space:nowrap}
.sc-done{margin-top:10px;padding:10px;background:rgba(52,211,153,.06);border:1px solid rgba(52,211,153,.2);border-radius:6px;font-size:11px;color:var(--grn);display:none}
.sc-done.on{display:block}
.fl input[type=password]{font-family:'DM Sans',sans-serif}
.pbtn{background:var(--s3);border:1px solid var(--br);border-radius:6px;padding:6px 12px;color:var(--teal2);font-family:'DM Sans',sans-serif;font-size:11px;font-weight:600;cursor:pointer;transition:all .15s}
.pbtn:hover{border-color:var(--teal);background:rgba(14,165,199,.08)}

/* Scheduler jobs */
.sj{display:flex;align-items:center;justify-content:space-between;padding:10px;background:var(--s2);border-radius:8px;border:1px solid var(--br);margin-bottom:6px}
.sj-info{flex:1}
.sj-name{font-weight:600;color:var(--txt);font-size:12px}
.sj-detail{font-size:10px;color:var(--mut);margin-top:2px}
.sj-status{font-size:9px;padding:2px 8px;border-radius:4px;font-weight:600}
.sj-on{background:rgba(52,211,153,.1);color:var(--grn)}
.sj-off{background:rgba(248,113,113,.1);color:var(--red)}
.sj-actions{display:flex;gap:4px}
/* Dashboard history */
.hist-row{padding:6px 0;border-bottom:1px solid var(--br);display:flex;gap:10px}
.hist-time{color:var(--mut);font-size:10px;min-width:120px}
.hist-type{font-size:9px;padding:1px 6px;border-radius:3px;font-weight:600}
.ht-scrape{background:rgba(14,165,199,.1);color:var(--teal2)}
.ht-variants{background:rgba(52,211,153,.1);color:var(--grn)}
/* Light theme override */
body.light{--bg:#f5f7fa;--s1:#ffffff;--s2:#f0f2f5;--s3:#e8ebef;--br:#d0d5dd;--txt:#1a1a2e;--dim:#4a5568;--mut:#718096;--teal:#0ea5c7;--teal2:#0891b2;--teal3:#06b6d4;--grn:#34d399;--red:#f87171}
body.light .c{background:var(--s1);border-color:var(--br)}
body.light input,body.light select,body.light textarea{background:var(--s2)!important;color:var(--txt)!important;border-color:var(--br)!important}
body.light .tab{color:var(--dim)}body.light .tab.on{color:var(--teal);border-color:var(--teal)}
body.light .tag{border-color:var(--br);color:var(--dim)}
</style></head><body>
<div class="w">

<div class="hdr">
  <img class="hdr-logo" src="data:image/png;base64,"""+LOGO_B64+r"""" alt="ZC">
  <div class="hdr-txt">
    <h1>Zy<span>Chad</span> Meta</h1>
    <p>Content Uniquifier · Video & Image</p>
  </div>
  <div style="margin-left:auto;display:flex;gap:8px;align-items:center">
    <select id="lang-sel" onchange="setLang(this.value)" style="background:var(--s2);border:1px solid var(--br);border-radius:6px;padding:4px 8px;color:var(--txt);font-size:11px;cursor:pointer">
      <option value="fr">🇫🇷 FR</option><option value="en">🇬🇧 EN</option><option value="es">🇪🇸 ES</option>
    </select>
    <button onclick="toggleTheme()" style="background:var(--s2);border:1px solid var(--br);border-radius:6px;padding:4px 10px;color:var(--txt);cursor:pointer;font-size:14px" title="Dark/Light mode" id="theme-btn">☀️</button>
  </div>
</div>

<div class="fw" id="fw"><h3>FFmpeg non détecté</h3><div id="fs"></div></div>

<!-- Tabs -->
<div class="tabs">
<button class="tab on" onclick="stab(0)">Uniquifier</button>
<button class="tab" onclick="stab(1)">IG Scraper</button>
<button class="tab" onclick="stab(2)">TikTok Scraper</button>
<button class="tab" onclick="stab(3)">Scheduler</button>
<button class="tab" onclick="stab(4)">Dashboard</button>
<button class="tab" onclick="stab(5)">Détecteur</button>
<button class="tab" onclick="stab(6)">API</button>
</div>

<!-- TAB 0: Uniquifier -->
<div class="sc on" id="t0">
<div class="c">
<div class="sl">Configuration</div>
<div class="fl"><label>Dossier source</label>
<div id="dropzone" style="border:2px dashed var(--br);border-radius:10px;padding:20px;text-align:center;cursor:pointer;transition:all .2s;margin-bottom:6px" onclick="pickFolder('idir')" ondragover="event.preventDefault();this.style.borderColor='var(--teal)';this.style.background='rgba(14,165,199,.05)'" ondragleave="this.style.borderColor='var(--br)';this.style.background='none'" ondrop="handleDrop(event)">
<div id="dz-text" style="color:var(--mut);font-size:12px">
<div style="font-size:28px;margin-bottom:8px;opacity:.5">📂</div>
Glisse tes fichiers ici ou clique pour parcourir<br>
<span style="font-size:10px;color:var(--mut)">Vidéos (.mp4 .mov .avi .mkv) · Images (.jpg .png .webp)</span>
</div>
<div id="dz-ok" style="display:none;color:var(--grn);font-size:12px"></div>
</div>
<div id="dz-filelist" style="display:none;max-height:150px;overflow-y:auto;margin-bottom:6px;border:1px solid var(--br);border-radius:8px;background:var(--s2)"></div>
<input type="text" id="idir" placeholder="Ou colle un chemin manuellement" style="font-size:11px">
</div>
<div class="fl"><label>Destination</label>
<div style="display:flex;gap:4px;margin-bottom:8px">
<button class="pbtn" id="dest-local-btn" onclick="destToggle('local')" style="font-size:10px;padding:4px 10px;background:var(--teal);color:#000">💻 Local</button>
<button class="pbtn" id="dest-drive-btn" onclick="destToggle('drive')" style="font-size:10px;padding:4px 10px">☁️ Google Drive</button>
<button class="pbtn" id="dest-tg-btn" onclick="destToggle('telegram')" style="font-size:10px;padding:4px 10px">📨 Telegram</button>
</div>
<div id="dest-local">
<div style="display:flex;gap:6px">
<input type="text" id="odir" placeholder="Auto-généré si vide" style="flex:1">
<button onclick="pickFolder('odir')" style="background:var(--s3);border:1px solid var(--br);border-radius:8px;padding:8px 14px;color:var(--teal2);font-family:'Sora',sans-serif;font-size:11px;font-weight:600;cursor:pointer;white-space:nowrap;transition:all .15s" onmouseover="this.style.borderColor='var(--teal)'" onmouseout="this.style.borderColor='var(--br)'">Parcourir</button>
</div></div>
<div id="dest-drive" style="display:none">
<div id="gd-not-connected">
<button class="btn" onclick="gdConnect()" style="width:100%;padding:10px;font-size:12px;margin-bottom:6px">🔗 Connecter Google Drive</button>
</div>
<div id="gd-connected" style="display:none">
<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
<div style="width:8px;height:8px;background:var(--grn);border-radius:50%"></div>
<span style="font-size:11px;color:var(--grn)" id="gd-user-email">Connecté</span>
<button class="pbtn" onclick="gdConnect()" style="font-size:9px;padding:2px 6px;margin-left:auto">Changer</button>
</div>
<input type="text" id="gd-folder-id" placeholder="Folder ID (optionnel — sinon ça va dans 'ZyChad Meta')" style="font-size:11px;padding:8px 10px;width:100%">
<div style="font-size:9px;color:var(--mut);margin-top:4px;line-height:1.5">L'ID est dans l'URL : drive.google.com/drive/folders/<strong style="color:var(--dim)">ID_ICI</strong></div>
</div>
<div id="gd-progress" style="display:none;margin-top:8px">
<div style="height:4px;background:var(--s2);border-radius:2px;overflow:hidden"><div id="gd-fill" style="height:100%;background:var(--teal);width:0%;transition:width .3s"></div></div>
<div id="gd-status" style="font-size:10px;color:var(--mut);margin-top:4px"></div>
</div>
</div>
<div id="dest-telegram" style="display:none">
<input type="text" id="tg-chat-id" placeholder="Chat ID (ex: -1001234567890)" style="font-size:11px;padding:8px 10px;width:100%;margin-bottom:6px">
<input type="text" id="tg-topic-id" placeholder="Topic ID (optionnel — pour les groupes avec topics)" style="font-size:11px;padding:8px 10px;width:100%;margin-bottom:6px">
<div style="font-size:9px;color:var(--mut);line-height:1.6">
Invite le bot <strong style="color:var(--teal3)" id="tg-bot-name">@ton_bot</strong> dans ton groupe en admin, puis colle le Chat ID.<br>
Tape <code style="background:var(--s2);padding:1px 4px;border-radius:3px">/chatid</code> pour le Chat ID et <code style="background:var(--s2);padding:1px 4px;border-radius:3px">/topicid</code> dans un topic pour son ID.
</div>
<div id="tg-progress" style="display:none;margin-top:8px">
<div style="height:4px;background:var(--s2);border-radius:2px;overflow:hidden"><div id="tg-fill" style="height:100%;background:var(--teal);width:0%;transition:width .3s"></div></div>
<div id="tg-status" style="font-size:10px;color:var(--mut);margin-top:4px"></div>
</div>
</div>
</div>
<div style="margin-bottom:12px">
<div style="font-size:11px;color:var(--mut);margin-bottom:6px;font-weight:500">Présets</div>
<div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center" id="presetBar">
<button onclick="savePreset()" class="pbtn" style="border-style:dashed">+ Sauvegarder</button>
</div>
</div>
<div class="rw">
<div class="fl"><label>Variantes / fichier</label><input type="number" id="nv" value="10" min="1" max="10000"></div>
<div class="fl"><label>Workers</label><input type="number" id="nw" value="4" min="1" max="16"></div>
</div>
<div style="margin:12px 0;display:flex;align-items:center;gap:8px">
<input type="checkbox" id="rn" style="width:16px;height:16px;accent-color:var(--teal)">
<label for="rn" style="font-size:12px;color:var(--dim);cursor:pointer">Renommer les carrousels avant traitement <span style="color:var(--mut);font-size:10px">(C5pFi_1.jpg → A1.jpg)</span></label>
</div>
<div style="margin:6px 0;display:flex;align-items:center;gap:8px">
<input type="checkbox" id="dbl" style="width:16px;height:16px;accent-color:var(--teal)">
<label for="dbl" style="font-size:12px;color:var(--dim);cursor:pointer">Double Process <span style="color:var(--mut);font-size:10px">(variante de variante — fingerprint encore plus unique)</span></label>
</div>
<div style="margin:6px 0;display:flex;align-items:center;gap:8px">
<input type="checkbox" id="stealth" style="width:16px;height:16px;accent-color:var(--red)">
<label for="stealth" style="font-size:12px;color:var(--dim);cursor:pointer">🥷 Mode Stealth <span style="color:var(--mut);font-size:10px">(zero metadata, format random, nom UUID, double process auto, pipeline aléatoire)</span></label>
</div>
<div class="tags">
<span class="tag">Ré-encodage H.264</span><span class="tag">Pixel Shift</span><span class="tag">Zoom Crop</span>
<span class="tag">Speed ±4%</span><span class="tag">Cut Start/End</span><span class="tag">Waveform Shift</span>
<span class="tag">Color Grading</span><span class="tag">Sharpening</span><span class="tag">Noise</span>
<span class="tag">Device Spoof</span><span class="tag">EXIF Inject</span><span class="tag">Date Spoof</span>
<span class="tag">GPS Spoof</span><span class="tag">Bitrate Variable</span><span class="tag">Audio AAC</span>
<span class="tag" style="border-color:var(--teal3)">Hue Shift</span><span class="tag" style="border-color:var(--teal3)">Micro Blur</span><span class="tag" style="border-color:var(--teal3)">Vignette</span>
<span class="tag" style="border-color:var(--teal3)">Grain Overlay</span><span class="tag" style="border-color:var(--teal3)">GOP Random</span><span class="tag" style="border-color:var(--teal3)">Letterbox</span>
<span class="tag" style="border-color:#e8a">Pitch Shift</span><span class="tag" style="border-color:#e8a">EQ Random</span><span class="tag" style="border-color:#e8a">Micro Reverb</span>
<span class="tag" style="border-color:#e8a">Phase Invert</span><span class="tag" style="border-color:#e8a">HP/LP Filter</span><span class="tag" style="border-color:#e8a">Stereo Width</span>
<span class="tag" style="border-color:#a8e">Chromatic Ab.</span><span class="tag" style="border-color:#a8e">Lens Distortion</span><span class="tag" style="border-color:#a8e">Shadow/Highlight</span>
</div>
</div>

<div style="display:flex;gap:6px;margin-bottom:10px">
<button class="btn b-main" id="sb" onclick="go()" style="flex:1">Lancer le traitement</button>
<button class="pbtn" id="preview-btn" onclick="genPreview()" style="font-size:10px;padding:8px 12px;white-space:nowrap" title="Générer 1 preview">👁 Preview</button>
</div>

<div id="preview-zone" style="display:none;margin-bottom:12px" class="c">
<div style="font-size:11px;color:var(--dim);font-weight:600;margin-bottom:8px">Preview — 1 variante générée</div>
<div style="display:flex;gap:8px">
<div style="flex:1;min-width:0"><div style="font-size:9px;color:var(--mut);margin-bottom:4px">ORIGINAL</div><div id="pv-orig" style="border-radius:8px;overflow:hidden;background:var(--s2);max-height:200px;display:flex;align-items:center;justify-content:center"></div></div>
<div style="flex:1;min-width:0"><div style="font-size:9px;color:var(--mut);margin-bottom:4px">VARIANTE</div><div id="pv-var" style="border-radius:8px;overflow:hidden;background:var(--s2);max-height:200px;display:flex;align-items:center;justify-content:center"></div></div>
</div>
<div style="display:flex;gap:6px;margin-top:8px">
<button class="btn b-main" onclick="go()" style="flex:1;font-size:11px;padding:8px">✅ Valider → Lancer le batch</button>
<button class="pbtn" onclick="genPreview()" style="font-size:10px;padding:6px 10px">🔄 Re-générer</button>
</div>
</div>

<div class="c pr" id="pc">
<div class="ph">
<span class="pt" id="pt">Initialisation...</span>
<span id="eta-display" style="font-size:10px;color:var(--teal3);margin-left:auto;white-space:nowrap"></span>
<span class="ps" id="ps">0 / 0</span>
</div>
<div class="pb"><div class="pf" id="pf"></div></div>
<div style="display:flex;gap:6px;margin:8px 0" id="proc-controls" class="hide">
<button class="pbtn" id="pause-btn" onclick="togglePause()" style="font-size:10px;padding:4px 12px">⏸ Pause</button>
<button class="pbtn" id="cancel-btn" onclick="cancelJob()" style="font-size:10px;padding:4px 12px;border-color:var(--red)">✕ Annuler</button>
<button class="pbtn" id="sound-btn" onclick="soundEnabled=!soundEnabled;this.textContent=soundEnabled?'🔔':'🔇'" style="font-size:10px;padding:4px 8px;margin-left:auto" title="Son de notification">🔔</button>
</div>
<div id="queue-list" style="margin:8px 0;max-height:120px;overflow-y:auto"></div>
<div class="pl" id="pl"></div></div>

<div class="c rs" id="rc">
<div class="rc" id="rn2">0</div>
<div class="rx">variantes uniques générées</div>
<div id="prev" style="display:none;margin:14px 0">
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
<div style="font-size:11px;color:var(--mut);font-weight:500">Preview avant / après</div>
<div style="display:flex;align-items:center;gap:6px">
<button onclick="prevNav(-1)" class="pbtn" style="padding:4px 10px;font-size:13px">←</button>
<span id="prev-idx" style="font-size:10px;color:var(--mut);min-width:40px;text-align:center">1/1</span>
<button onclick="prevNav(1)" class="pbtn" style="padding:4px 10px;font-size:13px">→</button>
</div>
</div>
<div style="display:flex;gap:8px">
<div style="flex:1;min-width:0"><div style="font-size:9px;color:var(--mut);margin-bottom:4px">ORIGINAL</div><div id="prev-orig" style="border-radius:8px;overflow:hidden;background:var(--s2);display:flex;align-items:center;justify-content:center"></div></div>
<div style="flex:1;min-width:0">
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px">
<div style="font-size:9px;color:var(--mut)">MODIFIÉ</div>
<div style="display:flex;align-items:center;gap:4px">
<button onclick="varNav(-1)" class="pbtn" style="padding:1px 6px;font-size:10px;line-height:1">‹</button>
<span id="var-idx" style="font-size:9px;color:var(--mut)">1/1</span>
<button onclick="varNav(1)" class="pbtn" style="padding:1px 6px;font-size:10px;line-height:1">›</button>
</div>
</div>
<div id="prev-mod" style="border-radius:8px;overflow:hidden;background:var(--s2);display:flex;align-items:center;justify-content:center"></div>
</div>
</div>
</div>
<button class="btn b-out" onclick="op()">Ouvrir le dossier de sortie</button>
<button class="btn b-zip" id="zb" style="display:none" onclick="oz()">Télécharger le ZIP</button>
</div>
</div><!-- /tab0 -->

<!-- TAB 1: Instagram Scraper -->
<div class="sc" id="t1">
<div class="c">
<div class="sl">Instagram Scraper</div>
<div class="fl"><label>Clé API RapidAPI</label><input type="password" id="skey" placeholder="Colle ta clé ici — elle reste en local">
<div class="hint">Ta clé <code>X-RapidAPI-Key</code> pour Instagram Scraper Stable API</div></div>
<div class="fl"><label>Username(s) Instagram</label><textarea id="suser" placeholder="@model1&#10;@model2&#10;@model3&#10;(1 par ligne ou séparés par virgule)" style="font-size:11px;height:60px;resize:vertical"></textarea>
<div class="hint">Un ou plusieurs usernames — 1 par ligne ou séparés par virgule</div></div>
<div class="rw">
<div class="fl"><label>Max posts</label><input type="number" id="smax" value="50" min="1" max="500"></div>
<div class="fl"><label>Dossier de sortie</label><input type="text" id="sout" placeholder="Auto: Downloads/zychad_scrape"></div>
</div>
<div style="margin:12px 0;display:flex;align-items:center;gap:8px">
<input type="checkbox" id="sskip" checked style="width:16px;height:16px;accent-color:var(--teal)">
<label for="sskip" style="font-size:12px;color:var(--dim);cursor:pointer">Ignorer les reels <span style="color:var(--mut);font-size:10px">(garder photos + carrousels)</span></label>
</div>
<div class="rw" style="margin:8px 0">
<div class="fl"><label>Période</label><select id="speriod" style="width:100%;background:var(--s2);border:1px solid var(--br);border-radius:8px;padding:10px;color:var(--txt);font-family:inherit;font-size:13px">
<option value="0">Tous</option><option value="7">7 derniers jours</option><option value="14">14 derniers jours</option><option value="30">30 derniers jours</option><option value="90">90 derniers jours</option>
</select></div>
<div class="fl"><label>Min likes</label><input type="number" id="sminlikes" value="0" min="0" placeholder="0 = pas de filtre"></div>
</div>
</div>
<button class="btn b-main" id="ssb" onclick="goScrape()">Scraper le profil</button>
<div class="sc-prog" id="sprog">
<div class="sc-bar"><div class="sc-fill" id="sfill"></div></div>
<div class="sc-num" id="snum">0/0</div>
</div>
<div class="sc-log" id="slog"></div>
<div class="sc-done" id="sdone">
<span id="sdmsg"></span>
<button class="btn b-out" style="margin-top:8px" onclick="useScrapeFolder()">Utiliser ce dossier dans l'Uniquifier →</button>
</div>
</div><!-- /tab1 -->

<!-- TAB 2: TikTok Scraper -->
<div class="sc" id="t2">
<div class="c">
<div class="sl">TikTok Scraper</div>
<div class="fl"><label>Clé API RapidAPI</label><input type="password" id="ttkey" placeholder="Clé pour TikTok Scrapper API">
<div class="hint">Ta clé <code>X-RapidAPI-Key</code> pour TikTok Scrapper Videos Music Challenges</div></div>
<div class="fl"><label>Username(s) TikTok</label><textarea id="ttuser" placeholder="@user1&#10;@user2&#10;(1 par ligne ou séparés par virgule)" style="font-size:11px;height:60px;resize:vertical"></textarea></div>
<div class="rw">
<div class="fl"><label>Max vidéos</label><input type="number" id="ttmax" value="50" min="1" max="500"></div>
<div class="fl"><label>Dossier de sortie</label><input type="text" id="ttout" placeholder="Auto: Downloads/zychad_scrape"></div>
</div>
</div>
<button class="btn b-main" id="ttsb" onclick="goTT()">Scraper le profil TikTok</button>
<div class="sc-prog" id="ttprog">
<div class="sc-bar"><div class="sc-fill" id="ttfill"></div></div>
<div class="sc-num" id="ttnum">0/0</div>
</div>
<div class="sc-log" id="ttlog"></div>
<div class="sc-done" id="ttdone">
<span id="ttdmsg"></span>
<button class="btn b-out" style="margin-top:8px" onclick="useTTFolder()">Utiliser ce dossier dans l'Uniquifier →</button>
</div>
</div><!-- /tab2 -->

<!-- TAB 3: Scheduler -->
<div class="sc" id="t3">
<div class="c">
<div class="sl">Programmer un scrape automatique</div>
<div class="rw">
<div class="fl"><label>Plateforme</label><select id="sch-plat" style="width:100%;background:var(--s2);border:1px solid var(--br);border-radius:8px;padding:10px;color:var(--txt);font-family:inherit;font-size:13px">
<option value="ig">Instagram</option><option value="tt">TikTok</option>
</select></div>
<div class="fl"><label>Username</label><input type="text" id="sch-user" placeholder="@username"></div>
</div>
<div class="rw">
<div class="fl"><label>Intervalle</label>
<div style="display:flex;gap:6px">
<input type="number" id="sch-val" value="24" min="1" max="720" style="flex:1">
<select id="sch-unit" style="width:90px;background:var(--s2);border:1px solid var(--br);border-radius:8px;padding:10px;color:var(--txt);font-family:inherit;font-size:13px">
<option value="h">heures</option><option value="d">jours</option>
</select>
</div></div>
<div class="fl"><label>Max posts</label><input type="number" id="sch-max" value="50" min="1" max="500"></div>
</div>
<div style="margin:8px 0;display:flex;align-items:center;gap:8px">
<input type="checkbox" id="sch-skip" checked style="width:16px;height:16px;accent-color:var(--teal)">
<label for="sch-skip" style="font-size:12px;color:var(--dim);cursor:pointer">Ignorer les reels (IG uniquement)</label>
</div>
<div class="hint" style="margin-bottom:12px">La clé API est récupérée automatiquement depuis tes paramètres sauvegardés</div>
</div>
<button class="btn b-main" onclick="addSchJob()">Ajouter au scheduler</button>
<div class="c" style="margin-top:14px">
<div class="sl">Jobs programmés</div>
<div id="sch-list" style="font-size:12px;color:var(--dim)">Aucun job programmé</div>
</div>
</div><!-- /tab3 -->

<!-- TAB 4: Dashboard -->
<div class="sc" id="t4">
<div class="c">
<div class="sl">Statistiques</div>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px">
<div style="text-align:center;padding:16px;background:var(--s2);border-radius:10px;border:1px solid var(--br)">
<div id="st-variants" style="font-family:'Sora',sans-serif;font-size:28px;font-weight:800;color:var(--teal3)">0</div>
<div style="font-size:10px;color:var(--mut)">Variantes créées</div>
</div>
<div style="text-align:center;padding:16px;background:var(--s2);border-radius:10px;border:1px solid var(--br)">
<div id="st-scrapes" style="font-family:'Sora',sans-serif;font-size:28px;font-weight:800;color:var(--teal3)">0</div>
<div style="font-size:10px;color:var(--mut)">Scrapes lancés</div>
</div>
<div style="text-align:center;padding:16px;background:var(--s2);border-radius:10px;border:1px solid var(--br)">
<div id="st-jobs" style="font-family:'Sora',sans-serif;font-size:28px;font-weight:800;color:var(--teal3)">0</div>
<div style="font-size:10px;color:var(--mut)">Jobs actifs</div>
</div>
</div>
</div>
<div class="c">
<div class="sl">Historique récent</div>
<div id="st-history" style="font-size:11px;color:var(--dim);max-height:300px;overflow-y:auto">Aucune activité</div>
</div>
</div><!-- /tab4 -->

<!-- TAB 5: Detector -->
<div class="sc" id="t5">
<div class="c">
<div class="sl">Similarity Checker</div>
<div style="font-size:12px;color:var(--dim);margin-bottom:14px">Compare 2 fichiers (original vs variante) pour mesurer le % de similarité. Plus le score est bas, mieux le contenu est uniquifié.</div>
<div style="display:flex;gap:12px">
<div style="flex:1;min-width:0">
<div style="font-size:10px;color:var(--mut);font-weight:600;margin-bottom:6px;text-align:center">FICHIER 1 (Original)</div>
<div id="sim-drop1" style="border:2px dashed var(--br);border-radius:10px;padding:20px 8px;text-align:center;cursor:pointer;transition:all .2s;min-height:70px;display:flex;align-items:center;justify-content:center;flex-direction:column;overflow:hidden"
ondragover="event.preventDefault();this.style.borderColor='var(--teal)'"
ondragleave="this.style.borderColor='var(--br)'"
ondrop="event.preventDefault();this.style.borderColor='var(--br)';simDrop(event,1)"
onclick="simPick(1)">
<div style="font-size:22px;margin-bottom:4px">📂</div>
<div style="font-size:11px;color:var(--mut)">Glisse ou clique</div>
<div id="sim-name1" style="font-size:9px;color:var(--teal3);margin-top:4px;display:none;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;padding:0 4px"></div>
</div>
</div>
<div style="flex:1;min-width:0">
<div style="font-size:10px;color:var(--mut);font-weight:600;margin-bottom:6px;text-align:center">FICHIER 2 (Variante)</div>
<div id="sim-drop2" style="border:2px dashed var(--br);border-radius:10px;padding:20px 8px;text-align:center;cursor:pointer;transition:all .2s;min-height:70px;display:flex;align-items:center;justify-content:center;flex-direction:column;overflow:hidden"
ondragover="event.preventDefault();this.style.borderColor='var(--teal)'"
ondragleave="this.style.borderColor='var(--br)'"
ondrop="event.preventDefault();this.style.borderColor='var(--br)';simDrop(event,2)"
onclick="simPick(2)">
<div style="font-size:22px;margin-bottom:4px">📂</div>
<div style="font-size:11px;color:var(--mut)">Glisse ou clique</div>
<div id="sim-name2" style="font-size:9px;color:var(--teal3);margin-top:4px;display:none;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;padding:0 4px"></div>
</div>
</div>
</div>
<button class="btn b-main" style="margin-top:14px" id="sim-btn" onclick="simCheck()">Analyser la similarité</button>
</div>

<div class="c" id="sim-result" style="display:none">
<div class="sl">Résultat de détection</div>
<div style="text-align:center;padding:10px 0">
<div id="sim-score" style="font-family:'Sora',sans-serif;font-size:52px;font-weight:800"></div>
<div style="font-size:11px;color:var(--mut);margin-top:2px">similarité (dHash 512-bit)</div>
</div>
<div id="sim-bar" style="height:8px;border-radius:4px;background:var(--s3);margin:10px 0;overflow:hidden">
<div id="sim-fill" style="height:100%;border-radius:4px;width:0%;transition:width .8s ease"></div>
</div>
<div style="display:flex;justify-content:space-between;font-size:9px;color:var(--mut)">
<span>0% — Totalement différent</span>
<span>100% — Identique</span>
</div>

<!-- Platform verdicts removed — we don't know real thresholds -->
</div>

<div class="c">
<div class="sl">Batch Similarity</div>
<div style="font-size:12px;color:var(--dim);margin-bottom:10px">Compare un original vs TOUTES les variantes d'un dossier.</div>
<div class="rw">
<div class="fl"><label>Fichier original</label><input type="text" id="bsim-orig" placeholder="/chemin/vers/original.mp4"></div>
<div class="fl"><label>Dossier variantes</label><input type="text" id="bsim-dir" placeholder="/chemin/vers/dossier_variantes"></div>
</div>
<button class="btn b-main" style="margin-top:8px" onclick="batchSim()">Analyser le batch</button>
<div id="bsim-result" style="display:none;margin-top:12px">
<div id="bsim-avg" style="font-size:18px;font-weight:700;text-align:center;margin:8px 0"></div>
<div id="bsim-table" style="max-height:200px;overflow-y:auto;font-size:11px"></div>
</div>
</div>

<div class="c">
<div class="sl">Invisible Watermark (LSB)</div>
<div style="font-size:12px;color:var(--dim);margin-bottom:10px">Injecte un ID invisible dans les pixels d'une image (PNG). Permet de tracker les leaks.</div>
<div class="rw">
<div class="fl"><label>Image (PNG)</label><input type="text" id="wm-img" placeholder="/chemin/vers/image.png"></div>
<div class="fl"><label>Message à encoder</label><input type="text" id="wm-msg" placeholder="ID unique ou texte"></div>
</div>
<div style="display:flex;gap:6px;margin-top:8px">
<button class="btn b-main" style="flex:1" onclick="wmEmbed()">Encoder watermark</button>
<button class="pbtn" style="flex:1" onclick="wmRead()">Lire watermark</button>
</div>
<div id="wm-result" style="display:none;margin-top:8px;font-size:12px;padding:8px;border-radius:6px;background:var(--s3)"></div>
</div>
</div><!-- /tab5 -->

<!-- TAB 6: API -->
<div class="sc" id="t6">
<div class="c">
<div class="sl">Clé API</div>
<div style="display:flex;gap:6px;align-items:center">
<input type="text" id="api-key-display" readonly style="flex:1;font-family:monospace;font-size:12px;background:var(--bg);cursor:pointer" onclick="this.select();document.execCommand('copy')">
<button class="pbtn" onclick="copyApiKey()">Copier</button>
<button class="pbtn" style="color:var(--red)" onclick="regenApiKey()">Régénérer</button>
</div>
<div class="hint" style="margin-top:6px">Cette clé protège ton API. Envoie-la dans le header <code>X-API-Key</code></div>
</div>

<div class="c">
<div class="sl">Mode réseau</div>
<div style="font-size:12px;color:var(--dim);line-height:1.8">
Par défaut, ZyChad Meta écoute uniquement en local (<code>127.0.0.1</code>).<br>
Pour ouvrir l'accès réseau (LAN, VPS, VAs à distance) :<br>
<code style="display:block;background:var(--bg);padding:8px 12px;border-radius:6px;margin:6px 0;color:var(--teal3)">python3 zychad_meta.py --network</code>
L'API sera alors accessible depuis n'importe quelle IP sur le réseau.
</div>
</div>

<div class="c">
<div class="sl">Endpoints</div>
<div style="font-size:11px;line-height:2.2;color:var(--dim)">

<div style="font-weight:600;color:var(--teal2);margin:8px 0 4px">GET /ext/status</div>
<div style="color:var(--mut);font-size:10px;margin-bottom:2px">État de tous les processus en cours</div>
<code style="display:block;background:var(--bg);padding:6px 10px;border-radius:6px;font-size:10px;color:var(--teal3);overflow-x:auto">curl -H "X-API-Key: VOTRE_CLE" http://HOST:PORT/ext/status</code>

<div style="font-weight:600;color:var(--teal2);margin:12px 0 4px">GET /ext/stats</div>
<div style="color:var(--mut);font-size:10px;margin-bottom:2px">Statistiques globales (variantes, scrapes, historique)</div>
<code style="display:block;background:var(--bg);padding:6px 10px;border-radius:6px;font-size:10px;color:var(--teal3);overflow-x:auto">curl -H "X-API-Key: VOTRE_CLE" http://HOST:PORT/ext/stats</code>

<div style="font-weight:600;color:var(--teal2);margin:12px 0 4px">POST /ext/scrape</div>
<div style="color:var(--mut);font-size:10px;margin-bottom:2px">Lancer un scrape IG ou TikTok</div>
<code style="display:block;background:var(--bg);padding:6px 10px;border-radius:6px;font-size:10px;color:var(--teal3);overflow-x:auto;white-space:pre">curl -X POST -H "X-API-Key: VOTRE_CLE" -H "Content-Type: application/json" \
  -d '{"platform":"ig","username":"model_name","max_posts":50}' \
  http://HOST:PORT/ext/scrape</code>
<div style="color:var(--mut);font-size:10px;margin-top:3px">Params: <code>platform</code> (ig/tt), <code>username</code>, <code>max_posts</code>, <code>skip_reels</code> (bool), <code>api_key</code> (optionnel, sinon utilise la clé sauvegardée)</div>

<div style="font-weight:600;color:var(--teal2);margin:12px 0 4px">POST /ext/process</div>
<div style="color:var(--mut);font-size:10px;margin-bottom:2px">Lancer l'uniquification d'un dossier</div>
<code style="display:block;background:var(--bg);padding:6px 10px;border-radius:6px;font-size:10px;color:var(--teal3);overflow-x:auto;white-space:pre">curl -X POST -H "X-API-Key: VOTRE_CLE" -H "Content-Type: application/json" \
  -d '{"input_dir":"/path/to/files","variants":50,"workers":4,"rename":true}' \
  http://HOST:PORT/ext/process</code>
<div style="color:var(--mut);font-size:10px;margin-top:3px">Params: <code>input_dir</code>, <code>output_dir</code> (opt), <code>variants</code>, <code>workers</code>, <code>rename</code> (bool)</div>

<div style="font-weight:600;color:var(--teal2);margin:12px 0 4px">GET /ext/download/{filename}</div>
<div style="color:var(--mut);font-size:10px;margin-bottom:2px">Télécharger un ZIP depuis le dossier output</div>
<code style="display:block;background:var(--bg);padding:6px 10px;border-radius:6px;font-size:10px;color:var(--teal3);overflow-x:auto">curl -H "X-API-Key: VOTRE_CLE" -o output.zip http://HOST:PORT/ext/download/zychad_3f_50v_20260210.zip</code>

</div>
</div>

<div class="c">
<div class="sl">Bot Telegram intégré</div>
<div id="tg-status-bar" style="padding:8px 12px;border-radius:6px;font-size:11px;margin-bottom:12px;display:none"></div>
<div style="font-size:12px;color:var(--dim);line-height:1.8;margin-bottom:12px">
Connecte ton bot Telegram pour que tes VAs puissent envoyer des fichiers et recevoir les variantes directement dans Telegram.
</div>

<div style="background:var(--s2);border-radius:8px;padding:14px;margin-bottom:12px">
<div style="font-size:11px;color:var(--teal2);font-weight:600;margin-bottom:8px">Setup en 3 étapes :</div>
<div style="font-size:11px;color:var(--dim);line-height:2">
1. Ouvre Telegram → cherche <code>@BotFather</code> → <code>/newbot</code><br>
2. Donne un nom (ex: ZyChad Uniquifier) → copie le token<br>
3. Colle le token ci-dessous et clique Connecter
</div>
</div>

<div class="fl"><label>Bot Token</label><input type="password" id="tg-token" placeholder="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11">
</div>
<div class="rw">
<div class="fl"><label>Variantes par défaut</label><input type="number" id="tg-nv" value="5" min="1" max="50"></div>
<div class="fl"><label>Max variantes</label><input type="number" id="tg-mx" value="50" min="1" max="200"></div>
</div>
<div class="fl"><label>IDs autorisés <span style="color:var(--mut);font-weight:400">(vide = tout le monde)</span></label>
<input type="text" id="tg-auth" placeholder="123456789, 987654321">
<div class="hint">IDs Telegram séparés par des virgules. Les VAs peuvent taper <code>/id</code> dans le bot pour connaître leur ID.</div>
</div>

<div style="display:flex;gap:8px;margin-top:12px">
<button class="btn b-main" style="flex:1" id="tg-conn-btn" onclick="tgConnect()">Connecter le bot</button>
<button class="pbtn" style="padding:13px 20px;color:var(--red)" id="tg-disc-btn" onclick="tgDisconnect()" disabled>Déconnecter</button>
</div>

<div style="background:var(--s2);border-radius:8px;padding:14px;margin-top:14px">
<div style="font-size:11px;color:var(--teal2);font-weight:600;margin-bottom:6px">Commandes VA :</div>
<div style="font-size:11px;color:var(--dim);line-height:2">
<code>/start</code> — Accueil<br>
<code>/variants 10</code> — Changer le nombre de variantes<br>
<code>/id</code> — Voir son Telegram ID<br>
Ou envoyer directement une vidéo/image → reçoit les variantes
</div>
</div>
</div>

<div class="c">
<div class="sl">Bot Discord</div>
<div id="dc-status-bar" style="padding:8px 12px;border-radius:6px;font-size:11px;margin-bottom:12px;display:none"></div>
<div style="font-size:12px;color:var(--dim);line-height:1.8;margin-bottom:12px">
Même fonctionnalité que Telegram mais pour Discord. Les utilisateurs envoient des fichiers et reçoivent les variantes.
</div>
<div style="background:var(--s2);border-radius:8px;padding:14px;margin-bottom:12px">
<div style="font-size:11px;color:var(--teal2);font-weight:600;margin-bottom:8px">Setup :</div>
<div style="font-size:11px;color:var(--dim);line-height:2">
1. Discord Developer Portal → New Application → Bot → Copy Token<br>
2. Invite le bot dans ton serveur avec les permissions Send Messages + Attach Files<br>
3. Colle le token ci-dessous
</div>
</div>
<div class="fl"><label>Bot Token Discord</label><input type="password" id="dc-token" placeholder="MTIz..."></div>
<div class="fl"><label>Channels autorisés <span style="color:var(--mut);font-weight:400">(vide = tous)</span></label>
<input type="text" id="dc-auth" placeholder="Channel IDs séparés par virgules">
</div>
<div style="display:flex;gap:8px;margin-top:12px">
<button class="btn b-main" style="flex:1" onclick="dcConnect()">Connecter le bot Discord</button>
</div>
<div style="background:var(--s2);border-radius:8px;padding:14px;margin-top:14px">
<div style="font-size:11px;color:var(--teal2);font-weight:600;margin-bottom:6px">Commandes :</div>
<div style="font-size:11px;color:var(--dim);line-height:2">
<code>/variants 10</code> — Changer le nombre de variantes<br>
<code>/stats</code> — Voir les statistiques<br>
Ou envoyer un fichier → reçoit les variantes
</div>
</div>
</div>
</div><!-- /tab6 -->

<script>
let poll,spoll;

/* Tabs */
function stab(n){
  document.querySelectorAll('.tab').forEach((t,i)=>t.classList.toggle('on',i===n));
  document.querySelectorAll('.sc').forEach((s,i)=>s.classList.toggle('on',i===n));
}

/* Config auto-load/save */
async function loadCfg(){
  try{
    const c=await(await fetch('/api/config')).json();
    if(c.ig_key) document.getElementById('skey').value=c.ig_key;
    if(c.tt_key) document.getElementById('ttkey').value=c.tt_key;
    if(c.variants) document.getElementById('nv').value=c.variants;
    if(c.workers) document.getElementById('nw').value=c.workers;
    if(c.gdrive_folder_id) document.getElementById('gd-folder-id').value=c.gdrive_folder_id;
    if(c.tg_dest_chat_id) document.getElementById('tg-chat-id').value=c.tg_dest_chat_id;
    if(c.tg_dest_topic_id) document.getElementById('tg-topic-id').value=c.tg_dest_topic_id;
  }catch(e){}
}
function saveCfg(){
  const d={ig_key:document.getElementById('skey').value,tt_key:document.getElementById('ttkey').value,variants:document.getElementById('nv').value,workers:document.getElementById('nw').value,gdrive_folder_id:document.getElementById('gd-folder-id').value,tg_dest_chat_id:document.getElementById('tg-chat-id').value,tg_dest_topic_id:document.getElementById('tg-topic-id').value};
  fetch('/api/save-config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});
}
// Auto-save when API key fields lose focus
document.addEventListener('DOMContentLoaded',()=>{
  ['skey','ttkey','nv','nw','gd-folder-id','tg-chat-id','tg-topic-id'].forEach(id=>{
    const el=document.getElementById(id);
    if(el) el.addEventListener('blur',saveCfg);
  });
});

/* Presets — custom, saved in config */
async function loadPresets(){
  try{
    const c=await(await fetch('/api/config')).json();
    const bar=document.getElementById('presetBar');
    // Clear existing preset buttons (keep the + button)
    bar.querySelectorAll('.preset-btn').forEach(b=>b.remove());
    const presets=c.presets||{};
    const addBtn=bar.querySelector('button');
    Object.keys(presets).forEach(name=>{
      const p=presets[name];
      const b=document.createElement('button');b.className='pbtn preset-btn';
      b.textContent=name;
      b.onclick=()=>{
        document.getElementById('nv').value=p.v||10;
        document.getElementById('nw').value=p.w||4;
        document.getElementById('rn').checked=!!p.r;
        saveCfg();
      };
      b.oncontextmenu=(e)=>{e.preventDefault();if(confirm('Supprimer le préset "'+name+'" ?')){deletePreset(name)}};
      bar.insertBefore(b,addBtn);
    });
  }catch(e){}
}
function savePreset(){
  const name=prompt('Nom du préset :');
  if(!name) return;
  const p={v:parseInt(document.getElementById('nv').value)||10,w:parseInt(document.getElementById('nw').value)||4,r:document.getElementById('rn').checked};
  fetch('/api/config').then(r=>r.json()).then(c=>{
    if(!c.presets) c.presets={};
    c.presets[name]=p;
    fetch('/api/save-config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({presets:c.presets})}).then(()=>loadPresets());
  });
}
function deletePreset(name){
  fetch('/api/config').then(r=>r.json()).then(c=>{
    if(c.presets) delete c.presets[name];
    fetch('/api/save-config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({presets:c.presets||{}})}).then(()=>loadPresets());
  });
}

/* Preview carousel — 2 levels: files (← →) and variants (‹ ›) */
let prevGroups=[];let fileIdx=0;let varIdx=0;

function showPreview(d){
  if(!d.preview||!d.preview.length) return;
  prevGroups=d.preview; fileIdx=0; varIdx=0;
  document.getElementById('prev').style.display='block';
  renderPreview();
}

function renderPreview(){
  const g=prevGroups[fileIdx];
  const fname=g.variants[varIdx];
  const origC=document.getElementById('prev-orig');
  const modC=document.getElementById('prev-mod');
  const isVid=fname.endsWith('.mp4');
  const origName=g.orig;
  if(isVid){
    origC.innerHTML='<video src="/api/original/'+origName+'" style="width:100%;border-radius:6px" controls muted></video>';
    modC.innerHTML='<video src="/api/preview/'+fname+'" style="width:100%;border-radius:6px" controls muted></video>';
  }else{
    origC.innerHTML='<img src="/api/original/'+origName+'" style="width:100%;border-radius:6px">';
    modC.innerHTML='<img src="/api/preview/'+fname+'" style="width:100%;border-radius:6px">';
  }
  document.getElementById('prev-idx').textContent=(fileIdx+1)+'/'+prevGroups.length;
  document.getElementById('var-idx').textContent=(varIdx+1)+'/'+g.variants.length;
}

/* ← → change file (both sides update) */
function prevNav(dir){
  if(!prevGroups.length) return;
  fileIdx=(fileIdx+dir+prevGroups.length)%prevGroups.length;
  varIdx=0;
  renderPreview();
}

/* ‹ › change variant (only right side updates) */
function varNav(dir){
  if(!prevGroups.length) return;
  const g=prevGroups[fileIdx];
  varIdx=(varIdx+dir+g.variants.length)%g.variants.length;
  // Only update right side
  const fname=g.variants[varIdx];
  const modC=document.getElementById('prev-mod');
  const isVid=fname.endsWith('.mp4');
  if(isVid){
    modC.innerHTML='<video src="/api/preview/'+fname+'" style="width:100%;border-radius:6px" controls muted></video>';
  }else{
    modC.innerHTML='<img src="/api/preview/'+fname+'" style="width:100%;border-radius:6px">';
  }
  document.getElementById('var-idx').textContent=(varIdx+1)+'/'+prevGroups[fileIdx].variants.length;
}

/* Folder picker */
async function pickFolder(targetId){
  const r=await(await fetch('/api/pick-folder')).json();
  if(r.folder) document.getElementById(targetId).value=r.folder;
  else alert('En mode web, utilise le glisser-d\u00e9poser des fichiers dans la zone ci-dessus.');
}

/* Drag & Drop files — batch with preview */
let droppedFiles=[];
async function handleDrop(e){
  e.preventDefault();
  const dz=document.getElementById('dropzone');
  dz.style.borderColor='var(--teal)';dz.style.background='rgba(14,165,199,.05)';
  const files=e.dataTransfer.files;
  if(!files.length) return;
  droppedFiles=Array.from(files);
  showDroppedFiles();
  document.getElementById('dz-text').style.display='none';
  const ok=document.getElementById('dz-ok');ok.style.display='block';ok.textContent='Envoi de '+files.length+' fichiers...';
  // Clear temp folder first
  await fetch('/api/upload-clear',{method:'POST'});
  let sent=0;
  for(const f of droppedFiles){
    await fetch('/api/upload-file',{method:'POST',headers:{'X-Filename':encodeURIComponent(f.name),'Content-Length':f.size},body:f});
    sent++;ok.textContent=sent+'/'+droppedFiles.length+' fichiers envoyés...';
    updateDroppedFileStatus(f.name,'ok');
  }
  const r=await(await fetch('/api/upload-done')).json();
  document.getElementById('idir').value=r.folder;
  ok.textContent='✅ '+droppedFiles.length+' fichiers prêts';
  dz.style.borderColor='var(--grn)';
  setTimeout(()=>{dz.style.borderColor='var(--br)';dz.style.background='none'},2000);
}
function showDroppedFiles(){
  const fl=document.getElementById('dz-filelist');
  if(!droppedFiles.length){fl.style.display='none';return}
  fl.style.display='block';
  const vidExts=['.mp4','.mov','.avi','.mkv','.webm'];
  const imgExts=['.jpg','.jpeg','.png','.webp','.gif','.bmp'];
  let totalSize=0;let vids=0;let imgs=0;
  droppedFiles.forEach(f=>{
    totalSize+=f.size;
    const ext='.'+f.name.split('.').pop().toLowerCase();
    if(vidExts.includes(ext))vids++;else if(imgExts.includes(ext))imgs++;
  });
  const sizeMB=(totalSize/1024/1024).toFixed(1);
  let html='<div style="padding:8px 10px;border-bottom:1px solid var(--br);display:flex;justify-content:space-between;align-items:center"><span style="font-size:10px;font-weight:600;color:var(--teal3)">'+droppedFiles.length+' fichiers · '+sizeMB+' MB</span>';
  html+='<span style="font-size:9px;color:var(--dim)">';
  if(vids)html+='🎬 '+vids+' vidéos ';
  if(imgs)html+='📸 '+imgs+' images';
  html+='</span></div>';
  droppedFiles.forEach((f,i)=>{
    const ext='.'+f.name.split('.').pop().toLowerCase();
    const icon=vidExts.includes(ext)?'🎬':'📸';
    const sz=(f.size/1024/1024).toFixed(1);
    html+='<div id="df-'+i+'" style="display:flex;align-items:center;gap:6px;padding:4px 10px;font-size:10px;border-bottom:1px solid rgba(20,51,69,0.3)">';
    html+='<span>'+icon+'</span>';
    html+='<span style="flex:1;color:var(--dim);overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="'+f.name+'">'+f.name+'</span>';
    html+='<span style="color:var(--mut);font-size:9px">'+sz+' MB</span>';
    html+='<span class="df-st" style="font-size:9px;color:var(--mut)">⏳</span>';
    html+='</div>';
  });
  fl.innerHTML=html;
}
function updateDroppedFileStatus(name,st){
  const idx=droppedFiles.findIndex(f=>f.name===name);
  if(idx<0)return;
  const el=document.querySelector('#df-'+idx+' .df-st');
  if(el){el.textContent=st==='ok'?'✅':'❌';el.style.color=st==='ok'?'var(--grn)':'var(--red)'}
}

/* Notification sounds */
let soundEnabled=true;
function playSound(type){
  if(!soundEnabled)return;
  try{
    const ctx=new(window.AudioContext||window.webkitAudioContext)();
    const osc=ctx.createOscillator();const g=ctx.createGain();
    osc.connect(g);g.connect(ctx.destination);
    if(type==='ok'){osc.frequency.value=880;g.gain.value=0.15;osc.start();osc.stop(ctx.currentTime+0.15)}
    else{osc.frequency.value=220;osc.type='square';g.gain.value=0.1;osc.start();osc.stop(ctx.currentTime+0.3)}
  }catch(e){}
}

/* Desktop Notifications */
function initNotifications(){
  if('Notification' in window && Notification.permission==='default'){
    Notification.requestPermission();
  }
}
function notifyDesktop(title,body){
  if(!('Notification' in window)) return;
  if(Notification.permission!=='granted') return;
  if(document.hasFocus()) return; // Don't notify if tab is focused
  try{
    const n=new Notification('⚡ ZyChad Meta — '+title,{
      body:body,
      icon:'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect fill="%230c222e" rx="20" width="100" height="100"/><text x="50" y="65" font-size="50" text-anchor="middle" fill="%2322d3ee">⚡</text></svg>',
      silent:false,
      tag:'zychad-proc'
    });
    n.onclick=function(){window.focus();n.close()};
    setTimeout(()=>n.close(),8000);
  }catch(e){}
}
initNotifications();

/* Uniquifier */
async function ck(){const r=await(await fetch('/api/status')).json();if(!r.ffmpeg){document.getElementById('fw').style.display='block';document.getElementById('fs').innerHTML=r.fi.steps.map(s=>'<p>'+s+'</p>').join('')}}
async function go(){const b=document.getElementById('sb');b.disabled=true;b.innerHTML='<span class="sp"></span>Traitement en cours...';
document.getElementById('pc').classList.add('on');document.getElementById('rc').classList.remove('on');document.getElementById('pl').innerHTML='';
document.getElementById('proc-controls').classList.remove('hide');
document.getElementById('preview-zone').style.display='none';
document.getElementById('pause-btn').innerHTML='⏸ Pause';
document.getElementById('eta-display').textContent='';
const d={input_dir:document.getElementById('idir').value,output_dir:document.getElementById('odir').value,variants:parseInt(document.getElementById('nv').value)||10,workers:parseInt(document.getElementById('nw').value)||4,rename:document.getElementById('rn').checked,double_process:document.getElementById('dbl').checked,stealth:document.getElementById('stealth').checked,naming_template:document.getElementById('ntpl')?document.getElementById('ntpl').value.trim():'',dest:destMode,gdrive_folder_id:document.getElementById('gd-folder-id')?document.getElementById('gd-folder-id').value.trim():'',tg_chat_id:document.getElementById('tg-chat-id')?document.getElementById('tg-chat-id').value.trim():'',tg_topic_id:document.getElementById('tg-topic-id')?document.getElementById('tg-topic-id').value.trim():''};
await fetch('/api/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});poll=setInterval(pp,400)}

async function pp(){const d=await(await fetch('/api/progress')).json();
const p=d.total>0?(d.progress/d.total*100):0;document.getElementById('pf').style.width=p+'%';
document.getElementById('ps').textContent=d.progress+' / '+d.total;document.getElementById('pt').textContent=d.file||'Traitement...';
if(d.eta)document.getElementById('eta-display').textContent=d.eta+' restantes';
// Queue display
if(d.queue&&d.queue.length>0){
  const ql=document.getElementById('queue-list');
  ql.innerHTML=d.queue.map((q,i)=>{
    const icons={waiting:'⏳',processing:'⚡',done:'✅',error:'❌',cancelled:'🛑'};
    const colors={waiting:'var(--mut)',processing:'var(--teal)',done:'var(--grn)',error:'var(--red)',cancelled:'var(--mut)'};
    return '<div style="display:flex;align-items:center;gap:6px;padding:3px 0;font-size:10px"><span>'+icons[q.status]+'</span><span style="color:'+colors[q.status]+';flex:1">'+q.name+'</span><span style="color:var(--mut)">'+q.type+'</span></div>';
  }).join('');
}
const l=document.getElementById('pl');l.innerHTML=d.log.map(e=>{const c=e.l==='ok'?'lo':e.l==='error'?'le':'li';return'<div><span class="lt">['+e.t+']</span><span class="'+c+'">'+e.m+'</span></div>'}).join('');l.scrollTop=l.scrollHeight;
if(d.done){clearInterval(poll);const b=document.getElementById('sb');b.disabled=false;b.innerHTML='Lancer le traitement';
document.getElementById('proc-controls').classList.add('hide');
document.getElementById('rc').classList.add('on');document.getElementById('rn2').textContent=d.results.length;
if(d.zip){document.getElementById('zb').style.display=destMode==='local'?'block':'none'}
if(d.gdrive_uploading||d.gdrive_done){gdPollUpload()}
if(d.tg_uploading||d.tg_done){tgPollUpload()}
if(d.preview&&d.preview.length>0){showPreview(d)}
playSound(d.cancelled?'err':'ok');
notifyDesktop(d.cancelled?'Traitement annulé':'Traitement terminé !',d.cancelled?'Le traitement a été annulé.':d.results.length+' variantes générées avec succès.');
saveCfg();}}

/* Pause / Cancel */
async function togglePause(){
  const r=await(await fetch('/api/pause')).json();
  document.getElementById('pause-btn').innerHTML=r.paused?'▶ Reprendre':'⏸ Pause';
  document.getElementById('pt').textContent=r.paused?'⏸ En pause...':document.getElementById('pt').textContent;
}
async function cancelJob(){
  if(!confirm('Annuler le traitement en cours ?'))return;
  await fetch('/api/cancel');
}

/* Preview */
async function genPreview(){
  const idir=document.getElementById('idir').value;
  if(!idir){alert('Sélectionne un dossier source d\'abord');return}
  document.getElementById('preview-btn').disabled=true;
  document.getElementById('preview-btn').innerHTML='⏳...';
  try{
    const r=await(await fetch('/api/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({input_dir:idir})})).json();
    if(r.error){alert(r.error);return}
    const pz=document.getElementById('preview-zone');pz.style.display='block';
    const orig=document.getElementById('pv-orig');const vari=document.getElementById('pv-var');
    if(r.type==='image'){
      orig.innerHTML='<img src="/api/file?p='+encodeURIComponent(r.original)+'" style="max-width:100%;max-height:200px">';
      vari.innerHTML='<img src="/api/file?p='+encodeURIComponent(r.variant)+'" style="max-width:100%;max-height:200px">';
    }else{
      orig.innerHTML='<video src="/api/file?p='+encodeURIComponent(r.original)+'" controls style="max-width:100%;max-height:200px"></video>';
      vari.innerHTML='<video src="/api/file?p='+encodeURIComponent(r.variant)+'" controls style="max-width:100%;max-height:200px"></video>';
    }
  }catch(e){alert('Erreur preview: '+e)}
  finally{document.getElementById('preview-btn').disabled=false;document.getElementById('preview-btn').innerHTML='👁 Preview'}
}
function op(){window.location.href='/api/download-zip'}
function oz(){window.location.href='/api/download-zip'}

/* Destination toggle */
let destMode='local';
function destToggle(mode){
  destMode=mode;
  document.getElementById('dest-local').style.display=mode==='local'?'block':'none';
  document.getElementById('dest-drive').style.display=mode==='drive'?'block':'none';
  document.getElementById('dest-telegram').style.display=mode==='telegram'?'block':'none';
  ['local','drive','tg'].forEach(k=>{
    const btn=document.getElementById('dest-'+k+'-btn');
    if(btn){btn.style.background=mode===(k==='tg'?'telegram':k)?'var(--teal)':'';btn.style.color=mode===(k==='tg'?'telegram':k)?'#000':'';}
  });
}

/* Google Drive */
let gdOAuthToken='';
function gdConnect(){
  const cid='1022698347622-n7l9vuj29ri8rn0ipridjdtuo078t52c.apps.googleusercontent.com';
  const redirect=window.location.origin+'/oauth-callback';
  const scope='https://www.googleapis.com/auth/drive.file';
  const url='https://accounts.google.com/o/oauth2/v2/auth?client_id='+encodeURIComponent(cid)+'&redirect_uri='+encodeURIComponent(redirect)+'&response_type=token&scope='+encodeURIComponent(scope)+'&prompt=consent';
  window.open(url,'gdrive_oauth','width=500,height=600');
  window.addEventListener('message',function handler(e){
    if(e.data&&e.data.access_token){
      gdOAuthToken=e.data.access_token;
      document.getElementById('gd-not-connected').style.display='none';
      document.getElementById('gd-connected').style.display='block';
      // Get user email
      fetch('https://www.googleapis.com/oauth2/v1/userinfo?access_token='+gdOAuthToken).then(r=>r.json()).then(d=>{
        if(d.email) document.getElementById('gd-user-email').textContent='✅ '+d.email;
      }).catch(()=>{});
      // Save token to backend
      fetch('/api/gdrive-token',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:gdOAuthToken})});
      window.removeEventListener('message',handler);
    }
  });
}
function gdPollUpload(){
  document.getElementById('gd-progress').style.display='block';
  document.getElementById('gd-status').textContent='Upload vers Drive...';
  document.getElementById('gd-fill').style.width='0%';
  const gi=setInterval(async()=>{
    const d=await(await fetch('/api/gdrive-progress')).json();
    const p=d.total>0?(d.progress/d.total*100):0;
    document.getElementById('gd-fill').style.width=p+'%';
    document.getElementById('gd-status').textContent=d.error?'❌ '+d.error:d.done?'✅ '+d.files_uploaded+' fichiers uploadés sur Drive !':d.progress+'/'+d.total+' fichiers...';
    if(d.done||d.error)clearInterval(gi);
  },500);
}
function tgPollUpload(){
  document.getElementById('tg-progress').style.display='block';
  document.getElementById('tg-status').textContent='Envoi sur Telegram...';
  document.getElementById('tg-fill').style.width='0%';
  const gi=setInterval(async()=>{
    const d=await(await fetch('/api/tg-send-progress')).json();
    const p=d.total>0?(d.progress/d.total*100):0;
    document.getElementById('tg-fill').style.width=p+'%';
    document.getElementById('tg-status').textContent=d.error?'❌ '+d.error:d.done?'✅ '+d.files_sent+' fichiers envoyés sur Telegram !':d.progress+'/'+d.total+' fichiers...';
    if(d.done||d.error)clearInterval(gi);
  },500);
}

/* Scraper */
async function goScrape(){
  const b=document.getElementById('ssb');const key=document.getElementById('skey').value.trim();
  const user=document.getElementById('suser').value.trim();
  if(!key||!user){alert('Remplis la clé API et le username');return}
  b.disabled=true;b.innerHTML='<span class="sp"></span>Scraping...';
  document.getElementById('sprog').classList.add('on');
  document.getElementById('slog').classList.add('on');document.getElementById('slog').innerHTML='';
  document.getElementById('sdone').classList.remove('on');
  const d={api_key:key,username:user,max_posts:parseInt(document.getElementById('smax').value)||50,skip_reels:document.getElementById('sskip').checked,output_base:document.getElementById('sout').value.trim(),days_filter:parseInt(document.getElementById('speriod').value)||0,min_likes:parseInt(document.getElementById('sminlikes').value)||0};
  await fetch('/api/scrape',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});
  spoll=setInterval(spp,500);
}
async function spp(){
  const d=await(await fetch('/api/scrape-progress')).json();
  const p=d.total>0?(d.downloaded/d.total*100):0;
  document.getElementById('sfill').style.width=p+'%';
  document.getElementById('snum').textContent=d.downloaded+'/'+d.total;
  const l=document.getElementById('slog');
  l.innerHTML=d.log.map(e=>{const c=e.l==='ok'?'lo':e.l==='error'?'le':'li';return'<div><span class="lt">['+e.t+']</span><span class="'+c+'">'+e.m+'</span></div>'}).join('');
  l.scrollTop=l.scrollHeight;
  if(d.done){clearInterval(spoll);
    const b=document.getElementById('ssb');b.disabled=false;b.innerHTML='Scraper le profil';
    if(d.folder){document.getElementById('sdone').classList.add('on');
      document.getElementById('sdmsg').textContent='✅ '+d.downloaded+' images dans '+d.folder;
      window._scrapeFolder=d.folder;
    }
    notifyDesktop('Scrape IG terminé',d.downloaded+' fichiers téléchargés');
  }
}
function useScrapeFolder(){
  if(window._scrapeFolder){
    document.getElementById('idir').value=window._scrapeFolder;
    document.getElementById('rn').checked=true;
    stab(0);
  }
}

/* TikTok Scraper */
let ttpoll;
async function goTT(){
  const b=document.getElementById('ttsb');const key=document.getElementById('ttkey').value.trim();
  const user=document.getElementById('ttuser').value.trim();
  if(!key||!user){alert('Remplis la clé API et le username');return}
  b.disabled=true;b.innerHTML='<span class="sp"></span>Scraping TikTok...';
  document.getElementById('ttprog').classList.add('on');
  document.getElementById('ttlog').classList.add('on');document.getElementById('ttlog').innerHTML='';
  document.getElementById('ttdone').classList.remove('on');
  const d={api_key:key,username:user,max_videos:parseInt(document.getElementById('ttmax').value)||50,output_base:document.getElementById('ttout').value.trim()};
  await fetch('/api/tt-scrape',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});
  ttpoll=setInterval(ttpp,500);
}
async function ttpp(){
  const d=await(await fetch('/api/tt-progress')).json();
  const p=d.total>0?(d.downloaded/d.total*100):0;
  document.getElementById('ttfill').style.width=p+'%';
  document.getElementById('ttnum').textContent=d.downloaded+'/'+d.total;
  const l=document.getElementById('ttlog');
  l.innerHTML=d.log.map(e=>{const c=e.l==='ok'?'lo':e.l==='error'?'le':'li';return'<div><span class="lt">['+e.t+']</span><span class="'+c+'">'+e.m+'</span></div>'}).join('');
  l.scrollTop=l.scrollHeight;
  if(d.done){clearInterval(ttpoll);
    const b=document.getElementById('ttsb');b.disabled=false;b.innerHTML='Scraper le profil TikTok';
    if(d.folder){document.getElementById('ttdone').classList.add('on');
      document.getElementById('ttdmsg').textContent='✅ '+d.downloaded+' vidéos dans '+d.folder;
      window._ttFolder=d.folder;
    }
    notifyDesktop('Scrape TikTok terminé',d.downloaded+' vidéos téléchargées');
  }
}
function useTTFolder(){
  if(window._ttFolder){
    document.getElementById('idir').value=window._ttFolder;
    document.getElementById('rn').checked=false;
    stab(0);
  }
}

/* Scheduler */
async function addSchJob(){
  const plat=document.getElementById('sch-plat').value;
  const user=document.getElementById('sch-user').value.trim();
  if(!user){alert('Remplis le username');return}
  const val=parseInt(document.getElementById('sch-val').value)||24;
  const unit=document.getElementById('sch-unit').value;
  const hours=unit==='d'?val*24:val;
  const cfg=await(await fetch('/api/config')).json();
  const key=plat==='ig'?cfg.ig_key:cfg.tt_key;
  if(!key){alert('Sauvegarde d\'abord ta clé API '+plat.toUpperCase()+' dans l\'onglet scraper');return}
  const job={platform:plat,username:user.replace('@',''),api_key:key,interval_h:hours,max_posts:parseInt(document.getElementById('sch-max').value)||50,skip_reels:document.getElementById('sch-skip').checked};
  await fetch('/api/scheduler-add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(job)});
  document.getElementById('sch-user').value='';
  loadScheduler();
}
async function loadScheduler(){
  const d=await(await fetch('/api/scheduler')).json();
  const el=document.getElementById('sch-list');
  if(!d.jobs||!d.jobs.length){el.innerHTML='Aucun job programmé';return}
  el.innerHTML=d.jobs.map(j=>{
    const intv=j.interval_h>=24?(j.interval_h/24)+'j':j.interval_h+'h';
    const plat=j.platform==='ig'?'📸 IG':'🎵 TT';
    const status=j.active?'<span class="sj-status sj-on">Actif</span>':'<span class="sj-status sj-off">Pause</span>';
    const lr=j.last_run?new Date(j.last_run).toLocaleString('fr-FR',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'}):'Jamais';
    const nr=j.next_run&&j.active?new Date(j.next_run).toLocaleString('fr-FR',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'}):'-';
    return '<div class="sj"><div class="sj-info"><div class="sj-name">'+plat+' @'+j.username+' — toutes les '+intv+'</div><div class="sj-detail">Dernier: '+lr+' · Prochain: '+nr+' · Max: '+j.max_posts+'</div></div><div class="sj-actions">'+status+'<button class="pbtn" style="padding:4px 8px;font-size:10px" onclick="toggleSch(\''+j.id+'\')">'+(j.active?'⏸':'▶')+'</button><button class="pbtn" style="padding:4px 8px;font-size:10px;color:var(--red)" onclick="removeSch(\''+j.id+'\')">✕</button></div></div>';
  }).join('');
}
async function toggleSch(id){
  await fetch('/api/scheduler-toggle',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});
  loadScheduler();loadDash();
}
async function removeSch(id){
  if(!confirm('Supprimer ce job ?')) return;
  await fetch('/api/scheduler-remove',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});
  loadScheduler();loadDash();
}

/* Dashboard */
async function loadDash(){
  try{
    const s=await(await fetch('/api/stats')).json();
    const sc=await(await fetch('/api/scheduler')).json();
    document.getElementById('st-variants').textContent=s.total_variants||0;
    document.getElementById('st-scrapes').textContent=s.total_scrapes||0;
    document.getElementById('st-jobs').textContent=(sc.jobs||[]).filter(j=>j.active).length;
    const hel=document.getElementById('st-history');
    if(!s.history||!s.history.length){hel.innerHTML='Aucune activité';return}
    hel.innerHTML=s.history.slice().reverse().slice(0,50).map(h=>{
      const dt=new Date(h.t).toLocaleString('fr-FR',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'});
      const cls=h.type==='scrape'?'ht-scrape':'ht-variants';
      const label=h.type==='scrape'?'SCRAPE':'PROCESS';
      return '<div class="hist-row"><span class="hist-time">'+dt+'</span><span class="hist-type '+cls+'">'+label+'</span><span>'+h.d+'</span></div>';
    }).join('');
  }catch(e){}
}

/* Similarity Checker */
let simFiles={1:null,2:null};
function simPick(slot){
  const inp=document.createElement('input');inp.type='file';inp.accept='video/*,image/*';
  inp.onchange=()=>{if(inp.files[0]) simUpload(inp.files[0],slot)};
  inp.click();
}
function simDrop(e,slot){
  if(e.dataTransfer.files.length) simUpload(e.dataTransfer.files[0],slot);
}
async function simUpload(f,slot){
  const el=document.getElementById('sim-name'+slot);
  const short=f.name.length>35?f.name.substring(0,32)+'...':f.name;
  el.style.display='block';el.textContent='⏳ '+short;
  await fetch('/api/sim-upload',{method:'POST',headers:{'X-Filename':encodeURIComponent(f.name),'X-Slot':slot,'Content-Length':f.size},body:f});
  simFiles[slot]=f.name;
  el.textContent='✅ '+short;
  document.getElementById('sim-drop'+slot).style.borderColor='var(--grn)';
}
async function simCheck(){
  if(!simFiles[1]||!simFiles[2]){alert('Uploade 2 fichiers');return}
  const btn=document.getElementById('sim-btn');btn.disabled=true;btn.innerHTML='<span class="sp"></span>Analyse...';
  document.getElementById('sim-result').style.display='none';
  const r=await(await fetch('/api/sim-check',{method:'POST'})).json();
  if(r.error){alert(r.error);btn.disabled=false;btn.textContent='Analyser la similarité';return}
  // Poll for result
  const poll=setInterval(async()=>{
    const s=await(await fetch('/api/sim-status')).json();
    if(!s.active&&s.result){
      clearInterval(poll);
      btn.disabled=false;btn.textContent='Analyser la similarité';
      showSimResult(s.result);
    }
  },500);
}
function showSimResult(r){
  if(r.error){alert('Erreur: '+r.error);return}
  const res=document.getElementById('sim-result');res.style.display='block';
  const score=r.mssim||r.combined||0;
  document.getElementById('sim-score').textContent=score+'%';
  // Color bar
  let color;
  if(score>80) color='var(--red)';
  else if(score>60) color='#f59e0b';
  else color='var(--grn)';
  document.getElementById('sim-score').style.color=color;
  document.getElementById('sim-fill').style.width=score+'%';
  document.getElementById('sim-fill').style.background=color;
}
async function batchSim(){
  const orig=document.getElementById('bsim-orig').value.trim();
  const vdir=document.getElementById('bsim-dir').value.trim();
  if(!orig||!vdir){alert('Remplis les 2 champs');return}
  const r=await(await fetch('/api/sim-batch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({original:orig,variants_dir:vdir})})).json();
  if(r.error){alert(r.error);return}
  const poll=setInterval(async()=>{
    const s=await(await fetch('/api/sim-status')).json();
    if(!s.active&&s.result){
      clearInterval(poll);
      const d=s.result;
      if(d.error){alert(d.error);return}
      document.getElementById('bsim-result').style.display='block';
      const ac=d.average>80?'var(--red)':d.average>60?'#f59e0b':'var(--grn)';
      document.getElementById('bsim-avg').innerHTML='Score moyen : <span style="color:'+ac+'">'+d.average+'%</span> ('+d.total+' fichiers'+(d.warnings>0?', <span style="color:var(--red)">'+d.warnings+' warnings</span>':'')+')';
      let h='<table style="width:100%;border-collapse:collapse"><tr style="color:var(--teal2);font-size:10px"><th style="text-align:left;padding:4px">Fichier</th><th style="text-align:right;padding:4px">Score</th><th style="text-align:center;padding:4px">Status</th></tr>';
      d.results.forEach(r=>{
        const c=r.score>80?'var(--red)':r.score>60?'#f59e0b':'var(--grn)';
        const st=r.status=='warning'?'⚠️':r.status=='error'?'❌':'✅';
        h+='<tr style="border-top:1px solid var(--br)"><td style="padding:4px;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+r.file+'</td><td style="text-align:right;padding:4px;color:'+c+';font-weight:700">'+r.score+'%</td><td style="text-align:center;padding:4px">'+st+'</td></tr>';
      });
      h+='</table>';
      document.getElementById('bsim-table').innerHTML=h;
    }
  },600);
}

/* Telegram Bot */
async function loadTgStatus(){
  try{
    const r=await(await fetch('/api/tg-status')).json();
    const bar=document.getElementById('tg-status-bar');
    const cfg=await(await fetch('/api/config')).json();
    if(cfg.tg_bot_token) document.getElementById('tg-token').value=cfg.tg_bot_token;
    if(cfg.tg_variants) document.getElementById('tg-nv').value=cfg.tg_variants;
    if(cfg.tg_max_variants) document.getElementById('tg-mx').value=cfg.tg_max_variants;
    if(cfg.tg_authorized&&cfg.tg_authorized.length) document.getElementById('tg-auth').value=cfg.tg_authorized.join(', ');
    if(r.active){
      bar.style.display='block';bar.style.background='rgba(52,211,153,.08)';bar.style.border='1px solid rgba(52,211,153,.2)';bar.style.color='var(--grn)';
      bar.textContent='🟢 Bot actif — @'+r.username;
      document.getElementById('tg-conn-btn').textContent='Reconnecter';
      document.getElementById('tg-disc-btn').disabled=false;
    }else if(r.error){
      bar.style.display='block';bar.style.background='rgba(248,113,113,.08)';bar.style.border='1px solid rgba(248,113,113,.2)';bar.style.color='var(--red)';
      bar.textContent='🔴 Erreur: '+r.error;
      document.getElementById('tg-disc-btn').disabled=true;
    }else{
      bar.style.display='none';
      document.getElementById('tg-disc-btn').disabled=true;
    }
  }catch(e){}
}
async function tgConnect(){
  const token=document.getElementById('tg-token').value.trim();
  if(!token){alert('Colle ton bot token');return}
  const nv=parseInt(document.getElementById('tg-nv').value)||5;
  const mx=parseInt(document.getElementById('tg-mx').value)||50;
  const authStr=document.getElementById('tg-auth').value.trim();
  const auth=authStr?authStr.split(',').map(s=>parseInt(s.trim())).filter(n=>!isNaN(n)):[];
  const btn=document.getElementById('tg-conn-btn');btn.disabled=true;btn.innerHTML='<span class="sp"></span>Connexion...';
  const r=await(await fetch('/api/tg-connect',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token,variants:nv,max_variants:mx,authorized:auth})})).json();
  btn.disabled=false;btn.innerHTML='Reconnecter';
  loadTgStatus();
}
async function tgDisconnect(){
  if(!confirm('Déconnecter le bot Telegram ?')) return;
  await fetch('/api/tg-disconnect',{method:'POST'});
  document.getElementById('tg-disc-btn').disabled=true;
  loadTgStatus();
}

/* API key */
async function loadApiKey(){
  try{const r=await(await fetch('/api/api-key')).json();document.getElementById('api-key-display').value=r.key||''}catch(e){}
}
function copyApiKey(){
  const el=document.getElementById('api-key-display');el.select();document.execCommand('copy');
  el.style.borderColor='var(--grn)';setTimeout(()=>el.style.borderColor='var(--br)',1000);
}
async function regenApiKey(){
  if(!confirm('Régénérer la clé API ? L\'ancienne ne fonctionnera plus.')) return;
  const r=await(await fetch('/api/api-key-regen')).json();
  document.getElementById('api-key-display').value=r.key||'';
}

ck();loadCfg();loadPresets();loadScheduler();loadDash();loadApiKey();loadTgStatus();
fetch('/api/tg-bot-status').then(r=>r.json()).then(d=>{if(d.username&&document.getElementById('tg-bot-name'))document.getElementById('tg-bot-name').textContent='@'+d.username;}).catch(()=>{});
document.getElementById('stealth').addEventListener('change',function(){if(this.checked){document.getElementById('dbl').checked=true}});
// ═══ Keyboard shortcuts ═══
document.addEventListener('keydown',function(e){
  // Ctrl+Enter: Launch process
  if(e.ctrlKey&&e.key==='Enter'){e.preventDefault();go();return}
  // Escape: Cancel job
  if(e.key==='Escape'&&state_active){e.preventDefault();cancelJob();return}
  // Space: Pause/Resume (only when not typing in input)
  if(e.key===' '&&e.target.tagName!=='INPUT'&&e.target.tagName!=='TEXTAREA'&&state_active){e.preventDefault();togglePause();return}
  // ? : Show shortcuts help
  if(e.key==='?'&&e.target.tagName!=='INPUT'&&e.target.tagName!=='TEXTAREA'){
    e.preventDefault();
    alert('⌨ Raccourcis clavier:\\n\\nCtrl+Enter → Lancer le traitement\\nEscape → Annuler\\nEspace → Pause/Resume\\n? → Afficher les raccourcis');
  }
});
var state_active=false;
setInterval(()=>{state_active=document.getElementById('sb').disabled;},500);
async function wmEmbed(){
  const img=document.getElementById('wm-img').value.trim();
  const msg=document.getElementById('wm-msg').value.trim();
  if(!img||!msg){alert('Remplis image + message');return}
  const r=await(await fetch('/api/watermark-embed',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({image:img,message:msg})})).json();
  const d=document.getElementById('wm-result');d.style.display='block';
  if(r.ok) d.innerHTML='<span style="color:var(--grn)">✅ Watermark encodé !</span> '+r.bits+' bits dans '+r.file;
  else d.innerHTML='<span style="color:var(--red)">❌ '+r.e+'</span>';
}
async function wmRead(){
  const img=document.getElementById('wm-img').value.trim();
  if(!img){alert('Remplis le chemin image');return}
  const r=await(await fetch('/api/watermark-read',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({image:img})})).json();
  const d=document.getElementById('wm-result');d.style.display='block';
  if(r.ok) d.innerHTML='<span style="color:var(--teal2)">🔍 Message trouvé :</span> <code>'+r.message+'</code>';
  else d.innerHTML='<span style="color:var(--red)">❌ '+r.e+'</span>';
}
// ═══ Dark/Light theme ═══
function toggleTheme(){
  document.body.classList.toggle('light');
  const isLight=document.body.classList.contains('light');
  localStorage.setItem('zc-theme',isLight?'light':'dark');
  document.getElementById('theme-btn').textContent=isLight?'🌙':'☀️';
}
(function(){const t=localStorage.getItem('zc-theme');if(t==='light'){document.body.classList.add('light');document.getElementById('theme-btn').textContent='🌙';}})();
// ═══ i18n ═══
// ═══ Discord bot ═══
async function dcConnect(){
  const token=document.getElementById('dc-token').value.trim();
  const auth=document.getElementById('dc-auth').value.trim();
  if(!token){alert('Colle le token Discord');return}
  const channels=auth?auth.split(',').map(s=>s.trim()).filter(Boolean):[];
  await fetch('/api/save-config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({dc_bot_token:token,dc_authorized_channels:channels})});
  await fetch('/api/dc-start',{method:'POST'});
  const sb=document.getElementById('dc-status-bar');sb.style.display='block';sb.style.background='rgba(14,165,199,.1)';sb.style.color='var(--teal2)';sb.textContent='🎮 Connexion en cours...';
  setTimeout(async()=>{
    const r=await(await fetch('/api/dc-status')).json();
    if(r.active){sb.style.background='rgba(52,211,153,.1)';sb.style.color='var(--grn)';sb.textContent='✅ Bot Discord @'+r.username+' connecté';}
    else{sb.style.background='rgba(248,113,113,.1)';sb.style.color='var(--red)';sb.textContent='❌ '+(r.error||'Erreur de connexion');}
  },3000);
}
// ═══ i18n ═══
const TR={
fr:{},
en:{
  'Configuration':'Configuration','Dossier source':'Source Folder','Destination':'Destination',
  'Variantes / fichier':'Variants / file','Workers':'Workers',
  'Lancer le traitement':'Launch Processing','Uniquifier':'Uniquifier',
  'IG Scraper':'IG Scraper','TikTok Scraper':'TikTok Scraper',
  'Scheduler':'Scheduler','Dashboard':'Dashboard','Détecteur':'Detector',
  'Renommer les carrousels avant traitement':'Rename carousels before processing',
  'Double Process':'Double Process','Mode Stealth':'Stealth Mode',
  'Instagram Scraper':'Instagram Scraper','Clé API RapidAPI':'RapidAPI Key',
  'Max posts':'Max posts','Dossier de sortie':'Output folder',
  'Ignorer les reels':'Skip reels','Période':'Period','Min likes':'Min likes',
  'Scraper le profil':'Scrape profile','Scraper le profil TikTok':'Scrape TikTok profile',
  'Tous':'All','7 derniers jours':'Last 7 days','14 derniers jours':'Last 14 days',
  '30 derniers jours':'Last 30 days','90 derniers jours':'Last 90 days',
  'Programmer un scrape automatique':'Schedule automatic scrape',
  'Plateforme':'Platform','Username':'Username','Intervalle':'Interval',
  'Ajouter au scheduler':'Add to scheduler','Jobs programmés':'Scheduled Jobs',
  'Aucun job programmé':'No scheduled jobs','heures':'hours','jours':'days',
  'Ignorer les reels (IG uniquement)':'Skip reels (IG only)',
  'Statistiques':'Statistics','Fichiers traités':'Files processed',
  'Variantes générées':'Variants generated','Scrapes effectués':'Scrapes completed',
  'Historique récent':'Recent history',
  'Similarity Checker':'Similarity Checker','Batch Similarity':'Batch Similarity',
  'Invisible Watermark (LSB)':'Invisible Watermark (LSB)',
  'Analyser la similarité':'Analyze similarity','Analyser le batch':'Analyze batch',
  'Fichier original':'Original file','Dossier variantes':'Variants folder',
  'Image (PNG)':'Image (PNG)','Message à encoder':'Message to encode',
  'Encoder watermark':'Encode watermark','Lire watermark':'Read watermark',
  'FICHIER 1 (Original)':'FILE 1 (Original)','FICHIER 2 (Variante)':'FILE 2 (Variant)',
  'Glisse ou clique':'Drag or click',
  'Clé API':'API Key','Mode réseau':'Network Mode','Endpoints':'Endpoints',
  'Bot Telegram intégré':'Integrated Telegram Bot','Bot Discord':'Discord Bot',
  'Connecter le bot':'Connect bot','Déconnecter':'Disconnect',
  'Connecter le bot Discord':'Connect Discord bot',
  'Variantes par défaut':'Default variants','Max variantes':'Max variants',
  'Copier':'Copy','Régénérer':'Regenerate','Parcourir':'Browse',
  'Présets':'Presets','+ Sauvegarder':'+ Save',
  'Glisse tes fichiers ici ou clique pour parcourir':'Drag files here or click to browse',
  'Ou colle un chemin manuellement':'Or paste a path manually',
  'Auto-généré si vide':'Auto-generated if empty',
  'Colle ta clé ici — elle reste en local':'Paste your key here — stays local',
},
es:{
  'Configuration':'Configuración','Dossier source':'Carpeta fuente','Destination':'Destino',
  'Variantes / fichier':'Variantes / archivo','Workers':'Workers',
  'Lancer le traitement':'Iniciar procesamiento','Uniquifier':'Uniquifier',
  'Scheduler':'Programador','Dashboard':'Panel','Détecteur':'Detector',
  'Renommer les carrousels avant traitement':'Renombrar carruseles antes del proceso',
  'Double Process':'Doble Proceso','Mode Stealth':'Modo Stealth',
  'Instagram Scraper':'Instagram Scraper','Clé API RapidAPI':'Clave API RapidAPI',
  'Max posts':'Max posts','Dossier de sortie':'Carpeta de salida',
  'Ignorer les reels':'Ignorar reels','Période':'Período','Min likes':'Min likes',
  'Scraper le profil':'Scrapear perfil','Scraper le profil TikTok':'Scrapear perfil TikTok',
  'Tous':'Todos','7 derniers jours':'Últimos 7 días','14 derniers jours':'Últimos 14 días',
  '30 derniers jours':'Últimos 30 días','90 derniers jours':'Últimos 90 días',
  'Programmer un scrape automatique':'Programar scrape automático',
  'Plateforme':'Plataforma','Username':'Usuario','Intervalle':'Intervalo',
  'Ajouter au scheduler':'Agregar al programador','Jobs programmés':'Trabajos programados',
  'Aucun job programmé':'Ningún trabajo programado','heures':'horas','jours':'días',
  'Ignorer les reels (IG uniquement)':'Ignorar reels (solo IG)',
  'Statistiques':'Estadísticas','Fichiers traités':'Archivos procesados',
  'Variantes générées':'Variantes generadas','Scrapes effectués':'Scrapes realizados',
  'Historique récent':'Historial reciente',
  'Similarity Checker':'Verificador de Similitud','Batch Similarity':'Similitud por Lote',
  'Invisible Watermark (LSB)':'Marca de Agua Invisible (LSB)',
  'Analyser la similarité':'Analizar similitud','Analyser le batch':'Analizar lote',
  'Fichier original':'Archivo original','Dossier variantes':'Carpeta variantes',
  'Image (PNG)':'Imagen (PNG)','Message à encoder':'Mensaje a codificar',
  'Encoder watermark':'Codificar marca','Lire watermark':'Leer marca',
  'Clé API':'Clave API','Mode réseau':'Modo de red',
  'Bot Telegram intégré':'Bot Telegram integrado','Bot Discord':'Bot Discord',
  'Connecter le bot':'Conectar bot','Déconnecter':'Desconectar',
  'Connecter le bot Discord':'Conectar bot Discord',
  'Copier':'Copiar','Régénérer':'Regenerar','Parcourir':'Explorar',
  'Présets':'Presets','+ Sauvegarder':'+ Guardar',
  'Glisse tes fichiers ici ou clique pour parcourir':'Arrastra archivos aquí o haz clic',
  'Ou colle un chemin manuellement':'O pega una ruta manualmente',
  'Auto-généré si vide':'Auto-generado si vacío',
  'Colle ta clé ici — elle reste en local':'Pega tu clave aquí — se queda local',
}
};
function setLang(lang){
  localStorage.setItem('zc-lang',lang);
  if(lang==='fr'){location.reload();return;}
  const d=TR[lang]||{};
  // Walk all text-bearing elements
  const walk=el=>{
    el.childNodes.forEach(n=>{
      if(n.nodeType===3){const t=n.textContent.trim();if(d[t])n.textContent=n.textContent.replace(t,d[t]);}
      else if(n.nodeType===1&&!['SCRIPT','STYLE','CODE'].includes(n.tagName))walk(n);
    });
  };
  walk(document.body);
  // Placeholders
  document.querySelectorAll('[placeholder]').forEach(el=>{const p=el.placeholder;if(d[p])el.placeholder=d[p];});
}
(function(){const l=localStorage.getItem('zc-lang');if(l&&l!=='fr'){document.getElementById('lang-sel').value=l;setTimeout(()=>setLang(l),200);}})();
</script></body></html>"""

# ─── Server ───
class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def _set_saas_user(self):
        global saas_user_id
        uid=self.headers.get("X-User-Id")
        if uid: saas_user_id=uid
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Headers","Content-Type, X-API-Key, X-Filename")
        self.send_header("Access-Control-Allow-Methods","GET, POST, OPTIONS")
        self.end_headers()
    def do_GET(self):
        self._set_saas_user()
        path_only=self.path.split("?")[0]
        if path_only in["/","/index.html"]: self._html(HTML)
        elif self.path=="/manifest.json":
            m=json.dumps({"name":"ZyChad Meta","short_name":"ZyChad","start_url":"/","display":"standalone","background_color":"#0a0f1c","theme_color":"#0ea5c7","icons":[{"src":"/icon-192.png","sizes":"192x192","type":"image/png"}]})
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.end_headers()
            self.wfile.write(m.encode())
            return
        elif self.path=="/api/status": self._json({"ffmpeg":FFMPEG_PATH is not None,"fp":FFMPEG_PATH,"fi":ffmpeg_install_info()})
        elif self.path=="/api/progress":
            import re as _re
            # Group results by original file
            preview_groups={}  # orig_name -> [variant_filenames]
            for r in state.get("results",[]):
                orig=_re.sub(r'_v\d+\.','.',r["f"])
                if orig not in preview_groups: preview_groups[orig]=[]
                preview_groups[orig].append(r["f"])
            # Sort groups and variants
            preview_sorted=[{"orig":k,"variants":sorted(v)} for k,v in sorted(preview_groups.items())]
            self._json({"active":state["active"],"progress":state["progress"],"total":state["total"],"file":state["file"],"log":state["log"][-150:],"results":state["results"],"done":state["done"],"zip":state["zip"],"input":state.get("input",""),"preview":preview_sorted,"gdrive_uploading":gdrive_state.get("uploading",False),"gdrive_done":gdrive_state.get("done",False),"gdrive_error":gdrive_state.get("error",""),"tg_uploading":tg_send_state.get("uploading",False),"tg_done":tg_send_state.get("done",False),"tg_error":tg_send_state.get("error",""),"paused":state.get("paused",False),"cancelled":state.get("cancelled",False),"eta":state.get("eta",""),"queue":state.get("files_list",[])})
        elif self.path=="/api/scrape-progress": self._json({"active":scrape_state["active"],"done":scrape_state["done"],"downloaded":scrape_state["downloaded"],"total":scrape_state["total"],"folder":scrape_state["folder"],"log":scrape_state["log"][-50:]})
        elif self.path=="/api/tt-progress": self._json({"active":tt_state["active"],"done":tt_state["done"],"downloaded":tt_state["downloaded"],"total":tt_state["total"],"folder":tt_state["folder"],"log":tt_state["log"][-50:]})
        elif self.path=="/api/config": self._json(load_config())
        elif self.path=="/api/api-key": self._json({"key":get_api_key()})
        elif self.path=="/api/api-key-regen":
            key=generate_api_key(); save_config({"api_key":key}); self._json({"key":key})
        elif self.path=="/api/tg-status":
            self._json({"active":tg_bot_state["active"],"username":tg_bot_state["username"],"error":tg_bot_state["error"]})
        elif self.path=="/api/sim-status":
            self._json({"active":sim_state["active"],"result":sim_state["result"]})
        elif self.path=="/api/dc-status":
            self._json({"active":dc_bot_state["active"],"username":dc_bot_state["username"],"error":dc_bot_state["error"]})
        # ── External API (requires X-API-Key) ──
        elif self.path=="/ext/status":
            if not check_api_key(self.headers): self._json_err(401,"Invalid API key"); return
            self._json({"uniquifier":{"active":state["active"],"progress":state["progress"],"total":state["total"],"done":state["done"]},"ig_scraper":{"active":scrape_state["active"],"done":scrape_state["done"],"downloaded":scrape_state["downloaded"],"total":scrape_state["total"]},"tt_scraper":{"active":tt_state["active"],"done":tt_state["done"],"downloaded":tt_state["downloaded"],"total":tt_state["total"]},"scheduler":{"jobs":len(scheduler_jobs),"active":len([j for j in scheduler_jobs if j.get("active")])}})
        elif self.path=="/ext/stats":
            if not check_api_key(self.headers): self._json_err(401,"Invalid API key"); return
            self._json(load_stats())
        elif self.path=="/ext/queue-status":
            if not check_api_key(self.headers): self._json_err(401,"Invalid API key"); return
            with ext_queue_lock:
                q=[{"id":j["id"],"url":j["url"][:80],"platform":j["platform"],"status":j["status"],"filename":j.get("filename",""),"error":j.get("error",""),"output":j.get("output",""),"added_at":j["added_at"]} for j in ext_queue]
            cfg=load_config()
            dest=ext_queue_dest or cfg.get("ext_queue_dest","") or str(Path.home()/"Downloads"/"zychad_inbox")
            out_dir=cfg.get("ext_output_dir","") or str(Path(dest).parent/"zychad_output")
            self._json({"queue":q,"dest":dest,"output_dir":out_dir,"auto_uniquify":cfg.get("ext_auto_uniquify",True),"pending":len([j for j in q if j["status"]=="pending"]),"downloading":len([j for j in q if j["status"]=="downloading"]),"uniquifying":len([j for j in q if j["status"]=="uniquifying"]),"done":len([j for j in q if j["status"]=="done"]),"errors":len([j for j in q if j["status"]=="error"])})
        elif self.path.startswith("/ext/download/"):
            if not check_api_key(self.headers): self._json_err(401,"Invalid API key"); return
            fname=self.path[len("/ext/download/"):]
            # Search in output dir and zychad_output
            fp=None
            for d in [state.get("output",""),str(Path.home()/"Downloads"/"zychad_output")]:
                if d:
                    for root,_,files in os.walk(d):
                        if fname in files: fp=Path(root)/fname; break
                if fp: break
            if fp and fp.exists():
                ct="application/zip" if fp.suffix==".zip" else "application/octet-stream"
                self.send_response(200); self.send_header("Content-Type",ct); self.send_header("Content-Disposition",f"attachment; filename={fname}"); self.send_header("Content-Length",str(fp.stat().st_size)); self.end_headers()
                with open(fp,"rb") as f: self.wfile.write(f.read())
            else: self._json_err(404,"File not found")
        elif self.path=="/api/gdrive-progress":
            self._json(gdrive_state)
        elif self.path=="/api/tg-send-progress":
            self._json(tg_send_state)
        elif self.path=="/api/pause":
            state["paused"]=not state.get("paused",False)
            self._json({"paused":state["paused"]})
        elif self.path=="/api/cancel":
            state["cancelled"]=True; state["paused"]=False
            self._json({"cancelled":True})
        elif self.path.startswith("/api/file"):
            from urllib.parse import urlparse,parse_qs
            qs=parse_qs(urlparse(self.path).query)
            fp=qs.get("p",[""])[0]
            if not fp or not Path(fp).exists():
                self.send_response(404); self.end_headers(); return
            p=Path(fp)
            mime_map={".mp4":"video/mp4",".jpg":"image/jpeg",".jpeg":"image/jpeg",".png":"image/png",".webp":"image/webp"}
            ct=mime_map.get(p.suffix.lower(),"application/octet-stream")
            self.send_response(200); self.send_header("Content-Type",ct); self.send_header("Content-Length",str(p.stat().st_size)); self.end_headers()
            with open(p,"rb") as f: self.wfile.write(f.read())
        elif self.path.startswith("/oauth-callback"):
            html = """<!DOCTYPE html><html><body><script>
const hash=window.location.hash.substring(1);const params=new URLSearchParams(hash);
const token=params.get('access_token');
if(token&&window.opener){window.opener.postMessage({access_token:token},'*');document.body.innerHTML='<h2 style="font-family:sans-serif;text-align:center;margin-top:50px">✅ Connecté ! Tu peux fermer cette fenêtre.</h2>';setTimeout(()=>window.close(),1500)}
else{document.body.innerHTML='<h2 style="font-family:sans-serif;text-align:center;margin-top:50px">❌ Erreur</h2>'}
</script></body></html>"""
            self.send_response(200); self.send_header("Content-Type","text/html"); self.end_headers()
            self.wfile.write(html.encode())
        elif self.path=="/api/stats": self._json(load_stats())
        elif self.path=="/api/scheduler": self._json({"jobs":scheduler_jobs})
        elif self.path.startswith("/api/original/"):
            # Serve original input file for preview comparison
            fname=self.path[len("/api/original/"):]
            fp=None
            # Find in last used input dir
            b=json.loads(self.rfile.read(0)) if False else {}
            idir=state.get("input","")
            if idir:
                fp2=Path(idir)/fname
                if fp2.exists(): fp=fp2
            if fp and fp.exists():
                ct="video/mp4" if fp.suffix==".mp4" else "image/jpeg" if fp.suffix in[".jpg",".jpeg"] else "image/png"
                self.send_response(200); self.send_header("Content-Type",ct); self.send_header("Content-Length",str(fp.stat().st_size)); self.end_headers()
                with open(fp,"rb") as f: self.wfile.write(f.read())
            else: self.send_response(404); self.end_headers()
        elif self.path.startswith("/api/preview/"):
            # Serve a file from output dir for preview
            fname=self.path[len("/api/preview/"):]
            fp=None
            o=state.get("output","")
            if o:
                # Search recursively
                for root,_,files in os.walk(o):
                    if fname in files: fp=Path(root)/fname; break
            if fp and fp.exists():
                ct="video/mp4" if fp.suffix==".mp4" else "image/jpeg" if fp.suffix in[".jpg",".jpeg"] else "image/png"
                self.send_response(200); self.send_header("Content-Type",ct); self.send_header("Content-Length",str(fp.stat().st_size)); self.end_headers()
                with open(fp,"rb") as f: self.wfile.write(f.read())
            else: self.send_response(404); self.end_headers()
        elif self.path=="/api/pick-folder":
            folder=""
            try:
                import tkinter as tk
                from tkinter import filedialog
                root=tk.Tk(); root.withdraw(); root.attributes("-topmost",True)
                folder=filedialog.askdirectory(title="Sélectionne un dossier")
                root.destroy()
            except: pass
            self._json({"folder":folder})
        elif self.path.startswith("/api/upload-done"):
            # Return the temp upload folder path
            self._json({"folder":str(Path(tempfile.gettempdir())/"zychad_drop")})
        elif self.path=="/api/download-zip":
            z=state.get("zip")
            if z and Path(z).exists():
                zp=Path(z)
                self.send_response(200)
                self.send_header("Content-Type","application/zip")
                self.send_header("Content-Disposition",f'attachment; filename="{zp.name}"')
                self.send_header("Content-Length",str(zp.stat().st_size))
                self.end_headers()
                with open(zp,"rb") as f: self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.send_header("Content-Type","text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"<html><body style='font-family:sans-serif;padding:2rem;text-align:center'><h2>Aucun ZIP disponible</h2><p>Lance un traitement et attends la fin pour t&eacute;l&eacute;charger le ZIP.</p><a href='/'>Retour</a></body></html>")
        elif self.path=="/api/open-output":
            o=state.get("output","")
            if o and Path(o).exists():
                try:
                    if platform.system()=="Windows": os.startfile(o)
                    elif platform.system()=="Darwin": subprocess.run(["open",o])
                    else: subprocess.run(["xdg-open",o])
                except (FileNotFoundError, OSError): pass  # Headless/Docker: pas de gestionnaire de fichiers
            self._json({"ok":True})
        elif self.path=="/api/open-zip":
            z=state.get("zip")
            if z and Path(z).exists():
                try:
                    if platform.system()=="Windows": os.startfile(str(Path(z).parent))
                    elif platform.system()=="Darwin": subprocess.run(["open","-R",z])
                    else: subprocess.run(["xdg-open",str(Path(z).parent)])
                except (FileNotFoundError, OSError): pass  # Headless/Docker: pas de gestionnaire de fichiers
            self._json({"ok":True})
        else: self.send_response(404); self.end_headers()
    def do_POST(self):
        self._set_saas_user()
        if self.path=="/api/upload-file":
            # Receive a single file via multipart-like simple upload
            cl=int(self.headers.get("Content-Length",0))
            fname=urllib.parse.unquote(self.headers.get("X-Filename","file"))
            data=self.rfile.read(cl)
            drop_dir=Path(tempfile.gettempdir())/"zychad_drop"
            drop_dir.mkdir(parents=True,exist_ok=True)
            fp=drop_dir/fname
            with open(fp,"wb") as f: f.write(data)
            self._json({"ok":True,"path":str(fp)})
        elif self.path=="/api/upload-clear":
            # Clear temp drop folder for fresh drop
            drop_dir=Path(tempfile.gettempdir())/"zychad_drop"
            if drop_dir.exists(): shutil.rmtree(drop_dir)
            drop_dir.mkdir(parents=True,exist_ok=True)
            self._json({"ok":True})
        elif self.path=="/api/scrape":
            b=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
            if scrape_state["active"]: self._json({"error":"busy"}); return
            ak=b.get("api_key","").strip(); un=b.get("username","").strip(); mp=b.get("max_posts",50); sr=b.get("skip_reels",True)
            df=b.get("days_filter",0); ml=b.get("min_likes",0)
            if not ak or not un: self._json({"error":"missing fields"}); return
            ob=b.get("output_base","").strip() or str(Path.home()/"Downloads"/"zychad_scrape")
            # Multi-username: split by newline or comma
            usernames=[u.strip().lstrip("@") for u in un.replace(",","\n").split("\n") if u.strip()]
            if len(usernames)>1:
                def _multi_scrape():
                    for idx,user in enumerate(usernames):
                        if scrape_state.get("cancelled",False): break
                        scrape_log(f"━━━ [{idx+1}/{len(usernames)}] @{user} ━━━")
                        run_scrape(ak,user,mp,sr,ob,df,ml)
                    scrape_state["active"]=False; scrape_state["done"]=True
                threading.Thread(target=_multi_scrape,daemon=True).start()
            else:
                threading.Thread(target=run_scrape,args=(ak,usernames[0] if usernames else un,mp,sr,ob,df,ml),daemon=True).start()
            self._json({"ok":True})
        elif self.path=="/api/gdrive-token":
            b=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
            gdrive_token["access_token"]=b.get("token","")
            self._json({"ok":True})
        elif self.path=="/api/preview":
            b=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
            i=b.get("input_dir","")
            if not i: self._json({"error":"No input"}); return
            o=str(Path(i).parent/"_zychad_preview")
            r=run_preview(i,o)
            self._json(r)
        elif self.path=="/api/save-config":
            b=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
            save_config(b); self._json({"ok":True})
        elif self.path=="/api/scheduler-add":
            b=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
            jid=scheduler_add(b); self._json({"ok":True,"id":jid})
        elif self.path=="/api/scheduler-remove":
            b=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
            scheduler_remove(b.get("id","")); self._json({"ok":True})
        elif self.path=="/api/scheduler-toggle":
            b=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
            scheduler_toggle(b.get("id","")); self._json({"ok":True})
        elif self.path=="/api/tg-connect":
            b=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
            token=b.get("token","").strip(); nv=b.get("variants",5); mx=b.get("max_variants",50); auth=b.get("authorized",[])
            if not token: self._json({"error":"no token"}); return
            save_config({"tg_bot_token":token,"tg_variants":nv,"tg_max_variants":mx,"tg_authorized":auth})
            if tg_bot_state["active"]: tg_bot_stop(); time.sleep(1)
            tg_bot_start()
            time.sleep(2)
            self._json({"ok":True,"active":tg_bot_state["active"],"username":tg_bot_state["username"],"error":tg_bot_state["error"]})
        elif self.path=="/api/tg-disconnect":
            tg_bot_stop(); save_config({"tg_bot_token":""})
            self._json({"ok":True})
        elif self.path=="/api/dc-start":
            dc_bot_start()
            time.sleep(2)
            self._json({"ok":True,"active":dc_bot_state["active"],"username":dc_bot_state["username"],"error":dc_bot_state["error"]})
        elif self.path=="/api/sim-upload":
            cl=int(self.headers.get("Content-Length",0))
            slot=self.headers.get("X-Slot","1")  # "1" or "2"
            fname=urllib.parse.unquote(self.headers.get("X-Filename","file"))
            data=self.rfile.read(cl)
            sim_dir=Path(tempfile.gettempdir())/"zychad_sim"
            sim_dir.mkdir(parents=True,exist_ok=True)
            fp=sim_dir/f"file{slot}_{fname}"
            # Clean old file for this slot
            for old in sim_dir.glob(f"file{slot}_*"):
                try: old.unlink()
                except: pass
            with open(fp,"wb") as f: f.write(data)
            self._json({"ok":True,"path":str(fp),"slot":slot})
        elif self.path=="/api/sim-check":
            sim_dir=Path(tempfile.gettempdir())/"zychad_sim"
            f1=list(sim_dir.glob("file1_*")) if sim_dir.exists() else []
            f2=list(sim_dir.glob("file2_*")) if sim_dir.exists() else []
            if not f1 or not f2: self._json({"error":"Upload 2 fichiers d'abord"}); return
            if sim_state["active"]: self._json({"error":"Analyse en cours..."}); return
            threading.Thread(target=run_similarity,args=(str(f1[0]),str(f2[0])),daemon=True).start()
            self._json({"ok":True})
        elif self.path=="/api/sim-batch":
            b=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
            orig=b.get("original","").strip(); vdir=b.get("variants_dir","").strip()
            if not orig or not vdir: self._json({"error":"Need original + variants_dir"}); return
            if not Path(orig).exists(): self._json({"error":"Original not found"}); return
            if not Path(vdir).exists(): self._json({"error":"Variants dir not found"}); return
            def _batch():
                sim_state.update(active=True,result=None)
                try:
                    r=batch_compare(orig,vdir)
                    sim_state.update(active=False,result=r)
                except Exception as e:
                    sim_state.update(active=False,result={"error":str(e)})
            threading.Thread(target=_batch,daemon=True).start()
            self._json({"ok":True})
        elif self.path=="/api/watermark-embed":
            b=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
            img=b.get("image","").strip(); msg=b.get("message","").strip(); outp=b.get("output","")
            if not img or not msg: self._json({"error":"Need image + message"}); return
            r=lsb_embed(img,msg,outp if outp else None)
            self._json(r)
        elif self.path=="/api/watermark-read":
            b=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
            img=b.get("image","").strip()
            if not img: self._json({"error":"Need image path"}); return
            r=lsb_extract(img)
            self._json(r)
        elif self.path=="/api/tt-scrape":
            b=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
            if tt_state["active"]: self._json({"error":"busy"}); return
            ak=b.get("api_key","").strip(); un=b.get("username","").strip(); mv=b.get("max_videos",50)
            if not ak or not un: self._json({"error":"missing fields"}); return
            ob=b.get("output_base","").strip() or str(Path.home()/"Downloads"/"zychad_scrape")
            threading.Thread(target=run_tt_scrape,args=(ak,un,mv,ob),daemon=True).start()
            self._json({"ok":True})
        elif self.path=="/api/start":
            b=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
            if state["active"]: self._json({"error":"busy"}); return
            i=b.get("input_dir","").strip(); o=b.get("output_dir","").strip()
            if not i: self._json({"error":"no input"}); return
            if not Path(i).exists(): reset(); state["done"]=True; log(f"❌ Dossier introuvable: {i}","error"); self._json({"error":"not found"}); return
            if not o: o=str(Path(i).parent/"zychad_output")
            dest=b.get("dest","local")
            gfid=b.get("gdrive_folder_id","")
            tgcid=b.get("tg_chat_id","")
            tgtid=b.get("tg_topic_id","")
            dbl=b.get("double_process",False)
            sth=b.get("stealth",False)
            ntpl=b.get("naming_template","")
            threading.Thread(target=run_proc,args=(i,o,b.get("variants",10),b.get("workers",4),b.get("rename",False),dest,gfid,tgcid,tgtid,dbl,sth,ntpl),daemon=True).start()
            self._json({"ok":True,"output":o})
        # ── External API POST (requires X-API-Key) ──
        elif self.path=="/ext/scrape":
            if not check_api_key(self.headers): self._json_err(401,"Invalid API key"); return
            b=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
            plat=b.get("platform","ig"); un=b.get("username","").strip(); mp=b.get("max_posts",50)
            if not un: self._json_err(400,"Missing username"); return
            cfg=load_config(); ak=b.get("api_key") or (cfg.get("ig_key") if plat=="ig" else cfg.get("tt_key"))
            if not ak: self._json_err(400,"No API key configured for "+plat); return
            ob=b.get("output_base","").strip() or str(Path.home()/"Downloads"/"zychad_scrape")
            if plat=="ig":
                if scrape_state["active"]: self._json_err(409,"IG scraper busy"); return
                threading.Thread(target=run_scrape,args=(ak,un,mp,b.get("skip_reels",True),ob),daemon=True).start()
            elif plat=="tt":
                if tt_state["active"]: self._json_err(409,"TT scraper busy"); return
                threading.Thread(target=run_tt_scrape,args=(ak,un,mp,ob),daemon=True).start()
            else: self._json_err(400,"Invalid platform: use ig or tt"); return
            self._json({"ok":True,"platform":plat,"username":un})
        elif self.path=="/ext/process":
            if not check_api_key(self.headers): self._json_err(401,"Invalid API key"); return
            b=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
            if state["active"]: self._json_err(409,"Uniquifier busy"); return
            i=b.get("input_dir","").strip(); o=b.get("output_dir","").strip()
            if not i: self._json_err(400,"Missing input_dir"); return
            if not Path(i).exists(): self._json_err(404,"Directory not found: "+i); return
            if not o: o=str(Path(i).parent/"zychad_output")
            nv=b.get("variants",10); nw=b.get("workers",4); rn=b.get("rename",False)
            threading.Thread(target=run_proc,args=(i,o,nv,nw,rn),daemon=True).start()
            self._json({"ok":True,"output":o})
        elif self.path=="/ext/queue":
            if not check_api_key(self.headers): self._json_err(401,"Invalid API key"); return
            b=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
            url=b.get("url","").strip()
            if not url: self._json_err(400,"Missing url"); return
            # Set destination folder
            global ext_queue_dest
            if b.get("dest"): ext_queue_dest=b["dest"]
            platform=b.get("platform","auto")
            job_id=ext_queue_add(url, platform)
            # Process queue in background
            threading.Thread(target=ext_queue_process,daemon=True).start()
            self._json({"ok":True,"id":job_id,"queue_size":len(ext_queue)})
        elif self.path=="/ext/queue-clear":
            if not check_api_key(self.headers): self._json_err(401,"Invalid API key"); return
            with ext_queue_lock:
                ext_queue.clear()
            self._json({"ok":True})
        elif self.path=="/ext/upload":
            if not check_api_key(self.headers): self._json_err(401,"Invalid API key"); return
            cl=int(self.headers.get("Content-Length",0))
            ct=self.headers.get("Content-Type","")
            cfg=load_config()
            dest=ext_queue_dest or cfg.get("ext_queue_dest","") or str(Path.home()/"Downloads"/"zychad_inbox")
            Path(dest).mkdir(parents=True,exist_ok=True)
            raw=self.rfile.read(cl)
            fname=None; fdata=None
            if "multipart" in ct:
                boundary=None
                for p in ct.split(";"):
                    p=p.strip()
                    if p.startswith("boundary="): boundary=p[9:].strip().strip('"')
                if not boundary: self._json_err(400,"No boundary"); return
                sep=("--"+boundary).encode()
                parts=raw.split(sep)
                for part in parts:
                    if b"Content-Disposition" not in part: continue
                    try:
                        hdr_end=part.index(b"\r\n\r\n")
                        hdr_raw=part[:hdr_end].decode("utf-8","ignore")
                        body=part[hdr_end+4:]
                        if body.endswith(b"\r\n"): body=body[:-2]
                        for line in hdr_raw.split("\r\n"):
                            if "filename=" in line:
                                fs=line.index('filename="')+10
                                fe=line.index('"',fs)
                                fname=line[fs:fe]; fdata=body; break
                    except: pass
                    if fname: break
                if not fname or not fdata: self._json_err(400,"No file found"); return
            else:
                fname=urllib.parse.unquote(self.headers.get("X-Filename","upload_"+str(int(time.time()))))
                fdata=raw
            fp=Path(dest)/fname
            with open(fp,"wb") as f: f.write(fdata)
            self._json({"ok":True,"file":fname,"dest":dest})
        else: self.send_response(404); self.end_headers()
    def _json(self,d):
        self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers()
        self.wfile.write(json.dumps(d).encode())
    def _json_err(self,code,msg):
        self.send_response(code); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers()
        self.wfile.write(json.dumps({"error":msg}).encode())
    def _html(self,h):
        self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.end_headers()
        self.wfile.write(h.encode())

def main():
    global FFMPEG_PATH; FFMPEG_PATH=find_ffmpeg()
    load_scheduler()
    threading.Thread(target=scheduler_loop,daemon=True).start()
    # Auto-start Telegram bot if configured
    cfg_check=load_config()
    if cfg_check.get("tg_bot_token","").strip():
        print("  🤖 Démarrage du bot Telegram...")
        tg_bot_start()
    # Check for --network flag or Docker (PORT env) to listen on all interfaces
    network_mode="--network" in sys.argv or "-n" in sys.argv or bool(os.environ.get("PORT"))
    bind_addr="0.0.0.0" if network_mode else "127.0.0.1"
    api_key=get_api_key()
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  ZyChad Meta — Content Uniquifier                            ║
╠══════════════════════════════════════════════════════════════╣
║  FFmpeg: {'✅ ' + str(FFMPEG_PATH)[:45] if FFMPEG_PATH else '❌ Non trouvé — instructions dans le navigateur'}
║  GUI:    http://localhost:{PORT}
║  API:    http://{bind_addr}:{PORT}/ext/
║  Key:    {api_key}
║  Mode:   {'🌐 Réseau (0.0.0.0)' if network_mode else '🔒 Local (127.0.0.1) — ajoute --network pour LAN'}
╚══════════════════════════════════════════════════════════════╝
""")
    srv=HTTPServer((bind_addr,PORT),H)
    url=f"http://localhost:{PORT}"
    if not network_mode:
        threading.Timer(.5,lambda:webbrowser.open(url)).start()
        print(f"  🌐 Ouverture de {url}...\n  ⏹  Ctrl+C pour arrêter\n")
    else:
        print(f"  🌐 Serveur sur {bind_addr}:{PORT}\n  ⏹  Ctrl+C pour arrêter\n")
    try: srv.serve_forever()
    except KeyboardInterrupt: print("\n  👋 Bye"); srv.shutdown()

if __name__=="__main__": main()
