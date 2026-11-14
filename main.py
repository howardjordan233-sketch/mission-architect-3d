"""Mission Architect 3D: design a NASA mission, launch it, live with the results.

Runs on the desktop (python main.py) and in the browser (python -m pygbag .).
The loop is async because pygbag needs `await asyncio.sleep(0)` every frame.
Nothing may follow asyncio.run(main()) at the bottom of this file.
"""
import asyncio
import sys

import pygame

from scenes import ui
from scenes.app import App, DEMO_SEED


TOUCH_MOUSE = (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION)


def translate(e, app):
    """Touch support. Phones, tablets and touch laptops send finger events with
    the true tap position; the mouse events SDL makes from a tap can carry a
    stale position. Use the finger events, skip the made-up mouse ones."""
    t = e.type
    if t in TOUCH_MOUSE and getattr(e, "touch", False):
        return []
    if t in (pygame.FINGERDOWN, pygame.FINGERUP, pygame.FINGERMOTION):
        pos = (int(e.x * ui.W), int(e.y * ui.H))
        app.mouse_pos = pos
        if t == pygame.FINGERDOWN:
            return [pygame.event.Event(pygame.MOUSEMOTION, pos=pos, rel=(0, 0), buttons=(0, 0, 0)),
                    pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)]
        if t == pygame.FINGERUP:
            return [pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=pos)]
        return [pygame.event.Event(pygame.MOUSEMOTION, pos=pos, buttons=(1, 0, 0),
                                   rel=(int(e.dx * ui.W), int(e.dy * ui.H)))]
    if hasattr(e, "pos"):
        app.mouse_pos = e.pos
    return [e]


async def main():
    pygame.init()
    pygame.display.set_caption("Mission Architect 3D")
    flags = pygame.SCALED if sys.platform != "emscripten" else 0
    screen = pygame.display.set_mode((ui.W, ui.H), flags)
    clock = pygame.time.Clock()
    app = App(screen)
    while app.running:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        events = []
        for raw in pygame.event.get():
            events.extend(translate(raw, app))
        for e in events:
            if e.type == pygame.QUIT:
                app.running = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_F9:
                on = app.toggle_demo() is not None
                app.scene.say("Demo seed %s" % ("ON (%d)" % DEMO_SEED if on else "OFF"))
            else:
                app.scene.handle(e)
        app.scene.update(dt)
        app.scene.draw(screen)
        ui.scanlines(screen)
        pygame.display.flip()
        await asyncio.sleep(0)


asyncio.run(main())
