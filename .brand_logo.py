#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「白石溪」品牌标识：宋体转 path（零字体依赖）+ 流动水纹设计语言。

设计意象——「流动不居」（stream that never stays）：
- 白石溪的水不是静止横条，而是**三股平行正弦水波**横贯字标下方，
  峰谷起伏、错相错频，制造「弹跳/涌动」的动感
- 单字章用「溪」（而非「白」）——溪本身就是流动与春的意象，
  章内底部嵌双水波，朱印与活水同框
- 错位重影：字形右下微移的实心剪影（低透明），印刷错位 + 动感余像

只取抽象原则（几何、减笔、水纹），不复刻任何受版权保护字体 / 具体作品形态。

产出：
- assets/brand_白石溪_字标.svg   墨色实心三字 + 底部三股水波，页头/水印
- assets/brand_白石溪_印章.svg   白文朱印 + 水波，封面/压角
- assets/brand_白石溪_单字章.svg 方形朱底「溪」+ 内嵌水波，favicon/头像

用法：.venv/bin/python3 .brand_logo.py
"""
import os
from fontTools.ttLib import TTCollection
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import ControlBoundsPen
from fontTools.misc.transform import Transform
from fontTools.pens.transformPen import TransformPen

ROOT = os.path.dirname(os.path.abspath(__file__))
FONT = "/System/Library/Fonts/Supplemental/Songti.ttc"
CHARS = "白石溪"

SIZE = 104.0
TRACKS = {"白": 28.0, "石": 30.0, "溪": 38.0}
X0 = 26.0
GHOST_DX, GHOST_DY = 7.0, 7.0
GHOST_OP = 0.18
LINE_WEIGHT = 3.2

# 水波参数：字标底部三股，错相位、错振幅，营造「流动不居」的涌动弹跳感
WAVE_AMP = 4.6        # 振幅
WAVE_LEN = 46.0       # 一个波长
WAVE_WEIGHT = 3.0     # 水波线宽
WAVES = [             # 三股：(相对字底偏移, 相位, 振幅系数)
    (6.0, 0.0, 1.0),
    (20.0, 1.4, 0.85),
    (34.0, 2.8, 1.0),
]


def face_for(ch):
    coll = TTCollection(FONT, lazy=False)
    for f in coll.fonts:
        if ord(ch) in f.getBestCmap():
            return f
    raise SystemExit("字体缺字: %s" % ch)


def glyph(ch, size):
    font = face_for(ch)
    upm = font["head"].unitsPerEm
    gs = font.getGlyphSet()
    name = font.getBestCmap()[ord(ch)]
    xf = Transform(size / upm, 0, 0, -size / upm, 0, size)
    pen = SVGPathPen(gs, ntos=lambda v: "%.2f" % v)
    gs[name].draw(TransformPen(pen, xf))
    bp = ControlBoundsPen(gs)
    gs[name].draw(TransformPen(bp, xf))
    adv = font["hmtx"][name][0] * size / upm
    return pen.getCommands(), adv, bp.bounds


def sine_wave(x0, x1, y, amp, phase, length):
    """生成一段正弦水波 path（平滑 Q 曲线近似），返回 d 字符串。"""
    import math
    # 分段：每半波长一段 Q
    n = max(2, int((x1 - x0) / length) * 2)   # 半波数量
    step = (x1 - x0) / n
    pts = [x0]
    segs = []
    cur_x = x0
    for i in range(n):
        mid = cur_x + step / 2
        end = cur_x + step
        # 交替上下：峰/谷
        sign = 1.0 if (i % 2 == 0) else -1.0
        ypeak = y - sign * amp
        segs.append((mid, ypeak, end))
        cur_x = end
    d = "M %.1f %.1f " % (x0, y)
    for mid, ypeak, end in segs:
        d += "Q %.1f %.1f %.1f %.1f " % (mid, ypeak, end, y)
    return d.strip()


def build(emblem: bool) -> str:
    paths = [glyph(c, SIZE) for c in CHARS]
    total_adv = sum(adv for _, adv, _ in paths) + sum(TRACKS[c] for c in CHARS[:-1])
    w = X0 * 2 + total_adv
    h = SIZE + 52
    ink = "#FDFCF7" if emblem else "#1A1A1A"

    x = X0
    positions = []
    for ch, (d, adv, bb) in zip(CHARS, paths):
        positions.append((d, adv, x))
        x += adv + TRACKS[ch]

    # 主字（实心）
    main = []
    for d, adv, tx in positions:
        main.append(f'  <path d="{d}" transform="translate({tx:.1f},0)" fill="{ink}"/>')
    # 重影剪影
    ghost = []
    for d, adv, tx in positions:
        ghost.append(
            f'  <path d="{d}" transform="translate({tx + GHOST_DX:.1f},{GHOST_DY:.1f})" '
            f'fill="{ink}" fill-opacity="{GHOST_OP}"/>')

    # 底部三股水波（横跨全幅，字下方，制造「流动不居」）
    water_top = SIZE + 4
    x_left = 4.0
    x_right = w - 4.0
    waves = []
    for off, phase, ampk in WAVES:
        y = water_top + off * 0.62
        d = sine_wave(x_left, x_right, y, WAVE_AMP * ampk, phase, WAVE_LEN)
        waves.append(
            f'  <path d="{d}" fill="none" stroke="{ink}" '
            f'stroke-width="{WAVE_WEIGHT:.2f}" stroke-linecap="round" '
            f'stroke-opacity="{"0.9" if off < 10 else "0.55"}"/>')

    bg = ""
    tail = ""
    if emblem:
        bg = (f'  <rect x="0" y="0" width="{w:.1f}" height="{h:.1f}" fill="#B81C1C"/>\n'
              f'  <rect x="8" y="8" width="{w-16:.1f}" height="{h-16:.1f}" fill="none" '
              f'stroke="{ink}" stroke-width="2.4" stroke-opacity="0.42"/>\n')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" '
            f'width="{w:.0f}" height="{h:.0f}" '
            f'role="img" aria-label="White Stone Spring 白石溪">\n'
            f'  <title>白石溪 White Stone Spring</title>\n'
            f'  <desc>Wordmark: solid character forms above three flowing water-current '
            f'lines, plus a low-opacity offset silhouette. Motif of "flow that never '
            f'stays". Original geometry; no third-party artwork reproduced.</desc>\n'
            f'{bg}{chr(10).join(ghost)}\n{chr(10).join(main)}\n{chr(10).join(waves)}\n'
            f'{tail}</svg>\n')


def build_monogram() -> str:
    """方形单字「溪」印章 —— favicon / 头像。
    章内底部嵌双水波，朱印 + 活水同框，呼应「流动不居」。
    """
    d, adv, bb = glyph("溪", SIZE * 1.28)
    bx0, by0, bx1, by1 = bb
    gw, gh = bx1 - bx0, by1 - by0
    m = 20.0
    size = max(gw, gh) + m * 2
    tx = (size - gw) / 2 - bx0
    ty = (size - gh) / 2 - by0 - 8.0     # 字略上抬，给底部水波留位
    ink = "#FDFCF7"
    bg = "#B81C1C"

    # 章内双水波（字下方）
    wv = []
    for off, ampk in [(8.0, 1.0), (18.0, 0.7)]:
        y = size - 30 + off * 0.6
        d = sine_wave(14, size - 14, y, 3.4 * ampk, off, WAVE_LEN * 0.8)
        wv.append(f'  <path d="{d}" fill="none" stroke="{ink}" stroke-width="2.4" '
                  f'stroke-linecap="round" stroke-opacity="{"0.85" if off < 12 else "0.5"}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size:.0f} {size:.0f}" '
            f'width="{size:.0f}" height="{size:.0f}" role="img" aria-label="白石溪">\n'
            f'  <title>白石溪 · 溪</title>\n'
            f'  <desc>Monogram seal: character 溪 (stream) on a vermillion field with two '
            f'flowing water lines. Motif of "flow that never stays". Original geometry; '
            f'no third-party artwork reproduced.</desc>\n'
            f'  <rect x="0" y="0" width="{size:.0f}" height="{size:.0f}" fill="{bg}"/>\n'
            f'  <rect x="{m*0.4:.1f}" y="{m*0.4:.1f}" width="{size-m*0.8:.0f}" '
            f'height="{size-m*0.8:.0f}" fill="none" stroke="{ink}" stroke-width="2.6" '
            f'stroke-opacity="0.5"/>\n'
            f'  <path d="{d}" transform="translate({tx + GHOST_DX:.1f},{ty + GHOST_DY:.1f})" '
            f'fill="{ink}" fill-opacity="0.26"/>\n'
            f'  <path d="{d}" transform="translate({tx:.1f},{ty:.1f})" fill="{ink}"/>\n'
            f'{chr(10).join(wv)}\n'
            f'</svg>\n')


if __name__ == "__main__":
    a = os.path.join(ROOT, "assets", "brand_白石溪_字标.svg")
    b = os.path.join(ROOT, "assets", "brand_白石溪_印章.svg")
    c = os.path.join(ROOT, "assets", "brand_白石溪_单字章.svg")
    open(a, "w", encoding="utf-8").write(build(False))
    open(b, "w", encoding="utf-8").write(build(True))
    open(c, "w", encoding="utf-8").write(build_monogram())
    for p in (a, b, c):
        print(os.path.basename(p), os.path.getsize(p), "B")
