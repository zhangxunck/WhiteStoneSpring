#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「白石溪」品牌标识：宋体转 path（零字体依赖）+ 线条画式处理。

设计手法——只取两个抽象风格，不临摹任何具体作品形态：
- 横向贯穿线（late-line-drawing 传统简化）：在每个字主字之上叠加 3 条
  等粗、等宽、带轻微弧度的水平线，制造"用线勾出字形"的印象；线不停在
  字形内——视觉上是连续贯穿字与字之间的气流，呼应"溪"
- 错位重影：同字形右下微移的实心剪影副本（低透明）；字形本身不挖空，保持完整识别度
- 几何切割感：贯穿线两端出字后继续延 30% 字宽，端点平切，形成"几何延长线"
- 不用描边填色（避免粗描边卡通感），不用 mask 挖空（避免主字变灰）

产出：
- assets/brand_白石溪_字标.svg   墨色，页头/水印
- assets/brand_白石溪_印章.svg   白文红底朱印，favicon/头像

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
LINE_Y_RATIO = (0.30, 0.50, 0.72)   # 3 条贯穿线的纵向位置（相对字高）
LINE_WEIGHT = 3.2                    # 线宽（等粗统一）
LINE_OVERHANG = 0.30                 # 线两端出字延伸（相对字宽）
GHOST_DX, GHOST_DY = 7.0, 7.0
GHOST_OP = 0.18

# 三字独立间距：溪笔画最密，给更多呼吸
TRACKS = {"白": 28.0, "石": 30.0, "溪": 38.0}
X0 = 26.0


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


def build(emblem: bool) -> str:
    paths = [glyph(c, SIZE) for c in CHARS]
    total_adv = sum(adv for _, adv, _ in paths) + sum(TRACKS[c] for c in CHARS[:-1])
    w = X0 * 2 + total_adv
    h = SIZE + 50
    ink = "#FDFCF7" if emblem else "#1A1A1A"
    ghost_color = ink if emblem else "#1A1A1A"

    # 找整组字的并集横向边界（用于贯穿线端点）
    x = X0
    positions = []
    gx_min, gx_max = 1e9, -1e9
    gy_min, gy_max = 1e9, -1e9
    for ch, (d, adv, bb) in zip(CHARS, paths):
        bx0, by0, bx1, by1 = bb
        positions.append((d, adv, x, bx0, by0, bx1, by1))
        gx_min = min(gx_min, bx0 + x)
        gx_max = max(gx_max, bx1 + x)
        gy_min = min(gy_min, by0)
        gy_max = max(gy_max, by1)
        x += adv + TRACKS[ch]

    # 主字层（实心，识别度保底）
    main = []
    for d, adv, tx, *_ in positions:
        main.append(f'  <path d="{d}" transform="translate({tx:.1f},0)" fill="{ink}"/>')
    # 重影剪影层（实心低透明）
    ghost = []
    for d, adv, tx, *_ in positions:
        ghost.append(
            f'  <path d="{d}" transform="translate({tx + GHOST_DX:.1f},{GHOST_DY:.1f})" '
            f'fill="{ghost_color}" fill-opacity="{GHOST_OP}"/>')

    # 贯穿线：跨整组字，但避开每个字形 bbox —— 在字间空白处延伸
    # 用 stroke-dasharray 不行（宽度不固定），改用 "断笔" 法：
    # 每条 y 上的贯穿线 = N 段，每段对应一个"字间空白区"
    bar_y = [gy_min + (gy_max - gy_min) * r for r in LINE_Y_RATIO]
    bars = []
    # 字间空白区间（每个字 bbox 之外的左右延伸）
    # positions 元素 = (d, adv, x, bx0, by0, bx1, by1)
    gaps = [(X0, positions[0][2] + positions[0][3])]  # 第一个字之前
    for i in range(len(positions) - 1):
        left_end = positions[i][2] + positions[i][5]     # i 字 bbox 右缘
        right_start = positions[i + 1][2] + positions[i + 1][3]  # i+1 字 bbox 左缘
        gaps.append((left_end, right_start))
    gaps.append((positions[-1][2] + positions[-1][5], w - X0))  # 最后一个字之后
    # 左右各延伸 30% 字宽
    ext = SIZE * LINE_OVERHANG
    gaps[0] = (gaps[0][0] - ext, gaps[0][1])
    gaps[-1] = (gaps[-1][0], gaps[-1][1] + ext)

    for y in bar_y:
        bow = (y - (gy_min + gy_max) / 2) * 0.04
        for g0, g1 in gaps:
            if g1 <= g0:
                continue
            bars.append(
                f'  <path d="M {g0:.1f} {y:.1f} '
                f'Q {(g0+g1)/2:.1f} {y+bow:.1f} {g1:.1f} {y:.1f}" '
                f'fill="none" stroke="{ink}" stroke-width="{LINE_WEIGHT:.2f}" stroke-linecap="butt"/>')

    if emblem:
        bg = (f'  <rect x="0" y="0" width="{w:.1f}" height="{h:.1f}" fill="#B81C1C"/>\n'
              f'  <rect x="8" y="8" width="{w-16:.1f}" height="{h-16:.1f}" fill="none" '
              f'stroke="{ink}" stroke-width="2.4" stroke-opacity="0.42"/>\n')
        # 右下角两道水波（呼应「溪」）
        tail = (f'  <g fill="none" stroke="{ink}" stroke-width="1.6" stroke-opacity="0.30" '
                f'stroke-linecap="round">\n'
                f'    <path d="M {w-92:.1f} {h-22:.1f} q 16 -7 32 0 t 32 0"/>\n'
                f'    <path d="M {w-86:.1f} {h-12:.1f} q 14 -6 28 0 t 28 0"/>\n  </g>\n')
    else:
        bg = ""
        tail = ""

    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" '
            f'width="{w:.0f}" height="{h:.0f}" '
            f'role="img" aria-label="White Stone Spring 白石溪">\n'
            f'  <title>白石溪 White Stone Spring</title>\n'
            f'  <desc>Wordmark: solid character forms with three equal-weight horizontal line strokes '
            f'spanning the full width, plus a low-opacity offset silhouette. Original geometry; no '
            f'third-party artwork reproduced.</desc>\n'
            f'{bg}{chr(10).join(ghost)}\n{chr(10).join(main)}\n{chr(10).join(bars)}\n{tail}</svg>\n')


def build_monogram(ink_bg="#B81C1C", ink="#FDFCF7") -> str:
    """方形单字「白」印章 —— favicon / 头像专用。
    横版三字在 32px 以下必然糊成一团，故另出单字方章。
    """
    d, adv, bb = glyph("白", SIZE * 1.34)
    bx0, by0, bx1, by1 = bb
    gw, gh = bx1 - bx0, by1 - by0
    m = 14.0
    size = max(gw, gh) + m * 2
    tx = (size - gw) / 2 - bx0
    ty = (size - gh) / 2 - by0
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size:.0f} {size:.0f}" '
            f'width="{size:.0f}" height="{size:.0f}" role="img" aria-label="白石溪">\n'
            f'  <title>白石溪</title>\n'
            f'  <rect x="0" y="0" width="{size:.0f}" height="{size:.0f}" fill="{ink_bg}"/>\n'
            f'  <rect x="{m*0.42:.1f}" y="{m*0.42:.1f}" width="{size-m*0.84:.0f}" '
            f'height="{size-m*0.84:.0f}" fill="none" stroke="{ink}" stroke-width="2.6" '
            f'stroke-opacity="0.5"/>\n'
            f'  <path d="{d}" transform="translate({GHOST_DX:.1f},{GHOST_DY:.1f})" fill="{ink}" '
            f'fill-opacity="0.28"/>\n'
            f'  <path d="{d}" transform="translate({tx:.1f},{ty:.1f})" fill="{ink}"/>\n'
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