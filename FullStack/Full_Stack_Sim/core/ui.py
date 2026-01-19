import pygame
import math
from settings import *

class HandheldChassis:
    """Renders the rugged industrial scanner device frame."""
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.inner_rect = self.rect.inflate(-20, -20)

    def draw(self, screen):
        # Draw body, bezel, and hazard stripes
        shadow_rect = self.rect.copy()
        shadow_rect.y += 5
        pygame.draw.rect(screen, (20, 20, 25), shadow_rect, border_radius=30)
        pygame.draw.rect(screen, DEVICE_BODY, self.rect, border_radius=30)
        pygame.draw.rect(screen, DEVICE_HIGHLIGHT, self.rect, width=3, border_radius=30)
        
        self._draw_hazard_stripes(screen, self.rect.left, self.rect.top + 40, 15, self.rect.height - 80)
        self._draw_hazard_stripes(screen, self.rect.right - 15, self.rect.top + 40, 15, self.rect.height - 80)
        
        self._draw_bolt(screen, self.rect.left + 20, self.rect.top + 20)
        self._draw_bolt(screen, self.rect.right - 20, self.rect.top + 20)
        self._draw_bolt(screen, self.rect.left + 20, self.rect.bottom - 20)
        self._draw_bolt(screen, self.rect.right - 20, self.rect.bottom - 20)

    def _draw_hazard_stripes(self, screen, x, y, w, h):
        bg_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(screen, STRIPE_BLACK, bg_rect)
        clip_rect = bg_rect
        screen.set_clip(clip_rect)
        stripe_width = 10
        gap = 10
        for i in range(-20, h + 20, stripe_width + gap):
            p1 = (x, y + i)
            p2 = (x + w, y + i + 10)
            p3 = (x + w, y + i + 10 + stripe_width)
            p4 = (x, y + i + stripe_width)
            pygame.draw.polygon(screen, STRIPE_YELLOW, [p1, p2, p3, p4])
        screen.set_clip(None)
        pygame.draw.rect(screen, (0,0,0), bg_rect, 2)

    def _draw_bolt(self, screen, x, y):
        pygame.draw.circle(screen, (50, 50, 50), (x, y+2), 7)
        pygame.draw.circle(screen, BOLT_COLOR, (x, y), 6)
        pygame.draw.circle(screen, (100, 100, 100), (x, y), 2)
        pygame.draw.line(screen, (100, 100, 100), (x-3, y), (x+3, y), 1)
        pygame.draw.line(screen, (100, 100, 100), (x, y-3), (x, y+3), 1)

class LCDDisplay:
    """Handles text input and status messages on the scanner screen."""
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = ""
        self.status_msg = "SYSTEM READY"
        self.font_large = pygame.font.SysFont("Consolas", 24, bold=True)
        self.font_small = pygame.font.SysFont("Consolas", 12)
        self.active = True
        self.cursor_blink = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                return self.text
            else:
                allowed_chars = ':-+*/^()'
                if event.unicode.isalnum() or event.unicode in allowed_chars:
                    self.text += event.unicode.upper()
        return None

    def update_status(self, msg):
        self.status_msg = msg

    def update(self):
        self.cursor_blink += 1

    def draw(self, screen):
        pygame.draw.rect(screen, (10, 15, 20), self.rect, border_radius=5)
        screen_rect = self.rect.inflate(-10, -10)
        pygame.draw.rect(screen, LCD_BG, screen_rect, border_radius=3)
        
        # Scanlines
        for i in range(screen_rect.top, screen_rect.bottom, 4):
            pygame.draw.line(screen, LCD_SCANLINE, (screen_rect.left, i), (screen_rect.right, i), 1)
            
        # Status Text
        status_surf = self.font_small.render(self.status_msg, True, LCD_TEXT_DIM)
        screen.blit(status_surf, (screen_rect.x + 10, screen_rect.y + 8))
        
        # Input Text
        display_text = self.text
        txt_surf = self.font_large.render(display_text, True, LCD_TEXT_MAIN)
        
        # Scroll text if too long
        while txt_surf.get_width() > screen_rect.width - 10:
            display_text = display_text[1:]
            txt_surf = self.font_large.render(display_text, True, LCD_TEXT_MAIN)
            
        txt_x = screen_rect.left + 5
        txt_y = screen_rect.centery - 5
        screen.set_clip(screen_rect)
        screen.blit(txt_surf, (txt_x, txt_y))
        
        # Blinking Cursor
        if (self.cursor_blink // 30) % 2 == 0:
            cursor_x = txt_x + txt_surf.get_width() + 2
            if cursor_x < screen_rect.right - 10:
                pygame.draw.rect(screen, LCD_TEXT_MAIN, (cursor_x, txt_y, 10, 24))
        screen.set_clip(None)

class RoundButton:
    """Circular interactive button."""
    def __init__(self, cx, cy, radius, color_base, color_light, text, callback):
        self.center = (cx, cy)
        self.radius = radius
        self.rect = pygame.Rect(cx - radius, cy - radius, radius*2, radius*2)
        self.color_base = color_base
        self.color_light = color_light
        self.text = text
        self.callback = callback
        self.font = pygame.font.SysFont("Arial", 14, bold=True)
        self.is_hovered = False
        self.is_pressed = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            dx = event.pos[0] - self.center[0]
            dy = event.pos[1] - self.center[1]
            if math.sqrt(dx*dx + dy*dy) <= self.radius:
                self.is_hovered = True
            else:
                self.is_hovered = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered and event.button == 1:
                self.is_pressed = True
        if event.type == pygame.MOUSEBUTTONUP:
            if self.is_pressed and self.is_hovered:
                self.is_pressed = False
                return self.callback()
            self.is_pressed = False

    def draw(self, screen):
        cx, cy = self.center
        r = self.radius
        offset_y = 4 if not self.is_pressed else 0
        
        # Shadow and Body
        pygame.draw.circle(screen, BTN_SHADOW, (cx, cy + 6), r + 2)
        pygame.draw.circle(screen, (self.color_base[0]//2, self.color_base[1]//2, self.color_base[2]//2), (cx, cy + offset_y + 4), r)
        pygame.draw.circle(screen, self.color_base, (cx, cy + offset_y), r)
        
        # Highlight
        pygame.draw.circle(screen, self.color_light, (cx, cy + offset_y - 2), r - 4)
        pygame.draw.circle(screen, self.color_base, (cx, cy + offset_y + 2), r - 4)
        
        # Text
        txt_surf = self.font.render(self.text, True, (255, 255, 255))
        txt_rect = txt_surf.get_rect(center=(cx, cy + offset_y))
        shadow_surf = self.font.render(self.text, True, (0, 0, 0, 100))
        screen.blit(shadow_surf, (txt_rect.x + 1, txt_rect.y + 1))
        screen.blit(txt_surf, txt_rect)
        
        if self.is_hovered and not self.is_pressed:
            pygame.draw.circle(screen, (255, 255, 255), (cx, cy + offset_y), r, 2)

class Button:
    """Rectangular interactive button."""
    def __init__(self, x, y, w, h, text, callback_func):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback_func
        self.font = pygame.font.SysFont("Arial", 12, bold=True)
        self.is_hovered = False
        self.is_pressed = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered and event.button == 1:
                self.is_pressed = True
        if event.type == pygame.MOUSEBUTTONUP:
            if self.is_pressed and self.is_hovered:
                self.is_pressed = False
                return self.callback()
            self.is_pressed = False

    def draw(self, screen):
        base_color = (60, 70, 80)
        hover_color = (80, 90, 100)
        press_color = (40, 50, 60)
        color = base_color
        if self.is_hovered: color = hover_color
        if self.is_pressed: color = press_color
        
        shadow_rect = self.rect.copy()
        shadow_rect.y += 3
        pygame.draw.rect(screen, (30, 35, 40), shadow_rect, border_radius=3)
        
        btn_rect = self.rect.copy()
        if self.is_pressed:
            btn_rect.y += 2
        pygame.draw.rect(screen, color, btn_rect, border_radius=3)
        
        # Accent stripe
        pygame.draw.rect(screen, (255, 200, 0), (btn_rect.x, btn_rect.y, 5, btn_rect.height), border_top_left_radius=3, border_bottom_left_radius=3)
        pygame.draw.line(screen, (255, 255, 255, 50), btn_rect.topleft, btn_rect.topright, 1)
        
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=btn_rect.center)
        screen.blit(text_surf, text_rect)