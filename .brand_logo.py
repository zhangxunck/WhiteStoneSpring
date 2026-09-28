#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""白石溪 / White Stone Spring — 品牌标识 v30（全套标准件 + 活字印刷阴刻版）

版本演进：
  - 标准版（阳文/底色版）：v29 绝对几何居中 + 零重叠清爽版式。
  - 阴刻版（活字印刷版）：
    1. 仿照毕昇活字·宋版古籍雕版与朱泥古印的阴刻形式（字面凹陷留白，印面朱红/玄黑充实）。
    2. 使用 SVG 滤镜（feTurbulence + feDisplacementMap）制造轻微的雕版刀痕、拓印墨晕与活字边缘手工质感。
    3. 阴刻正圆印章（朱泥白文）、阴刻方印（宋金古印白文）、阴刻字标（雕版木活字白文）。
"""
import os
import math
from fontTools.ttLib import TTFont, TTCollection
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import ControlBoundsPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform

ROOT = os.path.dirname(os.path.abspath(__file__))
CN_FONT = "/System/Library/Fonts/ヒラギノ明朝 ProN.ttc"
CN_FACE = "Hiragino Mincho ProN W3"
EN_FONT = "/System/Library/Fonts/Supplemental/SignPainter.ttc"
EN_INDEX = 0

CHARS = "白石溪"
INK = "#1A1A1A"
WHITE = "#FFFFFF"
RED = "#E03030"
BLACK = "#0A0A0A"

CN_SIZE = 56.0
CN_TRACKS = {"白": 12.0, "石": 14.0, "溪": 18.0}
EN_SIZE = 17.0
EN_TRACK = 0.8

GAP_RATIO = 0.12               # 中爻缺口 = 总宽 12%
N_SAMPLES = 96

# 活字印刷阴刻刀痕滤镜（全局统一：每个 path 都加此滤镜）
PRINT_FILTER = """  <defs>
    <filter id="movable-type-edge" x="-5%" y="-5%" width="110%" height="110%">
      <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" result="noise" seed="7" />
      <feDisplacementMap in="SourceGraphic" in2="noise" scale="1.4" xChannelSelector="R" yChannelSelector="G" />
    </filter>
  </defs>"""
INK_RIPPLE_FILTER = """    <filter id="ink-bleed" x="-5%" y="-5%" width="110%" height="110%">
      <feTurbulence type="fractalNoise" baseFrequency="0.025" numOctaves="2" result="noise" seed="3" />
      <feDisplacementMap in="SourceGraphic" in2="noise" scale="0.8" xChannelSelector="R" yChannelSelector="G" />
    </filter>"""


def _cn_face():
    for f in TTCollection(CN_FONT, lazy=False).fonts:
        if f["name"].getDebugName(4) == CN_FACE:
            return f
    raise SystemExit("CN face missing")


def _en_face():
    return TTCollection(EN_FONT, lazy=False).fonts[EN_INDEX]


def _glyph_d(face, ch, size):
    upm = face["head"].unitsPerEm
    gs = face.getGlyphSet()
    nm = face.getBestCmap().get(ord(ch))
    if nm is None:
        return None
    xf = Transform(size / upm, 0, 0, -size / upm, 0, size)
    pen = SVGPathPen(gs, ntos=lambda v: f"{v:.2f}")
    gs[nm].draw(TransformPen(pen, xf))
    return pen.getCommands(), face["hmtx"][nm][0] * size / upm


def _glyph_contours(face, ch, size):
    upm = face["head"].unitsPerEm
    gs = face.getGlyphSet()
    nm = face.getBestCmap().get(ord(ch))
    if nm is None:
        return []
    xf = Transform(size / upm, 0, 0, -size / upm, 0, size)
    rp = RecordingPen()
    gs[nm].draw(rp)
    contours, cur = [], []
    for op, args in rp.value:
        if op == "moveTo":
            if cur:
                contours.append(cur)
            cur = [("moveTo", args)]
        else:
            cur.append((op, args))
    if cur:
        contours.append(cur)
    out = []
    for ops in contours:
        pen = SVGPathPen(gs, ntos=lambda v: f"{v:.2f}")
        tp = TransformPen(pen, xf)
        for op, args in ops:
            getattr(tp, op)(*args)
        bp = ControlBoundsPen(gs)
        tp2 = TransformPen(bp, xf)
        for op, args in ops:
            getattr(tp2, op)(*args)
        out.append((pen.getCommands(), bp.bounds))
    return out


def _cn_layout(face):
    items, x = [], 0.0
    ink_boxes = []
    for ch in CHARS:
        g = _glyph_d(face, ch, CN_SIZE)
        if g is None:
            continue
        d, adv = g
        ink = None
        for _, bb in _glyph_contours(face, ch, CN_SIZE):
            if bb is None:
                continue
            b = (bb[0] + x, bb[1], bb[2] + x, bb[3])
            ink = b if ink is None else (min(ink[0], b[0]), min(ink[1], b[1]),
                                         max(ink[2], b[2]), max(ink[3], b[3]))
        items.append((d, x, ink))
        if ink:
            ink_boxes.append(ink)
        x += adv + CN_TRACKS[ch]
    total_w = x - CN_TRACKS[CHARS[-1]]
    total_ink = (min(b[0] for b in ink_boxes), min(b[1] for b in ink_boxes),
                 max(b[2] for b in ink_boxes), max(b[3] for b in ink_boxes))
    return items, total_w, total_ink


def _en_layout(face):
    items, x = [], 0.0
    ink_boxes = []
    i_dot_info = []              # (global_x, global_y, half_h) 灵感之火锚点
    for ch in "White Stone Spring":
        if ch == " ":
            x += EN_SIZE * 0.32
            continue
        g = _glyph_d(face, ch, EN_SIZE)
        if g is None:
            continue
        d, adv = g
        ink = None
        dot_seen_for_this_ch = False
        for cd, bb in _glyph_contours(face, ch, EN_SIZE):
            if bb is None:
                continue
            b = (bb[0] + x, bb[1], bb[2] + x, bb[3])
            ink = b if ink is None else (min(ink[0], b[0]), min(ink[1], b[1]),
                                         max(ink[2], b[2]), max(b[3], ink[3]))
            # i 的红圆点 = 灵感之火锚点（仅小写 i）
            if ch == "i":
                h = bb[3] - bb[1]
                if h < EN_SIZE * 0.28 and not dot_seen_for_this_ch:
                    cx = x + (bb[0] + bb[2]) / 2.0
                    cy = (bb[1] + bb[3]) / 2.0
                    i_dot_info.append((cx, cy, h * 0.50, cd))
                    dot_seen_for_this_ch = True
        items.append((d, x, ink))
        if ink:
            ink_boxes.append(ink)
        x += adv + EN_TRACK
    total_w = x - EN_TRACK
    total_ink = (min(b[0] for b in ink_boxes), min(b[1] for b in ink_boxes),
                 max(b[2] for b in ink_boxes), max(b[3] for b in ink_boxes))
    return items, total_w, total_ink, i_dot_info


# ==============================================================================
# 坎卦 ☵ 母版 — Braun 理性正弦实心带
# ==============================================================================
W_CANON = 1000.0
M = W_CANON / 24.0              # 模数 = 41.67
PITCH = 1.618 * M               # 瑞士黄金分割波距 = 67.4
THICK_HERO = 0.50 * M           # 中爻（主水脉）厚度 = 20.8
THICK_AUX = 0.20 * M            # 上/下爻厚度 = 8.3
AMP_HERO = 0.30 * M             # 中爻振幅 = 12.5
AMP_AUX = 0.38 * M              # 上/下爻振幅 = 15.8
CYCLES = 1.0


def _braun_ribbon(x0, x1, y, amp, thick, mirror=False, cycles=CYCLES, n=N_SAMPLES):
    top, bot = [], []
    for k in range(n + 1):
        t = k / n
        px = x0 + (x1 - x0) * t
        s = -1.0 if mirror else 1.0
        py = y + s * amp * math.sin(2.0 * math.pi * cycles * t)
        top.append((px, py - thick / 2.0))
        bot.append((px, py + thick / 2.0))
    pts = top + list(reversed(bot))
    d = [f"M {pts[0][0]:.2f} {pts[0][1]:.2f}"]
    for i in range(1, len(pts)):
        d.append(f"L {pts[i][0]:.2f} {pts[i][1]:.2f}")
    d.append("Z")
    return " ".join(d)


KAN_TOP = _braun_ribbon(0.0, W_CANON, -PITCH, AMP_AUX, THICK_AUX)
_half = 0.5 - GAP_RATIO / 2.0
KAN_YIN_L = _braun_ribbon(0.0, W_CANON * _half, 0.0, AMP_HERO, THICK_HERO, cycles=0.5)
KAN_YIN_R = _braun_ribbon(W_CANON * (1.0 - _half), W_CANON, 0.0,
                          AMP_HERO, THICK_HERO, cycles=0.5)
KAN_BOT = _braun_ribbon(0.0, W_CANON, PITCH, AMP_AUX, THICK_AUX, mirror=True)


def render_waves(x, yin_axis_y, width, hero_c, base_c, aux_opacity=0.38, with_filter=False):
    scale = width / W_CANON
    flt = ' filter="url(#movable-type-edge)"' if with_filter else ''
    s = [f'<g transform="translate({x:.2f},{yin_axis_y:.2f}) scale({scale:.4f})"{flt}>']
    s.append(f'  <path d="{KAN_TOP}" fill="{base_c}" fill-opacity="{aux_opacity}"{flt}/>')
    s.append(f'  <path d="{KAN_YIN_L}" fill="{hero_c}"{flt}/>')
    s.append(f'  <path d="{KAN_YIN_R}" fill="{hero_c}"{flt}/>')
    s.append(f'  <path d="{KAN_BOT}" fill="{base_c}" fill-opacity="{aux_opacity}"{flt}/>')
    s.append('</g>')
    return s


# ==============================================================================
# 标准字标（阳文/底色版）
# ==============================================================================
def build_wordmark(bg="white"):
    cnf = _cn_face()
    enf = _en_face()
    cn_items, cn_w, cn_ink = _cn_layout(cnf)
    en_items, en_w, en_ink, en_idot = _en_layout(enf)

    wave_w = cn_w * 1.28
    sc = wave_w / W_CANON
    P = PITCH * sc
    aux_h = (AMP_AUX + THICK_AUX / 2.0) * sc

    pad_top = 16.0
    cn_ink_h = cn_ink[3] - cn_ink[1]
    cn_translate_y = pad_top - cn_ink[1]
    cn_bottom_y = pad_top + cn_ink_h

    yin_axis_y = cn_bottom_y - cn_ink_h * 0.14
    bot_wave_bottom = yin_axis_y + P + aux_h

    gap_en = 16.0
    en_translate_y = bot_wave_bottom + gap_en - en_ink[1]
    en_bottom_y = bot_wave_bottom + gap_en + (en_ink[3] - en_ink[1])

    pad_bot = 16.0
    H = en_bottom_y + pad_bot
    W = wave_w + 32.0

    bg_fill = {"white": WHITE, "red": RED, "black": BLACK}[bg]
    text_color = INK if bg == "white" else WHITE
    if bg == "white":
        hero_c, base_c = RED, INK
    elif bg == "red":
        hero_c, base_c = INK, WHITE
    else:
        hero_c, base_c = RED, WHITE

    s = [f'<desc>White Stone Spring Wordmark ({bg}). Zero-overlap, Kan hexagram on Braun ribbons.</desc>',
         f'<rect width="{W:.1f}" height="{H:.1f}" fill="{bg_fill}"/>']

    cn_x = (W - cn_w) / 2.0
    for d, tx, _ in cn_items:
        s.append(f'<path d="{d}" transform="translate({cn_x+tx:.1f},{cn_translate_y:.1f})" '
                 f'fill="{text_color}" filter="url(#movable-type-edge)"/>')

    wave_x = (W - wave_w) / 2.0
    s.extend(render_waves(wave_x, yin_axis_y, wave_w, hero_c, base_c, with_filter=True))

    en_x = (W - en_w) / 2.0
    for d, tx, _ in en_items:
        s.append(f'<path d="{d}" transform="translate({en_x+tx:.1f},{en_translate_y:.1f})" '
                 f'fill="{text_color}" filter="url(#movable-type-edge)"/>')

    # 灵感之火锚点：英文中所有 i 的顶部小圆点改为强调色红点（品牌恒常元素）
    if en_idot:
        for cx, cy, r, _ in en_idot:
            s.append(f'<circle cx="{cx+en_x:.2f}" cy="{cy+en_translate_y:.2f}" r="{r:.2f}" '
                     f'fill="{hero_c}" filter="url(#movable-type-edge)"/>')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.1f} {H:.1f}" '
            f'width="{W:.1f}" height="{H:.1f}" role="img" aria-label="White Stone Spring 白石溪">\n'
            f'  <title>白石溪 White Stone Spring</title>\n' + PRINT_FILTER + '\n' + "\n".join(s) + "\n</svg>\n")


# ==============================================================================
# 阴刻字标（活字印刷·雕版白文）
# ==============================================================================
def build_wordmark_yin(ink_color=RED):
    """活字印刷阴刻字标：雕版底色实心填充，汉字与英文为白文凹刻，带微雕版刀刻纹理"""
    cnf = _cn_face()
    enf = _en_face()
    cn_items, cn_w, cn_ink = _cn_layout(cnf)
    en_items, en_w, en_ink, en_idot = _en_layout(enf)

    wave_w = cn_w * 1.28
    sc = wave_w / W_CANON
    P = PITCH * sc
    aux_h = (AMP_AUX + THICK_AUX / 2.0) * sc

    pad_top = 18.0
    cn_ink_h = cn_ink[3] - cn_ink[1]
    cn_translate_y = pad_top - cn_ink[1]
    cn_bottom_y = pad_top + cn_ink_h

    yin_axis_y = cn_bottom_y - cn_ink_h * 0.14
    bot_wave_bottom = yin_axis_y + P + aux_h

    gap_en = 16.0
    en_translate_y = bot_wave_bottom + gap_en - en_ink[1]
    en_bottom_y = bot_wave_bottom + gap_en + (en_ink[3] - en_ink[1])

    pad_bot = 18.0
    H = en_bottom_y + pad_bot
    W = wave_w + 36.0

    border_pad = 5.0
    s = [
        f'<desc>White Stone Spring Wordmark (Intaglio Movable-Type Print). White on {ink_color}.</desc>',
        f'<g filter="url(#movable-type-edge)">',
        f'  <rect x="{border_pad:.1f}" y="{border_pad:.1f}" width="{W - 2*border_pad:.1f}" height="{H - 2*border_pad:.1f}" rx="4" fill="{ink_color}"/>',
    ]

    # 阴刻白文：字形与主要水波全部使用纯白展现凹刻效果
    cn_x = (W - cn_w) / 2.0
    for d, tx, _ in cn_items:
        s.append(f'  <path d="{d}" transform="translate({cn_x+tx:.1f},{cn_translate_y:.1f})" fill="{WHITE}" filter="url(#movable-type-edge)"/>')

    # 水波以阴刻白文凹刻入印面中爻纯白贯通，上下阳爻略带透明度表现刻痕深度
    wave_x = (W - wave_w) / 2.0
    s.extend(["  " + line for line in render_waves(wave_x, yin_axis_y, wave_w, WHITE, WHITE, aux_opacity=0.45)])

    en_x = (W - en_w) / 2.0
    for d, tx, _ in en_items:
        s.append(f'  <path d="{d}" transform="translate({en_x+tx:.1f},{en_translate_y:.1f})" fill="{WHITE}" filter="url(#movable-type-edge)"/>')

    # 灵感之火锚点：阴刻中"白文"的 i 红点以红色实心圆凸显（恒常品牌符号）
    if en_idot:
        for cx, cy, r, _ in en_idot:
            s.append(f'  <circle cx="{cx+en_x:.2f}" cy="{cy+en_translate_y:.2f}" r="{r:.2f}" fill="{RED}" filter="url(#movable-type-edge)"/>')

    s.append('</g>')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.1f} {H:.1f}" '
            f'width="{W:.1f}" height="{H:.1f}" role="img" aria-label="White Stone Spring 活字阴刻">\n'
            f'  <title>白石溪 活字印刷阴刻字标</title>\n' + PRINT_FILTER + '\n' + "\n".join(s) + "\n</svg>\n")


# ==============================================================================
# 标准圆章（阳文/底色版）
# ==============================================================================
def build_xi(bg="white"):
    S = 180.0
    R = 78.0
    text_color = INK if bg == "white" else WHITE
    if bg == "white":
        hero_c, base_c = RED, INK
    elif bg == "black":
        hero_c, base_c = RED, WHITE
    else:
        hero_c, base_c = INK, WHITE

    face = _en_face()
    xi_size = 64.0
    track = -2.0

    x_contours = _glyph_contours(face, "X", xi_size)
    x_d, x_adv = _glyph_d(face, "X", xi_size)
    x_pts = []
    for _, bb in x_contours:
        if bb:
            x_pts.extend([(bb[0], bb[1]), (bb[2], bb[3])])

    i_contours = _glyph_contours(face, "i", xi_size)
    i_d, i_adv = _glyph_d(face, "i", xi_size)
    i_stem_d = []
    i_dot_bb = None
    i_pts = []
    x_shift = x_adv + track

    for cd, bb in i_contours:
        if bb is None: continue
        h = bb[3] - bb[1]
        if h < xi_size * 0.28:
            i_dot_bb = bb
            i_pts.extend([(bb[0] + x_shift, bb[1]), (bb[2] + x_shift, bb[3])])
        else:
            i_stem_d.append(cd)
            i_pts.extend([(bb[0] + x_shift, bb[1]), (bb[2] + x_shift, bb[3])])

    all_pts = x_pts + i_pts
    min_x, max_x = min(p[0] for p in all_pts), max(p[0] for p in all_pts)
    min_y, max_y = min(p[1] for p in all_pts), max(p[1] for p in all_pts)
    raw_center_x = (min_x + max_x) / 2.0
    raw_center_y = (min_y + max_y) / 2.0

    tx = (S / 2.0) - raw_center_x - 0.45
    ty = (S / 2.0) - raw_center_y - 0.09

    wave_w = 144.0
    yin_axis_y = S / 2.0

    blob = {"white": "#F6F5F0", "red": RED, "black": BLACK}[bg]
    s = [f'<circle cx="{S/2:.1f}" cy="{S/2:.1f}" r="{R:.1f}" fill="{blob}"/>']

    s.append(f'<path d="{x_d}" transform="translate({tx:.2f},{ty:.2f})" fill="{text_color}" filter="url(#movable-type-edge)"/>')

    i_tx = tx + x_shift
    for cd in i_stem_d:
        s.append(f'<path d="{cd}" transform="translate({i_tx:.2f},{ty:.2f})" fill="{text_color}" filter="url(#movable-type-edge)"/>')

    s.extend(render_waves((S - wave_w) / 2.0, yin_axis_y, wave_w, hero_c, base_c, with_filter=True))

    if i_dot_bb:
        dot_cx = i_tx + (i_dot_bb[0] + i_dot_bb[2]) / 2.0
        dot_cy = ty + (i_dot_bb[1] + i_dot_bb[3]) / 2.0
        dot_r = (i_dot_bb[3] - i_dot_bb[1]) * 0.50
        s.append(f'<circle cx="{dot_cx:.2f}" cy="{dot_cy:.2f}" r="{dot_r:.2f}" fill="{hero_c}" filter="url(#movable-type-edge)"/>')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S:.0f} {S:.0f}" '
            f'width="{S:.0f}" height="{S:.0f}" role="img" aria-label="Xi 白石溪">\n'
            f'  <title>Xi · 白石溪</title>\n' + PRINT_FILTER + '\n' + "\n".join(s) + "\n</svg>\n")


# ==============================================================================
# 阴刻印章（活字印刷·朱泥白文圆印 / 方印）
# ==============================================================================
def build_xi_yin(shape="circle", ink_color=RED):
    """活字印刷阴刻印章：朱泥印面，白文凹刻，带手工雕版微毛边"""
    S = 180.0
    R = 78.0

    face = _en_face()
    xi_size = 64.0
    track = -2.0

    x_contours = _glyph_contours(face, "X", xi_size)
    x_d, x_adv = _glyph_d(face, "X", xi_size)
    x_pts = []
    for _, bb in x_contours:
        if bb: x_pts.extend([(bb[0], bb[1]), (bb[2], bb[3])])

    i_contours = _glyph_contours(face, "i", xi_size)
    i_d, i_adv = _glyph_d(face, "i", xi_size)
    i_stem_d = []
    i_dot_bb = None
    i_pts = []
    x_shift = x_adv + track

    for cd, bb in i_contours:
        if bb is None: continue
        h = bb[3] - bb[1]
        if h < xi_size * 0.28:
            i_dot_bb = bb
            i_pts.extend([(bb[0] + x_shift, bb[1]), (bb[2] + x_shift, bb[3])])
        else:
            i_stem_d.append(cd)
            i_pts.extend([(bb[0] + x_shift, bb[1]), (bb[2] + x_shift, bb[3])])

    all_pts = x_pts + i_pts
    min_x, max_x = min(p[0] for p in all_pts), max(p[0] for p in all_pts)
    min_y, max_y = min(p[1] for p in all_pts), max(p[1] for p in all_pts)
    raw_center_x = (min_x + max_x) / 2.0
    raw_center_y = (min_y + max_y) / 2.0

    tx = (S / 2.0) - raw_center_x - 0.45
    ty = (S / 2.0) - raw_center_y - 0.09

    wave_w = 144.0
    yin_axis_y = S / 2.0

    s = [
        f'<desc>Xi Seal (Intaglio Movable-Type Print {shape}). White on {ink_color}.</desc>',
        f'<g filter="url(#movable-type-edge)">',
    ]

    # 印面底色
    if shape == "circle":
        s.append(f'  <circle cx="{S/2:.1f}" cy="{S/2:.1f}" r="{R:.1f}" fill="{ink_color}"/>')
    else: # 方印
        s.append(f'  <rect x="{S/2 - R:.1f}" y="{S/2 - R:.1f}" width="{R*2:.1f}" height="{R*2:.1f}" rx="6" fill="{ink_color}"/>')

    # 阴刻白文 X
    s.append(f'  <path d="{x_d}" transform="translate({tx:.2f},{ty:.2f})" fill="{WHITE}" filter="url(#movable-type-edge)"/>')

    # 阴刻白文 i
    i_tx = tx + x_shift
    for cd in i_stem_d:
        s.append(f'  <path d="{cd}" transform="translate({i_tx:.2f},{ty:.2f})" fill="{WHITE}" filter="url(#movable-type-edge)"/>')

    # 阴刻水波（纯白凹刻主波 + 半透辅波）
    wave_lines = render_waves((S - wave_w) / 2.0, yin_axis_y, wave_w, WHITE, WHITE, aux_opacity=0.45)
    s.extend(["  " + line for line in wave_lines])

    # 灵感之火（阴刻保留镂空实心白圆）
    if i_dot_bb:
        dot_cx = i_tx + (i_dot_bb[0] + i_dot_bb[2]) / 2.0
        dot_cy = ty + (i_dot_bb[1] + i_dot_bb[3]) / 2.0
        dot_r = (i_dot_bb[3] - i_dot_bb[1]) * 0.50
        s.append(f'  <circle cx="{dot_cx:.2f}" cy="{dot_cy:.2f}" r="{dot_r:.2f}" fill="{WHITE}" filter="url(#movable-type-edge)"/>')

    s.append('</g>')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S:.0f} {S:.0f}" '
            f'width="{S:.0f}" height="{S:.0f}" role="img" aria-label="Xi 活字阴刻印章">\n'
            f'  <title>Xi · 活字印刷阴刻印章 ({shape})</title>\n' + PRINT_FILTER + '\n' + "\n".join(s) + "\n</svg>\n")


# ==============================================================================
# 背景母版
# ==============================================================================
def build_wave_background(bg="white", width=1200, height=420):
    bg_fill = {"white": WHITE, "red": RED, "black": BLACK}[bg]
    if bg == "white":
        hero_c, base_c = RED, INK
    elif bg == "red":
        hero_c, base_c = INK, WHITE
    else:
        hero_c, base_c = RED, WHITE

    wave_w = width * 0.88
    s = [f'<rect width="{width}" height="{height}" fill="{bg_fill}"/>']
    s.extend(render_waves((width - wave_w) / 2.0, height / 2.0, wave_w, hero_c, base_c))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}" role="img" aria-label="Waves">\n'
            f'  <title>White Stone Spring · Kan Waves</title>\n' + PRINT_FILTER + '\n' + "\n".join(s) + "\n</svg>\n")


if __name__ == "__main__":
    # 三色循环生成：白底/红底/黑底 × 阳刻(字标/印章/水纹) + 阴刻(字标/圆印/方印)
    # 统一三色严格：#1A1A1A 黑 / #FFFFFF 白 / #E03030 红
    bg_label = {"white": "白底", "red": "红底", "black": "黑底"}
    out = {}
    for bg in ("white", "red", "black"):
        out[f"brand_白石溪_字标_{bg_label[bg]}.svg"] = build_wordmark(bg)
        out[f"brand_白石溪_Xi章_{bg_label[bg]}.svg"] = build_xi(bg)
        out[f"brand_白石溪_水纹背景_{bg_label[bg]}.svg"] = build_wave_background(bg)

    # 阴刻活字印刷版：朱红/玄黑两色 × 字标/圆印/方印
    yin_label = {RED: "朱红", BLACK: "玄黑"}
    for ink in (RED, BLACK):
        out[f"brand_白石溪_字标_阴刻_{yin_label[ink]}.svg"] = build_wordmark_yin(ink)
        out[f"brand_白石溪_Xi章_阴刻_圆_{yin_label[ink]}.svg"] = build_xi_yin("circle", ink)
        out[f"brand_白石溪_Xi章_阴刻_方_{yin_label[ink]}.svg"] = build_xi_yin("square", ink)
    assets = os.path.join(ROOT, "assets")
    os.makedirs(assets, exist_ok=True)
    for name, svg in out.items():
        dst = os.path.join(assets, name)
        with open(dst, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"{name} {os.path.getsize(dst)} B")
