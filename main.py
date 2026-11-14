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


async def main():
    pygame.init()
    pygame.display.set_caption("Mission Architect 3D")
    flags = pygame.SCALED if sys.platform != "emscripten" else 0
    screen = pygame.display.set_mode((ui.W, ui.H), flags)
    clock = pygame.time.Clock()
    app = App(screen)
    while app.running:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        for e in pygame.event.get():
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
