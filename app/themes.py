"""主题系统 v6：5 大风格（含黑客帝国）+ 换色 + 迷你窗形态。

阵容：
  paper     纸面极简    （无换色）
  8bit      8位像素风    （换色：红白机 / 掌机绿 / 世嘉红）
  matrix    黑客帝国    （矩阵绿，换色：经典矩阵绿 / 磷光青绿 / 毒绿）
  brutal    粗野主义    （无换色）
  redacted  机密档案    （无换色）

build_css(style_id, variant=None) -> CSS（:root 变量 + 主面板形态 + 迷你窗形态）
"""

DEFAULT_STYLE = "paper"

_WARN = "#d97706"
_DANGER = "#b91c1c"


def _hex_to_rgb(color):
    if not color or not isinstance(color, str):
        return None
    h = color.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    if len(h) != 6:
        return None
    try:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return None


def _rgba(hex_color, alpha):
    rgb = _hex_to_rgb(hex_color)
    if rgb is None:
        rgb = (100, 150, 200)
    return "rgba(%d,%d,%d,%s)" % (rgb[0], rgb[1], rgb[2], alpha)


# ================================================================ 8bit 配色
_8BIT_NES = {
    "accent": "#ffd54f", "accent2": "#4fc3f7",
    "bg": "#1a237e", "text": "#fafafa", "muted": "#9fb0d9",
    "glow": "rgba(255,213,79,0.45)",
    "card": "rgba(255,213,79,0.08)", "card-hi": "rgba(255,213,79,0.14)",
    "line": "rgba(255,213,79,0.35)", "panel": "rgba(79,195,247,0.08)",
    "border": "#ffd54f", "radius": "0px",
}
_8BIT_GB = {
    "accent": "#9bbc0f", "accent2": "#8bac0f",
    "bg": "#0f380f", "text": "#e0e6c3", "muted": "#a9c98a",   # muted 提亮（原 #758c4e 与深绿 bg 对比低，字体不清晰）
    "glow": "rgba(155,188,15,0.45)",
    "card": "rgba(155,188,15,0.08)", "card-hi": "rgba(155,188,15,0.14)",
    "line": "rgba(155,188,15,0.35)", "panel": "rgba(155,188,15,0.08)",
    "border": "#9bbc0f", "radius": "0px",
}
_8BIT_SEGA = {
    "accent": "#e60012", "accent2": "#ffdd00",
    "bg": "#1a1a1a", "text": "#f5f5f5", "muted": "#9a9a9a",
    "glow": "rgba(230,0,18,0.45)",
    "card": "rgba(230,0,18,0.08)", "card-hi": "rgba(230,0,18,0.14)",
    "line": "rgba(255,221,0,0.35)", "panel": "rgba(255,221,0,0.06)",
    "border": "#e60012", "radius": "0px",
}

# ================================================================ 黑客帝国配色
_MATRIX = {
    "accent": "#00ff41", "accent2": "#00e5a0",
    "bg": "#000000", "text": "#c8ffd9", "muted": "#3f9f5f",
    "glow": "rgba(0,255,65,0.5)",
    "card": "rgba(0,255,65,0.05)", "card-hi": "rgba(0,255,65,0.09)",
    "line": "rgba(0,255,65,0.3)", "panel": "rgba(0,255,65,0.05)",
    "border": "rgba(0,255,65,0.35)", "radius": "2px",
}
_MATRIX_PHOSPHOR = {
    "accent": "#1fff9e", "accent2": "#00b37e",
    "bg": "#020d08", "text": "#d9ffe9", "muted": "#5aa87e",
    "glow": "rgba(31,255,158,0.5)",
    "card": "rgba(31,255,158,0.05)", "card-hi": "rgba(31,255,158,0.09)",
    "line": "rgba(31,255,158,0.3)", "panel": "rgba(31,255,158,0.05)",
    "border": "rgba(31,255,158,0.35)", "radius": "2px",
}
_MATRIX_VENOM = {
    "accent": "#8aff2e", "accent2": "#ccff00",
    "bg": "#0a1200", "text": "#eeffe0", "muted": "#7aa860",
    "glow": "rgba(138,255,46,0.5)",
    "card": "rgba(138,255,46,0.05)", "card-hi": "rgba(138,255,46,0.09)",
    "line": "rgba(204,255,0,0.3)", "panel": "rgba(138,255,46,0.05)",
    "border": "rgba(138,255,46,0.35)", "radius": "2px",
}

STYLES = {
    # ================================================================ 纸面极简
    "paper": {
        "name": "纸面极简",
        "desc": "白纸清单 · 表格化",
        "palettes": [],
        "vars": {
            "accent": "#537d96", "accent2": "#6f9cb5",
            "bg": "#f5efe4", "text": "#2a2622", "muted": "#7a7266",
            "glow": "rgba(83,125,150,0.25)",
            "card": "#fbf7ee", "card-hi": "#ffffff",
            "line": "rgba(42,38,34,0.12)", "panel": "rgba(83,125,150,0.06)",
            "border": "#d8cfbe", "radius": "6px",
        },
        "css": (
            "body[data-style='paper']{background:#f5efe4}"
            "body[data-style='paper'] .pcard,body[data-style='paper'] .prow-card,"
            "body[data-style='paper'] .add-panel{background:#fbf7ee;"
            "border:1px solid #d8cfbe;border-radius:6px;box-shadow:0 1px 2px rgba(42,38,34,0.05)}"
            "body[data-style='paper'] .pcard .pcard-title{border-bottom:1px solid #e8e0d0;padding-bottom:4px}"
            "body[data-style='paper'] .bar{height:6px;background:#efe9dc;border-radius:3px}"
            "body[data-style='paper'] .fill{background:#537d96;border-radius:3px;box-shadow:none}"
            "body[data-style='paper'] .fill.warn{background:#b07a1e}"
            "body[data-style='paper'] .fill.danger{background:#8b2c1f}"
            "body[data-style='paper'] .nav-item{border:none;border-bottom:2px solid transparent;border-radius:0;color:#7a7266}"
            "body[data-style='paper'] .nav-item.active{background:none;color:#2a2622;border-bottom-color:#537d96}"
            "body[data-style='paper'] input,body[data-style='paper'] select{background:#fff;border-color:#d8cfbe;color:#2a2622}"
            "body[data-style='paper'] .page-head h1{font-family:'EB Garamond','Noto Serif SC',serif;letter-spacing:1px}"
        ),
    },
    # ================================================================ 8位像素
    "8bit": {
        "name": "8位像素",
        "desc": "像素方块 · 复古机台",
        "palettes": [
            {"id": "nes", "name": "红白机", "colors": ["#1a237e", "#ffd54f", "#e53935"]},
            {"id": "gameboy", "name": "掌机绿", "colors": ["#0f380f", "#9bbc0f", "#e0e6c3"]},
            {"id": "sega", "name": "世嘉红", "colors": ["#1a1a1a", "#e60012", "#ffdd00"]},
        ],
        "vars": dict(_8BIT_NES),
        "css": (
            "body[data-style='8bit']{background:#1a237e;image-rendering:pixelated}"
            "body[data-style='8bit']::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;"
            "background-image:linear-gradient(var(--line) 1px,transparent 1px),"
            "linear-gradient(90deg,var(--line) 1px,transparent 1px);background-size:14px 14px}"
            "body[data-style='8bit'] .pcard,body[data-style='8bit'] .prow-card,"
            "body[data-style='8bit'] .add-panel{background:var(--card-hi);"
            "border:4px solid var(--border);border-radius:0;"
            "box-shadow:6px 6px 0 rgba(0,0,0,0.5),inset 0 0 0 3px var(--bg)}"
            "body[data-style='8bit'] .bar{height:12px;background:rgba(0,0,0,0.45);border-radius:0;"
            "border:2px solid var(--border)}"
            "body[data-style='8bit'] .fill{background:repeating-linear-gradient(90deg,var(--accent) 0 8px,var(--muted) 8px 10px);"
            "box-shadow:none;border-radius:0}"
            "body[data-style='8bit'] .nav-item{border:2px solid var(--border);border-radius:0;"
            "box-shadow:3px 3px 0 rgba(0,0,0,0.5);background:var(--card-hi);color:var(--text);"
            "font-family:var(--font-num)}"
            "body[data-style='8bit'] .nav-item.active{background:var(--accent2);color:#fff;border-color:var(--border)}"
            "body[data-style='8bit'] .page-head h1{color:var(--accent);"
            "text-shadow:2px 2px 0 #000,4px 4px 0 rgba(0,0,0,0.4);font-family:var(--font-num)}"
            "body[data-style='8bit'] input,body[data-style='8bit'] select{background:var(--bg);"
            "border:2px solid var(--border);color:var(--text);border-radius:0;font-family:var(--font-num)}"
            "body[data-style='8bit'] #titlebar{background:var(--card-hi)}"
            "body[data-style='8bit'] #nav{background:var(--bg);border-right:3px solid var(--border)}"
            "body[data-style='8bit'] .add-provider-btn,.add-actions button{border:2px solid var(--border);border-radius:0}"
        ),
    },
    # ================================================================ 黑客帝国
    "matrix": {
        "name": "黑客帝国",
        "desc": "矩阵绿屏 · 数字雨",
        "palettes": [
            {"id": "matrix", "name": "经典矩阵绿", "colors": ["#000000", "#00ff41", "#00e5a0"]},
            {"id": "phosphor", "name": "磷光青绿", "colors": ["#020d08", "#1fff9e", "#00b37e"]},
            {"id": "venom", "name": "毒绿", "colors": ["#0a1200", "#8aff2e", "#ccff00"]},
        ],
        "vars": dict(_MATRIX),
        "css": (
            "body[data-style='matrix']{background:#000;font-family:var(--font-num)}"
            "body[data-style='matrix']::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;"
            "background-image:repeating-linear-gradient(90deg,transparent 0 26px,rgba(0,255,65,0.05) 26px 27px),"
            "repeating-linear-gradient(180deg,transparent 0 18px,rgba(0,255,65,0.04) 18px 19px)}"
            "body[data-style='matrix']::after{content:'';position:fixed;top:0;left:-60%;width:40%;height:2px;z-index:0;"
            "background:linear-gradient(90deg,transparent,rgba(0,255,65,0.5),transparent);"
            "animation:matscan 4s linear infinite;pointer-events:none}"
            "@keyframes matscan{to{left:120%}}"
            "body[data-style='matrix'] .pcard,body[data-style='matrix'] .prow-card,"
            "body[data-style='matrix'] .add-panel{background:var(--card);border:1px solid var(--border);border-radius:2px;"
            "box-shadow:0 0 14px rgba(0,255,65,0.1)}"
            "body[data-style='matrix'] .bar{height:8px;background:rgba(0,255,65,0.08);border-radius:0;"
            "border:1px solid var(--border)}"
            "body[data-style='matrix'] .fill{background:repeating-linear-gradient(90deg,var(--accent) 0 7px,rgba(0,255,65,0.2) 7px 9px);"
            "box-shadow:0 0 10px rgba(0,255,65,0.5);border-radius:0}"
            "body[data-style='matrix'] .nav-item{border-radius:0;border:1px solid var(--border);"
            "background:var(--panel);letter-spacing:2px;font-family:var(--font-num)}"
            "body[data-style='matrix'] .nav-item.active{background:var(--card-hi);border-color:var(--accent);"
            "box-shadow:0 0 10px rgba(0,255,65,0.2)}"
            "body[data-style='matrix'] .page-head h1{color:var(--accent);letter-spacing:4px;"
            "text-shadow:0 0 14px rgba(0,255,65,0.6)}"
            "body[data-style='matrix'] input,body[data-style='matrix'] select{background:#000;border:1px solid var(--border);"
            "color:var(--text);border-radius:0;font-family:var(--font-num)}"
            "body[data-style='matrix'] #titlebar{background:rgba(0,255,65,0.05);border-bottom:1px solid var(--border)}"
            "body[data-style='matrix'] #nav{border-right:1px solid var(--border)}"
        ),
    },
    # ================================================================ 粗野主义
    "brutal": {
        "name": "粗野主义",
        "desc": "纯黑白 · 硬边框宣言",
        "palettes": [],
        "vars": {
            "accent": "#111111", "accent2": "#ffeb3b",
            "bg": "#f5f0e6", "text": "#000000", "muted": "#555555",
            "glow": "rgba(0,0,0,0.3)",
            "card": "#fbf7ef", "card-hi": "#f0ead9",
            "line": "#000000", "panel": "#f5f5f5",
            "border": "#000000", "radius": "0px",
        },
        "css": (
            "body[data-style='brutal']{background:#f5f0e6;color:#000}"
            "body[data-style='brutal'] .pcard,body[data-style='brutal'] .prow-card,"
            "body[data-style='brutal'] .add-panel{background:#fbf7ef;"
            "border:3px solid #000;border-radius:0;box-shadow:6px 6px 0 #000}"
            "body[data-style='brutal'] .pcard.live{border-left:10px solid #000}"
            "body[data-style='brutal'] .bar{height:10px;background:#ddd;border-radius:0;border:2px solid #000}"
            "body[data-style='brutal'] .fill{background:#000;box-shadow:none;border-radius:0}"
            "body[data-style='brutal'] .fill.warn{background:#555}"
            "body[data-style='brutal'] .fill.danger{background:#111}"
            "body[data-style='brutal'] .nav-item{border:2px solid #000;border-radius:0;box-shadow:3px 3px 0 #000;"
            "background:#fff;color:#000;font-weight:900;letter-spacing:1px}"
            "body[data-style='brutal'] .nav-item.active{background:#000;color:#fff}"
            "body[data-style='brutal'] .page-head h1{font-size:26px;font-weight:900;text-transform:uppercase;"
            "letter-spacing:2px;border-bottom:4px solid #000;padding-bottom:4px}"
            "body[data-style='brutal'] input,body[data-style='brutal'] select{background:#fff;border:2px solid #000;color:#000;border-radius:0}"
            "body[data-style='brutal'] #titlebar{background:#fbf7ef;border-bottom:3px solid #000}"
            "body[data-style='brutal'] #nav{border-right:3px solid #000;background:#f5f0e6}"
            "body[data-style='brutal'] .add-provider-btn,.add-actions button{border:2px solid #000;border-radius:0;font-weight:900}"
        ),
    },
    # ================================================================ 机密档案
    "redacted": {
        "name": "机密档案",
        "desc": "米色档案纸 · 红章涂黑",
        "palettes": [],
        "vars": {
            "accent": "#8b2c1f", "accent2": "#5a4632",
            "bg": "#e8dcc8", "text": "#3a3128", "muted": "#7a6b58",
            "glow": "rgba(139,44,31,0.3)",
            "card": "#f5efe3", "card-hi": "#fbf7ee",
            "line": "rgba(58,49,40,0.18)", "panel": "rgba(139,44,31,0.05)",
            "border": "#c9b99e", "radius": "2px",
        },
        "css": (
            "body[data-style='redacted']{background:#e8dcc8}"
            "body[data-style='redacted']::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;opacity:.35;"
            "background-image:linear-gradient(rgba(58,49,40,0.05) 1px,transparent 1px);background-size:100% 22px}"
            "body[data-style='redacted'] .pcard,body[data-style='redacted'] .prow-card,"
            "body[data-style='redacted'] .add-panel{background:#f5efe3;"
            "border:1px solid #c9b99e;border-radius:2px;box-shadow:0 1px 3px rgba(58,49,40,0.12);position:relative}"
            "body[data-style='redacted'] .pcard::after,body[data-style='redacted'] .prow-card::after{"
            "content:'CONFIDENTIAL';position:absolute;top:8px;right:10px;"
            "font-family:var(--font-num);font-size:9px;letter-spacing:2px;color:rgba(139,44,31,0.5);"
            "border:1px solid rgba(139,44,31,0.4);padding:1px 6px;transform:rotate(2deg)}"
            "body[data-style='redacted'] .bar{height:7px;background:rgba(58,49,40,0.14);border-radius:0;border:1px solid #c9b99e}"
            "body[data-style='redacted'] .fill{background:#5a4632;box-shadow:none;border-radius:0}"
            "body[data-style='redacted'] .fill.warn{background:#8b2c1f}"
            "body[data-style='redacted'] .fill.danger{background:#111}"
            "body[data-style='redacted'] .nav-item{border:none;border-left:3px solid transparent;border-radius:0;"
            "font-family:var(--font-num);font-size:12px}"
            "body[data-style='redacted'] .nav-item.active{background:rgba(139,44,31,0.08);border-left-color:#8b2c1f}"
            "body[data-style='redacted'] .page-head h1{font-family:var(--font-num);"
            "color:#8b2c1f;letter-spacing:3px;text-transform:uppercase}"
            "body[data-style='redacted'] input,body[data-style='redacted'] select{background:#fbf7ee;border:1px solid #b8a888;"
            "color:#3a3128;border-radius:0;font-family:var(--font-num)}"
            "body[data-style='redacted'] #titlebar{background:rgba(139,44,31,0.06);border-bottom:2px solid #8b2c1f}"
            "body[data-style='redacted'] #nav{background:rgba(255,255,255,0.18)}"
        ),
    },
}

# 配色注册表：style_id -> {variant_id: vars}
_PALETTES = {
    "8bit": {"nes": _8BIT_NES, "gameboy": _8BIT_GB, "sega": _8BIT_SEGA},
    "matrix": {"matrix": _MATRIX, "phosphor": _MATRIX_PHOSPHOR, "venom": _MATRIX_VENOM},
}

# 迷你窗形态（body[data-style] 作用于 mini 的 .hud 等）
_MINI_CSS = {
    "paper": (
        "body[data-style='paper'] .hud{background:#fbf7ee;border:1px solid #d8cfbe;border-radius:6px;"
        "box-shadow:0 1px 2px rgba(42,38,34,0.08)}"
        "body[data-style='paper'] .bar{background:#efe9dc}"
        "body[data-style='paper'] .fill{background:#537d96;box-shadow:none;border-radius:3px}"
    ),
    "8bit": (
        "body[data-style='8bit'] .hud{background:#283593;border:4px solid var(--border);border-radius:0;"
        "box-shadow:5px 5px 0 rgba(0,0,0,0.5)}"
        "body[data-style='8bit'] .bar{background:rgba(0,0,0,0.45);border:2px solid var(--border)}"
        "body[data-style='8bit'] .fill{background:repeating-linear-gradient(90deg,var(--accent) 0 6px,var(--muted) 6px 8px)}"
    ),
    "matrix": (
        "body[data-style='matrix'] .hud{background:#000;border:1px solid var(--border);border-radius:2px;"
        "box-shadow:0 0 14px rgba(0,255,65,0.15)}"
        "body[data-style='matrix'] .bar{background:rgba(0,255,65,0.08);border:1px solid var(--border)}"
        "body[data-style='matrix'] .fill{background:repeating-linear-gradient(90deg,var(--accent) 0 6px,rgba(0,255,65,0.2) 6px 8px);"
        "box-shadow:0 0 10px rgba(0,255,65,0.5)}"
    ),
    "brutal": (
        "body[data-style='brutal'] .hud{background:#fbf7ef;border:3px solid #000;border-radius:0;"
        "box-shadow:5px 5px 0 #000}"
        "body[data-style='brutal'] .bar{background:#ddd;border:2px solid #000}"
        "body[data-style='brutal'] .fill{background:#000;box-shadow:none}"
    ),
    "redacted": (
        "body[data-style='redacted'] .hud{background:#f5efe3;border:1px solid #c9b99e;border-radius:2px}"
        "body[data-style='redacted'] .bar{background:rgba(58,49,40,0.14);border:1px solid #c9b99e}"
        "body[data-style='redacted'] .fill{background:#5a4632;box-shadow:none}"
    ),
}


def list_styles():
    out = []
    for sid, s in STYLES.items():
        out.append({
            "id": sid, "name": s["name"], "desc": s["desc"],
            "palettes": s.get("palettes") or [],
        })
    return out


def build_css(style_id, variant=None):
    style = STYLES.get(style_id) or STYLES[DEFAULT_STYLE]
    vars_map = dict(style["vars"])

    if variant:
        palette_vars = _PALETTES.get(style_id, {}).get(variant)
        if palette_vars:
            vars_map.update(palette_vars)

    vars_map["warn"] = _WARN
    vars_map["danger"] = _DANGER
    vars_map["warn-glow"] = "rgba(217,119,6,0.45)"
    vars_map["danger-glow"] = "rgba(185,28,28,0.45)"

    parts = [":root{"]
    for key in ("accent", "accent2", "bg", "text", "muted", "glow", "warn",
                "danger", "warn-glow", "danger-glow", "card", "card-hi",
                "line", "panel", "border", "radius"):
        if key in vars_map:
            parts.append("--%s:%s;" % (key, vars_map[key]))
    parts.append("}")
    css = "".join(parts) + (style.get("css") or "") + _MINI_CSS.get(style_id, "")
    return css
