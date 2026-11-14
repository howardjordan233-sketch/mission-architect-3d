"""Shared drawing helpers: fonts, text, buttons, panels, meters, starfield."""
import math
import os
import random

import pygame

from game import data as D
from game import render3d as R

W, H = 1280, 720
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_FILES = {
    "mono": os.path.join(ROOT, "assets", "fonts", "DejaVuSansMono.ttf"),
    "bold": os.path.join(ROOT, "assets", "fonts", "DejaVuSansMono-Bold.ttf"),
    "title": os.path.join(ROOT, "assets", "fonts", "Poppins-Bold.ttf"),
}
PANEL = (18, 22, 30)
PANEL_HI = (26, 32, 42)
EDGE = (40, 70, 78)

_fonts = {}


def font(size, kind="mono"):
    key = (size, kind)
    if key not in _fonts:
        try:
            _fonts[key] = pygame.font.Font(FONT_FILES[kind], size)
        except Exception:
            _fonts[key] = pygame.font.Font(None, int(size * 1.3))
    return _fonts[key]


def text(surf, s, pos, size=16, color=D.HUD, kind="mono", anchor="topleft", alpha=None):
    img = font(size, kind).render(str(s), True, color)
    if alpha is not None:
        img.set_alpha(alpha)
    r = img.get_rect(**{anchor: pos})
    surf.blit(img, r)
    return r


def wrap(s, size, width, kind="mono"):
    f = font(size, kind)
    lines = []
    for para in str(s).split("\n"):
        indent = para[:len(para) - len(para.lstrip(" "))]
        words = para.strip(" ").split(" ")
        line = indent
        for w in words:
            test = (line + " " + w) if line.strip() else indent + w
            if f.size(test)[0] <= width:
                line = test
            else:
                if line.strip():
                    lines.append(line)
                line = indent + w
        lines.append(line)
    return lines


def text_box(surf, s, rect, size=15, color=D.CREAM, kind="mono", gap=4):
    """Wrapped text inside rect. Returns the y below the last line."""
    x, y, w, h = rect
    lh = font(size, kind).get_linesize() + gap - 4
    for line in wrap(s, size, w, kind):
        if y + lh > rect[1] + h + 2:
            break
        text(surf, line, (x, y), size, color, kind)
        y += lh
    return y


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return (int(lerp(c1[0], c2[0], t)), int(lerp(c1[1], c2[1], t)), int(lerp(c1[2], c2[2], t)))


def state_color(state):
    return {"ok": D.HUD, "warn": D.YELLOW, "bad": D.RED}.get(state, D.HUD)


# ---------------------------------------------------------------- widgets
class Button:
    def __init__(self, rect, label, on=None, enabled=True, selected=False, accent=D.ORANGE,
                 size=15, sub=None, hint=None, kind="bold"):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.on = on
        self.enabled = enabled
        self.selected = selected
        self.accent = accent
        self.size = size
        self.sub = sub
        self.hint = hint
        self.kind = kind

    def hover(self, mouse):
        return self.rect.collidepoint(mouse)

    def draw(self, surf, mouse=(-1, -1)):
        hov = self.enabled and self.hover(mouse)
        if self.selected and not self.enabled:
            bg, fg, edge = mix(self.accent, PANEL, 0.55), D.SPACE, mix(self.accent, PANEL, 0.4)
        elif self.selected:
            bg, fg, edge = self.accent, D.SPACE, self.accent
        elif not self.enabled:
            bg, fg, edge = (20, 23, 28), D.DIM, (34, 40, 48)
        else:
            bg = PANEL_HI if not hov else mix(PANEL_HI, self.accent, 0.25)
            fg, edge = D.CREAM, self.accent if hov else EDGE
        pygame.draw.rect(surf, bg, self.rect, border_radius=6)
        pygame.draw.rect(surf, edge, self.rect, 2 if (hov or self.selected) else 1,
                         border_radius=6)
        if self.sub:
            text(surf, self.label, (self.rect.x + 10, self.rect.y + 6), self.size, fg, self.kind)
            text(surf, self.sub, (self.rect.x + 10, self.rect.bottom - 6), 12,
                 fg if self.selected else (D.HUD if self.enabled else D.DIM), "mono",
                 anchor="bottomleft")
        else:
            text(surf, self.label, self.rect.center, self.size, fg, self.kind, anchor="center")

    def click(self, pos):
        if self.enabled and self.rect.collidepoint(pos) and self.on:
            self.on()
            return True
        return False


def click_any(buttons, pos):
    for b in buttons:
        if b.click(pos):
            return True
    return False


class TextInput:
    def __init__(self, rect, value="", placeholder="", limit=14, upper=False):
        self.rect = pygame.Rect(rect)
        self.value = value
        self.placeholder = placeholder
        self.limit = limit
        self.active = False
        self.upper = upper

    def handle(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.active = self.rect.collidepoint(e.pos)
            return self.active
        if self.active and e.type == pygame.KEYDOWN:
            if e.key == pygame.K_BACKSPACE:
                self.value = self.value[:-1]
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_TAB, pygame.K_ESCAPE):
                self.active = False
            elif e.unicode and e.unicode.isprintable() and len(self.value) < self.limit:
                self.value += e.unicode.upper() if self.upper else e.unicode
            return True
        return False

    def draw(self, surf, t=0.0):
        pygame.draw.rect(surf, (10, 12, 16), self.rect, border_radius=5)
        pygame.draw.rect(surf, D.ORANGE if self.active else EDGE, self.rect, 1, border_radius=5)
        shown = self.value or self.placeholder
        col = D.CREAM if self.value else D.DIM
        r = text(surf, shown, (self.rect.x + 8, self.rect.centery), 15, col, anchor="midleft")
        if self.active and int(t * 2) % 2 == 0:
            x = r.right + 2 if self.value else self.rect.x + 8
            pygame.draw.line(surf, D.HUD, (x, self.rect.y + 7), (x, self.rect.bottom - 7), 2)


# ---------------------------------------------------------------- panels and meters
def panel(surf, rect, title=None, accent=D.TEAL):
    r = pygame.Rect(rect)
    pygame.draw.rect(surf, PANEL, r, border_radius=8)
    pygame.draw.rect(surf, EDGE, r, 1, border_radius=8)
    if title:
        pygame.draw.rect(surf, accent, (r.x + 1, r.y + 1, r.w - 2, 26),
                         border_top_left_radius=8, border_top_right_radius=8)
        lum = 0.3 * accent[0] + 0.59 * accent[1] + 0.11 * accent[2]
        text(surf, title, (r.x + 12, r.y + 14), 13, D.SPACE if lum > 110 else D.CREAM, "bold",
             anchor="midleft")
    return r


def meter(surf, rect, label, value, frac, state):
    x, y, w, h = rect
    col = state_color(state)
    text(surf, label.upper(), (x, y), 12, D.DIM, "bold")
    text(surf, value, (x + w, y), 12, col, anchor="topright")
    by = y + 18
    pygame.draw.rect(surf, (8, 10, 14), (x, by, w, 8), border_radius=3)
    fw = int(w * max(0.0, min(1.0, frac)))
    if fw > 0:
        pygame.draw.rect(surf, col, (x, by, fw, 8), border_radius=3)
    # tick marks like an analog gauge
    for i in range(1, 10):
        tx = x + w * i // 10
        pygame.draw.line(surf, (30, 36, 44), (tx, by), (tx, by + 7))


def star_shape(cx, cy, r):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    return pts


def stars(surf, center, n, size=22, total=5, gap=None):
    gap = gap or size * 2.3
    x0 = center[0] - gap * (total - 1) / 2
    for i in range(total):
        col = D.GOLD if i < n else (40, 44, 52)
        pygame.draw.polygon(surf, col, star_shape(x0 + i * gap, center[1], size))


# ---------------------------------------------------------------- backgrounds
class Starfield:
    def __init__(self, count=220, seed=3):
        rng = random.Random(seed)
        self.stars = [(rng.random() * W, rng.random() * H, rng.random()) for _ in range(count)]
        self.grad = pygame.Surface((W, H))
        for y in range(H):
            t = y / H
            pygame.draw.line(self.grad, mix((10, 12, 22), (16, 22, 30), t), (0, y), (W, y))

    def draw(self, surf, t=0.0, drift=4.0):
        surf.blit(self.grad, (0, 0))
        for x, y, b in self.stars:
            xx = (x - t * drift * (0.3 + b)) % W
            tw = 0.75 + 0.25 * math.sin(t * 2 + x)
            c = int(70 + 150 * b * tw)
            surf.set_at((int(xx), int(y)), (c, c, min(255, c + 15)))
            if b > 0.93:
                surf.set_at((int(xx) + 1, int(y)), (c, c, c))


_scan = None


def scanlines(surf):
    """Faint CRT lines over everything."""
    global _scan
    if _scan is None:
        _scan = pygame.Surface((W, H), pygame.SRCALPHA)
        for y in range(0, H, 3):
            pygame.draw.line(_scan, (0, 0, 0, 34), (0, y), (W, y))
        # vignette corners
        for i in range(60):
            a = int(90 * (1 - i / 60) ** 2)
            pygame.draw.rect(_scan, (0, 0, 0, a), (i, i, W - 2 * i, H - 2 * i), 1)
    surf.blit(_scan, (0, 0))


def grid_floor(surf, cam, ox=0, oy=0, size=6, step=1.0, color=(30, 60, 66)):
    """A perspective grid on y=0, like a hangar floor. Lines are cut into short
    segments so the parts near or behind the camera are simply skipped."""
    n = int(size / step)
    seg = 12

    def line(a, b):
        pts = [R.project_point((a[0] + (b[0] - a[0]) * k / seg, 0,
                                a[1] + (b[1] - a[1]) * k / seg), cam, ox, oy)
               for k in range(seg + 1)]
        for p, q in zip(pts, pts[1:]):
            if p and q and abs(p[0]) < 5000 and abs(q[0]) < 5000:
                pygame.draw.aaline(surf, color, p, q)

    for i in range(-n, n + 1):
        line((i * step, -size), (i * step, size))
        line((-size, i * step), (size, i * step))


def draw_faces(surf, faces, outline=True, alpha_surf=None):
    """Draw faces from render3d.render with flat shading and dark edges."""
    for pts, color, shade, depth, part in faces:
        a = part.get("alpha")
        col = R.lit(color, shade)
        if part.get("glow"):
            col = mix(col, part["glow"], 0.35)
        if a is not None and alpha_surf is not None:
            pygame.draw.polygon(alpha_surf, col + (a,), pts)
            pygame.draw.polygon(alpha_surf, part.get("edge", D.HUD) + (min(255, a * 4),), pts, 1)
            continue
        pygame.draw.polygon(surf, col, pts)
        if outline and not part.get("smooth"):
            pygame.draw.polygon(surf, R.lit(color, shade * 0.45), pts, 1)


_overlay = None


def overlay(surf, color, alpha):
    global _overlay
    if _overlay is None:
        _overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    _overlay.fill(tuple(color) + (int(max(0, min(255, alpha))),))
    surf.blit(_overlay, (0, 0))


def toast(surf, msg, t, color=D.HUD):
    if not msg:
        return
    r = text(surf, msg, (W // 2, H - 40), 15, color, "bold", anchor="center")
    bg = r.inflate(28, 14)
    s = pygame.Surface(bg.size, pygame.SRCALPHA)
    s.fill((10, 12, 16, 220))
    surf.blit(s, bg)
    pygame.draw.rect(surf, color, bg, 1, border_radius=6)
    text(surf, msg, (W // 2, H - 40), 15, color, "bold", anchor="center")
