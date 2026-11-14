"""Every scene has handle(event), update(dt) and draw(surface)."""
import pygame

from game import data as D
from scenes import ui


class Scene:
    def __init__(self, app):
        self.app = app
        self.t = 0.0
        self.buttons = []
        self.msg = ""
        self.msg_t = 0.0
        self.msg_color = D.HUD

    @property
    def s(self):
        return self.app.s

    def say(self, msg, color=D.HUD, secs=2.6):
        self.msg, self.msg_t, self.msg_color = msg, secs, color

    def mouse(self):
        return pygame.mouse.get_pos()

    def handle(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            ui.click_any(list(self.buttons), e.pos)

    def update(self, dt):
        self.t += dt
        if self.msg_t > 0:
            self.msg_t -= dt

    def draw_toast(self, surf):
        if self.msg_t > 0:
            ui.toast(surf, self.msg, self.t, self.msg_color)

    def draw_buttons(self, surf):
        m = self.mouse()
        for b in self.buttons:
            b.draw(surf, m)
