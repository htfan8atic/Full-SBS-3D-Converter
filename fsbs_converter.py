#!/usr/bin/env python3
"""
Full 3D FSBS and MVC Converter v1.1 - 3D MV-HEVC, Top/bottom or MVC Formats to FSBS Converter
By ht2tweak and Claude AI.

Converts 3D video to Full Side-by-Side (FSBS) .mkv using ffmpeg (and FRIM for Blu-ray 3D MVC).
Input  : MV-HEVC (Apple spatial / Vision Pro / Dolby Vision 3D), Half/Full SBS, Half/Full Top-Bottom,
         H.264 MVC (Blu-ray 3D, via FRIM)
Output : 3840x1080 FSBS (1920x1080 per eye) and/or 7680x2160 FSBS (3840x2160 per eye),
         Matroska tagged stereo_mode=left_right; optional HDR / Dolby Vision -> SDR tone mapping.

GUI : python fsbs_converter.py
CLI : python fsbs_converter.py --cli INPUT [INPUT...] --size 3840 [--size 7680] ...
"""

import fractions
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

APP_NAME = "Full 3D FSBS and MVC Converter"
APP_VERSION = "1.1"
IS_WIN = os.name == "nt"
NO_WINDOW = 0x08000000 if IS_WIN else 0  # CREATE_NO_WINDOW
EXE = ".exe" if IS_WIN else ""
SCRIPT_DIR = os.path.dirname(os.path.abspath(sys.argv[0] if getattr(sys, "frozen", False) else __file__))
# 64x64 "eyeglasses" icon (Noto Color Emoji U+1F453, Apache-2.0)
ICON_PNG_B64 = "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"
# "FSBS + MVC 3D CONVERTER" logo shown in the Output section (96 px tall, transparent PNG)
LOGO_PNG_B64 = "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"
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".fsbs_converter.json")

# ----------------------------------------------------------------------------- constants

OUTPUT_SIZES = {
    "3840": (1920, 1080),   # per-eye size -> 3840x1080 FSBS
    "7680": (3840, 2160),   # per-eye size -> 7680x2160 FSBS
    "mvc":  (1920, 1080),   # per-eye size -> H.264 MVC MKV (Blu-ray 3D style)
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
    "mvc_out": False, "mvc_encoder": "x264mvc", "mvc_preset": "slow", "mvc_crf": 18, "mvc_kbps": 28000,
    "x264mvc": "",
    "x264mvc_args": ("--mvc --mvc-layout sbs --demuxer y4m --preset {preset} --crf {crf} --bframes 0 --aud "
                     "--keyint 24 --level 4.1 --vbv-maxrate 40000 --vbv-bufsize 30000 --colorprim bt709 "
                     "--transfer bt709 --colormatrix bt709 --sar 1:1 -o {out} -"),
    "frimenc_args": ("-i {left} {right} -o:mvc {out} -w {w} -h {h} -f {fps} -vbr {kbps} {maxkbps} "
                     "-gop 24 1 -level 4.1 -u 4 -sw"),
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
    if s.get("mvc_encoder") not in MVC_ENCODERS:
        s["mvc_encoder"] = DEFAULTS["mvc_encoder"]
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


def build_filter(layout, w, h, sar, W, H, fit, swap, mv_variant=0, tm=None, ctb=0, tail="", stack="h"):
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
    parts.append("[%s][%s]%sstack=inputs=2,sidedata=mode=delete:type=STEREO3D%s[vout]"
                 % (first, second, "v" if stack == "v" else "h", ("," + tail) if tail else ""))
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
    if size_key == "mvc":
        return os.path.join(d, "%s_MVC_%dx%d.mkv" % (base, W, H))
    return os.path.join(d, "%s_FSBS_%dx%d.mkv" % (base, W * 2, H))


def output_label(size_key):
    W, H = OUTPUT_SIZES[size_key]
    return "MVC %dx%d" % (W, H) if size_key == "mvc" else "FSBS %dx%d" % (W * 2, H)


def build_command(ffmpeg, src, dst, info, opts, mv_variant=0, preview_at=None, pipe_out=None):
    """opts: layout(resolved), size, fit, swap, encoder, preset, quality, bitdepth, audio, subs, hwdec,
    tonemap, tm_engine, tm_curve, peak, sdr_gamma, sdr_sat, crop_tb.
    preview_at: seconds -> build a one-frame PNG preview command instead (dst = .png).
    pipe_out: 'y4m' (side-by-side) or 'tb' (top-bottom raw) -> stream 8-bit frames to stdout for an
    external MVC encoder instead of encoding (progress then goes to stderr)."""
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
                      int(opts.get("crop_tb", 0) or 0), tail, stack="v" if pipe_out == "tb" else "h")

    cmd = [ffmpeg, "-hide_banner", "-y"]
    if pipe_out:
        cmd += ["-nostdin", "-progress", "pipe:2", "-nostats"]
    elif preview_at is None:
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
    if pipe_out:
        return cmd + pipe_out_args(pipe_out), notes
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


def pipe_out_args(kind):
    """8-bit 4:2:0 frames to stdout: y4m for x264-mvc, raw top-bottom for the FRIM left/right splitter."""
    fmt = ["-f", "yuv4mpegpipe"] if kind == "y4m" else ["-f", "rawvideo"]
    return ["-an", "-sn", "-pix_fmt", "yuv420p", "-color_range", "tv"] + fmt + ["pipe:1"]


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
    if size == "mvc":
        return convert_to_mvc(ffmpeg, src, info, o, on_progress, on_log, cancel_event)
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


def build_mvc_command(ffmpeg, src, dst, info, opts, raw_input, preview_frame=None, pipe_out=None):
    """ffmpeg reading FRIM's raw side-by-side yuv (stdin '-' or a .yuv file) + audio/subs from the source."""
    ew, eh, fps, right_first = mvc_params(info)
    W, H = OUTPUT_SIZES[opts["size"]]
    swap = bool(opts.get("swap")) != right_first
    tail = ""
    if preview_frame is not None:
        tail = "select=eq(n\\,%d),scale=1920:-2:flags=bicubic,format=rgb24" % preview_frame
    fc = build_filter("fsbs", 2 * ew, eh, 1.0, W, H, opts["fit"], swap, 0, None,
                      int(opts.get("crop_tb", 0) or 0), tail, stack="v" if pipe_out == "tb" else "h")
    cmd = [ffmpeg, "-hide_banner", "-y"]
    if pipe_out:
        cmd += ["-progress", "pipe:2", "-nostats"]
    else:
        cmd += (["-nostdin", "-loglevel", "error"] if preview_frame is not None
                else ["-progress", "pipe:1", "-nostats"])
    cmd += ["-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", "%dx%d" % (2 * ew, eh),
            "-framerate", fps, "-i", raw_input]
    notes = ["MVC: FRIM decodes both eyes (%dx%d each, %s fps)%s" % (ew, eh, fps,
             ", source is right-eye-first -> swapped" if right_first else "")]
    if preview_frame is not None:
        return cmd + ["-filter_complex", fc, "-map", "[vout]", "-frames:v", "1", "-update", "1", dst], notes
    if pipe_out:
        return cmd + ["-filter_complex", fc, "-map", "[vout]"] + pipe_out_args(pipe_out), notes
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

# ----------------------------------------------------------------------------- H.264 MVC output (MVC MKV)
#
# Any input -> ffmpeg (decode, tone map, 1920x1080 per eye) -> MVC encoder -> combined AVC+MVC stream
#   x264-mvc     : reads side-by-side y4m from ffmpeg's stdout
#   FRIM Encoder : reads left and right eye from two named pipes; the app splits ffmpeg's top-bottom frames
# -> access-unit delimiters checked/inserted -> ffmpeg muxes it with the source's audio/subs/chapters into
#    an MKV flagged stereo_mode=block_lr ("both eyes laced in one block, left eye first"), the layout of
#    MakeMKV 3D rips that Zidoo/Dune/Kodi/PowerDVD play in 3D.  B-frames are off (raw streams carry no
#    timestamps; without B-frames decode order == display order).

MVC_ENCODERS = {"x264mvc": "x264-mvc (best quality)", "frim": "FRIM Encoder (Intel)"}


def find_x264mvc(saved=""):
    """Locate the x264-mvc encoder (a Windows build of github.com/blenheimears/x264-mvc)."""
    if saved and os.path.isfile(saved):
        return saved
    names = ("x264-mvc" + EXE, "x264mvc" + EXE, "x264" + EXE)
    pats = [os.path.join(SCRIPT_DIR, "x264-mvc" + EXE)]
    for n in names:
        pats += [os.path.join(SCRIPT_DIR, "x264*", n), os.path.join(SCRIPT_DIR, "x264*", "*", n)]
    for pat in pats:
        hits = sorted(h for h in glob.glob(pat) if os.path.isfile(h))
        if hits:
            return os.path.abspath(hits[0])
    return shutil.which("x264-mvc") or ""


def find_frim_encoder(frim_decoder=""):
    """FRIMEncode64.exe normally sits next to FRIMDecode64.exe."""
    d = os.path.dirname(frim_decoder or find_frim())
    for n in ("FRIMEncode64.exe", "FRIMEncode.exe", "FRIMEncode64"):
        p = os.path.join(d, n) if d else ""
        if p and os.path.isfile(p):
            return p
    return ""


def fill_template(exe, template, values):
    """Split an argument template on spaces and substitute {name} placeholders token by token
    (so paths with spaces stay one argument)."""
    cmd = [exe]
    for tok in template.split():
        tok = tok.strip('"')
        for k, v in values.items():
            tok = tok.replace("{%s}" % k, str(v))
        cmd.append(tok)
    return cmd


def fps_float(fps):
    try:
        a, b = str(fps).split("/")
        return "%.3f" % (float(a) / float(b))
    except ValueError:
        return "%.3f" % float(fps)


class PipeWriter(threading.Thread):
    """Serves one eye's raw frames to the encoder through a named pipe (Windows) or a FIFO (elsewhere)."""

    def __init__(self, tag):
        super().__init__(daemon=True)
        self.q = queue.Queue(maxsize=8)
        self.error = None
        if IS_WIN:
            import ctypes
            from ctypes import wintypes
            self._k32 = ctypes.windll.kernel32
            self._k32.CreateNamedPipeW.restype = wintypes.HANDLE
            self._k32.CreateNamedPipeW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                                   wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
                                                   wintypes.DWORD, ctypes.c_void_p]
            self._k32.ConnectNamedPipe.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
            self._k32.WriteFile.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
                                            ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
            self._ct, self._wt = ctypes, wintypes
            self.path = r"\\.\pipe\fsbs_%d_%s.yuv" % (os.getpid(), tag)
            PIPE_ACCESS_OUTBOUND, BUF = 0x2, 4 * 1024 * 1024
            self.h = self._k32.CreateNamedPipeW(self.path, PIPE_ACCESS_OUTBOUND, 0, 1, BUF, 0, 0, None)
            if not self.h or self.h == wintypes.HANDLE(-1).value:
                raise OSError("Could not create named pipe %s" % self.path)
        else:
            self.path = os.path.join(tempfile.mkdtemp(prefix="fsbs_pipe_"), "%s.yuv" % tag)
            os.mkfifo(self.path)

    def run(self):
        try:
            if IS_WIN:
                ok = self._k32.ConnectNamedPipe(self.h, None)
                if not ok and self._ct.GetLastError() != 535:     # 535 = already connected
                    raise OSError("encoder never opened %s" % self.path)
                written = self._wt.DWORD(0)
                while True:
                    buf = self.q.get()
                    if buf is None:
                        break
                    mv, off = memoryview(buf), 0
                    while off < len(buf):
                        chunk = mv[off:off + (1 << 20)]
                        cbuf = (self._ct.c_char * len(chunk)).from_buffer_copy(chunk)
                        if not self._k32.WriteFile(self.h, cbuf, len(chunk), self._ct.byref(written), None):
                            raise OSError("encoder stopped reading %s" % self.path)
                        off += written.value
            else:
                with open(self.path, "wb") as f:
                    while True:
                        buf = self.q.get()
                        if buf is None:
                            break
                        f.write(buf)
        except Exception as e:  # encoder closed the pipe / was killed
            self.error = str(e)
            while True:          # drain so the splitter never blocks
                try:
                    if self.q.get(timeout=2) is None:
                        break
                except queue.Empty:
                    break
        finally:
            self.close()

    def close(self):
        if IS_WIN:
            if getattr(self, "h", None):
                try:
                    self._k32.FlushFileBuffers(self.h)
                    self._k32.DisconnectNamedPipe(self.h)
                    self._k32.CloseHandle(self.h)
                except Exception:
                    pass
                self.h = None
        else:
            shutil.rmtree(os.path.dirname(self.path), ignore_errors=True)


def split_tb_frames(stream, w, h, left, right):
    """Read top-bottom yuv420p frames (w x 2h) and hand each eye to its PipeWriter."""
    ysz, csz = w * h, (w // 2) * (h // 2)
    frame = 2 * ysz + 4 * csz
    while True:
        b = stream.read(frame)
        if not b or len(b) < frame:
            break
        y, u, v = b[:2 * ysz], b[2 * ysz:2 * ysz + 2 * csz], b[2 * ysz + 2 * csz:]
        left.q.put(y[:ysz] + u[:csz] + v[:csz])
        right.q.put(y[ysz:] + u[csz:] + v[csz:])
    left.q.put(None)
    right.q.put(None)


_SC = re.compile(rb"\x00\x00\x01")


def iter_nals(path, chunk=8 << 20):
    """Yield NAL units (without start code) from an Annex-B file, streaming in chunks."""
    buf = b""
    with open(path, "rb") as f:
        while True:
            data = f.read(chunk)
            buf += data
            starts = [m.start() for m in _SC.finditer(buf)]
            if not starts:
                if not data:
                    return
                buf = buf[-3:]
                continue
            for i in range(len(starts) - 1):
                # trailing zeros belong to the next 4-byte start code (a NAL never ends in 0x00)
                yield buf[starts[i] + 3:starts[i + 1]].rstrip(b"\x00")
            if not data:
                yield buf[starts[-1] + 3:]
                return
            buf = buf[starts[-1]:]


def es_has_aud(path, probe_bytes=4 << 20):
    """True if the stream marks its access units with delimiters (NAL 9) before the first slice."""
    with open(path, "rb") as f:
        head = f.read(probe_bytes)
    for m in _SC.finditer(head):
        t = head[m.end()] & 0x1F if m.end() < len(head) else 0
        if t == 9:
            return True
        if t in (1, 5):
            return False
    return False


def iter_access_units(path):
    """Yield access units (lists of NALs: base view + dependent view) from a combined AVC+MVC stream.
    With delimiters (x264-mvc --aud) an access unit runs from one AUD to the next. Without them
    (FRIM) the start is found from the NAL types: non-VCL NALs after a picture are held back until
    the next slice shows whether it opens a new picture (first_mb_in_slice == 0), because MVC puts
    a prefix NAL (14) before every base slice and the dependent view's SPS/PPS after the base slices."""
    aud_mode = es_has_aud(path)
    cur, pending, pending_start = [], [], False
    seen_vcl = seen_dep = seen_subset = False
    has_mvc = None

    def has_vcl(nals):
        return any(n[0] & 0x1F in (1, 5) for n in nals)

    for nal in iter_nals(path):
        if not nal:
            continue
        t = nal[0] & 0x1F
        if aud_mode:
            if t == 9:
                if has_vcl(cur):
                    yield cur
                    cur = [nal]
                else:                       # headers written before the first delimiter
                    cur.insert(0, nal)
            else:
                cur.append(nal)
            continue
        if not seen_vcl:
            cur.append(nal)
            seen_vcl = t in (1, 5)
            continue
        if t == 15:                                  # subset SPS: dependent view, same access unit
            seen_subset = True
            cur += pending + [nal]
            pending, pending_start = [], False
        elif t == 7 or (t == 8 and not seen_subset):  # base SPS/PPS -> next access unit
            pending.append(nal)
            pending_start = True
        elif t == 14 or (t == 6 and (seen_dep or has_mvc is False)):
            pending.append(nal)
        elif t in (1, 5):
            if pending_start or (len(nal) > 1 and nal[1] & 0x80):     # first_mb_in_slice == 0
                if has_mvc is None:
                    has_mvc = seen_dep
                yield cur
                cur, seen_dep, seen_subset = [], False, False
            cur += pending + [nal]
            pending, pending_start = [], False
        else:                                        # 8 after subset SPS, 20 dependent slice, 24, ...
            cur += pending + [nal]
            pending, pending_start = [], False
            if t == 20:
                seen_dep = True
    cur += pending
    if has_vcl(cur):
        yield cur


def _ebml_id(i):
    return i.to_bytes((i.bit_length() + 7) // 8, "big")


def _ebml_size(n):
    for length in range(1, 9):
        if n < (1 << (7 * length)) - 1:
            return ((1 << (7 * length)) | n).to_bytes(length, "big")
    raise ValueError("EBML element too large")


def _el(i, payload):
    return _ebml_id(i) + _ebml_size(len(payload)) + payload


def _uint(i, v):
    return _el(i, v.to_bytes(max(1, (v.bit_length() + 7) // 8), "big"))


def write_mvc_video_mkv(es, out, fps, w, h, on_progress=None, total_frames=0, cancel_event=None):
    """Write the combined AVC+MVC stream as a video-only Matroska file with one block per access unit
    (both eyes laced in one block, the MakeMKV 3D layout). ffmpeg's raw H.264 reader can't be used
    for this: it starts a new frame at the dependent view's PPS. Returns the number of frames."""
    import struct
    fr = fractions.Fraction(str(fps))
    dur_ns = int(round(1e9 / float(fr)))
    sps = pps = None
    n = 0
    with open(out, "wb") as f:
        f.write(_el(0x1A45DFA3, _uint(0x4286, 1) + _uint(0x42F7, 1) + _uint(0x42F2, 4) + _uint(0x42F3, 8) +
                    _el(0x4282, b"matroska") + _uint(0x4287, 4) + _uint(0x4285, 2)))
        f.write(_ebml_id(0x18538067) + b"\x01\xff\xff\xff\xff\xff\xff\xff")   # Segment, unknown size
        cluster, cluster_tc = bytearray(), 0

        def flush_cluster():
            if cluster:
                f.write(_el(0x1F43B675, _uint(0xE7, cluster_tc) + bytes(cluster)))
                cluster.clear()

        for au in iter_access_units(es):
            if cancel_event is not None and cancel_event.is_set():
                raise Cancelled()
            if n == 0:
                for nal in au:
                    tt = nal[0] & 0x1F
                    if tt == 7 and sps is None:
                        sps = nal
                    elif tt == 8 and pps is None:
                        pps = nal
                if sps is None or pps is None:
                    raise RuntimeError("MVC stream has no SPS/PPS in its first frame")
                avcc = (bytes([1, sps[1], sps[2], sps[3], 0xFF, 0xE1]) + struct.pack(">H", len(sps)) + sps +
                        bytes([1]) + struct.pack(">H", len(pps)) + pps)
                info = _uint(0x2AD7B1, 1000000) + _el(0x4D80, b"FullSBS3DConverter") + \
                    _el(0x5741, b"FullSBS3DConverter")
                video = _uint(0xB0, w) + _uint(0xBA, h) + _uint(0x53B8, 12)     # StereoMode 12 = block_lr
                track = _el(0xAE, _uint(0xD7, 1) + _uint(0x73C5, 1) + _uint(0x83, 1) + _uint(0x9C, 0) +
                            _uint(0x23E383, dur_ns) + _el(0x86, b"V_MPEG4/ISO/AVC") + _el(0x63A2, avcc) +
                            _el(0xE0, video))
                f.write(_el(0x1549A966, info) + _el(0x1654AE6B, track))
            key = any(nal[0] & 0x1F == 5 for nal in au)
            tc_ms = int(n * dur_ns // 1000000)
            if key or not cluster or tc_ms - cluster_tc > 30000:
                flush_cluster()
                cluster_tc = tc_ms
            data = b"".join(struct.pack(">I", len(nal)) + nal for nal in au)
            cluster += _el(0xA3, b"\x81" + struct.pack(">h", tc_ms - cluster_tc) + (b"\x80" if key else b"\x00")
                           + data)
            n += 1
            if on_progress and total_frames and n % 240 == 0:
                on_progress(min(1.0, n / float(total_frames)), "", "packing")
        flush_cluster()
    return n


def mux_mvc_mkv(ffmpeg, video_mkv, src, info, opts, dst, duration, on_progress, on_log, cancel_event):
    """Add the source's audio, subtitles and chapters to the MVC video by stream copy (packets stay
    exactly as written: one access unit = both eyes per block)."""
    cmd = [ffmpeg, "-hide_banner", "-y", "-progress", "pipe:1", "-nostats",
           "-i", video_mkv, "-i", src, "-map", "0:v:0", "-c:v", "copy"]
    sargs, _ = stream_args(info, opts["audio"], opts["subs"], inp=1)
    cmd += sargs + ["-metadata:s:v:0", "stereo_mode=block_lr", "-map_metadata", "1", "-map_chapters", "1",
                    "-max_muxing_queue_size", "4096", dst]
    on_log("Mux: " + quote_cmd(cmd))
    rc, tail, _ = run_ffmpeg(cmd, duration, on_progress, on_log, cancel_event)
    if rc != 0:
        raise RuntimeError("Muxing the MVC stream into MKV failed:\n" + "\n".join(tail[-8:]))


def run_encode_chain(ff_cmd, enc_cmd, mode, geom, duration, on_progress, on_log, cancel_event,
                     pre_cmd=None, writers=None):
    """[pre (FRIM decode) ->] ffmpeg -> encoder. mode 'y4m': ffmpeg stdout -> encoder stdin;
    mode 'tb': ffmpeg stdout -> split_tb_frames -> writers (named pipes) -> encoder."""
    procs, threads, ftail, etail = [], [], [], []
    state = {"t": 0.0, "speed": "", "frames": False}

    def ff_err(stream):
        buf = b""
        while True:
            chunk = stream.read(4096)
            if not chunk:
                break
            buf += chunk
            lines = re.split(rb"[\r\n]+", buf)
            buf = lines.pop()
            for raw in lines:
                line = raw.decode("utf-8", "replace").strip()
                if line.startswith(("out_time_us=", "out_time_ms=")):
                    try:
                        state["t"] = int(line.split("=", 1)[1]) / 1e6
                        state["frames"] = state["frames"] or state["t"] > 0
                    except ValueError:
                        pass
                    eta = ""
                    try:
                        sp = float(state["speed"].rstrip("x"))
                        if sp > 0 and duration:
                            eta = fmt_time((duration - state["t"]) / sp)
                    except ValueError:
                        pass
                    on_progress(min(1.0, state["t"] / duration) if duration else 0.0, state["speed"], eta)
                elif line.startswith("speed="):
                    state["speed"] = line.split("=", 1)[1].strip()
                elif "=" in line and " " not in line.split("=")[0]:
                    pass                                    # other -progress keys
                elif line:
                    ftail.append(line)
                    del ftail[:-40]
                    on_log(line)

    try:
        pre = None
        if pre_cmd:
            pre = subprocess.Popen(pre_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=NO_WINDOW)
            procs.append(pre)
            threads.append(threading.Thread(target=_drain, args=(pre.stderr, [], 40, on_log), daemon=True))
        ff = subprocess.Popen(ff_cmd, stdin=pre.stdout if pre else subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, creationflags=NO_WINDOW)
        procs.append(ff)
        if pre:
            pre.stdout.close()
        threads.append(threading.Thread(target=ff_err, args=(ff.stderr,), daemon=True))
        if mode == "y4m":
            enc = subprocess.Popen(enc_cmd, stdin=ff.stdout, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                                   creationflags=NO_WINDOW)
            ff.stdout.close()
        else:
            for wtr in writers:
                wtr.start()
            enc = subprocess.Popen(enc_cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.PIPE, creationflags=NO_WINDOW)
            threads.append(threading.Thread(target=split_tb_frames,
                                            args=(ff.stdout, geom[0], geom[1], writers[0], writers[1]), daemon=True))
        procs.append(enc)
        threads.append(threading.Thread(target=_drain, args=(enc.stderr, etail, 40, on_log), daemon=True))
        for t in threads:
            t.start()
        while True:
            if cancel_event.is_set():
                raise Cancelled()
            if enc.poll() is not None:
                break
            time.sleep(0.2)
        rc = enc.returncode
        try:
            ff.wait(30)
        except subprocess.TimeoutExpired:
            pass
    finally:
        for p in procs:
            if p.poll() is None:
                try:
                    p.kill()
                except Exception:
                    pass
        for w in writers or ():
            try:
                w.q.put_nowait(None)
            except Exception:
                pass
    for t in threads:
        t.join(3)
    return rc, ff.returncode, ftail, etail, state["frames"]


def convert_to_mvc(ffmpeg, src, info, o, on_progress, on_log, cancel_event):
    """Any supported input -> H.264 MVC (Blu-ray 3D style) MKV, 1920x1080 per eye."""
    enc_kind = o.get("mvc_encoder", "x264mvc")
    if enc_kind == "frim":
        exe = find_frim_encoder(find_frim(o.get("frim", "")))
        if not exe:
            raise RuntimeError("FRIM Encoder (FRIMEncode64.exe) not found - it comes with FRIM; unzip FRIM into "
                               "the app's FRIM folder or set it with 'Browse FRIM…'.")
    else:
        exe = find_x264mvc(o.get("x264mvc", ""))
        if not exe:
            raise RuntimeError("x264-mvc not found - put x264-mvc.exe in the app's x264-mvc folder or set it "
                               "with 'Browse x264-mvc…'.")
    v = main_video(info)
    dst = output_path(src, o.get("outdir", ""), "mvc")
    if os.path.abspath(dst) == os.path.abspath(src):
        raise RuntimeError("Output would overwrite the source")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        duration = float(info.get("format", {}).get("duration") or v.get("duration") or 0)
    except ValueError:
        duration = 0.0
    W, H = OUTPUT_SIZES["mvc"]
    oo = dict(o, size="mvc", bitdepth="8")
    mode = "y4m" if enc_kind == "x264mvc" else "tb"
    base = os.path.splitext(dst)[0]
    es, es_fixed = base + ".mvc_encoded_temp.h264", base + ".mvc_video_temp.mkv"
    temps = [es, es_fixed]

    # frame source: ffmpeg (or FRIM decoder -> ffmpeg for MVC input)
    pre_cmd, writers = None, None
    if oo["layout"] == "mvc":
        frim = find_frim(oo.get("frim", ""))
        if not frim:
            raise RuntimeError(FRIM_MISSING_MSG)
        src_es = base + ".mvc_source_temp.h264"
        temps.append(src_es)
        _, _, fps, _ = mvc_params(info)
    else:
        fps = v.get("r_frame_rate") or v.get("avg_frame_rate") or "24000/1001"
        if fps in ("0/0", ""):
            fps = "24000/1001"
    try:
        if oo["layout"] == "mvc":
            on_log("Extracting the source 3D video stream for FRIM…")
            extract_mvc_es(ffmpeg, src, src_es, duration,
                           lambda f, sp, eta: on_progress(f * 0.05, sp, "extracting"), on_log, cancel_event)
            pre_cmd = frim_cmd(frim, oo.get("frim_args"), src_es, "-")
        variants = range(len(MV_VIEW_VARIANTS)) if oo["layout"] == "mvhevc" else [0]
        start = 0.05 if pre_cmd else 0.0
        on_log("Step 1/2: encoding MVC with %s" % MVC_ENCODERS[enc_kind])
        for vi in variants:
            if oo["layout"] == "mvc":
                ff_cmd, notes = build_mvc_command(ffmpeg, src, None, info, oo, "-", pipe_out=mode)
            else:
                ff_cmd, notes = build_command(ffmpeg, src, None, info, oo, vi, pipe_out=mode)
            for n in notes:
                on_log("Note: " + n)
            if enc_kind == "x264mvc":
                enc_cmd = fill_template(exe, oo.get("x264mvc_args") or DEFAULTS["x264mvc_args"],
                                        {"preset": oo.get("mvc_preset", "slow"), "crf": oo.get("mvc_crf", 18),
                                         "out": es})
            else:
                writers = [PipeWriter("L"), PipeWriter("R")]
                kbps = int(oo.get("mvc_kbps", 28000))
                enc_cmd = fill_template(exe, oo.get("frimenc_args") or DEFAULTS["frimenc_args"],
                                        {"left": writers[0].path, "right": writers[1].path, "out": es, "w": W,
                                         "h": H, "fps": fps_float(fps), "kbps": kbps,
                                         "maxkbps": min(40000, int(kbps * 1.4))})
            if pre_cmd:
                on_log("FRIM decode: " + quote_cmd(pre_cmd))
            on_log("ffmpeg: " + quote_cmd(ff_cmd))
            on_log("Encoder: " + quote_cmd(enc_cmd))
            rc, ffrc, ftail, etail, got = run_encode_chain(
                ff_cmd, enc_cmd, mode, (W, H), duration,
                lambda f, sp, eta: on_progress(start + f * (0.92 - start), sp, eta), on_log, cancel_event,
                pre_cmd=pre_cmd, writers=writers)
            if rc == 0 or got or vi + 1 >= len(variants):
                break
            on_log("View selection '%s' failed - retrying with '%s'"
                   % (MV_VIEW_VARIANTS[vi][0], MV_VIEW_VARIANTS[vi + 1][0]))
        if rc != 0 or not os.path.isfile(es) or os.path.getsize(es) == 0:
            raise RuntimeError("MVC encoding failed (encoder exit %s, ffmpeg exit %s)\nEncoder:\n%s\n\nffmpeg:\n%s"
                               % (rc, ffrc, "\n".join(etail[-8:]), "\n".join(ftail[-6:])))
        if writers and any(w.error for w in writers):
            on_log("Note: " + "; ".join(w.error for w in writers if w.error))

        on_log("Step 2/2: packing both eyes per frame into MKV (stereo_mode=block_lr), then adding the "
               "source's audio/subtitles/chapters")
        total = int(duration * float(fractions.Fraction(str(fps)))) if duration else 0
        nfr = write_mvc_video_mkv(es, es_fixed, fps, W, H,
                                  lambda f, sp, eta: on_progress(0.92 + f * 0.04, sp, "packing"), total, cancel_event)
        on_log("  %d stereo frames" % nfr)
        mux_mvc_mkv(ffmpeg, es_fixed, src, info, oo, dst, duration,
                    lambda f, sp, eta: on_progress(0.96 + f * 0.04, sp, "muxing"), on_log, cancel_event)
        on_progress(1.0, "", "")
        return dst
    except Cancelled:
        _remove_quietly(dst)
        raise
    except Exception:
        _remove_quietly(dst)
        raise
    finally:
        for w in writers or ():
            w.close()
        for t in temps:
            _remove_quietly(t)


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
        self.root.geometry("1240x%d" % min(1000, self.root.winfo_screenheight() - 90))
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
        try:
            from tkinter import font as tkfont
            bf = tkfont.nametofont("TkDefaultFont").actual()
            self._bold_font = (bf["family"], bf["size"], "bold")
        except Exception:
            self._bold_font = ("Segoe UI", 9, "bold")
        f0 = ttk.LabelFrame(r, text="3D MV-HEVC, Top/bottom or MVC Formats to FSBS Converter")
        f0.pack(fill="x", **pad)
        self.v_ff = tk.StringVar(value=self.s.get("ffmpeg", ""))
        self.v_frim = tk.StringVar(value=find_frim(self.s.get("frim", "")))
        self.v_x264 = tk.StringVar(value=find_x264mvc(self.s.get("x264mvc", "")))
        self.v_frim_args = tk.StringVar(value=self.s.get("frim_args") or DEFAULTS["frim_args"])
        tools = (("ffmpeg:", self.v_ff, "Browse ffmpeg.exe…", self._browse_ff),
                 ("FRIM:", self.v_frim, "Browse FRIM…", self._browse_frim),
                 ("x264-mvc:", self.v_x264, "Browse x264-mvc…", self._browse_x264))
        self.tool_status = []
        for i, (lbl, var, btn, cmd) in enumerate(tools):
            ttk.Label(f0, text=lbl, width=9).grid(row=i, column=0, sticky="w", padx=(4, 0), pady=2)
            ttk.Entry(f0, textvariable=var).grid(row=i, column=1, sticky="ew", padx=4, pady=2)
            st = ttk.Label(f0, text="", width=34)
            st.grid(row=i, column=2, sticky="w", padx=4)
            self.tool_status.append(st)
            ttk.Button(f0, text=btn, width=18, command=cmd).grid(row=i, column=3, sticky="ew", padx=(2, 4), pady=2)
        self.l_ver, self.l_frim, self.l_x264 = self.tool_status
        f0.columnconfigure(1, weight=1)
        self._frim_status()

        # files
        ttk.Style().configure("Bold.TLabelframe.Label", font=self._bold_font)
        f1 = ttk.LabelFrame(r, text="Input videos", style="Bold.TLabelframe")
        f1.pack(fill="both", expand=True, **pad)
        cols = ("file", "res", "codec", "layout", "status")
        self.tree = ttk.Treeview(f1, columns=cols, show="headings", height=4, selectmode="extended")
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
        f2 = ttk.LabelFrame(r, text="Output options", style="Bold.TLabelframe")
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

        ttk.Separator(f2, orient="horizontal").grid(row=6, column=0, columnspan=5, sticky="ew", padx=6, pady=(4, 2))
        ttk.Label(f2, text="Save to:").grid(row=7, column=0, sticky="w", **pad)
        self.v_out = tk.StringVar(value=self.s["outdir"])
        oe = ttk.Frame(f2)
        oe.grid(row=7, column=1, columnspan=4, sticky="ew", **pad)
        ttk.Entry(oe, textvariable=self.v_out).pack(side="left", fill="x", expand=True)
        ttk.Button(oe, text="Browse…", command=self._browse_out).pack(side="left", padx=4)
        ttk.Label(oe, text="(empty = next to source)", foreground="#666").pack(side="left")
        ttk.Label(f2, text="MVC MKV:").grid(row=5, column=0, sticky="w", **pad)
        mf = ttk.Frame(f2)
        mf.grid(row=5, column=1, columnspan=4, sticky="w", **pad)
        self.v_mvc = tk.BooleanVar(value=bool(self.s.get("mvc_out")))
        ttk.Checkbutton(mf, text="1920×1080 per eye (framepacked Blu-ray 3D)",
                        variable=self.v_mvc).pack(side="left")
        ttk.Label(mf, text="   Encoder:").pack(side="left")
        self.v_mvc_enc = tk.StringVar(value=MVC_ENCODERS[self.s.get("mvc_encoder", "x264mvc")])
        cbe = ttk.Combobox(mf, textvariable=self.v_mvc_enc, state="readonly",
                           width=fit_width(MVC_ENCODERS.values()), values=list(MVC_ENCODERS.values()))
        cbe.pack(side="left", padx=4)
        cbe.bind("<<ComboboxSelected>>", lambda e: self._mvc_enc_changed())
        self.mvc_x264 = ttk.Frame(mf)
        ttk.Label(self.mvc_x264, text="Preset:").pack(side="left")
        presets = [preset_label("libx265", p) for p in ENCODERS["libx265"][1]]
        self.v_mvc_preset = tk.StringVar(value=preset_label("libx265", self.s.get("mvc_preset", "slow")))
        ttk.Combobox(self.mvc_x264, textvariable=self.v_mvc_preset, state="readonly", width=fit_width(presets, 1) - 6,
                     values=presets).pack(side="left", padx=4)
        ttk.Label(self.mvc_x264, text="CRF:").pack(side="left")
        self.v_mvc_crf = tk.IntVar(value=int(self.s.get("mvc_crf", 18)))
        ttk.Spinbox(self.mvc_x264, from_=0, to=51, textvariable=self.v_mvc_crf, width=4).pack(side="left", padx=4)
        self.mvc_frim = ttk.Frame(mf)
        ttk.Label(self.mvc_frim, text="Bitrate:").pack(side="left")
        self.v_mvc_kbps = tk.IntVar(value=int(self.s.get("mvc_kbps", 28000)))
        ttk.Spinbox(self.mvc_frim, from_=8000, to=40000, increment=1000, textvariable=self.v_mvc_kbps,
                    width=7).pack(side="left", padx=4)
        ttk.Label(self.mvc_frim, text="kbps").pack(side="left")
        self.b_mvc_adv = ttk.Button(mf, text="Advanced…", command=self._mvc_advanced)
        self.b_mvc_adv.pack(side="right", padx=(10, 0))
        self._mvc_enc_changed()
        f2.columnconfigure(3, weight=1)
        try:
            self._logo = tk.PhotoImage(data=LOGO_PNG_B64)
            ttk.Label(f2, image=self._logo).grid(row=1, column=4, rowspan=3, sticky="ne", padx=(4, 8), pady=(0, 2))
        except tk.TclError:
            pass

        # HDR -> SDR
        fh = ttk.LabelFrame(r, text="HDR / Dolby Vision → SDR", style="Bold.TLabelframe")
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
        self.log = ScrolledText(f5, height=4, font=("Consolas" if IS_WIN else "monospace", 9), wrap="word")
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
            short = re.sub(r"^ffmpeg version\s+", "", ver).split(" ")[0][:24]
            txt = ("✔ " + short) if self.ffprobe else "⚠ ffprobe.exe missing next to ffmpeg"
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
            self.l_ver.configure(text="✖ not found - Browse to bin\\ffmpeg.exe", foreground="#c00")

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

    def _mvc_enc_key(self):
        return self._key(MVC_ENCODERS, self.v_mvc_enc.get())

    def _mvc_enc_changed(self):
        x264 = self._mvc_enc_key() == "x264mvc"
        self.mvc_x264.pack_forget()
        self.mvc_frim.pack_forget()
        (self.mvc_x264 if x264 else self.mvc_frim).pack(side="left", padx=(8, 0), before=self.b_mvc_adv)

    def _mvc_advanced(self):
        w = tk.Toplevel(self.root)
        w.title("MVC encoder arguments")
        w.transient(self.root)
        fr = ttk.Frame(w, padding=12)
        fr.pack(fill="both", expand=True)
        rows = (("FRIM decoder arguments, Blu-ray 3D MVC input  ({in} {out})", "frim_args"),
                ("x264-mvc arguments  ({preset} {crf} {out})", "x264mvc_args"),
                ("FRIM Encoder arguments  ({left} {right} {out} {w} {h} {fps} {kbps} {maxkbps})", "frimenc_args"))
        vars_ = {}
        for i, (label, key) in enumerate(rows):
            ttk.Label(fr, text=label).grid(row=2 * i, column=0, columnspan=2, sticky="w", pady=(8 if i else 0, 2))
            v = tk.StringVar(value=self.s.get(key) or DEFAULTS[key])
            ttk.Entry(fr, textvariable=v, width=120).grid(row=2 * i + 1, column=0, sticky="ew")
            ttk.Button(fr, text="Reset", width=6, command=lambda v=v, k=key: v.set(DEFAULTS[k])).grid(
                row=2 * i + 1, column=1, padx=(4, 0))
            vars_[key] = v
        ttk.Label(fr, foreground="#666", justify="left",
                  text="B-frames must stay off (x264: --bframes 0, FRIM: -gop N 1): raw MVC streams carry no\n"
                       "timestamps, so the MKV is only correct when frames are stored in display order.").grid(
            row=2 * len(rows), column=0, columnspan=2, sticky="w", pady=(10, 6))

        def save():
            for k, v in vars_.items():
                self.s[k] = v.get().strip() or DEFAULTS[k]
            self.v_frim_args.set(self.s["frim_args"])
            save_settings(self.s)
            w.destroy()
        ttk.Button(fr, text="OK", width=10, command=save).grid(row=2 * len(rows) + 1, column=0, columnspan=2)
        w.grab_set()

    def _browse_x264(self):
        p = filedialog.askopenfilename(title="Select the x264-mvc encoder",
                                       filetypes=[("x264-mvc", "*.exe"), ("All files", "*.*")])
        if p:
            self.v_x264.set(p)
            self._frim_status()

    def _frim_status(self):
        p = self.v_frim.get().strip()
        if p and os.path.isfile(p):
            enc = " + encoder" if find_frim_encoder(p) else ""
            self.l_frim.configure(text="✔ decoder%s (Blu-ray 3D MVC)" % enc, foreground="#2a6")
        else:
            self.l_frim.configure(text="optional - for Blu-ray 3D MVC", foreground="#888")
        x = self.v_x264.get().strip()
        if x and os.path.isfile(x):
            self.l_x264.configure(text="✔ ready (MVC MKV output)", foreground="#2a6")
        else:
            self.l_x264.configure(text="optional - for MVC MKV output", foreground="#888")

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
        o.update({
            "mvc_out": bool(self.v_mvc.get()), "mvc_encoder": self._mvc_enc_key(),
            "mvc_preset": preset_from_label(self.v_mvc_preset.get()) or "slow",
            "mvc_crf": int(self._num(self.v_mvc_crf, 18, 0, 51)),
            "mvc_kbps": int(self._num(self.v_mvc_kbps, 28000, 4000, 40000)),
            "x264mvc": self.v_x264.get().strip(),
            "x264mvc_args": self.s.get("x264mvc_args") or DEFAULTS["x264mvc_args"],
            "frimenc_args": self.s.get("frimenc_args") or DEFAULTS["frimenc_args"],
        })
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
        size = ([x for x in o["sizes"] if x != "mvc"] or ["3840"])[0]
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
        size = ([x for x in o["sizes"] if x != "mvc"] or ["3840"])[0]
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
        if o["mvc_out"]:
            o["sizes"] = [x for x in o["sizes"] if x != "mvc"] + ["mvc"]
        if not o["sizes"]:
            messagebox.showerror(APP_NAME, "Tick at least one output (FSBS size or MVC MKV).")
            return
        if o["mvc_out"]:
            if o["mvc_encoder"] == "x264mvc" and not find_x264mvc(o["x264mvc"]):
                messagebox.showerror(APP_NAME, "MVC MKV output with x264-mvc: x264-mvc.exe not found.\n\n"
                                               "Click 'Browse x264-mvc…', or choose the FRIM Encoder.")
                return
            if o["mvc_encoder"] == "frim" and not find_frim_encoder(find_frim(o["frim"])):
                messagebox.showerror(APP_NAME, "MVC MKV output with FRIM: FRIMEncode64.exe not found next to "
                                               "FRIMDecode64.exe.\n\nUnzip the full FRIM package into the app's "
                                               "FRIM folder, or choose x264-mvc.")
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
                label = output_label(size)
                self.q.put(("row", (f, "Converting %s…" % label)))
                self.q.put(("log", "\n=== %s  ->  %s ===" % (os.path.basename(f["path"]), label)))
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
    ap.add_argument("--size", action="append", choices=list(OUTPUT_SIZES), help="3840, 7680 and/or mvc")
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
    ap.add_argument("--mvc-encoder", default="x264mvc", choices=list(MVC_ENCODERS), help="for --size mvc")
    ap.add_argument("--mvc-preset", default="slow")
    ap.add_argument("--mvc-crf", type=int, default=18)
    ap.add_argument("--mvc-kbps", type=int, default=28000)
    ap.add_argument("--x264mvc", default="", help="path to x264-mvc.exe")
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
                crop_tb=a.crop_tb, vk_device=a.gpu, mvc_encoder=a.mvc_encoder, mvc_preset=a.mvc_preset,
                mvc_crf=a.mvc_crf, mvc_kbps=a.mvc_kbps, x264mvc=a.x264mvc)
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
            if a.print_cmd and size == "mvc":
                print("MVC output runs ffmpeg -> MVC encoder -> MKV mux; the exact commands are logged while converting.")
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
