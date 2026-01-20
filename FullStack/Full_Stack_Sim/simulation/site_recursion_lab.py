import pygame
import random
import math  # Added math import for lighting calculations
from settings import *
from core.ui import HandheldChassis, LCDDisplay, RoundButton, Button

# ... [Keep RecursionManager, DiskSprite, and MagneticCraneSprite classes unchanged] ...
class RecursionManager:
    def __init__(self):
        self.num_disks = 0
    def generate_moves_from_current_state(self, num_disks, current_pegs, destination_peg):
        self.num_disks = num_disks
        moves = []
        def find_disk(disk_val, pegs):
            for peg_name, disk_list in pegs.items():
                if disk_val in disk_list: return peg_name
            return None
        def _solve(n, dest):
            if n == 0: return
            src = find_disk(n, current_pegs)
            aux = [p for p in ['A', 'B', 'C'] if p != src and p != dest][0]
            if src == dest:
                _solve(n - 1, dest)
            else:
                _solve(n - 1, aux)
                moves.append({'from': src, 'to': dest})
                current_pegs[src].remove(n)
                current_pegs[dest].append(n)
                _solve(n - 1, dest)
        _solve(num_disks, destination_peg)
        return moves

class DiskSprite(pygame.sprite.Sprite):
    def __init__(self, value, max_value, height, color):
        super().__init__()
        self.value = value
        min_width = 80; max_width = 240
        self.width = int(min_width + (value / max_value) * (max_width - min_width))
        self.height = height; self.color = color
        self.pos_x, self.pos_y = 0.0, 0.0; self.target_x, self.target_y = 0.0, 0.0
        self.is_moving = False; self.on_finish_callback = None; self.attached_to = None
        self.is_dropping = False
        self.is_bouncing = False
        self.drop_velocity = 0.0
        self.gravity = 0.8
        self.bounce_factor = -0.4
        self.image = self._create_surface()
        self.rect = self.image.get_rect(midbottom=(0,0))
    def _create_surface(self):
        padding = 8
        surf = pygame.Surface((self.width + padding, self.height + padding), pygame.SRCALPHA)
        shadow_rect = pygame.Rect(padding, padding, self.width, self.height)
        pygame.draw.rect(surf, (0,0,0,50), shadow_rect, border_radius=4)
        main_rect = pygame.Rect(0, 0, self.width, self.height)
        dark_color = (self.color[0] * 0.7, self.color[1] * 0.7, self.color[2] * 0.7)
        highlight_color = (min(255, self.color[0] * 1.2), min(255, self.color[1] * 1.2), min(255, self.color[2] * 1.2))
        pygame.draw.rect(surf, self.color, main_rect, border_radius=4)
        pygame.draw.rect(surf, highlight_color, (0, 0, self.width, self.height // 4), border_top_left_radius=4, border_top_right_radius=4)
        for i in range(int(self.width * 0.1), int(self.width * 0.9), 12):
            pygame.draw.line(surf, dark_color, (i, 0), (i, self.height), 1)
        corner_size = 6
        pygame.draw.rect(surf, dark_color, (0,0,corner_size, corner_size))
        pygame.draw.rect(surf, dark_color, (self.width-corner_size,0,corner_size, corner_size))
        pygame.draw.rect(surf, dark_color, (0,self.height-corner_size,corner_size, corner_size))
        pygame.draw.rect(surf, dark_color, (self.width-corner_size,self.height-corner_size,corner_size, corner_size))
        pygame.draw.rect(surf, (20,20,20,150), main_rect, 2, border_radius=4)
        font_size = int(self.height * 0.7)
        try: font = pygame.font.SysFont("Impact", font_size)
        except: font = pygame.font.SysFont("Arial", font_size - 4, bold=True)
        text_surf = font.render(str(self.value), True, (255, 255, 255, 180))
        shadow_surf = font.render(str(self.value), True, (0, 0, 0, 80))
        text_rect = text_surf.get_rect(center=main_rect.center)
        surf.blit(shadow_surf, (text_rect.x + 2, text_rect.y + 2))
        surf.blit(text_surf, text_rect)
        return surf
    def move_to(self, target_pos, callback=None):
        self.target_x, self.target_y = target_pos; self.is_moving = True; self.on_finish_callback = callback
    def drop_to(self, target_pos, callback=None):
        self.target_x, self.target_y = target_pos
        self.is_dropping = True
        self.on_finish_callback = callback
    def update(self, speed_multiplier=1.0):
        padding = 8
        offset_x = padding // 2
        offset_y = padding
        if self.attached_to:
            self.rect.midtop = (int(self.attached_to.pos_x + offset_x), self.attached_to.rect.bottom)
            return
        if self.is_dropping:
            self.drop_velocity += self.gravity
            self.pos_y += self.drop_velocity
            if self.pos_y >= self.target_y:
                self.pos_y = self.target_y
                self.is_dropping = False
                self.is_bouncing = True
                self.drop_velocity *= self.bounce_factor
            self.rect.midbottom = (int(self.pos_x + offset_x), int(self.pos_y + offset_y))
            return
        if self.is_bouncing:
            self.drop_velocity += self.gravity
            self.pos_y += self.drop_velocity
            if self.pos_y >= self.target_y:
                self.pos_y = self.target_y
                self.is_bouncing = False
                self.drop_velocity = 0
                if self.on_finish_callback:
                    cb = self.on_finish_callback
                    self.on_finish_callback = None
                    cb()
            self.rect.midbottom = (int(self.pos_x + offset_x), int(self.pos_y + offset_y))
            return
        if not self.is_moving:
            self.rect.midbottom = (int(self.pos_x + offset_x), int(self.pos_y + offset_y))
            return
        dx = self.target_x - self.pos_x; dy = self.target_y - self.pos_y
        dist_sq = dx**2 + dy**2
        effective_speed = MIN_SPEED * speed_multiplier
        if dist_sq < effective_speed**2:
            self.pos_x, self.pos_y = self.target_x, self.target_y; self.is_moving = False
            if self.on_finish_callback: cb = self.on_finish_callback; self.on_finish_callback = None; cb()
        else:
            effective_lerp = LERP_FACTOR * speed_multiplier
            self.pos_x += dx * effective_lerp; self.pos_y += dy * effective_lerp
        self.rect.midbottom = (int(self.pos_x + offset_x), int(self.pos_y + offset_y))

class MagneticCraneSprite(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.trolley_width, self.trolley_height = 80, 25
        self.magnet_width, self.magnet_height = 40, 20
        self.min_cable_length = 20
        self.pos_x, self.pos_y = float(x), float(y); self.target_x, self.target_y = float(x), float(y)
        self.is_moving = False; self.move_callback = None
        self.cable_length = self.min_cable_length
        self.target_cable_length = self.min_cable_length
        self.is_hoisting = False; self.hoist_callback = None
        self.magnet_active = False
        self.image = self._create_surface()
        self.rect = self.image.get_rect(midtop=(x, y))
    def _create_surface(self):
        total_height = self.trolley_height + self.cable_length + self.magnet_height
        surf = pygame.Surface((self.trolley_width, total_height), pygame.SRCALPHA)
        trolley_rect = pygame.Rect(0, 0, self.trolley_width, self.trolley_height)
        pygame.draw.rect(surf, (80, 85, 90), trolley_rect, border_radius=3)
        pygame.draw.rect(surf, (50, 55, 60), trolley_rect, 2, border_radius=3)
        pygame.draw.rect(surf, (40,40,45), (5, -4, 10, 8)); pygame.draw.rect(surf, (40,40,45), (self.trolley_width - 15, -4, 10, 8))
        center_x = self.trolley_width / 2
        cable_end_y = self.trolley_height + self.cable_length
        pygame.draw.line(surf, (50, 55, 60), (center_x - 10, self.trolley_height), (center_x - 10, cable_end_y), 2)
        pygame.draw.line(surf, (50, 55, 60), (center_x + 10, self.trolley_height), (center_x + 10, cable_end_y), 2)
        magnet_rect = pygame.Rect(center_x - self.magnet_width/2, cable_end_y, self.magnet_width, self.magnet_height)
        pygame.draw.rect(surf, (80, 85, 90), magnet_rect, border_radius=3)
        pygame.draw.rect(surf, (50, 55, 60), magnet_rect, 2, border_radius=3)
        if self.magnet_active:
            glow_rect = magnet_rect.inflate(10, 10)
            glow_surf = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (255, 200, 0, 100), glow_surf.get_rect(), border_radius=8)
            surf.blit(glow_surf, (glow_rect.x - magnet_rect.x, glow_rect.y - magnet_rect.y))
        return surf
    def set_magnet(self, active):
        if self.magnet_active != active: self.magnet_active = active; self.image = self._create_surface()
    def move_to(self, target_pos, callback=None):
        self.target_x, self.target_y = target_pos; self.is_moving = True; self.move_callback = callback
    def set_hoist_length(self, length, callback=None):
        self.target_cable_length = max(self.min_cable_length, length)
        self.is_hoisting = True; self.hoist_callback = callback
    def update(self, speed_multiplier=1.0):
        moved = False
        if self.is_moving:
            dx = self.target_x - self.pos_x; dy = self.target_y - self.pos_y
            if (dx**2 + dy**2) < (MIN_SPEED * speed_multiplier)**2:
                self.pos_x, self.pos_y = self.target_x, self.target_y; self.is_moving = False
                if self.move_callback: cb = self.move_callback; self.move_callback = None; cb()
            else:
                self.pos_x += dx * LERP_FACTOR * speed_multiplier; self.pos_y += dy * LERP_FACTOR * speed_multiplier
            moved = True
        if self.is_hoisting:
            dc = self.target_cable_length - self.cable_length
            if abs(dc) < MIN_SPEED * speed_multiplier:
                self.cable_length = self.target_cable_length; self.is_hoisting = False
                if self.hoist_callback: cb = self.hoist_callback; self.hoist_callback = None; cb()
            else:
                self.cable_length += dc * LERP_FACTOR * speed_multiplier
            moved = True
        if moved:
            self.image = self._create_surface()
            self.rect = self.image.get_rect(midtop=(int(self.pos_x), int(self.pos_y)))

class RecursionSimulation:
    def __init__(self, screen):
        self.screen = screen; self.logic = RecursionManager()
        self.SIM_WIDTH = 750; self.FLOOR_Y = SCREEN_HEIGHT - 80
        self.DISK_HEIGHT = 40; self.GANTRY_Y = 80
        self.TRAVEL_Y = self.GANTRY_Y
        self.all_sprites = pygame.sprite.Group(); self.disks = pygame.sprite.Group()
        self.crane = MagneticCraneSprite(self.SIM_WIDTH / 2, self.TRAVEL_Y)
        self.all_sprites.add(self.crane)
        self.ui_x = 750; self.ui_w = 250
        self.chassis = HandheldChassis(self.ui_x + 10, 20, self.ui_w - 20, SCREEN_HEIGHT - 40)
        self.lcd = LCDDisplay(self.ui_x + 35, 80, self.ui_w - 70, 100)
        btn_cx = self.ui_x + self.ui_w // 2
        self.btn_load = RoundButton(btn_cx, 280, 45, BTN_BLUE_BASE, BTN_BLUE_LIGHT, "LOAD", self.action_load)
        self.btn_solve = RoundButton(btn_cx, 390, 45, BTN_GREEN_BASE, BTN_GREEN_LIGHT, "SOLVE", self.action_solve)
        self.btn_reset = RoundButton(btn_cx, 500, 45, BTN_RED_BASE, BTN_RED_LIGHT, "RESET", self.action_reset)
        self.speed_levels = [0.5, 1.0, 2.0, 4.0, 8.0]
        self.speed_index = 1
        self.speed_multiplier = self.speed_levels[self.speed_index]
        speed_btn_y = self.chassis.rect.bottom - 60
        speed_btn_w = 80
        speed_btn_h = 30
        self.btn_speed_down = Button(btn_cx - speed_btn_w - 5, speed_btn_y, speed_btn_w, speed_btn_h, "Speed -", self.decrease_speed)
        self.btn_speed_up = Button(btn_cx + 5, speed_btn_y, speed_btn_w, speed_btn_h, "Speed +", self.increase_speed)
        self.game_state = 'IDLE'; self.selected_disk = None; self.source_peg = None
        self.move_count = 0; self.auto_solve_queue = []; self.show_win_manifest = False
        self.disks_to_load = []
        self.visual_pegs = {'A': [], 'B': [], 'C': []}
        self.peg_coords = {'A': self.SIM_WIDTH * 0.2, 'B': self.SIM_WIDTH * 0.5, 'C': self.SIM_WIDTH * 0.8}
        self.peg_rects = {p: pygame.Rect(x - 130, self.TRAVEL_Y, 260, self.FLOOR_Y - self.TRAVEL_Y) for p, x in self.peg_coords.items()}
        self.background = self._generate_static_background()
        self.action_reset()

    def _generate_static_background(self):
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # 1. Wall with Gradient (Darker at top)
        for y in range(self.FLOOR_Y):
            ratio = y / self.FLOOR_Y
            c = (int(20 + 20*ratio), int(25 + 20*ratio), int(30 + 20*ratio))
            pygame.draw.line(bg, c, (0, y), (SCREEN_WIDTH, y))

        # 2. Shelves (Background details)
        for i in range(4, 0, -1):
            alpha = 30 + (i * 20)
            shelf_color = (80, 85, 90)
            box_color = (120, 90, 40)
            for y in range(150, self.FLOOR_Y, 70):
                pygame.draw.line(bg, shelf_color, (0, y), (SCREEN_WIDTH, y), 2)
                for x in range(20, SCREEN_WIDTH, 120):
                    if random.random() > 0.5:
                        bx = x + i*10 + random.randint(-10, 10)
                        by = y - 35
                        pygame.draw.rect(bg, box_color, (bx, by, 30, 35))
                        pygame.draw.rect(bg, (0,0,0), (bx, by, 30, 35), 1)

        # 3. Vertical Pillars (Structure)
        for i in range(int(SCREEN_WIDTH / 150) + 1):
            x = i * 150
            pygame.draw.rect(bg, (10, 12, 15), (x+30, 0, 10, self.FLOOR_Y)) 
            pygame.draw.rect(bg, (50, 55, 60), (x, 0, 30, self.FLOOR_Y))
            for py in range(20, self.FLOOR_Y, 40):
                pygame.draw.circle(bg, (30, 35, 40), (x+5, py), 2)
                pygame.draw.circle(bg, (30, 35, 40), (x+25, py), 2)

        # 4. Gantry Rail (Top)
        pygame.draw.rect(bg, (20, 22, 25), (0, 0, SCREEN_WIDTH, self.GANTRY_Y + 30))
        pygame.draw.rect(bg, (60, 65, 70), (0, self.GANTRY_Y, SCREEN_WIDTH, 20))
        pygame.draw.line(bg, (100, 105, 110), (0, self.GANTRY_Y), (SCREEN_WIDTH, self.GANTRY_Y), 2)
        pygame.draw.line(bg, (30, 35, 40), (0, self.GANTRY_Y+20), (SCREEN_WIDTH, self.GANTRY_Y+20), 2)

        # 5. Floor
        floor_rect = pygame.Rect(0, self.FLOOR_Y, SCREEN_WIDTH, SCREEN_HEIGHT - self.FLOOR_Y)
        bg.fill((30, 32, 35), floor_rect)
        for _ in range(10000):
            c = random.choice([(40, 42, 45), (25, 27, 30)])
            bg.set_at((random.randint(0, SCREEN_WIDTH - 1), random.randint(self.FLOOR_Y, SCREEN_HEIGHT - 1)), c)
        pygame.draw.line(bg, (10, 10, 10), (0, self.FLOOR_Y), (SCREEN_WIDTH, self.FLOOR_Y), 2)

        # 6. Platforms (The "Pegs")
        for peg, x_pos in self.peg_coords.items():
            plat_w = 240
            plat_top_h = 15
            plat_base_h = 25
            
            base_x = x_pos - plat_w // 2
            
            # Drop Shadow
            shadow_surf = pygame.Surface((plat_w + 40, 20), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, 150), (0, 0, plat_w + 40, 20))
            bg.blit(shadow_surf, (base_x - 20, self.FLOOR_Y + plat_base_h - 10))

            # Front Face
            front_rect = pygame.Rect(base_x, self.FLOOR_Y, plat_w, plat_base_h)
            pygame.draw.rect(bg, (50, 55, 60), front_rect)
            pygame.draw.rect(bg, (30, 35, 40), front_rect, 2)
            
            # Hazard Stripes
            clip_surf = pygame.Surface((plat_w, plat_base_h), pygame.SRCALPHA)
            clip_surf.fill((0,0,0,0))
            for i in range(-20, plat_w, 30):
                pygame.draw.polygon(clip_surf, (255, 200, 0, 180), [
                    (i, 0), (i+10, 0), (i-5, plat_base_h), (i-15, plat_base_h)
                ])
            bg.blit(clip_surf, front_rect.topleft)

            # Top Surface
            top_rect = pygame.Rect(base_x + 5, self.FLOOR_Y - plat_top_h, plat_w - 10, plat_top_h)
            pygame.draw.rect(bg, (90, 95, 100), top_rect)
            pygame.draw.rect(bg, (120, 125, 130), top_rect, 1)
            
            # Peg Label
            label_bg_radius = 15
            pygame.draw.circle(bg, (20, 20, 20), (int(x_pos), int(self.FLOOR_Y + plat_base_h/2)), label_bg_radius)
            pygame.draw.circle(bg, (200, 200, 200), (int(x_pos), int(self.FLOOR_Y + plat_base_h/2)), label_bg_radius, 1)
            
            font = pygame.font.SysFont("Arial", 16, bold=True)
            text_surf = font.render(peg, True, (255, 255, 255))
            bg.blit(text_surf, (x_pos - text_surf.get_width()/2, self.FLOOR_Y + plat_base_h/2 - text_surf.get_height()/2))

        # 7. Lighting Effects
        light_layer = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        light_layer.fill((0, 0, 0, 80)) 

        for x_pos in self.peg_coords.values():
            lx, ly = x_pos, 40 
            cone_color = (220, 230, 255)
            
            points = [
                (lx - 10, ly), (lx + 10, ly),
                (x_pos + 100, self.FLOOR_Y), (x_pos - 100, self.FLOOR_Y)
            ]
            pygame.draw.polygon(light_layer, (*cone_color, 15), points)
            
            points_inner = [
                (lx - 5, ly), (lx + 5, ly),
                (x_pos + 60, self.FLOOR_Y), (x_pos - 60, self.FLOOR_Y)
            ]
            pygame.draw.polygon(light_layer, (*cone_color, 25), points_inner)

            spot_w, spot_h = 200, 40
            spot_rect = pygame.Rect(x_pos - spot_w//2, self.FLOOR_Y - spot_h//2, spot_w, spot_h)
            pygame.draw.ellipse(light_layer, (*cone_color, 40), spot_rect)
            
            pygame.draw.rect(bg, (20, 20, 20), (lx - 15, ly - 5, 30, 10))
            pygame.draw.ellipse(bg, (200, 255, 255), (lx - 10, ly, 20, 6))

        bg.blit(light_layer, (0,0))
        return bg

    def increase_speed(self):
        if self.speed_index < len(self.speed_levels) - 1:
            self.speed_index += 1
            self.speed_multiplier = self.speed_levels[self.speed_index]
            self.lcd.update_status(f"SPEED: {self.speed_multiplier}x")

    def decrease_speed(self):
        if self.speed_index > 0:
            self.speed_index -= 1
            self.speed_multiplier = self.speed_levels[self.speed_index]
            self.lcd.update_status(f"SPEED: {self.speed_multiplier}x")

    def action_load(self):
        if self.game_state == 'ANIMATING': return
        try:
            num_disks = int(self.lcd.text)
            if not 3 <= num_disks <= 7: self.lcd.update_status("ERR: USE 3-7 DISKS"); return
        except ValueError: self.lcd.update_status("ERR: INVALID NUMBER"); return
        self.action_reset()
        self.logic.num_disks = num_disks
        colors = [CONTAINER_RED, CONTAINER_BLUE, (180, 120, 40), (80, 80, 80), (50, 100, 60), (100, 50, 120), (120, 120, 50)]
        for i in range(num_disks):
            disk_val = num_disks - i
            config = {
                'value': disk_val, 'max_value': num_disks, 'height': self.DISK_HEIGHT,
                'color': colors[i % len(colors)],
                'target_x': self.peg_coords['A'],
                'target_y': self.FLOOR_Y - (i * self.DISK_HEIGHT)
            }
            self.disks_to_load.append(config)
        self.game_state = 'ANIMATING'
        self.lcd.update_status("LOADING CONTAINERS...")
        self.animate_next_disk_drop()

    def animate_next_disk_drop(self):
        if not self.disks_to_load:
            self.game_state = 'IDLE'
            self.update_lcd_status()
            return
        config = self.disks_to_load.pop(0)
        disk = DiskSprite(config['value'], config['max_value'], config['height'], config['color'])
        disk.pos_x = config['target_x']
        disk.pos_y = -50
        self.all_sprites.add(disk); self.disks.add(disk)
        def on_drop_complete():
            self.visual_pegs['A'].append(disk)
            self.animate_next_disk_drop()
        disk.drop_to((config['target_x'], config['target_y']), on_drop_complete)

    def action_solve(self):
        if self.game_state != 'IDLE' or self.logic.num_disks == 0: return
        self.game_state = 'ANIMATING'; self.lcd.update_status("CALCULATING...")
        current_peg_state = {p: [d.value for d in disks] for p, disks in self.visual_pegs.items()}
        self.auto_solve_queue = self.logic.generate_moves_from_current_state(self.logic.num_disks, current_peg_state, 'C')
        if self.auto_solve_queue: self.lcd.update_status("AUTO-SOLVING..."); self.process_next_auto_move()
        else: self.game_state = 'IDLE'; self.check_win_condition()

    def action_reset(self):
        self.game_state = 'IDLE'; self.selected_disk = None; self.source_peg = None
        self.move_count = 0; self.logic.num_disks = 0; self.auto_solve_queue.clear()
        self.disks_to_load.clear()
        self.show_win_manifest = False
        for disk in self.disks: disk.kill()
        self.visual_pegs = {'A': [], 'B': [], 'C': []}
        self.crane.move_to((self.SIM_WIDTH / 2, self.TRAVEL_Y)); self.crane.set_magnet(False)
        self.crane.set_hoist_length(self.crane.min_cable_length)
        self.lcd.update_status("LOAD DISKS [3-7]")

    def update_lcd_status(self):
        if self.game_state == 'IDLE': self.lcd.update_status(f"MOVES: {self.move_count} | SELECT DISK")
        elif self.game_state == 'DISK_SELECTED': self.lcd.update_status(f"MOVES: {self.move_count} | SELECT PEG")
        elif self.game_state == 'WIN': self.lcd.update_status(f"SOLVED IN {self.move_count} MOVES!")

    def handle_mouse_click(self, pos):
        if self.game_state == 'IDLE':
            for peg_name, peg_disks in self.visual_pegs.items():
                if peg_disks and peg_disks[-1].rect.collidepoint(pos):
                    self.source_peg = peg_name; self.selected_disk = peg_disks[-1]
                    self.game_state = 'ANIMATING'; self.animate_pickup()
                    return
        elif self.game_state == 'DISK_SELECTED':
            for peg_name, rect in self.peg_rects.items():
                if rect.collidepoint(pos): self.handle_place_attempt(peg_name)

    def handle_place_attempt(self, dest_peg):
        is_valid = not self.visual_pegs[dest_peg] or self.selected_disk.value < self.visual_pegs[dest_peg][-1].value
        self.game_state = 'ANIMATING'
        if is_valid: self.animate_place(dest_peg)
        else: self.lcd.update_status("INVALID MOVE! RETURNING..."); self.animate_return()

    def check_win_condition(self):
        if self.logic.num_disks > 0 and (len(self.visual_pegs['C']) == self.logic.num_disks or len(self.visual_pegs['B']) == self.logic.num_disks):
            self.game_state = 'WIN'; self.show_win_manifest = True; return True
        return False

    def animate_pickup(self):
        pickup_x = self.peg_coords[self.source_peg]
        disk_center_y = self.selected_disk.rect.centery
        disk_top_y = disk_center_y - self.DISK_HEIGHT / 2
        target_cable_len = disk_top_y - self.TRAVEL_Y - self.crane.trolley_height - self.crane.magnet_height
        def on_rise(): self.game_state = 'DISK_SELECTED'; self.update_lcd_status()
        def on_attach(): self.selected_disk.attached_to = self.crane; self.crane.set_magnet(True); self.crane.set_hoist_length(self.crane.min_cable_length, callback=on_rise)
        def on_lower(): self.crane.set_hoist_length(target_cable_len, callback=on_attach)
        self.crane.move_to((pickup_x, self.TRAVEL_Y), callback=on_lower)

    def animate_place(self, dest_peg):
        dest_x = self.peg_coords[dest_peg]
        dest_y_bottom = self.FLOOR_Y - (len(self.visual_pegs[dest_peg]) * self.DISK_HEIGHT)
        disk_top_y = dest_y_bottom - self.DISK_HEIGHT
        target_cable_len = disk_top_y - self.TRAVEL_Y - self.crane.trolley_height - self.crane.magnet_height
        def on_placed():
            self.visual_pegs[dest_peg].append(self.visual_pegs[self.source_peg].pop())
            self.selected_disk = None; self.source_peg = None; self.move_count += 1
            if not self.check_win_condition(): self.game_state = 'IDLE'
            self.update_lcd_status()
        def on_detach():
            self.selected_disk.pos_x = dest_x
            self.selected_disk.pos_y = dest_y_bottom
            self.selected_disk.attached_to = None
            self.crane.set_magnet(False)
            self.crane.set_hoist_length(self.crane.min_cable_length, callback=on_placed)
        def on_lower(): self.crane.set_hoist_length(target_cable_len, callback=on_detach)
        self.crane.move_to((dest_x, self.TRAVEL_Y), callback=on_lower)

    def animate_return(self):
        dest_x = self.peg_coords[self.source_peg]
        dest_y_bottom = self.FLOOR_Y - ((len(self.visual_pegs[self.source_peg]) - 1) * self.DISK_HEIGHT)
        disk_top_y = dest_y_bottom - self.DISK_HEIGHT
        target_cable_len = disk_top_y - self.TRAVEL_Y - self.crane.trolley_height - self.crane.magnet_height
        def on_returned():
            self.selected_disk = None; self.source_peg = None; self.game_state = 'IDLE'; self.update_lcd_status()
        def on_detach():
            self.selected_disk.pos_x = dest_x
            self.selected_disk.pos_y = dest_y_bottom
            self.selected_disk.attached_to = None
            self.crane.set_magnet(False)
            self.crane.set_hoist_length(self.crane.min_cable_length, callback=on_returned)
        def on_lower(): self.crane.set_hoist_length(target_cable_len, callback=on_detach)
        self.crane.move_to((dest_x, self.TRAVEL_Y), callback=on_lower)

    def process_next_auto_move(self):
        if not self.auto_solve_queue:
            self.game_state = 'IDLE'
            if not self.check_win_condition(): self.lcd.update_status("AUTO-SOLVE FINISHED!")
            else: self.update_lcd_status()
            self.crane.set_magnet(False)
            return
        move = self.auto_solve_queue.pop(0)
        from_peg, to_peg = move['from'], move['to']
        disk = self.visual_pegs[from_peg][-1]
        source_x = self.peg_coords[from_peg]; dest_x = self.peg_coords[to_peg]
        source_disk_top_y = self.FLOOR_Y - ((len(self.visual_pegs[from_peg]) - 1) * self.DISK_HEIGHT) - self.DISK_HEIGHT
        dest_disk_top_y = self.FLOOR_Y - (len(self.visual_pegs[to_peg]) * self.DISK_HEIGHT) - self.DISK_HEIGHT
        pickup_cable_len = source_disk_top_y - self.TRAVEL_Y - self.crane.trolley_height - self.crane.magnet_height
        place_cable_len = dest_disk_top_y - self.TRAVEL_Y - self.crane.trolley_height - self.crane.magnet_height
        def on_raised_final(): self.process_next_auto_move()
        def on_placed():
            disk.pos_x = dest_x; disk.pos_y = self.FLOOR_Y - (len(self.visual_pegs[to_peg]) * self.DISK_HEIGHT)
            self.visual_pegs[to_peg].append(self.visual_pegs[from_peg].pop()); self.move_count += 1; self.update_lcd_status()
            self.crane.set_hoist_length(self.crane.min_cable_length, callback=on_raised_final)
        def on_detach(): disk.attached_to = None; self.crane.set_magnet(False); on_placed()
        def on_lower_to_place(): self.crane.set_hoist_length(place_cable_len, callback=on_detach)
        def on_move_horizontally(): on_lower_to_place()
        def on_raised_with_disk(): self.crane.move_to((dest_x, self.TRAVEL_Y), callback=on_move_horizontally)
        def on_attach(): disk.attached_to = self.crane; self.crane.set_magnet(True); self.crane.set_hoist_length(self.crane.min_cable_length, callback=on_raised_with_disk)
        def on_lower_to_pickup(): self.crane.set_hoist_length(pickup_cable_len, callback=on_attach)
        self.crane.move_to((source_x, self.TRAVEL_Y), callback=on_lower_to_pickup)

    def handle_events(self, event):
        if self.game_state == 'ANIMATING':
            self.btn_reset.handle_event(event); return
        if self.show_win_manifest:
            if event.type == pygame.MOUSEBUTTONDOWN: self.action_reset()
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.handle_mouse_click(event.pos)
        self.lcd.handle_event(event)
        self.btn_load.handle_event(event)
        self.btn_solve.handle_event(event)
        self.btn_reset.handle_event(event)
        self.btn_speed_up.handle_event(event)
        self.btn_speed_down.handle_event(event)

    def update(self):
        if self.show_win_manifest: return
        self.all_sprites.update(self.speed_multiplier)
        self.lcd.update()

    def draw_hover_effects(self):
        if self.game_state != 'DISK_SELECTED' or not self.selected_disk: return

        mouse_pos = pygame.mouse.get_pos()
        for peg, rect in self.peg_rects.items():
            if rect.collidepoint(mouse_pos):
                # Determine validity
                is_valid = True
                if self.visual_pegs[peg]:
                    if self.selected_disk.value > self.visual_pegs[peg][-1].value:
                        is_valid = False
                
                # Hologram Color
                holo_color = (0, 255, 255) if is_valid else (255, 50, 50)
                
                # Calculate Position
                peg_x = self.peg_coords[peg]
                dest_y = self.FLOOR_Y - (len(self.visual_pegs[peg]) * self.DISK_HEIGHT)
                
                # Draw the hologram rect
                w, h = self.selected_disk.width, self.selected_disk.height
                ghost_rect = pygame.Rect(0, 0, w, h)
                ghost_rect.midbottom = (peg_x, dest_y)
                
                # Draw fill
                s = pygame.Surface((w, h), pygame.SRCALPHA)
                pygame.draw.rect(s, (*holo_color, 80), (0,0,w,h), border_radius=4)
                pygame.draw.rect(s, (*holo_color, 200), (0,0,w,h), 2, border_radius=4)
                
                # Scanline effect for hologram
                for i in range(0, h, 4):
                    pygame.draw.line(s, (*holo_color, 50), (0, i), (w, i), 1)
                
                self.screen.blit(s, ghost_rect)
                
                # Draw guide line from top
                pygame.draw.line(self.screen, (*holo_color, 100), (peg_x, self.TRAVEL_Y + 30), (peg_x, ghost_rect.top), 1)
                pygame.draw.circle(self.screen, holo_color, (peg_x, ghost_rect.top), 2)

    def draw_win_manifest(self):
        overlay = pygame.Surface((self.SIM_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        w, h = 450, 250; x, y = (self.SIM_WIDTH - w) // 2, (SCREEN_HEIGHT - h) // 2
        pygame.draw.rect(self.screen, (0,0,0,80), (x+5, y+5, w, h), border_radius=3)
        pygame.draw.rect(self.screen, (230, 230, 220), (x, y, w, h), border_radius=3)
        pygame.draw.rect(self.screen, (100,100,100), (x,y,w,h), 1, border_radius=3)
        font_header = pygame.font.SysFont("Impact", 30)
        header_surf = font_header.render("PUZZLE COMPLETE", True, (30,30,30))
        self.screen.blit(header_surf, (x + w//2 - header_surf.get_width()//2, y + 25))
        pygame.draw.line(self.screen, (180,180,170), (x+20, y+70), (x+w-20, y+70), 2)
        font_label = pygame.font.SysFont("Courier New", 18, bold=True)
        font_result = pygame.font.SysFont("Courier New", 20)
        moves_label = font_label.render("Total Moves:", True, (80,80,80))
        self.screen.blit(moves_label, (x + 40, y + 100))
        moves_surf = font_result.render(str(self.move_count), True, (40, 40, 40))
        self.screen.blit(moves_surf, (x + w - moves_surf.get_width() - 40, y + 100))
        optimal_moves = 2**self.logic.num_disks - 1
        optimal_label = font_label.render("Optimal Moves:", True, (80,80,80))
        self.screen.blit(optimal_label, (x + 40, y + 140))
        optimal_surf = font_result.render(str(optimal_moves), True, (40, 40, 40))
        self.screen.blit(optimal_surf, (x + w - optimal_surf.get_width() - 40, y + 140))
        font_prompt = pygame.font.SysFont("Arial", 12)
        prompt_surf = font_prompt.render("Click anywhere to reset", True, (150, 150, 150))
        self.screen.blit(prompt_surf, (x + w - prompt_surf.get_width() - 10, y + h - prompt_surf.get_height() - 10))

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.draw_hover_effects()
        self.disks.draw(self.screen)
        self.screen.blit(self.crane.image, self.crane.rect)
        self.chassis.draw(self.screen); self.lcd.draw(self.screen)
        self.btn_load.draw(self.screen); self.btn_solve.draw(self.screen); self.btn_reset.draw(self.screen)
        self.btn_speed_up.draw(self.screen); self.btn_speed_down.draw(self.screen)
        if self.show_win_manifest:
            self.draw_win_manifest()