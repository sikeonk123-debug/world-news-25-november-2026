#!/usr/bin/env python3
"""Draw entry.png: a one-page newspaper front page summing up 25 Nov 2026.

Wednesday 25 November 2026. 35 stories across 7 regions (EUROPE 9,
AMERICAS 10, ASIA 5, AFRICA 5, MIDDLE EAST 3, OCEANIA 2, WORLD 1),
3 hero + 10 secondary original flat illustrations, a THE DAY IN UTC
timeline strip, a numbers strip of six separate cells where every
number tells a complete mini-story, verification tags on every
illustrated story, a pinned dotted world map whose legend carries the
region counts, a 22-story numbered list, a DATE CHECK box with dated
exclusions plus a "Not yet" tail, and a sources footer. Counts
reconcile: 3 + 10 + 22 = 35; region counts sum to 35; 15 fields.

Every story was verified as having happened, or first been reported,
on Wednesday 25 November 2026, from Reuters, AP, AFP, BBC, Al
Jazeera, Yonhap, Xinhua, Kyodo and ChessBase. Disputed figures are
shown as claims, never as fact. Near-misses are named in the DATE
CHECK box, not shown as news. Drawn with Pillow only; no photos, no
copied art. Layout follows the winning newspaper pattern (date header,
timeline, region strip, numbers strip, 3 heroes, map, numbered list,
date check); all content, headlines and drawings are original to
this day.
"""
from PIL import Image, ImageDraw, ImageFont
import math
import os

W = H = 1024
PAPER = (248, 245, 238)
INK = (20, 20, 20)
MUTED = (90, 86, 78)
RED = (166, 27, 27)
NAVY = (18, 34, 64)
RULE = (180, 174, 162)
CARD = (255, 255, 255)
MAPDOT = (158, 168, 180)
GREEN = (46, 134, 74)

SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def F(path, size):
    return ImageFont.truetype(path, size)


def wrap_text(d, text, fnt, width):
    """Greedy word wrap; returns list of lines that fit width."""
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if d.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def put_text(d, xy, text, fnt, width, fill, leading=2, limit=None):
    """Draw wrapped text; returns y after last line. Warns on overflow."""
    x, y = xy
    lines = wrap_text(d, text, fnt, width)
    if limit is not None and len(lines) > limit:
        print(f"OVERFLOW: {text[:48]!r} -> {len(lines)} lines (max {limit})")
        lines = lines[:limit]
    for line in lines:
        d.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + leading
    return y


# ---------- small flat-drawing primitives ----------
def sky(d, box, top, mid, bot):
    x0, y0, x1, y1 = box
    for i, c in enumerate((top, mid, bot)):
        d.rectangle([x0, y0 + (y1 - y0) * i // 3,
                     x1, y0 + (y1 - y0) * (i + 1) // 3], fill=c)


def disc(d, cx, cy, r, color):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)


def puff(d, x, y, s, color):
    d.ellipse([x, y, x + s, y + s * 0.55], fill=color)
    d.ellipse([x + s * 0.5, y - s * 0.25, x + s * 1.5, y + s * 0.4], fill=color)
    d.ellipse([x + s, y, x + s * 2, y + s * 0.55], fill=color)


def block(d, x, y, w, h, color, lit=(255, 214, 90)):
    d.rectangle([x, y, x + w, y + h], fill=color)
    for wy in range(y + 7, y + h - 7, 13):
        for wx in range(x + 5, x + w - 7, 13):
            d.rectangle([wx, wy, wx + 5, wy + 6], fill=lit)


def spark(d, cx, cy, r, color):
    d.polygon([(cx, cy - r), (cx + r * 0.28, cy - r * 0.28), (cx + r, cy),
               (cx + r * 0.28, cy + r * 0.28), (cx, cy + r),
               (cx - r * 0.28, cy + r * 0.28), (cx - r, cy),
               (cx - r * 0.28, cy - r * 0.28)], fill=color)


def fire(d, x, y, s):
    """Flame with base at (x, y), height s."""
    d.polygon([(x - s * 0.4, y), (x, y - s), (x + s * 0.4, y)], fill=(255, 140, 40))
    d.polygon([(x - s * 0.2, y), (x, y - s * 0.55), (x + s * 0.2, y)],
              fill=(255, 220, 120))


def figure(d, x, y, s, skin=(232, 190, 160), shirt=(30, 90, 160)):
    """Small standing person: head, torso, legs."""
    d.ellipse([x - s * 0.28, y, x + s * 0.28, y + s * 0.55], fill=skin)
    d.rectangle([x - s * 0.3, y + s * 0.55, x + s * 0.3, y + s * 1.15], fill=shirt)
    d.rectangle([x - s * 0.22, y + s * 1.15, x - s * 0.02, y + s * 1.7],
                fill=(30, 30, 34))
    d.rectangle([x + s * 0.02, y + s * 1.15, x + s * 0.22, y + s * 1.7],
                fill=(30, 30, 34))


def banner(d, box, text):
    """Red key-number banner across the bottom of a hero picture."""
    x0, y0, x1, y1 = box
    d.rectangle([x0, y1 - 18, x1, y1], fill=RED)
    f = F(SANS_B, 13)
    d.text((x0 + (x1 - x0 - d.textlength(text, font=f)) / 2, y1 - 16),
           text, font=f, fill=(255, 255, 255))


# ---------- hero pictures (310 x 124) ----------
def pic_cairo(d, box):
    """Hero 1: Cairo's Ring Road at dusk — an overturned fuel tanker
    with flames from its side, smoke, charred cars, a fire truck and
    a stretcher team."""
    x0, y0, x1, y1 = box
    sky(d, box, (238, 176, 130), (228, 162, 122), (214, 146, 110))
    disc(d, x0 + 24, y0 + 12, 9, (255, 214, 90))
    # overturned tanker: cylinder on its side, cab at the left,
    # wheels in the air where it rolled
    tx, ty = x0 + 96, y1 - 62
    d.rectangle([tx, ty, tx + 26, ty + 22], fill=(30, 90, 160))
    d.rectangle([tx + 4, ty + 4, tx + 22, ty + 12], fill=(180, 220, 240))
    d.ellipse([tx + 26, ty - 4, tx + 128, ty + 26], fill=(210, 210, 206))
    d.ellipse([tx + 26, ty - 4, tx + 128, ty + 26], outline=(150, 150, 146),
              width=1)
    disc(d, tx + 50, ty - 6, 5, (20, 20, 20))
    disc(d, tx + 102, ty - 6, 5, (20, 20, 20))
    fire(d, tx + 56, ty - 4, 30)
    fire(d, tx + 104, ty - 2, 24)
    puff(d, tx + 40, y0 + 2, 20, (110, 110, 116))
    puff(d, tx + 96, y0 + 12, 16, (130, 130, 134))
    puff(d, tx + 140, y0 + 0, 14, (120, 120, 124))
    # charred cars on the road
    for cx in (x0 + 14, x0 + 48):
        d.rectangle([cx, y1 - 36, cx + 30, y1 - 24], fill=(40, 38, 36))
        d.rectangle([cx + 6, y1 - 44, cx + 24, y1 - 36], fill=(40, 38, 36))
        disc(d, cx + 8, y1 - 24, 4, (20, 20, 20))
        disc(d, cx + 22, y1 - 24, 4, (20, 20, 20))
    fire(d, x0 + 30, y1 - 36, 12)
    # fire truck at the right
    fx, fy = x0 + 258, y1 - 44
    d.rectangle([fx, fy, fx + 46, fy + 18], fill=(178, 34, 34))
    d.rectangle([fx + 32, fy - 12, fx + 46, fy], fill=(178, 34, 34))
    d.rectangle([fx + 35, fy - 9, fx + 43, fy - 2], fill=(180, 220, 240))
    disc(d, fx + 10, fy + 18, 6, (20, 20, 20))
    disc(d, fx + 36, fy + 18, 6, (20, 20, 20))
    # stretcher team at the left
    figure(d, x0 + 76, y1 - 62, 13, shirt=(220, 180, 60))
    figure(d, x0 + 92, y1 - 62, 13, shirt=(60, 140, 90))
    d.rectangle([x0 + 82, y1 - 44, x0 + 96, y1 - 40], fill=(200, 200, 196))
    d.rectangle([x0, y1 - 18, x1, y1], fill=(110, 88, 66))
    banner(d, box, "31 DEAD IN CAIRO FIRE")


def pic_hormuz(d, box):
    """Hero 2: the Strait of Hormuz at dawn — two tankers with flames
    and smoke columns, naval mines in the water, a patrol boat."""
    x0, y0, x1, y1 = box
    sky(d, box, (232, 196, 150), (224, 188, 158), (210, 178, 150))
    disc(d, x0 + 22, y0 + 12, 9, (255, 214, 90))
    # sea
    d.rectangle([x0, y1 - 34, x1, y1], fill=(36, 76, 118))
    for wx in range(x0 + 8, x1 - 8, 26):
        d.line([wx, y1 - 22, wx + 12, y1 - 22], fill=(90, 140, 180), width=1)
    # first tanker, left
    hx, hy = x0 + 16, y1 - 52
    d.polygon([(hx, hy + 14), (hx + 118, hy + 14), (hx + 126, hy + 2),
               (hx, hy + 2)], fill=(24, 24, 28))
    d.rectangle([hx + 8, hy - 8, hx + 34, hy + 2], fill=(200, 60, 50))
    d.rectangle([hx + 40, hy - 8, hx + 66, hy + 2], fill=(240, 240, 238))
    fire(d, hx + 52, hy - 8, 26)
    puff(d, hx + 30, y0 + 4, 18, (110, 110, 116))
    puff(d, hx + 76, y0 + 14, 14, (130, 130, 134))
    # second tanker, right, partly behind smoke
    hx2, hy2 = x0 + 168, y1 - 56
    d.polygon([(hx2, hy2 + 14), (hx2 + 122, hy2 + 14), (hx2 + 130, hy2 + 2),
               (hx2, hy2 + 2)], fill=(30, 30, 34))
    d.rectangle([hx2 + 10, hy2 - 8, hx2 + 36, hy2 + 2], fill=(36, 84, 160))
    d.rectangle([hx2 + 42, hy2 - 8, hx2 + 68, hy2 + 2], fill=(220, 160, 40))
    fire(d, hx2 + 88, hy2 - 8, 22)
    puff(d, hx2 + 66, y0 + 2, 16, (120, 120, 124))
    # naval mines: spiky dots in the water between the tankers
    for mx, my in [(x0 + 150, y1 - 16), (x0 + 168, y1 - 10),
                   (x0 + 132, y1 - 8)]:
        spark(d, mx, my, 5, (20, 20, 20))
    # small patrol boat at the far right
    bx, by = x0 + 282, y1 - 28
    d.polygon([(bx, by + 6), (bx + 22, by + 6), (bx + 26, by),
               (bx, by)], fill=(120, 120, 124))
    d.rectangle([bx + 8, by - 6, bx + 16, by], fill=(120, 120, 124))
    d.rectangle([x0, y1 - 18, x1, y1], fill=(24, 56, 92))
    banner(d, box, "2 TANKERS HIT MINES")


def pic_tariffs(d, box):
    """Hero 3: the tariff board — four tariff rows: partner, rate and
    what it covers. No bars: the rates differ in kind, not just size,
    so bars would lie about the small ones."""
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(244, 240, 228))
    d.rectangle([x0, y1 - 18, x1, y1], fill=(232, 224, 204))
    rows = [("CHINA", "+20%", "45% total", RED),
            ("BRAZIL", "10%", "aircraft", RED),
            ("VIETNAM", "+20%", "on goods", RED),
            ("PARTNERS", "14", "Jan 25", INK)]
    for i, (name, lvl, chg, col) in enumerate(rows):
        ry = y0 + 8 + i * 24
        d.text((x0 + 14, ry), name, font=F(SANS_B, 13), fill=INK)
        d.text((x0 + 118, ry - 1), lvl, font=F(SERIF_B, 16), fill=col)
        d.text((x0 + 232, ry), chg, font=F(SANS, 11), fill=MUTED)
        if i < 3:
            d.line([x0 + 12, ry + 20, x1 - 12, ry + 20], fill=(210, 204, 190),
                   width=1)
    banner(d, box, "CHINA +20% · 14 PARTNERS HIT")

# ---------- secondary pictures (185 x 58) ----------
def pic_sudan(d, box):
    """4: Damazin at dusk — low town blocks, a drone in the sky, a
    smoke plume and a burst where the strike fell."""
    x0, y0, x1, y1 = box
    sky(d, box, (232, 176, 130), (222, 162, 122), (208, 146, 112))
    disc(d, x0 + 18, y0 + 10, 8, (255, 214, 90))
    # drone silhouette in the sky
    dx, dy = x0 + 140, y0 + 10
    d.rectangle([dx - 12, dy, dx + 12, dy + 3], fill=(30, 30, 34))
    d.ellipse([dx - 16, dy - 2, dx - 8, dy + 2], fill=(30, 30, 34))
    d.ellipse([dx + 8, dy - 2, dx + 16, dy + 2], fill=(30, 30, 34))
    d.rectangle([dx - 3, dy + 3, dx + 3, dy + 7], fill=(30, 30, 34))
    # low town blocks
    for bx, bw, bh in [(x0 + 8, 36, 20), (x0 + 48, 32, 26), (x0 + 140, 38, 18)]:
        d.rectangle([bx, y1 - bh, bx + bw, y1 - 8], fill=(176, 158, 128))
        d.rectangle([bx + 4, y1 - bh - 5, bx + bw - 4, y1 - bh],
                    fill=(146, 128, 100))
    # smoke plume and burst over the middle block
    puff(d, x0 + 84, y0 + 2, 16, (110, 110, 116))
    puff(d, x0 + 104, y0 + 12, 12, (130, 130, 134))
    spark(d, x0 + 96, y0 + 28, 9, (255, 140, 40))
    fire(d, x0 + 96, y1 - 26, 14)
    # a figure carrying a stretcher at the foot of the rubble
    figure(d, x0 + 122, y1 - 38, 12, shirt=(220, 180, 60))
    figure(d, x0 + 142, y1 - 38, 12, shirt=(60, 140, 90))
    d.rectangle([x0 + 128, y1 - 24, x0 + 142, y1 - 20], fill=(200, 200, 196))
    d.rectangle([x0, y1 - 8, x1, y1], fill=(110, 94, 74))


def pic_nigeria(d, box):
    """5: a Niger state village at night — thatched huts, flames from
    a roof, smoke, a figure fleeing with a bundle."""
    x0, y0, x1, y1 = box
    sky(d, box, (14, 22, 46), (24, 36, 68), (36, 52, 92))
    spark(d, x0 + 18, y0 + 8, 3, (255, 255, 255))
    spark(d, x0 + 168, y0 + 12, 3, (255, 255, 255))
    disc(d, x0 + 150, y0 + 8, 7, (240, 240, 230))
    # three thatched huts
    for hx, hw in [(x0 + 12, 40), (x0 + 62, 44), (x0 + 118, 40)]:
        d.rectangle([hx, y1 - 24, hx + hw, y1 - 8], fill=(150, 110, 80))
        d.polygon([(hx - 4, y1 - 24), (hx + hw // 2, y1 - 40),
                   (hx + hw + 4, y1 - 24)], fill=(120, 86, 60))
        d.rectangle([hx + hw // 2 - 5, y1 - 16, hx + hw // 2 + 5, y1 - 8],
                    fill=(60, 44, 36))
    # flames and smoke from the middle hut's roof
    fire(d, x0 + 84, y1 - 40, 18)
    fire(d, x0 + 66, y1 - 32, 12)
    puff(d, x0 + 62, y0 + 2, 14, (118, 126, 146))
    puff(d, x0 + 92, y0 + 10, 12, (130, 130, 134))
    # a figure fleeing at the right with a bundle
    figure(d, x0 + 168, y1 - 36, 12, shirt=(200, 60, 40))
    d.ellipse([x0 + 172, y1 - 44, x0 + 182, y1 - 36], fill=(220, 160, 40))
    d.rectangle([x0, y1 - 8, x1, y1], fill=(12, 18, 34))


def pic_gaza(d, box):
    """6: Gaza at dusk — low blocks, a smoke plume and a burst where
    the strike fell."""
    x0, y0, x1, y1 = box
    sky(d, box, (232, 176, 130), (222, 162, 122), (208, 146, 112))
    disc(d, x0 + 20, y0 + 10, 8, (255, 214, 90))
    for bx, bw, bh in [(x0 + 8, 36, 22), (x0 + 48, 32, 28), (x0 + 140, 38, 20)]:
        d.rectangle([bx, y1 - bh, bx + bw, y1 - 8], fill=(176, 158, 128))
        d.rectangle([bx + 4, y1 - bh - 5, bx + bw - 4, y1 - bh],
                    fill=(146, 128, 100))
    # smoke plume and burst over the middle block
    puff(d, x0 + 84, y0 + 2, 16, (110, 110, 116))
    puff(d, x0 + 104, y0 + 12, 12, (130, 130, 134))
    spark(d, x0 + 96, y0 + 30, 9, (255, 140, 40))
    fire(d, x0 + 96, y1 - 28, 14)
    # a figure carrying a stretcher at the foot of the rubble
    figure(d, x0 + 122, y1 - 40, 12, shirt=(220, 180, 60))
    figure(d, x0 + 142, y1 - 40, 12, shirt=(60, 140, 90))
    d.rectangle([x0 + 128, y1 - 26, x0 + 142, y1 - 22], fill=(200, 200, 196))
    d.rectangle([x0, y1 - 8, x1, y1], fill=(110, 94, 74))


def pic_ras(d, box):
    """7: Ras Tanura at dawn — storage tanks and distillation towers,
    a thick black smoke column and flames where the strike is claimed."""
    x0, y0, x1, y1 = box
    sky(d, box, (232, 196, 150), (224, 188, 158), (210, 178, 150))
    disc(d, x0 + 18, y0 + 10, 8, (255, 214, 90))
    # distillation towers
    for tx in (x0 + 20, x0 + 44):
        d.rectangle([tx, y1 - 48, tx + 10, y1 - 8], fill=(150, 150, 154))
        d.rectangle([tx - 2, y1 - 52, tx + 12, y1 - 48], fill=(120, 120, 124))
    # storage tanks
    for tx, tw in [(x0 + 70, 34), (x0 + 110, 38)]:
        d.rectangle([tx, y1 - 34, tx + tw, y1 - 8], fill=(200, 200, 204))
        d.pieslice([tx - 2, y1 - 42, tx + tw + 2, y1 - 28], start=180,
                   end=360, fill=(180, 180, 184))
    # black smoke column and flames over the right tank
    puff(d, x0 + 128, y0 + 2, 16, (40, 40, 44))
    puff(d, x0 + 148, y0 + 12, 12, (60, 60, 64))
    fire(d, x0 + 128, y1 - 34, 16)
    fire(d, x0 + 146, y1 - 30, 12)
    # a small drone in the sky
    dx, dy = x0 + 168, y0 + 8
    d.rectangle([dx - 8, dy, dx + 8, dy + 2], fill=(30, 30, 34))
    d.ellipse([dx - 11, dy - 1, dx - 5, dy + 1], fill=(30, 30, 34))
    d.ellipse([dx + 5, dy - 1, dx + 11, dy + 1], fill=(30, 30, 34))
    d.rectangle([x0, y1 - 8, x1, y1], fill=(110, 94, 74))


def pic_shenzhou(d, box):
    """8: Jiuquan — a rocket climbing past the Tiangong station,
    stars, the Earth curving below."""
    x0, y0, x1, y1 = box
    sky(d, box, (8, 12, 30), (14, 22, 48), (22, 34, 66))
    for sx, sy in [(x0 + 16, y0 + 8), (x0 + 52, y0 + 16), (x0 + 96, y0 + 6),
                   (x0 + 140, y0 + 14), (x0 + 172, y0 + 8)]:
        spark(d, sx, sy, 2, (255, 255, 255))
    # Earth curve at the bottom, kept inside the picture box; drawn
    # before the rocket so the exhaust plume stays in front of it
    d.pieslice([x0 - 20, y1 - 14, x1 + 20, y1 + 14], start=180, end=360,
               fill=(40, 110, 180))
    # Tiangong station: core module and two solar wings
    sx, sy = x0 + 108, y0 + 12
    d.rectangle([sx, sy, sx + 40, sy + 10], fill=(200, 200, 204))
    d.rectangle([sx + 14, sy + 10, sx + 26, sy + 16], fill=(180, 180, 184))
    d.rectangle([sx - 26, sy + 2, sx, sy + 8], fill=(40, 90, 180))
    d.rectangle([sx + 40, sy + 2, sx + 66, sy + 8], fill=(40, 90, 180))
    # rocket climbing, flame below
    rx, ry = x0 + 30, y0 + 26
    d.polygon([(rx + 4, ry - 10), (rx + 10, ry - 18), (rx + 16, ry - 10),
               (rx + 16, ry + 10), (rx + 4, ry + 10)], fill=(240, 240, 238))
    d.rectangle([rx, ry + 2, rx + 4, ry + 8], fill=(178, 44, 44))
    d.rectangle([rx + 16, ry + 2, rx + 20, ry + 8], fill=(178, 44, 44))
    fire(d, rx + 10, ry + 12, 12)
    puff(d, rx - 2, ry + 18, 10, (200, 200, 204))
    d.rectangle([x0, y1 - 8, x1, y1], fill=(16, 32, 56))


def pic_solomon(d, box):
    """9: the treaty — a Pacific island with a palm, the Australian
    and Solomon Islands flags on poles, a ship on the sea."""
    x0, y0, x1, y1 = box
    sky(d, box, (150, 196, 220), (178, 212, 232), (206, 226, 240))
    disc(d, x0 + 18, y0 + 10, 8, (255, 214, 90))
    # sea
    d.rectangle([x0, y1 - 16, x1, y1], fill=(36, 76, 118))
    for wx in range(x0 + 8, x1 - 8, 26):
        d.line([wx, y1 - 10, wx + 12, y1 - 10], fill=(90, 140, 180), width=1)
    # island with a palm
    d.polygon([(x0 + 60, y1 - 8), (x0 + 140, y1 - 8), (x0 + 128, y1 - 24),
               (x0 + 74, y1 - 24)], fill=(120, 150, 90))
    px, py = x0 + 100, y1 - 24
    d.line([px, py, px + 2, py - 16], fill=(110, 86, 60), width=2)
    for dx, dy in [(-10, -14), (10, -14), (-8, -8), (8, -8)]:
        d.line([px + 1, py - 16, px + 1 + dx, py - 16 + dy],
               fill=(46, 134, 74), width=2)
    # Australian flag on a pole (blue, Union Jack corner, stars)
    fx, fy = x0 + 148, y0 + 8
    d.line([fx, fy, fx, y1 - 8], fill=(220, 220, 220), width=2)
    d.rectangle([fx + 1, fy, fx + 19, fy + 12], fill=(36, 84, 160))
    d.line([fx + 1, fy, fx + 10, fy + 12], fill=(255, 255, 255), width=1)
    d.line([fx + 1, fy + 12, fx + 10, fy], fill=(255, 255, 255), width=1)
    spark(d, fx + 15, fy + 6, 2, (255, 255, 255))
    # Solomon Islands flag on a pole (blue over green, yellow stars)
    gx, gy = x0 + 168, y0 + 8
    d.line([gx, gy, gx, y1 - 8], fill=(220, 220, 220), width=2)
    d.polygon([(gx + 1, gy), (gx + 19, gy), (gx + 1, gy + 12)],
              fill=(36, 84, 160))
    d.polygon([(gx + 1, gy + 12), (gx + 19, gy), (gx + 19, gy + 12)],
              fill=(46, 134, 74))
    d.line([gx + 1, gy + 12, gx + 19, gy], fill=(255, 214, 0), width=1)
    spark(d, gx + 5, gy + 4, 2, (255, 214, 0))
    spark(d, gx + 13, gy + 8, 2, (255, 214, 0))
    # small ship at the left
    hx, hy = x0 + 10, y1 - 26
    d.polygon([(hx, hy + 8), (hx + 40, hy + 8), (hx + 44, hy + 2),
               (hx, hy + 2)], fill=(24, 24, 28))
    d.rectangle([hx + 8, hy - 4, hx + 20, hy + 2], fill=(240, 240, 238))
    d.rectangle([x0, y1 - 8, x1, y1], fill=(24, 56, 92))


def pic_markets(d, box):
    """10: the whipsaw — a chart line plunging then rebounding to a
    small green gain, with the Dow close and the GDP revision."""
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(244, 240, 228))
    # chart frame
    cx0, cy0, cx1, cy1 = x0 + 8, y0 + 6, x1 - 8, y1 - 20
    d.rectangle([cx0, cy0, cx1, cy1], fill=(255, 255, 255),
                outline=(210, 204, 190), width=1)
    # plunge then rebound: red down, green up
    pts = [(cx0 + 6, cy0 + 10), (cx0 + 40, cy0 + 14), (cx0 + 74, cy0 + 26),
           (cx0 + 100, cy0 + 22), (cx0 + 126, cy0 + 14)]
    d.line(pts[:3], fill=RED, width=2)
    d.line(pts[2:], fill=GREEN, width=2)
    # green up arrow at the end of the rebound
    ex, ey = pts[-1]
    d.polygon([(ex, ey - 6), (ex + 5, ey + 2), (ex - 5, ey + 2)], fill=GREEN)
    d.text((cx0 + 8, cy1 + 2), "DOW 50,183  +0.33%",
           font=F(SANS_B, 10), fill=GREEN)
    gdp = "GDP 4.3%"
    d.text((cx1 - d.textlength(gdp, font=F(SANS_B, 10)), cy1 + 2), gdp,
           font=F(SANS_B, 10), fill=INK)
    d.rectangle([x0, y1 - 8, x1, y1], fill=(232, 224, 204))


def pic_spacex(d, box):
    """11: orbit — a grid of small satellites over the Earth's curve,
    one larger satellite with solar wings in front."""
    x0, y0, x1, y1 = box
    sky(d, box, (8, 12, 30), (14, 22, 48), (22, 34, 66))
    # grid of small satellites: rows of dots with tiny wings
    for row in range(3):
        for cx in range(x0 + 14, x1 - 10, 26):
            cy = y0 + 8 + row * 12
            disc(d, cx, cy, 2, (220, 220, 224))
            d.line([cx - 5, cy, cx + 5, cy], fill=(90, 140, 180), width=1)
    # Earth curve at the bottom
    d.pieslice([x0 - 20, y1 - 14, x1 + 20, y1 + 14], start=180, end=360,
               fill=(40, 110, 180))
    # one larger satellite with solar wings, centre-right
    sx, sy = x0 + 108, y0 + 30
    d.rectangle([sx, sy, sx + 22, sy + 8], fill=(200, 200, 204))
    d.rectangle([sx - 22, sy + 2, sx, sy + 6], fill=(40, 90, 180))
    d.rectangle([sx + 22, sy + 2, sx + 44, sy + 6], fill=(40, 90, 180))
    spark(d, sx + 11, sy + 4, 3, (255, 214, 90))
    d.rectangle([x0, y1 - 8, x1, y1], fill=(16, 32, 56))


def pic_aus(d, box):
    """12: Canberra — a phone with a shield tick, parliament house
    with its flag mast behind."""
    x0, y0, x1, y1 = box
    sky(d, box, (150, 196, 220), (178, 212, 232), (206, 226, 240))
    # parliament: low building and tall flag mast
    px, py = x0 + 96, y1 - 30
    d.rectangle([px, py, px + 76, y1 - 8], fill=(200, 196, 188))
    d.rectangle([px + 30, py - 8, px + 46, py], fill=(200, 196, 188))
    d.line([px + 38, py - 8, px + 38, y0 + 6], fill=(60, 60, 60), width=2)
    d.rectangle([px + 39, y0 + 6, px + 57, y0 + 16], fill=(36, 84, 160))
    for k in range(4):
        d.rectangle([px + 6 + k * 18, py + 6, px + 12 + k * 18, py + 16],
                    fill=(160, 156, 148))
    # phone with a shield
    phx, phy = x0 + 14, y0 + 6
    d.rectangle([phx, phy, phx + 52, phy + 44], fill=(20, 20, 24))
    d.rectangle([phx + 3, phy + 3, phx + 49, phy + 41], fill=(90, 150, 220))
    d.polygon([(phx + 26, phy + 8), (phx + 42, phy + 12), (phx + 42, phy + 26),
               (phx + 26, phy + 38), (phx + 10, phy + 26),
               (phx + 10, phy + 12)], fill=(255, 255, 255))
    d.line([phx + 18, phy + 24, phx + 24, phy + 30, phx + 34, phy + 16],
           fill=GREEN, width=2)
    d.rectangle([x0, y1 - 8, x1, y1], fill=(90, 110, 130))


def pic_iowa(d, box):
    """13: the Iowa blast — two low earth bunkers in an open field,
    twin white smoke plumes rising, a fence and a distant monitor."""
    x0, y0, x1, y1 = box
    sky(d, box, (214, 200, 170), (200, 186, 158), (186, 170, 144))
    disc(d, x0 + 18, y0 + 10, 8, (255, 214, 90))
    # field
    d.rectangle([x0, y1 - 22, x1, y1], fill=(120, 150, 90))
    # two low bunkers: grass mounds with dark doors
    for bx, bw in [(x0 + 22, 56), (x0 + 96, 60)]:
        d.pieslice([bx, y1 - 44, bx + bw, y1 - 8], start=180, end=360,
                   fill=(100, 120, 70))
        d.rectangle([bx + bw // 2 - 6, y1 - 22, bx + bw // 2 + 6, y1 - 8],
                    fill=(60, 44, 36))
    # twin white smoke plumes rising from the bunkers
    puff(d, x0 + 30, y0 + 4, 16, (240, 240, 238))
    puff(d, x0 + 58, y0 + 12, 12, (230, 230, 228))
    puff(d, x0 + 104, y0 + 2, 16, (240, 240, 238))
    puff(d, x0 + 132, y0 + 12, 12, (230, 230, 228))
    # fence posts along the field and a small monitor station
    for fx in range(x0 + 8, x1 - 8, 22):
        d.line([fx, y1 - 18, fx, y1 - 10], fill=(90, 70, 50), width=2)
    d.rectangle([x0 + 164, y1 - 30, x0 + 178, y1 - 8], fill=(150, 150, 154))
    d.rectangle([x0, y1 - 8, x1, y1], fill=(90, 110, 70))


PICS = {1: pic_cairo, 2: pic_hormuz, 3: pic_tariffs, 4: pic_shenzhou,
        5: pic_sudan, 6: pic_nigeria, 7: pic_gaza, 8: pic_ras,
        9: pic_aus, 10: pic_solomon, 11: pic_markets, 12: pic_spacex,
        13: pic_iowa}

# ---------- story data ----------
# (num, region, topic, source, tag, headline, summary)
HEROES = [
    (1, "AFRICA", "EGYPT", "AP", "CONFIRMED",
     "Cairo tanker fire kills 31",
     "Fuel truck overturns on Ring Road; 21 hurt, dozens of cars charred."),
    (2, "MIDDLE EAST", "IRAN", "REUTERS", "REPORTED",
     "Iran says tankers hit mines in Hormuz",
     "IRGC says two tankers exploded; US tells citizens to leave Iran."),
    (3, "AMERICAS", "TRADE", "AP", "OFFICIAL",
     "US unveils new tariffs on 14 partners",
     "China +20%, Brazil 10% on aircraft; no duties before 25 Jan hearing."),
]
SECONDARY = [
    (4, "ASIA", "CHINA", "XINHUA", "OFFICIAL",
     "Shenzhou 24 launches",
     "First foreign astronaut aboard: Pakistan's Zeeshan Ali."),
    (5, "AFRICA", "SUDAN", "REUTERS", "REPORTED",
     "Sudan drone strikes kill 19",
     "Rights group: Tuesday-night strikes on Damazin; 20 hurt."),
    (6, "AFRICA", "NIGERIA", "REUTERS", "REPORTED",
     "Militants kill 30 in Nigeria",
     "Residents: Tuesday-evening raids in Niger state; homes burned."),
    (7, "MIDDLE EAST", "GAZA", "REUTERS", "CONFIRMED",
     "Israel kills Hamas colonel in Gaza",
     "Abuelouf, wife and two daughters killed in Shati camp."),
    (8, "MIDDLE EAST", "SAUDI", "REUTERS", "REPORTED",
     "Houthis say they hit Ras Tanura",
     "Refinery fires claimed; satellite smoke seen; 4 drones downed."),
    (9, "OCEANIA", "AUSTRALIA", "REUTERS", "OFFICIAL",
     "Australia passes tech duty of care",
     "Fines up to 5% of global revenue; users can sue platforms."),
    (10, "OCEANIA", "PACIFIC", "AP", "OFFICIAL",
     "Solomons sign Australia pact",
     "No foreign military base; A$740m over 10 years."),
    (11, "AMERICAS", "MARKETS", "REUTERS", "OFFICIAL",
     "Wall Street whipsaws; GDP 4.3%",
     "Dow erases 1,100-point drop to close +0.33%; inflation 3.8%."),
    (12, "AMERICAS", "TECH", "REUTERS", "OFFICIAL",
     "FCC clears 1m SpaceX satellites",
     "Starmind orbital data centres approved; first launch by 2033."),
    (13, "AMERICAS", "USA", "AP", "OFFICIAL",
     "Iowa blast succeeds",
     "Army detonates 5 tons of lead azide; no lead in early air checks."),
]
LISTED = [
    "Bangladesh garment wage up 36% to $139",
    "North Korea expels Swiss diplomat",
    "Japan aims to be No. 3 AI power",
    "Myanmar rebel with artificial leg vows to fight on",
    "Lukoil deal: Boehly-led group buys overseas assets",
    "Eurostar strike cancels Paris–London trains",
    "Chess game 2: 20-move draw, match 1–1",
    "Poland plans eastern no-fly zone",
    "Venice Biennale: Nick Cave and India win",
    "Pope Leo XIV laments COP31 failure",
    "US approves $622m F-16 kit sale to Kyiv",
    "Russia hits Kyiv with missiles; 2 killed",
    "Champions League: Man Utd draw; Liverpool win",
    "Birthright order blocked by second judge",
    "Ábrego García arrives in Spain",
    "Macy's 100th parade postponed to Saturday",
    "US intel agencies hit by cyber breach",
    "Steelers release Aaron Rodgers",
    "FinCEN takes systems offline after cyber incident",
    "UN evacuates 10 Ebola workers in Ituri",
    "Kenya cult leader convicted of new charges",
    "Famine monitor FEWS NET to halt reporting",
]
REGIONS = [("EUROPE", 9, (36, 84, 160)), ("AMERICAS", 10, (14, 128, 128)),
           ("ASIA", 5, (122, 62, 158)), ("AFRICA", 5, (46, 134, 74)),
           ("MIDDLE EAST", 3, (178, 44, 44)), ("OCEANIA", 2, (214, 122, 26)),
           ("WORLD", 1, (96, 96, 100))]
FIELDS = ["DISASTER", "CONFLICT", "TRADE", "SPACE", "DIPLOMACY",
          "TECHNOLOGY", "LAW", "ECONOMY", "MARKETS", "HEALTH",
          "MIGRATION", "SPORT", "CULTURE", "ENERGY", "DEFENCE"]
# numbers strip: six cells, two rows of three; each a complete mini-story
NUMBERS = [("31", "killed in the Cairo tanker fire"),
           ("1,000,000", "satellites FCC lets SpaceX deploy"),
           ("20%", "new US tariff proposed on Chinese goods"),
           ("4.3%", "US third-quarter GDP growth, revised up"),
           ("30", "killed in Nigeria's Niger state attacks"),
           ("36%", "Bangladesh garment workers' pay rise")]
# timeline strip: seven timed events across the day (UTC)
TIMELINE = [("00:18", "Shenzhou 24 launches"),
            ("06:29", "Solomons sign Australia pact"),
            ("09:46", "Iran says tankers hit mines"),
            ("13:51", "Israel kills Hamas colonel"),
            ("15:00", "Iowa blast goes off"),
            ("20:00", "US unveils new tariffs"),
            ("21:00", "Dow closes up after plunge")]
# map pins: (num, x, y); red for 1-3, navy for 4-13
PINS = [(1, 210, 862), (2, 246, 868), (3, 88, 840), (4, 282, 853),
        (5, 206, 892), (6, 192, 885), (7, 224, 872), (8, 230, 858),
        (9, 300, 924), (10, 307, 908), (11, 86, 864), (12, 110, 856),
        (13, 104, 832)]
LAND = [  # ellipses (x0, y0, x1, y1) forming a coarse dotted world map
    (45, 826, 170, 880), (175, 824, 200, 837), (130, 883, 185, 940),
    (185, 837, 235, 862), (190, 865, 250, 929), (235, 830, 310, 880),
    (255, 880, 285, 897), (265, 912, 305, 935), (180, 840, 192, 851),
    (300, 844, 312, 862), (235, 862, 265, 894), (190, 855, 230, 869),
    (165, 840, 195, 858), (205, 865, 235, 887), (185, 826, 205, 844),
    (308, 928, 318, 940),
]


def kicker(d, x, y, num, region, topic, src, tag, width, size=10):
    """Left: 'N · REGION · TOPIC'; right: 'SOURCE · TAG'. Drops topic if tight."""
    f, sf = F(SANS_B, size), F(SANS, size - 1)
    right = f"{src} · {tag}"
    full = f"{num} · {region} · {topic}"
    if d.textlength(full, font=f) + d.textlength(right, font=sf) + 12 > width:
        full = f"{num} · {region}"
    d.text((x, y), full, font=f, fill=RED)
    d.text((x + width - d.textlength(right, font=sf), y), right, font=sf,
           fill=MUTED)


def kicker2(d, x, y, num, region, topic, src, tag, width):
    """Two-line kicker for the narrow secondary cards: line 1 is the
    number/region/topic, line 2 is the source and verification tag."""
    d.text((x, y), f"{num} · {region} · {topic}", font=F(SANS_B, 9), fill=RED)
    d.text((x, y + 11), f"{src} · {tag}", font=F(SANS, 8), fill=MUTED)


def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    M = 24
    X1 = W - M

    # ---- header ----
    d.rectangle([M, 14, 116, 136], fill=RED)
    d.text((30, 20), "NOV", font=F(SANS_B, 22), fill=(255, 255, 255))
    d.text((30, 44), "25", font=F(SERIF_B, 52), fill=(255, 255, 255))
    d.text((30, 104), "WED 2026", font=F(SANS_B, 13), fill=(255, 255, 255))
    d.text((132, 18), "THE DAY IN WORLD NEWS", font=F(SANS_B, 15), fill=RED)
    d.text((132, 38), "Wednesday 25 November 2026", font=F(SERIF_B, 44), fill=INK)
    d.text((132, 98),
           "Everything on this page happened, or was first reported, on Wednesday 25 November 2026.",
           font=F(SANS, 15), fill=MUTED)
    for i, line in enumerate(["35 STORIES", "7 REGIONS", "15 FIELDS"]):
        f = F(SANS_B, 19)
        d.text((X1 - d.textlength(line, font=f), 24 + i * 26), line, font=f, fill=INK)
    d.line([M, 142, X1, 142], fill=INK, width=2)

    # ---- timeline strip: seven timed events across the day ----
    ty = 147
    d.text((M, ty), "THE DAY IN UTC", font=F(SANS_B, 11), fill=RED)
    tw = (X1 - M) / 7
    for i, (t, lab) in enumerate(TIMELINE):
        cx = M + i * tw
        d.text((cx, ty + 13), t, font=F(SANS_B, 12), fill=RED)
        put_text(d, (cx, ty + 26), lab, F(SANS, 9), tw - 8, INK, leading=1,
                 limit=1)
    d.line([M, 182, X1, 182], fill=RULE, width=1)

    # ---- region strip ----
    y0, y1 = 186, 210
    total_w = X1 - M
    widths = [max(64, int(total_w * n / 35)) for _, n, _ in REGIONS]
    scale = total_w / sum(widths)
    widths = [int(w * scale) for w in widths]
    widths[-1] += total_w - sum(widths)
    x = M
    for (name, n, col), w in zip(REGIONS, widths):
        d.rectangle([x, y0, x + w - 1, y1], fill=col)
        label = f"{name} {n}"
        f = F(SANS_B, 13)
        if d.textlength(label, font=f) <= w - 8:
            d.text((x + (w - d.textlength(label, font=f)) / 2, y0 + 6),
                   label, font=f, fill=(255, 255, 255))
        else:
            f2 = F(SANS_B, 10)
            d.text((x + (w - d.textlength(name, font=f2)) / 2, y0 + 2),
                   name, font=f2, fill=(255, 255, 255))
            d.text((x + (w - d.textlength(str(n), font=f2)) / 2, y0 + 13),
                   str(n), font=f2, fill=(255, 255, 255))
        x += w

    # ---- numbers strip: six cells, two rows of three ----
    ny = 216
    for row in range(2):
        for col in range(3):
            num, lab = NUMBERS[row * 3 + col]
            cx = M + col * 325
            cy = ny + row * 23
            f1, f2 = F(SANS_B, 16), F(SANS, 11)
            d.text((cx, cy), num, font=f1, fill=RED)
            lx = cx + d.textlength(num + " ", font=f1)
            d.text((lx, cy + 3), lab, font=f2, fill=INK)
            end = lx + d.textlength(lab, font=f2)
            if end > X1:
                print(f"OVERFLOW: numbers cell {num!r} ends at {end}, edge {X1}")
    d.line([M, 266, X1, 266], fill=RULE, width=1)

    # ---- hero stories ----
    hy, hh = 272, 228
    hw, gap = 312, 20
    for i, (num, region, topic, src, tag, head, summ) in enumerate(HEROES):
        x = M + i * (hw + gap)
        d.rectangle([x, hy, x + hw, hy + hh], fill=CARD, outline=RULE, width=1)
        PICS[num](d, (x + 1, hy + 1, x + hw - 1, hy + 125))
        ky = hy + 132
        kicker(d, x + 10, ky, num, region, topic, src, tag, hw - 20, size=11)
        y2 = put_text(d, (x + 10, ky + 17), head, F(SERIF_B, 21),
                      hw - 20, INK, leading=1, limit=2)
        put_text(d, (x + 10, y2 + 3), summ, F(SANS, 12),
                 hw - 20, MUTED, leading=1, limit=2)

    # ---- secondary stories: 5 columns x 2 rows ----
    sy = 508
    cw, cgap = 187, 10
    ch = 140
    for i, (num, region, topic, src, tag, head, summ) in enumerate(SECONDARY):
        col, row = i % 5, i // 5
        x = M + col * (cw + cgap)
        yy = sy + row * (ch + 8)
        d.rectangle([x, yy, x + cw, yy + ch], fill=CARD, outline=RULE, width=1)
        PICS[num](d, (x + 1, yy + 1, x + cw - 1, yy + 57))
        kicker2(d, x + 8, yy + 61, num, region, topic, src, tag, cw - 16)
        y2 = put_text(d, (x + 8, yy + 86), head, F(SERIF_B, 14),
                      cw - 16, INK, leading=1, limit=2)
        put_text(d, (x + 8, y2 + 2), summ, F(SANS, 10),
                 cw - 16, MUTED, leading=1, limit=2)

    # ---- map + list ----
    my = 804
    d.line([M, my - 4, X1, my - 4], fill=INK, width=2)
    d.text((M, my), "WHERE IT HAPPENED", font=F(SANS_B, 14), fill=INK)
    d.text((330, my), "ALSO ON WEDNESDAY 25 NOVEMBER — 22 MORE STORIES",
           font=F(SANS_B, 14), fill=INK)
    # dotted map
    mx0, my0, mx1, my1 = M, my + 20, 318, 940
    for gx in range(mx0, mx1, 6):
        for gy in range(my0, my1, 6):
            cx, cy = gx + 3, gy + 3
            if any((cx - (a + c) / 2) ** 2 / (((c - a) / 2) ** 2) +
                   (cy - (b + e) / 2) ** 2 / (((e - b) / 2) ** 2) <= 1
                   for a, b, c, e in LAND):
                d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=MAPDOT)
    for num, px, py in PINS:
        col = RED if num <= 3 else NAVY
        d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=col,
                  outline=(255, 255, 255), width=1)
        f = F(SANS_B, 9 if num < 10 else 8)
        t = str(num)
        d.text((px - d.textlength(t, font=f) / 2, py - 5), t, font=f,
               fill=(255, 255, 255))
    d.text((M, 944),
           "Europe 9 · Americas 10 · Asia 5 · Africa 5 · Middle East 3 · Oceania 2 · World 1",
           font=F(SANS, 9), fill=MUTED)
    # numbered list, two columns of 11
    lf = F(SANS, 11)
    for i, item in enumerate(LISTED):
        col = i // 11
        row = i % 11
        lx = 330 + col * 336
        ly = my + 22 + row * 10.5
        num = 14 + i
        d.text((lx, ly), f"{num}", font=F(SANS_B, 11), fill=RED)
        d.text((lx + 22, ly), item, font=lf, fill=INK)

    # ---- date check box ----
    by0 = 954
    d.rectangle([M, by0, X1, by0 + 48], outline=RED, width=2)
    d.text((M + 10, by0 + 3), "DATE CHECK", font=F(SANS_B, 12), fill=RED)
    d.text((M + 108, by0 + 3),
           "Left out on purpose — each was first reported before Wednesday:",
           font=F(SANS, 12), fill=INK)
    dc = F(SANS, 9)
    d.text((M + 10, by0 + 16),
           "Shenzhou 24 crew named · Cikande toll 26 · CAS restores Senegal title · Dow tops 50,000 · UAE bus crash 13 · Hanoi blast 6 · Abu Nahal killed (all 24 Nov)",
           font=dc, fill=MUTED)
    d.text((M + 10, by0 + 26),
           "Huawei convicted · Odesa strike kills 2 · Riyadh tower hit, 11 hurt · Mississippi crash, 6 killed · Martha Ford dies at 101 · N Korean boat return (24 Nov) · China death sentence (23 Nov)",
           font=dc, fill=MUTED)
    d.text((M + 10, by0 + 36),
           "Not yet: Thanksgiving Day (Thu) · Macy's parade (Sat 28 Nov) · Chess game 3 (Thu) · Tariff hearing (25 Jan) · Hasina returns 16 Dec · Rohingya returns (Dec)",
           font=dc, fill=RED)
    # ---- footer ----
    d.text((M, 1006),
           "Tags: CONFIRMED — two or more outlets · OFFICIAL — on the record · REPORTED — one outlet",
           font=F(SANS, 8), fill=MUTED)
    d.text((M, 1015),
           "Sources: Reuters · AP · AFP · BBC · Al Jazeera · Yonhap · Xinhua",
           font=F(SANS, 8), fill=MUTED)
    attr = "Original drawings. Claims are attributed, not stated as fact."
    d.text((X1 - d.textlength(attr, font=F(SANS, 8)), 1015), attr,
           font=F(SANS, 8), fill=MUTED)

    total = len(HEROES) + len(SECONDARY) + len(LISTED)
    rsum = sum(n for _, n, _ in REGIONS)
    print(f"counts: heroes {len(HEROES)} + secondary {len(SECONDARY)} + listed {len(LISTED)} = {total}; regions sum {rsum}; fields {len(FIELDS)}")
    assert total == 35 and rsum == 35, "counts do not reconcile to 35"
    assert len(FIELDS) == 15, "field count wrong"

    img.save("entry.png", optimize=True)
    print("saved entry.png", img.size, "bytes:", os.path.getsize("entry.png"))


if __name__ == "__main__":
    main()
