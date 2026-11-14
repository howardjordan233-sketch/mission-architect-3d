"""Draws the round mission patch from game.patch.patch_design() data."""
import math
import os
import sys

import pygame

from game import data as D
from scenes import ui


def _ring_text(surf, txt, center, radius, size, color, start, sweep, flip=False):
    f = ui.font(size, "bold")
    n = max(1, len(txt))
    for i, ch in enumerate(txt):
        k = (i + 0.5) / n
        a = start + sweep * k
        img = f.render(ch, True, color)
        rot = -math.degrees(a) - 90 if not flip else -math.degrees(a) + 90
        img = pygame.transform.rotate(img, rot)
        x = center[0] + math.cos(a) * radius
        y = center[1] + math.sin(a) * radius
        surf.blit(img, img.get_rect(center=(x, y)))


def _icon(surf, kind, c, r, color):
    x, y = c
    if kind == "panel":
        pygame.draw.rect(surf, color, (x - r, y - r * 0.5, r * 2, r), 2)
        pygame.draw.line(surf, color, (x, y - r * 0.5), (x, y + r * 0.5), 2)
    elif kind == "atom":
        pygame.draw.circle(surf, color, c, 3)
        for k in range(3):
            rect = pygame.Rect(0, 0, r * 2, r * 0.8)
            rect.center = c
            s = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.ellipse(s, color, s.get_rect(), 2)
            s = pygame.transform.rotate(s, k * 60)
            surf.blit(s, s.get_rect(center=c))
    elif kind == "lens":
        pygame.draw.circle(surf, color, c, int(r * 0.8), 2)
        pygame.draw.circle(surf, color, c, int(r * 0.35))
    elif kind == "prism":
        pygame.draw.polygon(surf, color, [(x, y - r), (x + r, y + r * 0.7), (x - r, y + r * 0.7)], 2)
    elif kind == "drill":
        pygame.draw.polygon(surf, color, [(x - r * 0.5, y - r), (x + r * 0.5, y - r), (x, y + r)])
    elif kind == "waves":
        for k in range(3):
            pygame.draw.arc(surf, color, (x - r + k * 4, y - r + k * 4, (r - k * 4) * 2,
                                          (r - k * 4) * 2), -0.8, 0.8, 2)
    elif kind == "loop":
        pygame.draw.circle(surf, color, c, int(r * 0.8), 2)
        pygame.draw.line(surf, color, (x, y - r), (x, y + r), 2)
    elif kind == "flame":
        pygame.draw.polygon(surf, color, [(x, y - r), (x + r * 0.6, y + r * 0.4),
                                          (x, y + r), (x - r * 0.6, y + r * 0.4)])


def draw_patch(surf, p, center, radius=180):
    cx, cy = center
    pygame.draw.circle(surf, p["ring"], center, radius)
    pygame.draw.circle(surf, D.CREAM, center, radius, 4)
    inner = int(radius * 0.74)
    pygame.draw.circle(surf, p["field"], center, inner)
    pygame.draw.circle(surf, D.CREAM, center, inner, 3)
    _ring_text(surf, p["top_text"], center, radius * 0.87, int(radius * 0.11), D.SPACE,
               -math.pi * 0.92, math.pi * 0.84)
    _ring_text(surf, p["bottom_text"], center, radius * 0.87, int(radius * 0.09), D.SPACE,
               math.pi * 0.92, -math.pi * 0.84, flip=True)
    # stars inside the field
    for i in range(30):
        a = i * 2.39996
        rr = inner * (0.15 + 0.8 * ((i * 37) % 100) / 100)
        sx, sy = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        surf.set_at((int(sx), int(sy)), D.CREAM)
    # planet arc at the bottom of the field
    planet = pygame.Surface((inner * 2, inner * 2), pygame.SRCALPHA)
    pygame.draw.circle(planet, p["planet"] + (255,), (inner, int(inner * 2.05)), int(inner * 1.25))
    mask = pygame.Surface((inner * 2, inner * 2), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (inner, inner), inner - 2)
    planet.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(planet, (cx - inner, cy - inner))
    # spacecraft silhouette
    bw = inner * 0.22
    by = cy - inner * 0.18
    pygame.draw.rect(surf, D.CREAM, (cx - bw / 2, by - bw / 2, bw, bw))
    pygame.draw.rect(surf, D.TEAL, (cx - bw * 2.2, by - bw * 0.12, bw * 1.6, bw * 0.24))
    pygame.draw.rect(surf, D.TEAL, (cx + bw * 0.6, by - bw * 0.12, bw * 1.6, bw * 0.24))
    pygame.draw.polygon(surf, D.CREAM, [(cx - bw * 0.4, by - bw / 2), (cx + bw * 0.4, by - bw / 2),
                                        (cx, by - bw * 1.1)])
    if p["lander"]:
        for s in (-1, 1):
            pygame.draw.line(surf, D.CREAM, (cx + s * bw * 0.4, by + bw / 2),
                             (cx + s * bw * 0.8, by + bw), 3)
    # icons
    icons = p["icons"][:5]
    gap = inner * 0.32
    x0 = cx - gap * (len(icons) - 1) / 2
    for i, k in enumerate(icons):
        _icon(surf, k, (int(x0 + i * gap), int(cy + inner * 0.32)), int(inner * 0.1), D.CREAM)
    ui.stars(surf, (cx, cy + inner * 0.62), p["stars"], size=int(inner * 0.07),
             gap=inner * 0.17)


def save_patch(p, code):
    """Renders a 512 px patch and saves it. In the browser it also downloads it.

    Returns a message for the player.
    """
    img = pygame.Surface((512, 512), pygame.SRCALPHA)
    draw_patch(img, p, (256, 256), 250)
    name = "mission_patch_%s.png" % (code.replace("-", "_") or "design")
    if sys.platform == "emscripten":
        path = "/tmp/" + name
        try:
            pygame.image.save(img, path)
            import platform  # pygbag's browser bridge
            platform.window.MM.download(path)
            return "Patch downloaded: " + name
        except Exception:
            return "Couldn't download here. Take a screenshot to keep it!"
    try:
        path = os.path.abspath(name)
        pygame.image.save(img, path)
        return "Saved " + path
    except Exception:
        return "Couldn't save the patch on this computer."


def save_text(text, name):
    """Saves the mission report. In the browser it downloads as a .txt file."""
    if sys.platform == "emscripten":
        path = "/tmp/" + name
        try:
            with open(path, "w") as fh:
                fh.write(text)
            import platform  # pygbag's browser bridge
            platform.window.MM.download(path)
            return "Report downloaded: " + name
        except Exception:
            return "Couldn't download here. Take a screenshot to keep it!"
    try:
        path = os.path.abspath(name)
        with open(path, "w") as fh:
            fh.write(text)
        return "Saved " + path
    except Exception:
        return "Couldn't save the report on this computer."
