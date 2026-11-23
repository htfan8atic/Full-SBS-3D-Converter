#!/usr/bin/env python3
"""
Full SBS 3D Converter v1.0 - 3D MV-HEVC, Top/bottom or MVC Formats to FSBS Converter
By ht2tweak and Claude AI.

Converts 3D video to Full Side-by-Side (FSBS) .mkv using ffmpeg (and FRIM for Blu-ray 3D MVC).
Input  : MV-HEVC (Apple spatial / Vision Pro / Dolby Vision 3D), Half/Full SBS, Half/Full Top-Bottom,
         H.264 MVC (Blu-ray 3D, via FRIM)
Output : 3840x1080 FSBS (1920x1080 per eye) and/or 7680x2160 FSBS (3840x2160 per eye),
         Matroska tagged stereo_mode=left_right; optional HDR / Dolby Vision -> SDR tone mapping.

GUI : python fsbs_converter.py
CLI : python fsbs_converter.py --cli INPUT [INPUT...] --size 3840 [--size 7680] ...
"""

import glob
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from tkinter.scrolledtext import ScrolledText
except ImportError:  # CLI still works without tkinter
    tk = None

APP_NAME = "Full SBS 3D Converter"
APP_VERSION = "1.0"
IS_WIN = os.name == "nt"
NO_WINDOW = 0x08000000 if IS_WIN else 0  # CREATE_NO_WINDOW
EXE = ".exe" if IS_WIN else ""
SCRIPT_DIR = os.path.dirname(os.path.abspath(sys.argv[0] if getattr(sys, "frozen", False) else __file__))
# 64x64 "eyeglasses" icon (Noto Color Emoji U+1F453, Apache-2.0)
ICON_PNG_B64 = "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"
# "FULL SBS 3D" logo shown in the Output section (103x88, transparent PNG)
LOGO_PNG_B64 = "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V37l5ptP1lqb06ZNuzoej5efXVdX94ePfvSjcytzzBPhok3Loqmp6R4R8lVuaTwhhGdatn7vmQtWHTfj26YVazeaLFprVuaGpmlywQUXTJ03b97nx40b92+JRKLHMAwdzaUsU8dx9IQJE3514YUXzqlY/5EK3NLSotrb2/3m5ua3b9my5V89zwsAYZpmMHny5FsTicTugwcPrujt7T09n8+f4rpuwvP61coChAiEkEKHLbiypM1SShzHoba29juvvPLK37zjHe847bHHHvu14ziPf+1rX/vAmjVrDkXa4o3AlutRlTV2zxG0r9Faa/Okk0761d69e1dHz9aAOWbMmD3nXXTxqd/d+3z4QojZs/WQRwd3twtaWvpOYZd62vb9Yz8qyjAMLr/88gkPPPDAO/fs2XN+d3f3qkKhEPf9SuuDHrAWBch0Ot1x5plnrnnwwQcfKuEwWD7M6aeffpZhGOXd1tDQ8EvDMMpCtm2btWvXnrx48eL3TZo06ab6+vqHk8nkIcuytJSyUrMCoCiEcKOTaVoIoWtqal646KKLZtxyyy3jb7nlllQom9lWJpORLS0tKpqHMcSmDn/X0qIigIbZ+CGA9913X/WECRN+ZVmWNgxD19bWvvzud7972TFUgEU0fnl3G4bBHXfcUX/aaad9dNy4cT9MpVIdkexKn2K0KYKytenbJBrwI/noZDKZe+c737liqHlJgKampgWRWXMBXVtbe4fWWgLOYGpnmiZXXnnl2LPOOutt06dPX9fQ0PCzdDr9quM4labQr5isTqVSXQsWLPi41toaivmwLIvvfve7zrJly1Jr166NW5aFUmooksWIgBWDaZ5t2yxbtuztp5122gfuvPPOmqOoYYmKDVPeoG1tbVVLly59f1NT073pdHrfAEC8AYBU/rtWSulYLFaIxWIdpmmWTG0R0FVVVa+vW7fupGhusnIREgjmzZs37/nnn/9DLpfzAKOmpmZjR0fHZ4MgqDQ7siLK6KeuSinuv//+1De/+c25r7766rL9+/d/+ODBgwuDMDyRpejMMAxSqdQfa2tr76+urv7tmDFj9iulgo6OjnFvvPHGimw2uyybzTbm83nHNM1iLBY74DjOs/F4fEddXd3v5s+f/8fvfe97rxeLxcrIpxIwAQSZTIbWI+l4OUx0JCrk4ZUYkiAIYmefffbyl1566fwDBw68J5vNNlbkXv4AuRyRvwkh1JgxY15ubGz88pw5c36pte56+eWXm3ft2vX3XV1dE4QQRa21OXHixPv37t37Qc/z+gKETGTH3/ve985MJBJBCena2tp/isI/NQqVNwaqpNbaaGxsvDdyhl6FySurt2ma2rIsbVmWLu2moT5CCG2apk4mk93V1dVPTZw48Z45c+b87erVq1dlMplxpmkOxkNKwJ42bZodBT5imDVUzl2dc845y6dNm3Z7dXX185FF0QNMVDDcfAHPMAzd1NR0z9133107cNALL7xwfjwe74ie55qmqVesWPHefgFCCZyPfexjU1OplFvSiKqqqntGAc4RC42eZ0aLtNLp9AsDTFzpz8XoZ1Ch/sVI1d3SRwjhVvivymdopZR2HEcnEomO6urqxydMmHDXrFmzLm5ubl5244031g4BmIg2U78ajG3bvOtd71o8ZcqU62tra//gOE5llOUPNv4wn6Jpmnr27NnXm6ZZmSaWNMwWQjB58uSbozEKQFBXV/f0j3/841RZi0vgfOlLXzo5nU73loQVj8d/EC3sWPkOA2DKlCk3RhMojmJRQUlLlFL9QtASgCWwKgALBgJm27ZOpVL76urqtk2YMOHrs2bN+lRzc/OijRs3VlUIC8uy0Fonly1bdmldXd2OWCxWGdwERwlIGRjDMPSsWbNao4DKyBwZZUpArFu37qREItFV2gCWZelTTjllXvk7pRs3btx4Ujqd7igNMn78+B9HjviY8o+Soz777LPPtG1bj8IMBJHGvjpr1qwvTp8+/UOTJ0++tr6+/oF0Ov1SPB4PBjjgfpFhBNYQgIW5RSqV2lNbW7u5qanplunTp19VX1//6NixY59eunTpfYZhBMcBSBkYKaWeOnXqt0rADBOASKUU9fX1Py+Na5pmMGHChPmVgZoA+PjHPz7Gtu29FeD88njAKd137rnnTrJtO09/vm0wIQfxeLzj05/+9Jx+6mcYvPLKK7Hzzjtv7oIFCz48efLkOxoaGrakUqk3bNseGMaXTVAEWLEirO3nvyq1csaMGf+SSqX2jDDHkT4eoMeNG/dvUZSrRogMDUCceeaZ50T+1kskEu6nPvWppiPAyWQyScdxXi0NVl9f/9CJAOeiiy462XGcnhEWXgT0pEmT7oxMqV3hF2R/2ktgmiY33XRT9erVq5fMnz//4qamprvq6uof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"
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".fsbs_converter.json")

# ----------------------------------------------------------------------------- constants

OUTPUT_SIZES = {
    "3840": (1920, 1080),   # per-eye size -> 3840x1080 FSBS
    "7680": (3840, 2160),   # per-eye size -> 7680x2160 FSBS
}

LAYOUTS = {
    "auto":   "Auto-detect",
    "mvhevc": "MV-HEVC (Apple spatial / Vision Pro / 3D HEVC)",
    "hsbs":   "Half Side-by-Side",
    "fsbs":   "Full Side-by-Side",
    "htb":    "Half Top-Bottom (Over-Under)",
    "ftb":    "Full Top-Bottom (Over-Under)",
    "mvc":    "H.264 MVC (Blu-ray 3D, decoded with FRIM)",
}

LAYOUT_SHORT = {"auto": "Auto", "mvhevc": "MV-HEVC 3D", "hsbs": "Half SBS", "fsbs": "Full SBS",
                "htb": "Half Top-Bottom", "ftb": "Full Top-Bottom", "mvc": "H.264 MVC (Blu-ray 3D)"}

VIDEO_EXTS = {".mov", ".mp4", ".m4v", ".mkv", ".ts", ".m2ts", ".mts", ".avi", ".webm", ".hevc", ".wmv", ".mk3d"}

FRIM_MISSING_MSG = (
    "This is H.264 MVC (Blu-ray 3D, e.g. a MakeMKV 3D rip). ffmpeg can only decode its left eye, so the "
    "free FRIM decoder is used for both eyes.\n\nDownload FRIM (videohelp.com/software/FRIM), unzip it into "
    "the app's FRIM folder and click 'Browse FRIM…' to pick FRIMDecode64.exe if it isn't found automatically.")

FIT_MODES = {
    "pad":     "Fit with black bars (keep aspect)",
    "stretch": "Stretch to fill",
    "crop":    "Crop to fill (keep aspect)",
}

# encoder id -> (label, presets, default preset, default quality, quality label, max width)
ENCODERS = {
    "libx265":    ("H.265 / HEVC  (CPU, x265)", ["ultrafast", "superfast", "veryfast", "faster", "fast",
                   "medium", "slow", "slower", "veryslow"], "medium", 20, "CRF", 16384),
    "hevc_nvenc": ("H.265 / HEVC  (NVIDIA NVENC)", ["p1", "p2", "p3", "p4", "p5", "p6", "p7"], "p5", 21, "CQ", 8192),
    "av1_nvenc":  ("AV1  (NVIDIA NVENC, RTX 40+)", ["p1", "p2", "p3", "p4", "p5", "p6", "p7"], "p5", 26, "CQ", 8192),
    "hevc_qsv":   ("H.265 / HEVC  (Intel Quick Sync)", ["veryfast", "faster", "fast", "medium", "slow",
                   "slower", "veryslow"], "medium", 22, "ICQ", 8192),
    "hevc_amf":   ("H.265 / HEVC  (AMD AMF)", ["speed", "balanced", "quality"], "quality", 22, "QP", 8192),
}

PRESET_NOTES = {
    "nvenc": {"p1": "fastest, lowest quality", "p2": "very fast, streaming", "p3": "fast, good",
              "p4": "balanced, everyday", "p5": "very good, default", "p6": "excellent, archival",
              "p7": "best, slowest"},
    "x26x": {"ultrafast": "fastest, largest files", "superfast": "very fast, low efficiency",
             "veryfast": "fast, quick encodes", "faster": "fast, good", "fast": "good, everyday",
             "medium": "very good, default", "slow": "excellent, archival", "slower": "near-best, very slow",
             "veryslow": "best, extremely slow"},
    "qsv": {"veryfast": "fastest, lowest quality", "faster": "very fast", "fast": "fast, good",
            "medium": "balanced, default", "slow": "excellent, archival", "slower": "near-best, slow",
            "veryslow": "best, slowest"},
    "amf": {"speed": "fastest, lower quality", "balanced": "balanced, everyday", "quality": "best, archival"},
}


def preset_family(enc):
    if enc.endswith("_nvenc"):
        return "nvenc"
    if enc == "libx265":
        return "x26x"
    return "qsv" if enc.endswith("_qsv") else "amf"


def preset_label(enc, p):
    note = PRESET_NOTES[preset_family(enc)].get(p)
    return "%s  (%s)" % (p, note) if note else p


def preset_from_label(label):
    return (label or "").split("  (")[0].strip()


AUDIO_MODES = {
    "copy": "Copy original (convert unsupported to AAC)",
    "aac":  "Re-encode to AAC 320k",
    "none": "No audio",
}

BITDEPTHS = {"auto": "Auto (match source)", "8": "8-bit", "10": "10-bit"}

MKV_SAFE_AUDIO = {"aac", "ac3", "eac3", "dts", "truehd", "flac", "opus", "mp3", "mp2", "vorbis", "alac",
                  "pcm_s16le", "pcm_s24le", "pcm_s32le", "pcm_f32le", "pcm_s16be", "pcm_s24be"}
TEXT_SUBS = {"subrip", "srt", "ass", "ssa", "webvtt", "mov_text", "text"}
MKV_SAFE_SUBS = {"subrip", "srt", "ass", "ssa", "webvtt", "hdmv_pgs_subtitle", "dvd_subtitle", "dvb_subtitle"}

DEFAULTS = {
    "ffmpeg": "", "layout": "auto", "sizes": ["3840"], "fit": "pad", "swap": False,
    "encoder": "libx265", "preset": "medium", "quality": 20, "bitdepth": "auto", "audio": "copy",
    "subs": True, "outdir": "", "hwdec": False,
    "tonemap": "auto", "tm_engine": "nits", "tm_curve": "mobius", "peak": "brighter",
    "frim": "", "frim_args": "-i:mvc {in} -sw -sbs -o {out}", "temp_dir": "",
    "sdr_nits": 75, "boost": "off", "sdr_gamma": 1.0, "sdr_sat": 1.0, "crop_tb": 0, "preview_at": "00:20:00", "vk_device": "auto",
}

# ----------------------------------------------------------------------------- settings


def load_settings():
    s = dict(DEFAULTS)
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            s.update(json.load(f))
    except Exception:
        pass
    for k, valid in (("fit", FIT_MODES), ("encoder", ENCODERS), ("bitdepth", BITDEPTHS), ("audio", AUDIO_MODES)):
        if s.get(k) not in valid:
            s[k] = DEFAULTS[k]
    for k, valid in (("tonemap", TONEMAP_MODES), ("tm_engine", TM_ENGINES), ("peak", PEAK_MODES)):
        if s.get(k) not in valid:
            s[k] = DEFAULTS[k]
    if s.get("tm_curve") not in TM_CURVES:
        s["tm_curve"] = DEFAULTS["tm_curve"]
    if s.get("boost") not in BOOSTS:
        s["boost"] = DEFAULTS["boost"]
    try:
        s["sdr_nits"] = int(s.get("sdr_nits", 75))
    except (TypeError, ValueError):
        s["sdr_nits"] = 75
    if s.get("_v", 0) < 2:   # settings from older versions: move to the new nits-based defaults
        s.update(tm_engine="nits", tm_curve="mobius", sdr_nits=75, boost="off", sdr_gamma=1.0,
                 sdr_sat=1.0, crop_tb=0, _v=2)
    if not isinstance(s.get("sizes"), list):
        s["sizes"] = DEFAULTS["sizes"]
    return s


def save_settings(s):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(s, f, indent=2)
    except Exception:
        pass

# ----------------------------------------------------------------------------- ffmpeg discovery


def find_ffmpeg(saved=""):
    """Look for ffmpeg: saved path, next to this app (incl. extracted gyan build folders), then PATH."""
    if saved and os.path.isfile(saved):
        return saved
    pats = [os.path.join(SCRIPT_DIR, "ffmpeg" + EXE),
            os.path.join(SCRIPT_DIR, "bin", "ffmpeg" + EXE),
            os.path.join(SCRIPT_DIR, "ffmpeg*", "bin", "ffmpeg" + EXE),
            os.path.join(SCRIPT_DIR, "ffmpeg*", "ffmpeg*", "bin", "ffmpeg" + EXE),
            os.path.join(SCRIPT_DIR, "..", "ffmpeg*", "bin", "ffmpeg" + EXE)]
    if IS_WIN:
        dl = os.path.join(os.path.expanduser("~"), "Downloads")
        pats += [os.path.join(dl, "ffmpeg*", "bin", "ffmpeg.exe"),
                 os.path.join(dl, "ffmpeg*", "ffmpeg*", "bin", "ffmpeg.exe"),
                 r"C:\ffmpeg\bin\ffmpeg.exe", r"C:\ffmpeg*\bin\ffmpeg.exe"]
    for p in pats:
        hits = sorted((h for h in glob.glob(p) if os.path.isfile(h)), reverse=True)  # newest build first
        if hits:
            return os.path.abspath(hits[0])
    w = shutil.which("ffmpeg")
    return w or ""


def ffprobe_for(ffmpeg):
    d = os.path.dirname(ffmpeg)
    p = os.path.join(d, "ffprobe" + EXE)
    if os.path.isfile(p):
        return p
    return shutil.which("ffprobe") or ""


def run_quiet(cmd, timeout=60):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout,
                          creationflags=NO_WINDOW)


def ffmpeg_version(ffmpeg):
    try:
        out = run_quiet([ffmpeg, "-hide_banner", "-version"], 15).stdout.decode("utf-8", "replace")
        return out.splitlines()[0] if out else "unknown"
    except Exception as e:
        return "error: %s" % e


def available_encoders(ffmpeg):
    try:
        out = run_quiet([ffmpeg, "-hide_banner", "-encoders"], 20).stdout.decode("utf-8", "replace")
        return {e for e in ENCODERS if re.search(r"\s%s\s" % re.escape(e), out)}
    except Exception:
        return set(ENCODERS)


# ----------------------------------------------------------------------------- probing / detection


def probe(ffprobe, path):
    cmd = [ffprobe, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path]
    r = run_quiet(cmd, 120)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode("utf-8", "replace").strip() or "ffprobe failed")
    return json.loads(r.stdout.decode("utf-8", "replace"))


def main_video(info):
    for s in info.get("streams", []):
        if s.get("codec_type") == "video" and not s.get("disposition", {}).get("attached_pic"):
            return s
    return None


def parse_ratio(r, default=1.0):
    try:
        a, b = str(r).split(":")
        a, b = float(a), float(b)
        return a / b if a > 0 and b > 0 else default
    except Exception:
        return default


def has_second_view(ffmpeg, path):
    """True if ffmpeg (7.1+) can decode a second MV-HEVC view from the file."""
    if not ffmpeg:
        return False
    r = run_quiet([ffmpeg, "-v", "error", "-nostdin", "-i", path,
                   "-filter_complex", "[0:v:0:vidx:1]null[o]", "-map", "[o]",
                   "-frames:v", "1", "-f", "null", "-"], 60)
    return r.returncode == 0


def detect_layout(info, filename="", mv_check=None):
    """Return (layout, reason). mv_check: optional callable that tests for a second MV-HEVC view."""
    v = main_video(info)
    if not v:
        return None, "no video stream"
    w, h = int(v.get("width", 0)), int(v.get("height", 0))
    codec = (v.get("codec_name") or "").lower()
    profile = (v.get("profile") or "").lower()
    st_type = ""
    for sd in v.get("side_data_list", []) or []:
        if "stereo" in (sd.get("side_data_type") or "").lower():
            st_type = (sd.get("type") or "").lower()
    tags = {k.lower(): str(val).lower() for k, val in (v.get("tags") or {}).items()}
    st_tag = tags.get("stereo_mode", "")
    name = os.path.basename(filename).lower()
    ar = w / h if h else 0

    if codec == "h264" and ("block" in st_tag or "frame" in st_type or "sequence" in st_type
                            or "alternat" in st_type or re.search(r"(^|[^a-z])mvc([^a-z]|$)", name)):
        return "mvc", ("MKV 3D flag %s" % st_tag) if st_tag else ("3D metadata" if st_type else "filename")
    for sd in v.get("side_data_list", []) or []:
        if sd.get("dv_profile") == 20:
            return "mvhevc", "Dolby Vision profile 20 (3D MV-HEVC)"
    if codec == "hevc" and ("multiview" in profile or (st_type and "side" not in st_type
                                                       and "top" not in st_type and "2d" not in st_type)):
        return "mvhevc", "MV-HEVC stream"
    if "side by side" in st_type or "left_right" in st_tag or "right_left" in st_tag:
        return ("fsbs" if ar >= 3.0 else "hsbs"), "stereo metadata: side-by-side"
    if "top" in st_type or "top_bottom" in st_tag or "bottom_top" in st_tag:
        return ("ftb" if ar <= 1.0 else "htb"), "stereo metadata: top-bottom"
    if re.search(r"(^|[^a-z])(h[-_. ]?sbs|half[-_. ]?sbs)", name):
        return "hsbs", "filename"
    if re.search(r"(^|[^a-z])(f[-_. ]?sbs|full[-_. ]?sbs)", name):
        return "fsbs", "filename"
    if re.search(r"(^|[^a-z])(h[-_. ]?(ou|tab|tb)|half[-_. ]?(ou|tab|tb))([^a-z]|$)", name):
        return "htb", "filename"
    if re.search(r"(^|[^a-z])(f[-_. ]?(ou|tab|tb)|full[-_. ]?(ou|tab|tb))([^a-z]|$)", name):
        return "ftb", "filename"
    if codec == "hevc" and re.search(r"spatial|mv-?hevc|vision", name):
        return "mvhevc", "filename"
    if codec == "hevc" and mv_check is not None:
        try:
            if mv_check():
                return "mvhevc", "second HEVC view found"
        except Exception:
            pass
    if ar >= 3.0:
        return "fsbs", "aspect ratio %dx%d" % (w, h)
    if 0 < ar <= 1.0:
        return "ftb", "aspect ratio %dx%d" % (w, h)
    if re.search(r"(^|[^a-z])sbs([^a-z]|$)", name):
        return "hsbs", "filename"
    if re.search(r"(^|[^a-z])(ou|tab)([^a-z]|$)", name):
        return "htb", "filename"
    return "hsbs", "guess - please confirm"

# ----------------------------------------------------------------------------- command building


def even(x):
    return max(2, int(round(x / 2.0)) * 2)


def eye_geometry(layout, w, h, sar=1.0, ctb=0):
    """Return (crop_left, crop_right, display_aspect_of_one_eye) for a packed frame of w x h.
    ctb = extra pixels to crop from top and bottom of each eye (e.g. to the clean aperture)."""
    if layout in ("hsbs", "fsbs"):
        cw = w // 2
        eh = max(2, h - 2 * ctb)
        cl, cr = "%d:%d:0:%d" % (cw, eh, ctb), "%d:%d:%d:%d" % (cw, eh, cw, ctb)
        # half SBS: unsqueeze 2x, unless the file's pixel aspect ratio already does that
        unsq = 2.0 if (layout == "hsbs" and abs(sar - 1.0) < 0.01) else 1.0
        aspect = (cw * sar * unsq) / eh
        return cl, cr, aspect
    if layout in ("htb", "ftb"):
        ch = h // 2
        eh = max(2, ch - 2 * ctb)
        cl, cr = "%d:%d:0:%d" % (w, eh, ctb), "%d:%d:0:%d" % (w, eh, ch + ctb)
        unsq = 2.0 if (layout == "htb" and abs(sar - 1.0) < 0.01) else 1.0
        aspect = (w * sar) / (eh * unsq)
        return cl, cr, aspect
    raise ValueError("unknown layout %s" % layout)


def fit_chain_runtime(W, H, mode):
    """Fit using the frame's real size at run time (square pixels assumed)."""
    if mode == "stretch":
        return "scale=%d:%d:flags=lanczos,setsar=1" % (W, H)
    if mode == "crop":
        return ("scale=%d:%d:force_original_aspect_ratio=increase:force_divisible_by=2:flags=lanczos,"
                "crop=%d:%d,setsar=1" % (W, H, W, H))
    return ("scale=%d:%d:force_original_aspect_ratio=decrease:force_divisible_by=2:flags=lanczos,"
            "pad=%d:%d:(ow-iw)/2:(oh-ih)/2:black,setsar=1" % (W, H, W, H))


def fit_chain(W, H, aspect, mode):
    if mode == "stretch":
        return "scale=%d:%d:flags=lanczos,setsar=1" % (W, H)
    target = W / float(H)
    if mode == "crop":
        if aspect > target:
            sw, sh = even(H * aspect), H
        else:
            sw, sh = W, even(W / aspect)
        return "scale=%d:%d:flags=lanczos,crop=%d:%d,setsar=1" % (sw, sh, W, H)
    # pad
    if aspect > target:
        sw, sh = W, even(W / aspect)
    else:
        sw, sh = even(H * aspect), H
    sw, sh = min(sw, W), min(sh, H)
    if (sw, sh) == (W, H):
        return "scale=%d:%d:flags=lanczos,setsar=1" % (W, H)
    return ("scale=%d:%d:flags=lanczos,pad=%d:%d:(ow-iw)/2:(oh-ih)/2:black,setsar=1"
            % (sw, sh, W, H))


# MV-HEVC view selectors, tried in order (needs ffmpeg 7.1+)
MV_VIEW_VARIANTS = [
    ("vpos:left", "vpos:right"),   # by signalled eye position
    ("vidx:0", "vidx:1"),          # by view order (base view = left on Apple spatial video)
]

# ---- HDR / Dolby Vision -> SDR

TONEMAP_MODES = {"auto": "Auto (when source is HDR / Dolby Vision)", "on": "Always", "off": "Off (keep HDR)"}
TM_ENGINES = {"nits": "Nits target (GPU DV + CPU tone map) - recommended",
              "libplacebo": "Adaptive (libplacebo GPU, per-scene)",
              "zscale": "Nits target, CPU only (HDR10/HLG, not DV)"}
ADAPTIVE_CURVES = ["spline", "bt.2390", "bt.2446a", "st2094-40", "mobius", "hable", "reinhard"]  # libplacebo
ZSCALE_CURVES = ["mobius", "reinhard", "hable"]                                                    # ffmpeg tonemap
TM_CURVES = ADAPTIVE_CURVES  # every valid curve name
SDR_NITS = {50: "50 nits (very bright)", 75: "75 nits (bright, recommended for 3D)",
            100: "100 nits (standard)", 150: "150 nits (dimmer)", 203: "203 nits (reference, dim)"}
BOOSTS = {"off": ("Off", 1.0), "low": ("Low (+10%)", 1.10), "medium": ("Medium (+20%)", 1.20),
          "high": ("High (+30%)", 1.30)}
ASSUMED_MASTER_PEAK = 1000.0   # nits; used as the highlight roll-off ceiling for the nits target
PEAK_MODES = {"standard": ("Standard", 99.995), "brighter": ("Brighter (ignore tiny highlights)", 99.6),
              "brightest": ("Brightest", 99.0)}


def hdr_info(v):
    """Return dict: hdr(bool), dv_profile(int|None), dv_compat(int|None), transfer(str)."""
    trc = (v.get("color_transfer") or "").lower()
    prof = compat = None
    for sd in v.get("side_data_list", []) or []:
        if "dovi" in (sd.get("side_data_type") or "").lower() or "dv_profile" in sd:
            prof = sd.get("dv_profile")
            compat = sd.get("dv_bl_signal_compatibility_id")
    hdr = trc in ("smpte2084", "arib-std-b67") or prof is not None
    return {"hdr": hdr, "dv_profile": prof, "dv_compat": compat, "transfer": trc}


def needs_dv_processing(hi):
    """Dolby Vision without an HDR10/HLG-compatible base (profiles 5 and 20) must use libplacebo."""
    return hi["dv_profile"] is not None and (hi["dv_compat"] in (0, None) or hi["dv_profile"] in (5, 20))


def vulkan_device(setting):
    """GPU used by libplacebo. 'auto' -> NVIDIA card if present (avoids picking an integrated GPU),
    otherwise let libplacebo choose. Any other text = index or part of the GPU name, e.g. 'RTX 5080'."""
    s = (setting or "auto").strip()
    if s.lower() == "auto":
        return "NVIDIA" if shutil.which("nvidia-smi") else ""
    return s


def tonemap_chain(tm, scale=None):
    """Filter chain HDR/DV -> SDR BT.709.
    scale: None, or (W, H, fit, ctb) to let libplacebo crop/scale on the GPU (output then needs pad/crop)."""
    fmt = "yuv420p10le" if tm["tenbit"] else "yuv420p"
    lp_scale = ""
    if scale:
        W, H, fit, ctb = scale
        foar = {"pad": "decrease", "crop": "increase", "stretch": "disable"}[fit]
        lp_scale = ":w=%d:h=%d:force_original_aspect_ratio=%s:force_divisible_by=2" % (W, H, foar)
        if ctb:
            lp_scale += ":crop_h=ih-%d" % (2 * ctb)
    engine = tm["engine"]
    if engine == "libplacebo":
        curve = tm["curve"] if tm["curve"] in ADAPTIVE_CURVES else "spline"
        return ("libplacebo=tonemapping=%s:peak_detect=1:percentile=%s:gamut_mode=perceptual:"
                "contrast_recovery=0.3:apply_dolbyvision=1:colorspace=bt709:color_primaries=bt709:"
                "color_trc=bt709:range=tv:format=%s%s" % (curve, tm["peak"], fmt, lp_scale))
    nits = float(tm.get("nits", 75))
    curve = tm["curve"] if tm["curve"] in ZSCALE_CURVES else "mobius"
    peak = max(1.0, ASSUMED_MASTER_PEAK / nits)
    zs = ("zscale=t=linear:npl=%g,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=%s:desat=0:peak=%.3f,"
          "zscale=t=bt709:m=bt709:r=tv:d=error_diffusion,format=%s" % (nits, curve, peak, fmt))
    if engine == "zscale":
        return zs
    # nits: libplacebo only decodes Dolby Vision into plain HDR10 (PQ / BT.2020) and scales on the GPU
    stage1 = ("libplacebo=apply_dolbyvision=1:tonemapping=clip:peak_detect=0:gamut_mode=clip:"
              "contrast_recovery=0:colorspace=bt2020nc:color_primaries=bt2020:color_trc=smpte2084:"
              "range=tv:format=yuv420p10le%s" % lp_scale)
    return stage1 + "," + zs


def adjust_chain(gamma, sat):
    """Full-precision brightness (gamma on luma) and saturation via lutyuv (works at 8 and 10 bit)."""
    parts = []
    if abs(gamma - 1.0) > 1e-3:
        parts.append("y='minval+(maxval-minval)*pow(clip((val-minval)/(maxval-minval),0,1),%.4f)'"
                     % (1.0 / gamma))
    if abs(sat - 1.0) > 1e-3:
        e = "'clip(((minval+maxval)/2)+(val-(minval+maxval)/2)*%.4f,minval,maxval)'" % sat
        parts += ["u=" + e, "v=" + e]
    return ("lutyuv=" + ":".join(parts)) if parts else ""


# HDR metadata removed after tone mapping (libplacebo strips the Dolby Vision RPU itself once applied)
HDR_SIDEDATA = ["MASTERING_DISPLAY_METADATA", "CONTENT_LIGHT_LEVEL", "DYNAMIC_HDR_PLUS"]


def build_filter(layout, w, h, sar, W, H, fit, swap, mv_variant=0, tm=None, ctb=0, tail=""):
    """tm: None or dict(engine, curve, peak, nits, tenbit, gamma, sat). tail: extra filters after hstack.
    w, h = decoded frame size (after any crop the file itself applies)."""
    post = []
    if tm:
        post += ["sidedata=mode=delete:type=%s" % t for t in HDR_SIDEDATA]
        adj = adjust_chain(tm.get("gamma", 1.0), tm.get("sat", 1.0))
        if adj:
            post.append(adj)
    parts = []
    if layout == "mvhevc":
        # Each MV-HEVC view carries its own Dolby Vision metadata, so process every eye on its own
        # (joining the eyes first loses that metadata), then put them side by side.
        a, b = MV_VIEW_VARIANTS[mv_variant]
        eye = []
        if tm and tm["engine"] in ("nits", "libplacebo"):
            eye.append(tonemap_chain(tm, scale=(W, H, fit, ctb)))   # crop + scale on the GPU
            eye += post
            eye.append({"pad": "pad=%d:%d:(ow-iw)/2:(oh-ih)/2:black,setsar=1" % (W, H),
                        "crop": "crop=%d:%d,setsar=1" % (W, H), "stretch": "setsar=1"}[fit])
        else:
            if tm:
                eye.append(tonemap_chain(tm))
                eye += post
            if ctb:
                eye.append("crop=iw:ih-%d:0:%d" % (2 * ctb, ctb))
            eye.append(fit_chain_runtime(W, H, fit))
        chain = ",".join(eye)
        parts.append("[0:v:0:%s]%s[L]" % (a, chain))
        parts.append("[0:v:0:%s]%s[R]" % (b, chain))
    else:
        pre = ([tonemap_chain(tm)] + post) if tm else []
        pre.append("split=2[a][b]")
        parts.append("[0:v:0]%s" % ",".join(pre))
        cl, cr, aspect = eye_geometry(layout, w, h, sar, ctb)
        fc = fit_chain(W, H, aspect, fit)
        parts.append("[a]crop=%s,%s[L]" % (cl, fc))
        parts.append("[b]crop=%s,%s[R]" % (cr, fc))
    first, second = ("R", "L") if swap else ("L", "R")
    parts.append("[%s][%s]hstack=inputs=2,sidedata=mode=delete:type=STEREO3D%s[vout]"
                 % (first, second, ("," + tail) if tail else ""))
    return ";".join(parts)


def container_crop(v):
    """Crop that ffmpeg applies automatically from the file (e.g. MP4 clean aperture): (t, b, l, r)."""
    for sd in v.get("side_data_list", []) or []:
        if "crop" in (sd.get("side_data_type") or "").lower():
            try:
                return tuple(int(sd.get(k, 0) or 0) for k in ("crop_top", "crop_bottom", "crop_left", "crop_right"))
            except (TypeError, ValueError):
                pass
    return (0, 0, 0, 0)


def source_is_10bit(v):
    pf = (v.get("pix_fmt") or "")
    hdr = (v.get("color_transfer") or "") in ("smpte2084", "arib-std-b67")
    return bool(re.search(r"(10|12)(le|be)?$", pf) or "p010" in pf) or hdr


def resolve_tonemap(v, opts):
    """Return (tm dict or None, tenbit, notes)."""
    notes = []
    hi = hdr_info(v)
    mode = opts.get("tonemap", "auto")
    do_tm = mode == "on" or (mode == "auto" and hi["hdr"])
    bd = opts.get("bitdepth", "auto")
    if bd == "auto":
        tenbit = False if do_tm else source_is_10bit(v)
    else:
        tenbit = bd == "10"
    if not do_tm:
        if hi["dv_profile"] is not None and needs_dv_processing(hi):
            notes.append("WARNING: Dolby Vision profile %s has no HDR10/SDR base - without tone mapping "
                         "colours will be wrong on most players." % hi["dv_profile"])
        return None, tenbit, notes
    engine = opts.get("tm_engine", "nits")
    if engine == "zscale" and hi["dv_profile"] is not None:
        notes.append("Dolby Vision (profile %s) needs the GPU stage - switching to 'Nits target (GPU DV + CPU tone map)'."
                     % hi["dv_profile"])
        engine = "nits"
    if hi["dv_profile"] is not None:
        notes.append("Source: Dolby Vision profile %s -> SDR BT.709 (%s)" % (hi["dv_profile"], engine))
    else:
        notes.append("Source: HDR (%s) -> SDR BT.709 (%s)" % (hi["transfer"] or "?", engine))
    if engine != "libplacebo":
        notes.append("HDR %s nits -> SDR white" % opts.get("sdr_nits", 75))
    tm = {"engine": engine, "curve": opts.get("tm_curve", "mobius"), "nits": float(opts.get("sdr_nits", 75)),
          "peak": PEAK_MODES.get(opts.get("peak", "brighter"), PEAK_MODES["brighter"])[1],
          "tenbit": tenbit, "gamma": float(opts.get("sdr_gamma", 1.0)), "sat": float(opts.get("sdr_sat", 1.0))}
    return tm, tenbit, notes


def encoder_args(enc, preset, q, tenbit):
    a = ["-c:v:0", enc]
    if enc == "libx265":
        a += ["-preset", preset, "-crf", str(q), "-pix_fmt", "yuv420p10le" if tenbit else "yuv420p",
              "-x265-params", "log-level=error"]
    elif enc.endswith("_nvenc"):
        a += ["-preset", preset, "-tune", "hq", "-rc", "vbr", "-cq", str(q), "-b:v", "0",
              "-rc-lookahead", "32", "-spatial-aq", "1"]
        if enc != "av1_nvenc":
            a += ["-temporal-aq", "1"]
        a += ["-pix_fmt", "p010le" if tenbit else "yuv420p"]
    elif enc == "hevc_qsv":
        a += ["-preset", preset, "-global_quality", str(q)]
        a += ["-pix_fmt", "p010le" if tenbit else "nv12"]
    elif enc == "hevc_amf":
        a += ["-quality", preset, "-rc", "cqp", "-qp_i", str(q), "-qp_p", str(q), "-qp_b", str(q)]
        a += ["-pix_fmt", "p010le" if tenbit else "nv12"]
    return a


def stream_args(info, audio_mode, subs, inp=0):
    args, notes = [], []
    if audio_mode != "none":
        aidx = 0
        for s in info.get("streams", []):
            if s.get("codec_type") != "audio":
                continue
            codec = s.get("codec_name") or ""
            n = s["index"]
            if not codec or codec == "none":
                notes.append("Skipping audio stream #%d (codec not supported by this ffmpeg)" % n)
                continue
            args += ["-map", "%d:%d" % (inp, n)]
            if audio_mode == "copy" and codec in MKV_SAFE_AUDIO:
                args += ["-c:a:%d" % aidx, "copy"]
            else:
                if audio_mode == "copy":
                    notes.append("Audio stream #%d (%s) can't go in MKV as-is -> AAC" % (n, codec))
                args += ["-c:a:%d" % aidx, "aac", "-b:a:%d" % aidx, "320k"]
            aidx += 1
    if subs:
        sidx = 0
        for s in info.get("streams", []):
            if s.get("codec_type") != "subtitle":
                continue
            codec = s.get("codec_name") or ""
            n = s["index"]
            if codec in MKV_SAFE_SUBS:
                args += ["-map", "%d:%d" % (inp, n), "-c:s:%d" % sidx, "copy"]
            elif codec in TEXT_SUBS:
                args += ["-map", "%d:%d" % (inp, n), "-c:s:%d" % sidx, "srt"]
            else:
                notes.append("Skipping subtitle stream #%d (%s)" % (n, codec or "unknown"))
                continue
            sidx += 1
    return args, notes


def output_path(src, outdir, size_key):
    W, H = OUTPUT_SIZES[size_key]
    base = os.path.splitext(os.path.basename(src))[0]
    d = outdir or os.path.dirname(os.path.abspath(src))
    return os.path.join(d, "%s_FSBS_%dx%d.mkv" % (base, W * 2, H))


def build_command(ffmpeg, src, dst, info, opts, mv_variant=0, preview_at=None):
    """opts: layout(resolved), size, fit, swap, encoder, preset, quality, bitdepth, audio, subs, hwdec,
    tonemap, tm_engine, tm_curve, peak, sdr_gamma, sdr_sat, crop_tb.
    preview_at: seconds -> build a one-frame PNG preview command instead (dst = .png)."""
    v = main_video(info)
    if opts["layout"] == "mvc":
        raise RuntimeError("MVC files are converted through FRIM - use build_mvc_command()")
    w, h = int(v["width"]), int(v["height"])
    ct, cb, cl_, cr_ = container_crop(v)
    if any((ct, cb, cl_, cr_)):
        w, h = w - cl_ - cr_, h - ct - cb   # ffmpeg applies this crop while decoding
    sar = parse_ratio(v.get("sample_aspect_ratio", "1:1"))
    W, H = OUTPUT_SIZES[opts["size"]]
    layout = opts["layout"]
    tm, tenbit, notes = resolve_tonemap(v, opts)
    tail = "scale=1920:-2:flags=bicubic,format=rgb24" if preview_at is not None else ""
    fc = build_filter(layout, w, h, sar, W, H, opts["fit"], opts["swap"], mv_variant, tm,
                      int(opts.get("crop_tb", 0) or 0), tail)

    cmd = [ffmpeg, "-hide_banner", "-y"]
    if preview_at is None:
        cmd += ["-progress", "pipe:1", "-nostats"]
    else:
        cmd += ["-nostdin", "-loglevel", "error"]
    if opts.get("hwdec") and layout != "mvhevc":
        cmd += ["-hwaccel", "auto"]
    if tm and tm["engine"] in ("libplacebo", "nits"):   # both run libplacebo on the GPU
        dev = vulkan_device(opts.get("vk_device", "auto"))
        if dev:
            cmd += ["-init_hw_device", "vulkan=vk:%s" % dev, "-filter_hw_device", "vk"]
            notes.append("Tone mapping on Vulkan GPU matching '%s'" % dev)
    if preview_at is not None:
        cmd += ["-ss", "%.3f" % preview_at]
    cmd += ["-i", src, "-filter_complex", fc, "-map", "[vout]"]
    if preview_at is not None:
        return cmd + ["-frames:v", "1", "-update", "1", dst], notes
    sargs, snotes = stream_args(info, opts["audio"], opts["subs"])
    notes += snotes
    cmd += sargs
    cmd += encoder_args(opts["encoder"], opts["preset"], opts["quality"], tenbit)
    if tm:
        cmd += ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                "-color_range", "tv"]
    cmd += ["-metadata:s:v:0", "stereo_mode=left_right",
            "-map_metadata", "0", "-map_chapters", "0",
            "-max_muxing_queue_size", "4096", dst]
    return cmd, notes


def render_preview(ffmpeg, src, info, opts, at_seconds, png, log=print):
    """Render one FSBS frame (scaled to 1920 wide) with the current settings. Returns png path."""
    layout = opts["layout"]
    if layout == "mvc":
        return preview_mvc(ffmpeg, src, info, opts, at_seconds, png, log)
    variants = range(len(MV_VIEW_VARIANTS)) if layout == "mvhevc" else [0]
    err = ""
    for vi in variants:
        cmd, notes = build_command(ffmpeg, src, png, info, opts, vi, preview_at=at_seconds)
        log("Preview: " + quote_cmd(cmd))
        r = run_quiet(cmd, 600)
        if r.returncode == 0 and os.path.isfile(png):
            return png
        err = r.stderr.decode("utf-8", "replace").strip()[-1500:]
    hint = ""
    if "libplacebo" in err.lower() or "vulkan" in err.lower():
        hint = ("\n\nlibplacebo needs a Vulkan-capable GPU and up-to-date graphics drivers. "
                "For HDR10 (not Dolby Vision) sources you can switch the engine to zscale (CPU).")
    raise RuntimeError((err or "ffmpeg failed") + hint)


def quote_cmd(cmd):
    if IS_WIN:
        return subprocess.list2cmdline(cmd)
    import shlex
    return " ".join(shlex.quote(c) for c in cmd)

# ----------------------------------------------------------------------------- running


class Cancelled(Exception):
    pass


def run_ffmpeg(cmd, duration, on_progress, on_log, cancel_event, stdin_src=None, companions=()):
    """Run ffmpeg, report progress (0..1, speed, eta). Returns (returncode, last_stderr_lines, got_frames).
    stdin_src: pipe to feed ffmpeg's stdin (e.g. FRIM output); companions: processes to kill on cancel."""
    p = subprocess.Popen(cmd, stdin=stdin_src if stdin_src is not None else subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=NO_WINDOW)
    tail = []
    state = {"frames": False}

    def read_err():
        for raw in iter(p.stderr.readline, b""):
            line = raw.decode("utf-8", "replace").rstrip()
            if line:
                tail.append(line)
                del tail[:-60]
                on_log(line)

    def read_out():
        speed = ""
        for raw in iter(p.stdout.readline, b""):
            line = raw.decode("utf-8", "replace").strip()
            if line.startswith("out_time_us=") or line.startswith("out_time_ms="):
                try:
                    t = int(line.split("=", 1)[1]) / 1e6
                except ValueError:
                    continue
                if t > 0:
                    state["frames"] = True
                frac = min(1.0, t / duration) if duration else 0.0
                eta = ""
                try:
                    sp = float(speed.rstrip("x"))
                    if sp > 0 and duration:
                        eta = fmt_time((duration - t) / sp)
                except ValueError:
                    pass
                on_progress(frac, speed, eta)
            elif line.startswith("speed="):
                speed = line.split("=", 1)[1].strip()
            elif line.startswith("frame=") and line != "frame=0":
                state["frames"] = True

    te = threading.Thread(target=read_err, daemon=True)
    to = threading.Thread(target=read_out, daemon=True)
    te.start()
    to.start()
    cancelled = False
    while p.poll() is None:
        if cancel_event.is_set() and not cancelled:
            cancelled = True
            for c in companions:
                try:
                    c.kill()
                except Exception:
                    pass
            try:
                if stdin_src is None:
                    p.stdin.write(b"q")
                    p.stdin.flush()
            except Exception:
                pass
            for _ in range(50):
                if p.poll() is not None:
                    break
                time.sleep(0.1)
            if p.poll() is None:
                p.kill()
        time.sleep(0.2)
    te.join(2)
    to.join(2)
    if cancelled:
        raise Cancelled()
    return p.returncode, tail, state["frames"]


def _remove_quietly(path):
    """Delete a file if it exists; never raises."""
    try:
        if path and os.path.isfile(path):
            os.remove(path)
    except OSError:
        pass


def parse_time(t):
    """'1:02:03', '20:00', '75.5' -> seconds"""
    t = str(t).strip()
    secs = 0.0
    for part in t.split(":"):
        secs = secs * 60 + float(part or 0)
    return secs


def fmt_time(s):
    s = int(max(0, s))
    return "%d:%02d:%02d" % (s // 3600, s % 3600 // 60, s % 60)


def convert_one(ffmpeg, ffprobe, src, size, opts, on_progress, on_log, cancel_event, overwrite=True):
    """Convert one file to one output size. Returns output path. Raises on failure."""
    info = probe(ffprobe, src)
    v = main_video(info)
    if not v:
        raise RuntimeError("No video stream found")
    layout = opts["layout"]
    if layout == "auto":
        layout, why = detect_layout(info, src, lambda: has_second_view(ffmpeg, src))
        on_log("Detected layout: %s (%s)" % (LAYOUTS[layout], why))
    o = dict(opts, layout=layout, size=size)
    W, H = OUTPUT_SIZES[size]
    if layout == "mvc":
        return convert_mvc(ffmpeg, src, info, o, on_progress, on_log, cancel_event)
    if 2 * W > ENCODERS[o["encoder"]][5]:
        raise RuntimeError("%s cannot encode %dx%d - pick an HEVC/AV1 encoder for this size."
                           % (o["encoder"], 2 * W, H))
    dst = output_path(src, opts.get("outdir", ""), size)
    if os.path.abspath(dst) == os.path.abspath(src):
        raise RuntimeError("Output would overwrite the source")
    if os.path.exists(dst) and not overwrite:
        raise RuntimeError("Output exists: %s" % dst)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        duration = float(info.get("format", {}).get("duration") or v.get("duration") or 0)
    except ValueError:
        duration = 0.0

    variants = range(len(MV_VIEW_VARIANTS)) if layout == "mvhevc" else [0]
    for vi in variants:
        cmd, notes = build_command(ffmpeg, src, dst, info, o, vi)
        for n in notes:
            on_log("Note: " + n)
        on_log("Command: " + quote_cmd(cmd))
        try:
            rc, tail, got = run_ffmpeg(cmd, duration, on_progress, on_log, cancel_event)
        except Cancelled:
            _remove_quietly(dst)
            raise
        if rc == 0:
            on_progress(1.0, "", "")
            return dst
        if layout == "mvhevc" and not got and vi + 1 < len(MV_VIEW_VARIANTS):
            on_log("View selection '%s' failed - retrying with '%s'"
                   % (MV_VIEW_VARIANTS[vi][0], MV_VIEW_VARIANTS[vi + 1][0]))
            continue
        msg = "\n".join(tail[-8:])
        if "libplacebo" in msg.lower() or "vulkan" in msg.lower():
            msg += ("\n\nlibplacebo (HDR/Dolby Vision tone mapping) needs a Vulkan-capable GPU with current "
                    "drivers. For plain HDR10 you can use the zscale (CPU) engine instead.")
        if layout == "mvhevc" and ("view" in msg.lower() or "option" in msg.lower()):
            msg += ("\n\nMV-HEVC decoding needs ffmpeg 7.1 or newer. If this file isn't MV-HEVC, "
                    "choose its real input layout instead of Auto/MV-HEVC.")
        _remove_quietly(dst)
        raise RuntimeError("ffmpeg failed (exit %s):\n%s" % (rc, msg))
    raise RuntimeError("ffmpeg failed")

# ----------------------------------------------------------------------------- H.264 MVC via FRIM


def find_frim(saved=""):
    """Locate FRIMDecode64.exe (FRIM, the free Intel-Media-SDK based MVC decoder)."""
    if saved and os.path.isfile(saved):
        return saved
    roots = [SCRIPT_DIR]
    if IS_WIN:
        roots += [os.path.join(os.path.expanduser("~"), "Downloads"), "C:\\"]
    for root in roots:
        for name in ("FRIMDecode64.exe", "FRIMDecode.exe"):
            pats = [os.path.join(root, name)] if root == SCRIPT_DIR else []
            pats += [os.path.join(root, "FRIM*", name), os.path.join(root, "FRIM*", "*", name),
                     os.path.join(root, "FRIM*", "*", "*", name)]
            for pat in pats:
                hits = sorted((h for h in glob.glob(pat) if os.path.isfile(h)), reverse=True)
                if hits:
                    return os.path.abspath(hits[0])
    return shutil.which("FRIMDecode64") or ""


def frim_cmd(frim, template, es, out):
    cmd = [frim]
    for tok in (template or DEFAULTS["frim_args"]).split():
        tok = tok.strip('"')
        cmd.append(tok.replace("{in}", es).replace("{out}", out))
    return cmd


def mvc_params(info):
    """(eye_w, eye_h, fps_string, source_is_right_first)"""
    v = main_video(info)
    ew, eh = int(v.get("width", 1920)), int(v.get("height", 1080))
    fps = v.get("r_frame_rate") or v.get("avg_frame_rate") or "24000/1001"
    if fps in ("0/0", ""):
        fps = "24000/1001"
    tags = {k.lower(): str(x).lower() for k, x in (v.get("tags") or {}).items()}
    right_first = tags.get("stereo_mode", "") in ("block_rl", "right_left", "bottom_top")
    return ew, eh, fps, right_first


def build_mvc_command(ffmpeg, src, dst, info, opts, raw_input, preview_frame=None):
    """ffmpeg reading FRIM's raw side-by-side yuv (stdin '-' or a .yuv file) + audio/subs from the source."""
    ew, eh, fps, right_first = mvc_params(info)
    W, H = OUTPUT_SIZES[opts["size"]]
    swap = bool(opts.get("swap")) != right_first
    tail = ""
    if preview_frame is not None:
        tail = "select=eq(n\\,%d),scale=1920:-2:flags=bicubic,format=rgb24" % preview_frame
    fc = build_filter("fsbs", 2 * ew, eh, 1.0, W, H, opts["fit"], swap, 0, None,
                      int(opts.get("crop_tb", 0) or 0), tail)
    cmd = [ffmpeg, "-hide_banner", "-y"]
    cmd += (["-nostdin", "-loglevel", "error"] if preview_frame is not None else ["-progress", "pipe:1", "-nostats"])
    cmd += ["-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", "%dx%d" % (2 * ew, eh),
            "-framerate", fps, "-i", raw_input]
    notes = ["MVC: FRIM decodes both eyes (%dx%d each, %s fps)%s" % (ew, eh, fps,
             ", source is right-eye-first -> swapped" if right_first else "")]
    if preview_frame is not None:
        return cmd + ["-filter_complex", fc, "-map", "[vout]", "-frames:v", "1", "-update", "1", dst], notes
    cmd += ["-i", src, "-filter_complex", fc, "-map", "[vout]"]
    sargs, snotes = stream_args(info, opts["audio"], opts["subs"], inp=1)
    cmd += sargs
    tenbit = opts.get("bitdepth") == "10"
    cmd += encoder_args(opts["encoder"], opts["preset"], opts["quality"], tenbit)
    cmd += ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
            "-metadata:s:v:0", "stereo_mode=left_right", "-map_metadata", "1", "-map_chapters", "1",
            "-max_muxing_queue_size", "4096", "-shortest", dst]
    return cmd, notes + snotes


def extract_mvc_es(ffmpeg, src, es, duration, on_progress, on_log, cancel_event, start=None, frames=None):
    """Copy the combined AVC+MVC video (both views, MakeMKV keeps them in one track) to an Annex-B .h264."""
    cmd = [ffmpeg, "-hide_banner", "-y", "-progress", "pipe:1", "-nostats", "-loglevel", "error"]
    if start:
        cmd += ["-ss", "%.3f" % start]
    cmd += ["-i", src, "-map", "0:v:0", "-c:v", "copy", "-bsf:v", "h264_mp4toannexb"]
    if frames:
        cmd += ["-frames:v", str(frames)]
    cmd += ["-f", "h264", es]
    on_log("Extract: " + quote_cmd(cmd))
    rc, tail, _ = run_ffmpeg(cmd, duration, on_progress, lambda m: None, cancel_event)
    if rc != 0 or not os.path.isfile(es) or os.path.getsize(es) == 0:
        raise RuntimeError("Extracting the MVC video stream failed:\n" + "\n".join(tail[-8:]))


def _drain(stream, sink, keep=40, log=None, log_first=25):
    """Read a process pipe split on CR/LF; keep the last lines, log the first few."""
    buf, n = b"", 0
    while True:
        chunk = stream.read(4096) if hasattr(stream, "read") else b""
        if not chunk:
            break
        buf += chunk
        parts = re.split(rb"[\r\n]+", buf)
        buf = parts.pop()
        for raw in parts:
            line = raw.decode("utf-8", "replace").strip()
            if not line:
                continue
            sink.append(line)
            del sink[:-keep]
            n += 1
            if log and n <= log_first:
                log("FRIM: " + line)
    if buf.strip():
        sink.append(buf.decode("utf-8", "replace").strip())


def convert_mvc(ffmpeg, src, info, o, on_progress, on_log, cancel_event):
    frim = find_frim(o.get("frim", ""))
    if not frim:
        raise RuntimeError(FRIM_MISSING_MSG)
    dst = output_path(src, o.get("outdir", ""), o["size"])
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    v = main_video(info)
    try:
        duration = float(info.get("format", {}).get("duration") or v.get("duration") or 0)
    except ValueError:
        duration = 0.0
    tmpdir = o.get("temp_dir") or os.path.dirname(dst)
    es = os.path.join(tmpdir, os.path.splitext(os.path.basename(src))[0] + ".mvc_temp.h264")
    on_log("Step 1/2: extracting the 3D (AVC+MVC) video stream to a temporary file:\n  " + es)
    try:
        extract_mvc_es(ffmpeg, src, es, duration,
                       lambda f, sp, eta: on_progress(f * 0.08, sp, ("extracting, " + eta) if eta else "extracting"),
                       on_log, cancel_event)
        on_log("Step 2/2: FRIM decodes both eyes -> ffmpeg resizes and encodes")
        fcmd = frim_cmd(frim, o.get("frim_args"), es, "-")
        on_log("FRIM: " + quote_cmd(fcmd))
        fp = subprocess.Popen(fcmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=NO_WINDOW)
        ftail = []
        tf = threading.Thread(target=_drain, args=(fp.stderr, ftail, 40, on_log), daemon=True)
        tf.start()
        cmd, notes = build_mvc_command(ffmpeg, src, dst, info, o, "-")
        for n in notes:
            on_log("Note: " + n)
        on_log("Command: " + quote_cmd(cmd))
        try:
            rc, tail, got = run_ffmpeg(cmd, duration,
                                       lambda f, sp, eta: on_progress(0.08 + f * 0.92, sp, eta),
                                       on_log, cancel_event, stdin_src=fp.stdout, companions=(fp,))
        except Cancelled:
            _remove_quietly(dst)
            raise
        finally:
            try:
                fp.stdout.close()
            except Exception:
                pass
        try:
            fp.wait(15)
        except subprocess.TimeoutExpired:
            fp.kill()
        tf.join(3)
        if rc != 0 or not got:
            _remove_quietly(dst)
            raise RuntimeError("MVC conversion failed (ffmpeg exit %s, FRIM exit %s)\nffmpeg:\n%s\n\nFRIM:\n%s"
                               % (rc, fp.returncode, "\n".join(tail[-6:]), "\n".join(ftail[-10:])))
        if fp.returncode not in (0, None):
            on_log("Warning: FRIM exited with code %s - check the end of the movie." % fp.returncode)
        on_progress(1.0, "", "")
        return dst
    finally:
        _remove_quietly(es)


def preview_mvc(ffmpeg, src, info, opts, at_seconds, png, log=print):
    """Extract ~2 s of MVC at the chosen time, decode with FRIM to a .yuv, render one frame."""
    frim = find_frim(opts.get("frim", ""))
    if not frim:
        raise RuntimeError(FRIM_MISSING_MSG)
    tmp = tempfile.mkdtemp(prefix="fsbs_mvc_")
    seg, yuv = os.path.join(tmp, "seg.h264"), os.path.join(tmp, "seg.yuv")
    try:
        extract_mvc_es(ffmpeg, src, seg, 0, lambda *a: None, log, threading.Event(), start=at_seconds, frames=60)
        fcmd = frim_cmd(frim, opts.get("frim_args"), seg, yuv)
        log("FRIM: " + quote_cmd(fcmd))
        r = run_quiet(fcmd, 600)
        out = (r.stdout + r.stderr).decode("utf-8", "replace")
        for line in [l.strip() for l in re.split(r"[\r\n]+", out) if l.strip()][:20]:
            log("FRIM: " + line)
        yuvs = sorted(glob.glob(os.path.join(tmp, "*.yuv")), key=os.path.getsize, reverse=True)
        if not yuvs or os.path.getsize(yuvs[0]) == 0:
            raise RuntimeError("FRIM produced no output (exit %s).\n%s\n\nIf the file was ripped without the "
                               "'Mpeg4 MVC' track ticked in MakeMKV it only contains the left eye."
                               % (r.returncode, out.strip()[-1200:]))
        yuv = yuvs[0]
        ew, eh, fps, _ = mvc_params(info)
        fsize = 2 * ew * eh * 3 // 2
        size = os.path.getsize(yuv)
        if size % fsize:
            log("Warning: FRIM output size doesn't match %dx%d side-by-side frames - check the FRIM "
                "arguments (e.g. -sbs) and the frame size FRIM reports above." % (2 * ew, eh))
        nframes = max(1, size // fsize)
        cmd, _ = build_mvc_command(ffmpeg, src, png, info, opts, yuv, preview_frame=min(24, nframes - 1))
        log("Preview: " + quote_cmd(cmd))
        r = run_quiet(cmd, 300)
        if r.returncode != 0 or not os.path.isfile(png):
            raise RuntimeError(r.stderr.decode("utf-8", "replace").strip()[-1500:] or "ffmpeg failed")
        return png
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

# ----------------------------------------------------------------------------- GUI


def expand_dropped(paths):
    """Files as-is; folders -> the video files directly inside them."""
    out = []
    for p in paths:
        if os.path.isdir(p):
            for n in sorted(os.listdir(p)):
                fp = os.path.join(p, n)
                if os.path.isfile(fp) and os.path.splitext(n)[1].lower() in VIDEO_EXTS:
                    out.append(fp)
        else:
            out.append(p)
    return out


def enable_windows_drop(widget, callback):
    """Accept files dropped from Windows Explorer onto a Tk window (WM_DROPFILES, Unicode-safe)."""
    import ctypes
    from ctypes import wintypes
    user32, shell32 = ctypes.windll.user32, ctypes.windll.shell32
    LRESULT = ctypes.c_ssize_t
    WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
    is64 = ctypes.sizeof(ctypes.c_void_p) == 8
    set_wl = user32.SetWindowLongPtrW if is64 else user32.SetWindowLongW
    set_wl.restype = ctypes.c_void_p
    set_wl.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
    user32.CallWindowProcW.restype = LRESULT
    user32.CallWindowProcW.argtypes = [ctypes.c_void_p, wintypes.HWND, wintypes.UINT, wintypes.WPARAM,
                                       wintypes.LPARAM]
    shell32.DragQueryFileW.restype = wintypes.UINT
    shell32.DragQueryFileW.argtypes = [ctypes.c_void_p, wintypes.UINT, ctypes.c_wchar_p, wintypes.UINT]
    shell32.DragFinish.restype = None
    shell32.DragFinish.argtypes = [ctypes.c_void_p]
    shell32.DragAcceptFiles.restype = None
    shell32.DragAcceptFiles.argtypes = [wintypes.HWND, wintypes.BOOL]
    WM_DROPFILES, GWLP_WNDPROC = 0x0233, -4
    hwnd = widget.winfo_id()
    old = [None]

    def proc(h, msg, wp, lp):
        if msg == WM_DROPFILES:
            files = []
            try:
                n = shell32.DragQueryFileW(wp, 0xFFFFFFFF, None, 0)
                for i in range(n):
                    ln = shell32.DragQueryFileW(wp, i, None, 0)
                    buf = ctypes.create_unicode_buffer(ln + 1)
                    shell32.DragQueryFileW(wp, i, buf, ln + 1)
                    files.append(buf.value)
            finally:
                shell32.DragFinish(wp)
            try:
                callback(files)
            except Exception:
                pass
            return 0
        return user32.CallWindowProcW(old[0], h, msg, wp, lp)

    new_proc = WNDPROC(proc)
    widget._fsbs_drop_proc = new_proc          # keep the callback alive
    shell32.DragAcceptFiles(hwnd, True)
    old[0] = set_wl(hwnd, GWLP_WNDPROC, ctypes.cast(new_proc, ctypes.c_void_p).value)
    if not old[0]:
        raise OSError("SetWindowLongPtr failed")
    return True


def fit_width(values, extra=3):
    """Combobox width (in average characters) that shows the longest value in full, for the
    font actually in use (Segoe UI on Windows)."""
    try:
        from tkinter import font as tkfont
        f = tkfont.nametofont("TkTextFont")
        zero = max(1, f.measure("0"))
        return int(max(f.measure(v) for v in values) / zero + 0.999) + extra
    except Exception:
        return max(len(v) for v in values) + extra


def _pick_font(root, names, size):
    try:
        from tkinter import font as tkfont
        fams = set(tkfont.families(root))
    except Exception:
        fams = set()
    for n in names:
        if n in fams:
            return (n, size, "bold")
    return ("Helvetica", size, "bold")


class PillButton(tk.Canvas if tk else object):
    """Compact black rounded 'CONVERT!' button. The shape is drawn as an anti-aliased image
    (Tk's own canvas shapes have jagged edges on Windows); ttk buttons can't be coloured."""
    COLORS = {"normal": "#111111", "hover": "#3a3a3a", "pressed": "#5a5a5a", "disabled": "#a8a8a8"}

    def __init__(self, parent, text, command, height=30, radius=8, pad_x=18):
        bg = ttk.Style().lookup("TFrame", "background") or parent.winfo_toplevel().cget("bg")
        font = _pick_font(parent, ["Bahnschrift SemiBold Condensed", "Bahnschrift Condensed", "Bahnschrift",
                                   "Segoe UI Semibold", "Segoe UI", "DejaVu Sans Condensed"], 12)
        try:
            from tkinter import font as tkfont
            tw = tkfont.Font(root=parent, font=font).measure(text)
        except Exception:
            tw = 8 * len(text)
        width = tw + 2 * pad_x
        super().__init__(parent, width=width, height=height, bg=bg, highlightthickness=0, bd=0, cursor="hand2")
        self.command, self.state, self.w, self.h = command, "normal", width, height
        bg_rgb = tuple(c // 257 for c in self.winfo_rgb(bg))
        mask = self._mask(width, height, radius)
        self.images = {k: self._image(mask, width, height, self._hex(v), bg_rgb) for k, v in self.COLORS.items()}
        self.img_item = self.create_image(0, 0, anchor="nw", image=self.images["normal"])
        self.create_text(width // 2, height // 2, text=text, fill="white", font=font)
        self.bind("<Enter>", lambda e: self.state == "normal" and self._paint("hover"))
        self.bind("<Leave>", lambda e: self.state == "normal" and self._paint("normal"))
        self.bind("<ButtonPress-1>", lambda e: self.state == "normal" and self._paint("pressed"))
        self.bind("<ButtonRelease-1>", self._release)

    @staticmethod
    def _hex(c):
        return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))

    @staticmethod
    def _mask(w, h, r, ss=4):
        """Coverage (0..1) of a rounded rectangle per pixel, 4x4 supersampled for smooth edges."""
        offs = [(i + 0.5) / ss for i in range(ss)]
        mask = []
        for y in range(h):
            row = []
            for x in range(w):
                hit = 0
                for oy in offs:
                    py = y + oy
                    cy = min(max(py, r), h - r)
                    for ox in offs:
                        px = x + ox
                        cx = min(max(px, r), w - r)
                        if (px - cx) ** 2 + (py - cy) ** 2 <= r * r:
                            hit += 1
                row.append(hit / float(ss * ss))
            mask.append(row)
        return mask

    def _image(self, mask, w, h, fill, bg):
        """Blend the fill colour onto the background colour using the coverage mask."""
        rows = ["{" + " ".join("#%02x%02x%02x" % tuple(int(bg[i] + (fill[i] - bg[i]) * a + 0.5) for i in range(3))
                               for a in row) + "}" for row in mask]
        img = tk.PhotoImage(master=self, width=w, height=h)
        img.put(" ".join(rows))
        return img

    def _paint(self, key):
        self.itemconfigure(self.img_item, image=self.images[key])

    def _release(self, e):
        if self.state != "normal":
            return
        inside = 0 <= e.x <= self.w and 0 <= e.y <= self.h
        self._paint("hover" if inside else "normal")
        if inside and self.command:
            self.command()

    def set_state(self, state):
        self.state = "disabled" if state == "disabled" else "normal"
        self._paint(self.state)
        self.configure(cursor="arrow" if self.state == "disabled" else "hand2")


class App:
    def __init__(self):
        self.s = load_settings()
        if IS_WIN:
            try:  # own taskbar entry/icon instead of Python's
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("FullSBS3DConverter")
            except Exception:
                pass
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        try:
            self._icon = tk.PhotoImage(data=ICON_PNG_B64)
            self.root.iconphoto(True, self._icon)
        except Exception:
            pass
        self.root.geometry("1240x920")
        self.root.minsize(1000, 760)
        self.q = queue.Queue()
        self.cancel_event = threading.Event()
        self.worker = None
        self.files = []          # list of dicts: path, info, detected, iid
        self._previews = []      # preview PNGs in %TEMP%, deleted when the app closes
        self.ffprobe = ""
        self._build()
        ttk.Style().configure("About.TButton", padding=(8, 0), font=("Segoe UI", 8))
        ttk.Button(self.root, text="About", style="About.TButton", command=self._about).place(
            relx=1.0, x=-8, y=1, anchor="ne")
        self._set_ffmpeg(find_ffmpeg(self.s.get("ffmpeg", "")), quiet=True)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(100, self._poll)

    # ---- layout
    def _build(self):
        r = self.root
        style = ttk.Style()
        try:
            style.theme_use("vista" if IS_WIN else "clam")
        except tk.TclError:
            pass
        pad = dict(padx=6, pady=4)

        # ffmpeg row
        f0 = ttk.LabelFrame(r, text="3D MV-HEVC, Top/bottom or MVC Formats to FSBS Converter")
        f0.pack(fill="x", **pad)
        self.v_ff = tk.StringVar(value=self.s.get("ffmpeg", ""))
        ttk.Entry(f0, textvariable=self.v_ff).grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        ttk.Button(f0, text="Browse ffmpeg.exe…", command=self._browse_ff).grid(row=0, column=1, columnspan=2,
                                                                              sticky="ew", padx=2)
        self.l_ver = ttk.Label(f0, text="", foreground="#555")
        self.l_ver.grid(row=1, column=0, columnspan=3, sticky="w", padx=4)
        self.v_frim = tk.StringVar(value=find_frim(self.s.get("frim", "")))
        ttk.Entry(f0, textvariable=self.v_frim).grid(row=2, column=0, sticky="ew", padx=4, pady=(6, 2))
        ttk.Button(f0, text="Browse FRIM…", command=self._browse_frim).grid(row=2, column=1, columnspan=2,
                                                                         sticky="ew", padx=2, pady=(6, 2))
        ff = ttk.Frame(f0)
        ff.grid(row=3, column=0, columnspan=3, sticky="w", padx=4)
        self.l_frim = ttk.Label(ff, text="")
        self.l_frim.pack(side="left")
        ttk.Label(ff, text="   FRIM arguments:").pack(side="left")
        self.v_frim_args = tk.StringVar(value=self.s.get("frim_args") or DEFAULTS["frim_args"])
        ttk.Entry(ff, textvariable=self.v_frim_args, width=40).pack(side="left", padx=4)
        ttk.Button(ff, text="Reset", width=6,
                   command=lambda: self.v_frim_args.set(DEFAULTS["frim_args"])).pack(side="left")
        f0.columnconfigure(0, weight=1)
        self._frim_status()

        # files
        f1 = ttk.LabelFrame(r, text="Input videos")
        f1.pack(fill="both", expand=True, **pad)
        cols = ("file", "res", "codec", "layout", "status")
        self.tree = ttk.Treeview(f1, columns=cols, show="headings", height=7, selectmode="extended")
        for c, t, wdt in (("file", "File", 260), ("res", "Resolution", 85), ("codec", "Codec", 80),
                          ("layout", "Detected input", 210), ("status", "Status", 95)):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=wdt, minwidth=60, anchor="w", stretch=(c == "file"))
        sb = ttk.Scrollbar(f1, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(4, 0), pady=4)
        sb.grid(row=0, column=1, sticky="ns", pady=4)
        bf = ttk.Frame(f1)
        bf.grid(row=0, column=2, sticky="n", padx=4, pady=4)
        ttk.Button(bf, text="Add files…", command=self._add_files).pack(fill="x", pady=1)
        ttk.Button(bf, text="Remove", command=self._remove).pack(fill="x", pady=1)
        ttk.Button(bf, text="Clear", command=self._clear).pack(fill="x", pady=1)
        ttk.Separator(bf).pack(fill="x", pady=4)
        ttk.Label(bf, text="Set input for selected file(s):").pack(anchor="w")
        self.v_override = tk.StringVar(value=LAYOUTS["auto"])
        cb = ttk.Combobox(bf, textvariable=self.v_override, state="readonly", width=46,
                          values=[LAYOUTS[k] for k in LAYOUTS])
        cb.pack(fill="x", pady=1)
        ttk.Button(bf, text="Apply", command=self._apply_override).pack(fill="x", pady=1)
        f1.columnconfigure(0, weight=1)
        f1.rowconfigure(0, weight=1)
        self._enable_dnd()

        # options
        f2 = ttk.LabelFrame(r, text="Output")
        f2.pack(fill="x", **pad)
        self.v_s3840 = tk.BooleanVar(value="3840" in self.s["sizes"])
        self.v_s7680 = tk.BooleanVar(value="7680" in self.s["sizes"])
        ttk.Label(f2, text="FSBS size:").grid(row=0, column=0, sticky="w", **pad)
        sz = ttk.Frame(f2)
        sz.grid(row=0, column=1, columnspan=4, sticky="w")
        ttk.Checkbutton(sz, text="3840×1080  (1920×1080 per eye = 1080p 3D)", variable=self.v_s3840).pack(side="left")
        ttk.Checkbutton(sz, text="7680×2160  (3840×2160 per eye = 4K 3D)", variable=self.v_s7680).pack(side="left", padx=16)
        ttk.Label(sz, foreground="#666", justify="left",
                  text="(If higher resolution output than source, Lanczos (CPU) used to upscale.\n"
                       " For HDR/DV, Spline36 (GPU, libplacebo) used)").pack(side="left")

        ttk.Label(f2, text="Fit:").grid(row=1, column=0, sticky="w", **pad)
        self.v_fit = tk.StringVar(value=FIT_MODES[self.s["fit"]])
        ttk.Combobox(f2, textvariable=self.v_fit, state="readonly", width=32,
                     values=list(FIT_MODES.values())).grid(row=1, column=1, sticky="w", **pad)
        self.v_swap = tk.BooleanVar(value=self.s["swap"])
        ttk.Checkbutton(f2, text="Swap eyes (source is right-left)", variable=self.v_swap).grid(
            row=1, column=2, columnspan=2, sticky="w", **pad)

        ttk.Label(f2, text="Encoder:").grid(row=2, column=0, sticky="w", **pad)
        self.v_enc = tk.StringVar(value=ENCODERS[self.s["encoder"]][0])
        self.cb_enc = ttk.Combobox(f2, textvariable=self.v_enc, state="readonly", width=40,
                                   values=[ENCODERS[e][0] for e in ENCODERS])
        self.cb_enc.grid(row=2, column=1, sticky="w", **pad)
        self.cb_enc.bind("<<ComboboxSelected>>", lambda e: self._enc_changed(True))
        ef = ttk.Frame(f2)
        ef.grid(row=2, column=2, columnspan=2, sticky="w")
        ttk.Label(ef, text="Preset:").pack(side="left")
        self.v_preset = tk.StringVar(value=preset_label(self.s["encoder"], self.s["preset"]))
        self.cb_preset = ttk.Combobox(ef, textvariable=self.v_preset, state="readonly", width=30)
        self.cb_preset.pack(side="left", padx=4)
        self.l_q = ttk.Label(ef, text="CRF:")
        self.l_q.pack(side="left", padx=(10, 0))
        self.v_q = tk.IntVar(value=self.s["quality"])
        ttk.Spinbox(ef, from_=0, to=51, textvariable=self.v_q, width=5).pack(side="left", padx=4)
        ttk.Label(ef, text="(lower = better)", foreground="#666").pack(side="left")

        ttk.Label(f2, text="Bit depth:").grid(row=3, column=0, sticky="w", **pad)
        self.v_bd = tk.StringVar(value=BITDEPTHS[self.s["bitdepth"]])
        ttk.Combobox(f2, textvariable=self.v_bd, state="readonly", width=20,
                     values=list(BITDEPTHS.values())).grid(row=3, column=1, sticky="w", **pad)
        af = ttk.Frame(f2)
        af.grid(row=3, column=2, columnspan=2, sticky="w")
        ttk.Label(af, text="Audio:").pack(side="left")
        self.v_audio = tk.StringVar(value=AUDIO_MODES[self.s["audio"]])
        ttk.Combobox(af, textvariable=self.v_audio, state="readonly", width=38,
                     values=list(AUDIO_MODES.values())).pack(side="left", padx=4)

        self.v_subs = tk.BooleanVar(value=self.s["subs"])
        self.v_hw = tk.BooleanVar(value=self.s["hwdec"])
        of = ttk.Frame(f2)
        of.grid(row=4, column=1, columnspan=4, sticky="w")
        ttk.Checkbutton(of, text="Keep subtitles", variable=self.v_subs).pack(side="left", padx=(6, 12))
        ttk.Checkbutton(of, text="Hardware decoding (non MV-HEVC)", variable=self.v_hw).pack(side="left")
        ttk.Label(of, text="   Crop top & bottom of each eye:").pack(side="left")
        self.v_ctb = tk.IntVar(value=int(self.s.get("crop_tb", 0)))
        ttk.Spinbox(of, from_=0, to=540, increment=2, textvariable=self.v_ctb, width=5).pack(side="left", padx=4)
        ttk.Label(of, text="px extra (the file's own crop is automatic)",
                  foreground="#666").pack(side="left")

        ttk.Label(f2, text="Save to:").grid(row=5, column=0, sticky="w", **pad)
        self.v_out = tk.StringVar(value=self.s["outdir"])
        oe = ttk.Frame(f2)
        oe.grid(row=5, column=1, columnspan=4, sticky="ew", **pad)
        ttk.Entry(oe, textvariable=self.v_out).pack(side="left", fill="x", expand=True)
        ttk.Button(oe, text="Browse…", command=self._browse_out).pack(side="left", padx=4)
        ttk.Label(oe, text="(empty = next to source)", foreground="#666").pack(side="left")
        f2.columnconfigure(3, weight=1)
        try:
            self._logo = tk.PhotoImage(data=LOGO_PNG_B64)
            ttk.Label(f2, image=self._logo).grid(row=1, column=4, rowspan=3, sticky="ne", padx=(4, 8), pady=(0, 2))
        except tk.TclError:
            pass

        # HDR -> SDR
        fh = ttk.LabelFrame(r, text="HDR / Dolby Vision → SDR")
        fh.pack(fill="x", **pad)
        ttk.Label(fh, text="HDR handling:").grid(row=0, column=0, sticky="w", **pad)
        self.v_tm = tk.StringVar(value=TONEMAP_MODES[self.s["tonemap"]])
        hdr_w = fit_width(list(TONEMAP_MODES.values()) + list(SDR_NITS.values()))
        ttk.Combobox(fh, textvariable=self.v_tm, state="readonly", width=hdr_w,
                     values=list(TONEMAP_MODES.values())).grid(row=0, column=1, sticky="w", **pad)
        ttk.Label(fh, text="Method:").grid(row=0, column=2, sticky="e", **pad)
        self.v_tme = tk.StringVar(value=TM_ENGINES[self.s["tm_engine"]])
        cbm = ttk.Combobox(fh, textvariable=self.v_tme, state="readonly", width=fit_width(TM_ENGINES.values()),
                           values=list(TM_ENGINES.values()))
        cbm.grid(row=0, column=3, sticky="w", **pad)
        cbm.bind("<<ComboboxSelected>>", lambda e: self._method_changed(True))

        ttk.Label(fh, text="HDR → SDR brightness:").grid(row=1, column=0, sticky="w", **pad)
        self.v_nits = tk.StringVar(value=SDR_NITS.get(int(self.s["sdr_nits"]), SDR_NITS[75]))
        self.cb_nits = ttk.Combobox(fh, textvariable=self.v_nits, state="readonly", width=hdr_w,
                                    values=list(SDR_NITS.values()))
        self.cb_nits.grid(row=1, column=1, sticky="w", **pad)
        ttk.Label(fh, text="SDR brightness boost:").grid(row=1, column=2, sticky="e", **pad)
        bf2 = ttk.Frame(fh)
        bf2.grid(row=1, column=3, sticky="w")
        self.v_boost = tk.StringVar(value=BOOSTS[self.s["boost"]][0])
        ttk.Combobox(bf2, textvariable=self.v_boost, state="readonly", width=14,
                     values=[b[0] for b in BOOSTS.values()]).pack(side="left", padx=6)
        ttk.Label(bf2, text="Saturation:").pack(side="left", padx=(8, 0))
        self.v_sat = tk.DoubleVar(value=float(self.s["sdr_sat"]))
        ttk.Spinbox(bf2, from_=0.5, to=2.0, increment=0.05, format="%.2f", textvariable=self.v_sat,
                    width=5).pack(side="left", padx=4)

        ttk.Label(fh, text="Curve:").grid(row=2, column=0, sticky="w", **pad)
        hf = ttk.Frame(fh)
        hf.grid(row=2, column=1, columnspan=3, sticky="w")
        self.v_curve = tk.StringVar(value=self.s["tm_curve"])
        self.cb_curve = ttk.Combobox(hf, textvariable=self.v_curve, state="readonly", width=11)
        self.cb_curve.pack(side="left", padx=(6, 12))
        self.l_peak = ttk.Label(hf, text="Highlights:")
        self.l_peak.pack(side="left")
        self.v_peak = tk.StringVar(value=PEAK_MODES[self.s["peak"]][0])
        self.cb_peak = ttk.Combobox(hf, textvariable=self.v_peak, state="readonly", width=30,
                                    values=[v[0] for v in PEAK_MODES.values()])
        self.cb_peak.pack(side="left", padx=(4, 12))
        ttk.Label(fh, text="Lower nits = brighter picture, which helps offset the light lost through 3D glasses. "
                           "Boost lifts midtones further. Use Preview frame to compare.",
                  foreground="#666").grid(row=3, column=1, columnspan=3, sticky="w", padx=6)
        ttk.Label(fh, text="GPU (Vulkan):").grid(row=4, column=0, sticky="w", **pad)
        gf = ttk.Frame(fh)
        gf.grid(row=4, column=1, columnspan=3, sticky="w")
        self.v_vk = tk.StringVar(value=self.s.get("vk_device", "auto"))
        ttk.Entry(gf, textvariable=self.v_vk, width=16).pack(side="left", padx=6)
        ttk.Label(gf, text="auto = NVIDIA card if present. Or type part of the GPU name, e.g. RTX 5080",
                  foreground="#666").pack(side="left")
        self._method_changed(False)

        # actions / progress
        f3 = ttk.Frame(r)
        f3.pack(fill="x", **pad)
        self.b_start = PillButton(f3, "CONVERT!", self._start)
        self.b_start.pack(side="left", padx=(0, 8))
        self.b_cancel = ttk.Button(f3, text="Cancel", command=self._cancel, state="disabled")
        self.b_cancel.pack(side="left", padx=4)
        ttk.Button(f3, text="Show ffmpeg command", command=self._show_cmd).pack(side="left", padx=4)
        ttk.Separator(f3, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Label(f3, text="at").pack(side="left")
        self.v_pat = tk.StringVar(value=self.s.get("preview_at", "00:20:00"))
        ttk.Entry(f3, textvariable=self.v_pat, width=9).pack(side="left", padx=4)
        self.b_prev = ttk.Button(f3, text="🖼  Preview frame", command=self._preview)
        self.b_prev.pack(side="left")
        ttk.Label(f3, text="(of what output will look like)", foreground="#666").pack(side="left", padx=(4, 0))
        ttk.Separator(f3, orient="vertical").pack(side="left", fill="y", padx=(10, 0))
        self.l_stat = ttk.Label(f3, text="Ready")
        self.l_stat.pack(side="left", padx=10)
        self._status("Ready")

        f4 = ttk.Frame(r)
        f4.pack(fill="x", **pad)
        ttk.Label(f4, text="Current:", width=8).grid(row=0, column=0, sticky="w")
        self.pb1 = ttk.Progressbar(f4, maximum=1000)
        self.pb1.grid(row=0, column=1, sticky="ew")
        ttk.Label(f4, text="Overall:", width=8).grid(row=1, column=0, sticky="w")
        self.pb2 = ttk.Progressbar(f4, maximum=1000)
        self.pb2.grid(row=1, column=1, sticky="ew", pady=2)
        f4.columnconfigure(1, weight=1)

        f5 = ttk.LabelFrame(r, text="Log")
        f5.pack(fill="both", expand=True, **pad)
        self.log = ScrolledText(f5, height=9, font=("Consolas" if IS_WIN else "monospace", 9), wrap="word")
        self.log.pack(fill="both", expand=True, padx=4, pady=4)
        self.log.configure(state="disabled")

        self._enc_changed(False)

    def _enable_dnd(self):
        """Drag & drop files/folders from Explorer onto the window (native Windows, no extra packages)."""
        def dropped(paths):
            self.root.after(10, lambda: self._add_paths(expand_dropped(paths)))
        if IS_WIN:
            try:
                self.root.update_idletasks()
                enable_windows_drop(self.root, dropped)
            except Exception:
                pass   # drag & drop unavailable; "Add files…" still works

    # ---- helpers
    def _key(self, mapping, label):
        for k, v in mapping.items():
            if v == label:
                return k
        return next(iter(mapping))

    def _enc_key(self):
        for k, v in ENCODERS.items():
            if v[0] == self.v_enc.get():
                return k
        return "libx265"

    def _enc_changed(self, reset):
        e = ENCODERS[self._enc_key()]
        enc = self._enc_key()
        labels = [preset_label(enc, p) for p in e[1]]
        self.cb_preset.configure(values=labels)
        cur = preset_from_label(self.v_preset.get())
        if reset or cur not in e[1]:
            cur = e[2]
        self.v_preset.set(preset_label(enc, cur))
        if reset:
            self.v_q.set(e[3])
        self.l_q.configure(text=e[4] + ":")

    STATUS_COLORS = {"ok": "#1a8f3c", "busy": "#000000", "error": "#c00000"}

    def _status(self, text, kind=None):
        """Status text next to the buttons: green when ready/finished OK, red on failures."""
        if kind is None:
            kind = "ok" if text.startswith("Ready") else "busy"
        self.l_stat.configure(text=text, foreground=self.STATUS_COLORS[kind])

    def _logline(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        n = int(self.log.index("end-1c").split(".")[0])
        if n > 3000:
            self.log.delete("1.0", "%d.0" % (n - 3000))
        self.log.see("end")
        self.log.configure(state="disabled")

    def _set_ffmpeg(self, path, quiet=False):
        self.v_ff.set(path or "")
        if path and quiet and path == getattr(self, "_checked_ff", None) and self.ffprobe:
            return   # already checked this ffmpeg
        if path and os.path.isfile(path):
            self._checked_ff = path
            self.ffprobe = ffprobe_for(path)
            ver = ffmpeg_version(path)
            encs = available_encoders(path)
            missing = [ENCODERS[e][0].split("(")[0].strip() + " " + e for e in ENCODERS if e not in encs]
            txt = ver + ("" if self.ffprobe else "   ⚠ ffprobe not found next to ffmpeg")
            self.l_ver.configure(text=txt, foreground="#2a6" if self.ffprobe else "#c60")
            self.cb_enc.configure(values=[ENCODERS[e][0] for e in ENCODERS if e in encs] or
                                  [ENCODERS[e][0] for e in ENCODERS])
            self.s["ffmpeg"] = path
            if not quiet:
                self._logline("Using " + ver)
            if missing and not quiet:
                self._logline("Encoders not in this build: " + ", ".join(e.split()[-1] for e in missing))
        else:
            self.ffprobe = ""
            self.l_ver.configure(text="ffmpeg not found - extract your ffmpeg download, then click "
                                      "'Browse ffmpeg.exe…' and pick bin\\ffmpeg.exe", foreground="#c00")

    # ---- actions
    def _browse_ff(self):
        p = filedialog.askopenfilename(title="Select ffmpeg executable",
                                       filetypes=[("ffmpeg", "ffmpeg.exe ffmpeg"), ("All files", "*.*")])
        if p:
            self._set_ffmpeg(p)

    def _about(self):
        w = tk.Toplevel(self.root)
        w.title("About")
        w.resizable(False, False)
        w.transient(self.root)
        fr = ttk.Frame(w, padding=(24, 18, 24, 14))
        fr.pack(fill="both", expand=True)
        try:
            ttk.Label(fr, image=self._icon).pack()
        except Exception:
            pass
        ttk.Label(fr, text=APP_NAME, font=("Segoe UI", 12, "bold")).pack(pady=(6, 2))
        ttk.Label(fr, text="By ht2tweak and Claude AI, v%s" % APP_VERSION).pack()
        ttk.Label(fr, text="2026").pack(pady=(0, 14))
        ok = ttk.Button(fr, text="OK", width=10, command=w.destroy)
        ok.pack()
        w.bind("<Return>", lambda e: w.destroy())
        w.bind("<Escape>", lambda e: w.destroy())
        w.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - w.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - w.winfo_height()) // 3
        w.geometry("+%d+%d" % (max(0, x), max(0, y)))
        ok.focus_set()
        w.grab_set()

    def _frim_status(self):
        p = self.v_frim.get().strip()
        if p and os.path.isfile(p):
            self.l_frim.configure(text="FRIM ready - Blu-ray 3D (MVC) files can be converted", foreground="#2a6")
        else:
            self.l_frim.configure(text="FRIM not set (only needed for Blu-ray 3D MVC files)", foreground="#888")

    def _browse_frim(self):
        p = filedialog.askopenfilename(title="Select FRIMDecode64.exe",
                                       filetypes=[("FRIM decoder", "FRIMDecode64.exe FRIMDecode.exe"),
                                                  ("All files", "*.*")])
        if p:
            self.v_frim.set(p)
            self._frim_status()

    def _browse_out(self):
        d = filedialog.askdirectory(title="Output folder")
        if d:
            self.v_out.set(d)

    def _add_files(self):
        ps = filedialog.askopenfilenames(
            title="Select 3D videos",
            filetypes=[("Video", " ".join("*" + e for e in sorted(VIDEO_EXTS))),
                       ("All files", "*.*")])
        self._add_paths(ps)

    def _add_paths(self, paths):
        if not self.ffprobe:
            messagebox.showwarning(APP_NAME, "Set up ffmpeg first (ffprobe is needed to read the files).")
            return
        for p in paths:
            p = os.path.abspath(p)
            if not os.path.isfile(p) or any(f["path"] == p for f in self.files):
                continue
            if os.path.splitext(p)[1].lower() not in VIDEO_EXTS:
                self._logline("Skipped (not a video file): " + os.path.basename(p))
                continue
            iid = self.tree.insert("", "end", values=(os.path.basename(p), "…", "", "probing…", "Waiting"))
            f = {"path": p, "info": None, "layout": None, "forced": None, "iid": iid}
            self.files.append(f)
            threading.Thread(target=self._probe_file, args=(f,), daemon=True).start()

    def _probe_file(self, f):
        try:
            info = probe(self.ffprobe, f["path"])
            lay, why = detect_layout(info, f["path"], lambda: has_second_view(self.v_ff.get().strip(), f["path"]))
            self.q.put(("probed", (f, info, lay, why, None)))
        except Exception as e:
            self.q.put(("probed", (f, None, None, None, str(e))))

    def _remove(self):
        sel = set(self.tree.selection())
        for iid in sel:
            self.tree.delete(iid)
        self.files = [f for f in self.files if f["iid"] not in sel]

    def _clear(self):
        if self.worker:
            return
        self.tree.delete(*self.tree.get_children())
        self.files = []

    def _apply_override(self):
        k = self._key(LAYOUTS, self.v_override.get())
        for f in self.files:
            if f["iid"] in self.tree.selection():
                f["forced"] = None if k == "auto" else k
                self._refresh_row(f)

    def _refresh_row(self, f, status=None):
        if not self.tree.exists(f["iid"]):   # file was removed from the list meanwhile
            return
        vals = list(self.tree.item(f["iid"], "values"))
        if f.get("info"):
            v = main_video(f["info"]) or {}
            vals[1] = "%sx%s" % (v.get("width", "?"), v.get("height", "?"))
            hi = hdr_info(v)
            vals[2] = v.get("codec_name", "") + (" DV%s" % hi["dv_profile"] if hi["dv_profile"] is not None
                                                 else " HDR" if hi["hdr"] else "")
        lay = f["forced"] or f["layout"]
        if lay:
            vals[3] = LAYOUT_SHORT[lay] + ("  (set by you)" if f["forced"] else "  (%s)" % f.get("why", ""))
        if status is not None:
            vals[4] = status
        self.tree.item(f["iid"], values=vals)

    def _opts(self):
        sizes = [k for k, var in (("3840", self.v_s3840), ("7680", self.v_s7680)) if var.get()]
        try:
            q = max(0, min(51, int(self.v_q.get())))
        except (tk.TclError, ValueError):
            q = ENCODERS[self._enc_key()][3]
            self.v_q.set(q)
        o = {
            "ffmpeg": self.v_ff.get().strip(), "layout": "auto", "sizes": sizes,
            "fit": self._key(FIT_MODES, self.v_fit.get()), "swap": bool(self.v_swap.get()),
            "encoder": self._enc_key(), "preset": preset_from_label(self.v_preset.get()), "quality": q,
            "bitdepth": self._key(BITDEPTHS, self.v_bd.get()), "audio": self._key(AUDIO_MODES, self.v_audio.get()),
            "subs": bool(self.v_subs.get()), "outdir": self.v_out.get().strip(), "hwdec": bool(self.v_hw.get()),
            "tonemap": self._key(TONEMAP_MODES, self.v_tm.get()), "tm_engine": self._key(TM_ENGINES, self.v_tme.get()),
            "tm_curve": self.v_curve.get() or "spline",
            "peak": next((k for k, v in PEAK_MODES.items() if v[0] == self.v_peak.get()), "brighter"),
            "boost": next((k for k, v in BOOSTS.items() if v[0] == self.v_boost.get()), "off"),
            "sdr_nits": next((k for k, v in SDR_NITS.items() if v == self.v_nits.get()), 75),
            "sdr_sat": self._num(self.v_sat, 1.0, 0.0, 3.0),
            "crop_tb": int(self._num(self.v_ctb, 0, 0, 1000)),
            "frim": self.v_frim.get().strip(), "frim_args": self.v_frim_args.get().strip() or DEFAULTS["frim_args"], "vk_device": self.v_vk.get().strip() or "auto", "preview_at": self.v_pat.get().strip() or "0",
        }
        o["sdr_gamma"] = BOOSTS[o["boost"]][1]
        self.s.update(o)
        save_settings(self.s)
        return o

    def _method_changed(self, reset):
        m = self._key(TM_ENGINES, self.v_tme.get())
        curves = ADAPTIVE_CURVES if m == "libplacebo" else ZSCALE_CURVES
        self.cb_curve.configure(values=curves)
        if reset or self.v_curve.get() not in curves:
            self.v_curve.set(curves[0])
        adaptive = m == "libplacebo"
        self.cb_nits.configure(state="disabled" if adaptive else "readonly")
        self.cb_peak.configure(state="readonly" if adaptive else "disabled")

    def _num(self, var, default, lo, hi):
        try:
            return max(lo, min(hi, float(var.get())))
        except (tk.TclError, ValueError):
            var.set(default)
            return default

    def _preview(self):
        o = self._opts()
        if not os.path.isfile(o["ffmpeg"]):
            messagebox.showerror(APP_NAME, "Set up ffmpeg first.")
            return
        sel = [f for f in self.files if f["iid"] in self.tree.selection()] or self.files[:1]
        if not sel or not sel[0].get("info"):
            messagebox.showinfo(APP_NAME, "Add (and select) a file first.")
            return
        f = sel[0]
        try:
            at = parse_time(o["preview_at"])
        except ValueError:
            messagebox.showerror(APP_NAME, "Preview time should look like 00:20:00")
            return
        try:
            dur = float(f["info"].get("format", {}).get("duration") or 0)
            if dur and at >= dur:
                at = dur * 0.2
        except ValueError:
            pass
        size = (o["sizes"] or ["3840"])[0]
        oo = dict(o, layout=f["forced"] or f["layout"], size=size)
        png = os.path.join(tempfile.gettempdir(), "fsbs_preview_%d.png" % int(time.time() * 1000))
        self._previews.append(png)
        self.b_prev.configure(state="disabled")
        self._status("Rendering preview at %s…" % fmt_time(at))

        def job():
            try:
                out = render_preview(o["ffmpeg"], f["path"], f["info"], oo, at, png,
                                     log=lambda m: self.q.put(("log", m)))
                self.q.put(("preview", (out, None, os.path.basename(f["path"]), at, oo)))
            except Exception as e:
                self.q.put(("preview", (None, str(e), "", at, oo)))
        threading.Thread(target=job, daemon=True).start()

    def _show_preview(self, png, name, at, oo):
        w = tk.Toplevel(self.root)
        if oo.get("tonemap") == "off":
            tm = "no tone mapping"
        elif oo.get("tm_engine") == "libplacebo":
            tm = "SDR adaptive (%s, boost %s, saturation %.2f)" % (oo["tm_curve"], BOOSTS[oo["boost"]][0],
                                                                   oo["sdr_sat"])
        else:
            tm = "SDR %s nits (%s, boost %s, saturation %.2f)" % (oo["sdr_nits"], oo["tm_curve"],
                                                                  BOOSTS[oo["boost"]][0], oo["sdr_sat"])
        w.title("Preview - %s @ %s - %s" % (name, fmt_time(at), tm))
        try:
            img = tk.PhotoImage(file=png)
            sw = self.root.winfo_screenwidth() - 80
            if img.width() > sw:
                img = img.subsample(2, 2)
            lbl = ttk.Label(w, image=img)
            lbl.image = img
            lbl.pack()
        except tk.TclError as e:
            ttk.Label(w, text="Can't display image: %s" % e).pack()
        bf = ttk.Frame(w)
        bf.pack(fill="x", pady=4)
        ttk.Label(bf, text="Left eye | Right eye.  Change the nits / boost / curve and preview again "
                           "to compare.").pack(side="left", padx=6)
        if IS_WIN:
            ttk.Button(bf, text="Open full size", command=lambda: os.startfile(png)).pack(side="right", padx=6)

    def _show_cmd(self):
        o = self._opts()
        sel = [f for f in self.files if f["iid"] in self.tree.selection()] or self.files[:1]
        if not sel or not sel[0].get("info"):
            messagebox.showinfo(APP_NAME, "Add (and select) a file first.")
            return
        f = sel[0]
        size = (o["sizes"] or ["3840"])[0]
        oo = dict(o, layout=f["forced"] or f["layout"], size=size)
        dst = output_path(f["path"], o["outdir"], size)
        if oo["layout"] == "mvc":
            es = os.path.splitext(dst)[0] + ".mvc_temp.h264"
            frim = find_frim(o.get("frim", "")) or "FRIMDecode64.exe"
            cmd2, notes = build_mvc_command(o["ffmpeg"], f["path"], dst, f["info"], oo, "-")
            text = ("1) ffmpeg extracts the 3D video stream to:\n%s\n\n2) %s\n   |  (piped into)\n%s"
                    % (es, quote_cmd(frim_cmd(frim, o.get("frim_args"), es, "-")), quote_cmd(cmd2)))
        else:
            cmd, notes = build_command(o["ffmpeg"], f["path"], dst, f["info"], oo)
            text = quote_cmd(cmd)
        w = tk.Toplevel(self.root)
        w.title("ffmpeg command")
        t = tk.Text(w, wrap="word", width=110, height=14)
        t.pack(fill="both", expand=True)
        t.insert("1.0", text + ("\n\n" + "\n".join(notes) if notes else ""))

    def _start(self):
        o = self._opts()
        if not os.path.isfile(o["ffmpeg"]):
            messagebox.showerror(APP_NAME, "ffmpeg not found. Click 'Browse ffmpeg.exe…' and pick bin\\ffmpeg.exe from your extracted ffmpeg folder.")
            return
        self._set_ffmpeg(o["ffmpeg"], quiet=True)
        if not o["sizes"]:
            messagebox.showerror(APP_NAME, "Tick at least one output size.")
            return
        jobs = [f for f in self.files if f.get("info")]
        if not jobs:
            messagebox.showerror(APP_NAME, "Add some videos first.")
            return
        # pre-flight
        if any((f["forced"] or f["layout"]) == "mvc" for f in jobs) and not find_frim(o.get("frim", "")):
            messagebox.showerror(APP_NAME, FRIM_MISSING_MSG)
            return
        maxw = ENCODERS[o["encoder"]][5]
        if "7680" in o["sizes"] and maxw < 7680:
            messagebox.showerror(APP_NAME, "%s can't encode 7680-wide video. Choose an HEVC or AV1 encoder, "
                                           "or untick 7680×2160." % ENCODERS[o["encoder"]][0])
            return
        existing = [output_path(f["path"], o["outdir"], s) for f in jobs for s in o["sizes"]]
        existing = [p for p in existing if os.path.exists(p)]
        if existing and not messagebox.askyesno(APP_NAME, "%d output file(s) already exist. Overwrite?\n\n%s"
                                                % (len(existing), "\n".join(existing[:6]))):
            return
        self.cancel_event.clear()
        self.b_start.set_state("disabled")
        self.b_cancel.configure(state="normal")
        self.worker = threading.Thread(target=self._work, args=(jobs, o), daemon=True)
        self.worker.start()

    def _work(self, jobs, o):
        total = len(jobs) * len(o["sizes"])
        done = 0
        ok = fail = 0
        t0 = time.time()
        for f in jobs:
            for size in o["sizes"]:
                if self.cancel_event.is_set():
                    break
                W, H = OUTPUT_SIZES[size]
                label = "%dx%d" % (W * 2, H)
                self.q.put(("row", (f, "Converting %s…" % label)))
                self.q.put(("log", "\n=== %s  ->  FSBS %s ===" % (os.path.basename(f["path"]), label)))
                oo = dict(o, layout=f["forced"] or f["layout"] or "auto")
                base = done

                def prog(frac, speed, eta, base=base, label=label):
                    self.q.put(("prog", (frac, (base + frac) / total, "%s  %s  %s" % (
                        label, ("speed " + speed) if speed else "", ("ETA " + eta) if eta else ""))))
                try:
                    dst = convert_one(o["ffmpeg"], self.ffprobe, f["path"], size, oo, prog,
                                      lambda m: self.q.put(("log", m)), self.cancel_event)
                    ok += 1
                    self.q.put(("log", "✔ Saved: " + dst))
                    self.q.put(("row", (f, "Done")))
                except Cancelled:
                    self.q.put(("row", (f, "Cancelled")))
                    self.q.put(("log", "Cancelled."))
                    break
                except Exception as e:
                    fail += 1
                    self.q.put(("row", (f, "Failed")))
                    self.q.put(("log", "✖ " + str(e)))
                done += 1
                self.q.put(("prog", (0, done / total, "")))
        self.q.put(("finished", (ok, fail, time.time() - t0)))

    def _cancel(self):
        self.cancel_event.set()
        self._status("Cancelling…")

    def _poll(self):
        try:
            while True:
                kind, data = self.q.get_nowait()
                try:
                    self._handle(kind, data)
                except Exception as e:   # never let one bad message stop the update loop
                    self._logline("Internal error: %s" % e)
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def _handle(self, kind, data):
        """Apply one message from the worker/probe/preview threads to the GUI (main thread only)."""
        if kind == "log":
            self._logline(data)
        elif kind == "prog":
            a, b, txt = data
            self.pb1["value"] = a * 1000
            self.pb2["value"] = b * 1000
            if txt:
                self._status(txt)
        elif kind == "row":
            self._refresh_row(data[0], data[1])
        elif kind == "probed":
            f, info, lay, why, err = data
            if err:
                self._refresh_row(f, "Can't read file")
                self._logline("✖ %s: %s" % (os.path.basename(f["path"]), err))
            else:
                f["info"], f["layout"], f["why"] = info, lay, why
                self._refresh_row(f, "Ready")
        elif kind == "preview":
            png, err, name, at, oo = data
            self.b_prev.configure(state="normal")
            if not self.worker:
                self._status("Ready")
            if err:
                self._logline("✖ Preview failed: " + err)
                messagebox.showerror(APP_NAME, "Preview failed:\n\n" + err[-1200:])
            else:
                self._show_preview(png, name, at, oo)
        elif kind == "finished":
            ok, fail, secs = data
            self.worker = None
            self.b_start.set_state("normal")
            self.b_cancel.configure(state="disabled")
            self.pb1["value"] = 0
            msg = "Finished: %d done, %d failed (%s)" % (ok, fail, fmt_time(secs))
            self._status(msg, "error" if fail else "ok")
            self._logline(msg)

    def _on_close(self):
        if self.worker and not messagebox.askyesno(APP_NAME, "A conversion is running. Stop it and quit?"):
            return
        self.cancel_event.set()
        try:
            self._opts()
        except Exception:
            pass
        for png in self._previews:
            _remove_quietly(png)
        self._close_when_idle(time.time() + 10)

    def _close_when_idle(self, deadline):
        """Wait (max ~10 s) for the conversion thread to stop ffmpeg/FRIM and delete partial files."""
        if self.worker and self.worker.is_alive() and time.time() < deadline:
            self._status("Stopping conversion…")
            self.root.after(200, lambda: self._close_when_idle(deadline))
        else:
            self.root.destroy()

    def run(self):
        self.root.mainloop()

# ----------------------------------------------------------------------------- CLI


def cli(argv):
    import argparse
    ap = argparse.ArgumentParser(description="Convert 3D video to FSBS MKV")
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--ffmpeg", default="")
    ap.add_argument("--size", action="append", choices=list(OUTPUT_SIZES), help="3840 and/or 7680")
    ap.add_argument("--layout", default="auto", choices=list(LAYOUTS))
    ap.add_argument("--fit", default="pad", choices=list(FIT_MODES))
    ap.add_argument("--swap", action="store_true")
    ap.add_argument("--encoder", default="libx265", choices=list(ENCODERS))
    ap.add_argument("--preset", default=None)
    ap.add_argument("--quality", type=int, default=None)
    ap.add_argument("--bitdepth", default="auto", choices=list(BITDEPTHS))
    ap.add_argument("--audio", default="copy", choices=list(AUDIO_MODES))
    ap.add_argument("--no-subs", action="store_true")
    ap.add_argument("--outdir", default="")
    ap.add_argument("--tonemap", default="auto", choices=list(TONEMAP_MODES))
    ap.add_argument("--tm-engine", default="nits", choices=list(TM_ENGINES))
    ap.add_argument("--tm-curve", default="mobius", choices=TM_CURVES)
    ap.add_argument("--nits", type=int, default=75, help="HDR nits that become SDR white (lower = brighter)")
    ap.add_argument("--peak", default="brighter", choices=list(PEAK_MODES))
    ap.add_argument("--brightness", type=float, default=1.0, help="extra SDR gamma boost, 1.0 = off")
    ap.add_argument("--saturation", type=float, default=1.0, help="1.0 = neutral")
    ap.add_argument("--gpu", default="auto", help="Vulkan GPU for libplacebo: auto, index, or name part")
    ap.add_argument("--crop-tb", type=int, default=0, help="pixels to crop top+bottom of each eye")
    ap.add_argument("--preview", default=None, help="render one PNG frame at this time (e.g. 00:20:00)")
    ap.add_argument("--print-cmd", action="store_true", help="only print the ffmpeg command")
    a = ap.parse_args(argv)
    ff = find_ffmpeg(a.ffmpeg)
    if not ff:
        sys.exit("ffmpeg not found (use --ffmpeg)")
    fp = ffprobe_for(ff)
    e = ENCODERS[a.encoder]
    opts = dict(layout=a.layout, fit=a.fit, swap=a.swap, encoder=a.encoder, preset=a.preset or e[2],
                quality=e[3] if a.quality is None else a.quality, bitdepth=a.bitdepth, audio=a.audio,
                subs=not a.no_subs, outdir=a.outdir, hwdec=False, tonemap=a.tonemap, tm_engine=a.tm_engine,
                tm_curve=a.tm_curve, peak=a.peak, sdr_gamma=a.brightness, sdr_nits=a.nits, sdr_sat=a.saturation,
                crop_tb=a.crop_tb, vk_device=a.gpu)
    rc = 0
    for src in a.inputs:
        for size in (a.size or ["3840"]):
            if a.preview:
                info = probe(fp, src)
                lay = a.layout if a.layout != "auto" else detect_layout(info, src, lambda: has_second_view(ff, src))[0]
                png = os.path.splitext(output_path(src, a.outdir, size))[0] + "_preview.png"
                print("Preview ->", render_preview(ff, src, info, dict(opts, layout=lay, size=size),
                                                   parse_time(a.preview), png))
                continue
            if a.print_cmd:
                info = probe(fp, src)
                lay = a.layout if a.layout != "auto" else detect_layout(info, src, lambda: has_second_view(ff, src))[0]
                o2 = dict(opts, layout=lay, size=size)
                dst = output_path(src, a.outdir, size)
                if lay == "mvc":
                    es = os.path.splitext(dst)[0] + ".mvc_temp.h264"
                    print(quote_cmd(frim_cmd(find_frim() or "FRIMDecode64.exe", None, es, "-")) + " | " +
                          quote_cmd(build_mvc_command(ff, src, dst, info, o2, "-")[0]))
                else:
                    print(quote_cmd(build_command(ff, src, dst, info, o2)[0]))
                continue
            last = [0.0]

            def prog(frac, speed, eta):
                if frac - last[0] >= 0.1 or frac >= 1.0:
                    last[0] = frac
                    print("  %3d%%  %s  ETA %s" % (frac * 100, speed, eta or "-"))
            try:
                out = convert_one(ff, fp, src, size, opts, prog,
                                  lambda m: print("  " + m) if not m.startswith(("frame=", "  ")) else None,
                                  threading.Event())
                print("OK ->", out)
            except Exception as ex:
                print("FAILED:", ex)
                rc = 1
    return rc


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        sys.exit(cli(sys.argv[2:]))
    if tk is None:
        sys.exit("tkinter is not available. Install Python from python.org (includes tkinter) "
                 "or use --cli.")
    App().run()


if __name__ == "__main__":
    main()
