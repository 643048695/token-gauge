# -*- coding: utf-8 -*-
"""生成透明底真实感燃烧太阳 GIF（fbm 等离子表面 + 球体光照 + 沸腾动画）。
3 风格: plasma 橙黄 / lava 熔岩暗红 / cyber 赛博绿。输出 ui/assets/sun_<style>.gif"""
import numpy as np
from PIL import Image
import os

W = 240
CX = CY = W // 2
R = 100          # 球体半径
FRAMES = 36      # 帧数
DUR = 120        # ms/帧 -> 4.3s 循环
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui", "assets")

def fbm_field(phase, seed, freq0=1.6, octaves=4):
    """低分辨率值噪声场 -> bilinear 放大（平滑无混叠的等离子湍流）。"""
    LS = 96                                   # 低分辨率网格
    x = (np.arange(LS)[:, None] - LS / 2) / (LS / 2)
    y = (np.arange(LS)[None, :] - LS / 2) / (LS / 2)
    v = np.zeros((LS, LS))
    amp, fr = 1.0, freq0
    for o in range(octaves):
        ph = phase * (o * 0.53 + 1) + seed * 7.3 + o * 2.1
        v += amp * (np.sin(x * fr * 3.1 + ph) * np.cos(y * fr * 3.1 - ph * 0.8)
                    + 0.5 * np.sin((x + y) * fr * 2.2 + ph * 1.4))
        amp *= 0.5
        fr *= 2.0
    v /= (2.0 * (1 - 0.5 ** octaves) / (1 - 0.5))
    # 平滑放大到 WxW
    from PIL import Image as _I
    lo = _I.fromarray(((v - v.min()) / (v.max() - v.min()) * 255).astype(np.uint8), "L")
    hi = lo.resize((W, W), _I.BILINEAR)
    return (np.asarray(hi, dtype=np.float32) / 255.0 - 0.5) * 2.0

def render_frame(phase, style):
    """黑底太阳帧（配合 CSS mix-blend-mode:screen 实现透明发光，规避透明 GIF 兼容坑）。"""
    xx, yy = np.meshgrid(np.arange(W), np.arange(W))
    d = np.sqrt((xx - CX) ** 2 + (yy - CY) ** 2) / R          # 0..1+（边缘外 >1）
    mask = d <= 1.0
    noise = fbm_field(phase, style["seed"], style.get("freq", 1.6))
    n = np.clip(noise * 0.5 + 0.5, 0, 1)                      # 0..1 表面噪声

    # ---- 球体基础色（两段插值：核心亮白 → 中段主色 → 边缘暗色）----
    core = np.clip(1 - d, 0, 1) ** 1.15
    c0, c1, c2 = style["core"], style["mid"], style["edge"]    # RGB 三元组
    base = np.zeros((W, W, 3))
    for i in range(3):
        # core=1(中心)→c0, core=0.55→c1, core=0(边缘)→c2
        base[:, :, i] = (c0[i] + (c1[i] - c0[i]) * np.clip((1 - core) / 0.45, 0, 1)
                         + (c2[i] - c1[i]) * np.clip((0.55 - core) / 0.55, 0, 1))

    # ---- 噪声调制：亮斑随噪声、暗纹随噪声反转（等离子沸腾）----
    glow = np.clip(n * 1.3 - 0.2, 0, 1)
    dark = np.clip(1.25 - n * 1.1, 0, 1) * 0.4
    mod = 0.66 + 0.34 * glow - 0.22 * dark
    hshift = (glow - 0.5) * style.get("hue", 60) * mask      # 色相偏移仅限球内（球外保持纯黑）
    img = np.zeros((W, W, 3), dtype=np.float32)
    for i in range(3):
        img[:, :, i] = np.clip(base[:, :, i] * mod + hshift * (style["hl"][i] - base[:, :, i]) * 0.12, 0, 255)
    img *= mask[..., None]                                    # 球外强制纯黑（screen 混合才干净）

    # ---- 球体本体（黑底：球外黑色，screen 混合后消失）----
    img[mask, :] *= np.clip(1 - d[mask, None] * 0.05, 0, 1)

    # ---- 高光（左上球面反射 + 左下环境光）----
    hx, hy, hr = CX - R * 0.34, CY - R * 0.36, R * 0.30
    hd = np.sqrt((xx - hx) ** 2 + (yy - hy) ** 2) / hr
    hl = np.exp(-hd ** 2 * 2.2) * mask * 0.55
    for i in range(3):
        img[:, :, i] += hl * (255 - img[:, :, i]) * 0.85
    hx2, hy2, hr2 = CX + R * 0.30, CY + R * 0.42, R * 0.16
    hd2 = np.sqrt((xx - hx2) ** 2 + (yy - hy2) ** 2) / hr2
    hl2 = np.exp(-hd2 ** 2 * 2.5) * mask * 0.18
    for i in range(3):
        img[:, :, i] += hl2 * (255 - img[:, :, i]) * 0.7

    return np.clip(img, 0, 255).astype(np.uint8)

STYLES = {
    "plasma": dict(seed=7, freq=2.6,
                   core=(255, 250, 214), mid=(255, 154, 46), edge=(163, 32, 0),
                   hl=(255, 245, 200), hue=50, corona=0.9, corona_rgb=(255, 120, 20)),
    "lava":   dict(seed=11, freq=4.2,
                   core=(255, 190, 120), mid=(140, 30, 10), edge=(40, 4, 0),
                   hl=(255, 220, 160), hue=30, corona=0.55, corona_rgb=(200, 60, 10)),
    "cyber":  dict(seed=3, freq=3.0,
                   core=(214, 255, 234), mid=(0, 201, 110), edge=(0, 62, 32),
                   hl=(220, 255, 240), hue=-40, corona=0.75, corona_rgb=(0, 255, 156)),
}

def main():
    os.makedirs(OUT, exist_ok=True)
    for name, st in STYLES.items():
        frames = []
        for f in range(FRAMES):
            phase = f / FRAMES * np.pi * 2 * 1.1   # 表面流动
            frames.append(Image.fromarray(render_frame(phase, st), "RGB"))
        path = os.path.join(OUT, f"sun_{name}.gif")
        frames[0].save(path, save_all=True, append_images=frames[1:],
                       duration=DUR, loop=0, disposal=3)
        print(f"{name}: {os.path.getsize(path)/1024:.0f}KB  {W}x{W} {FRAMES}帧 x{DUR}ms")

if __name__ == "__main__":
    main()
