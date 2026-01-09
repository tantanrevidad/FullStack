# Full_Stack_Sim/simulation/site_conveyor_list.py

import pygame
import random
from settings import *
from core.sprites import CrateSprite 
from core.ui import HandheldChassis, LCDDisplay, RoundButton

# --- SPRITE (Unchanged) ---
BOX_SIZES = { 'small': (40, 40), 'medium': (60, 50), 'large': (80, 60) }
class BoxSprite(CrateSprite):
    def __init__(self, x, y, data_label, size_type='medium'):
        self.size_type = size_type; self.width, self.height = BOX_SIZES[self.size_type]
        super().__init__(x, y, data_label)
        self.plate = str(data_label); self.is_dropping = False; self.is_bouncing = False
        self.drop_speed = 0; self.gravity = 0.4; self.bounce_speed = -5; self.target_y_for_drop = 0
        self.drop_callback = None; self.original_image = self.generate_box_surface()
        self.image = self.original_image.copy(); self.rect = self.image.get_rect(center=(x, y))
    def generate_box_surface(self):
        surf = pygame.Surface((self.width + 6, self.height + 6), pygame.SRCALPHA)
        pygame.draw.rect(surf, (0, 0, 0, 60), (5, 5, self.width, self.height), border_radius=4)
        box_rect = pygame.Rect(2, 2, self.width, self.height)
        pygame.draw.rect(surf, BOX_COLOR_1, box_rect, border_radius=4)
        pygame.draw.rect(surf, (0,0,0, 40), box_rect, 2)
        pygame.draw.line(surf, BOX_TAPE, (box_rect.centerx, box_rect.top), (box_rect.centerx, box_rect.bottom), 15)
        label_w, label_h = self.label_surf.get_size()
        label_x = (surf.get_width() - label_w) / 2; label_y = (surf.get_height() - label_h) / 2
        surf.blit(self.label_surf, (label_x, label_y)); return surf
    def drop_to(self, target_y, callback):
        self.is_dropping = True; self.target_y_for_drop = target_y; self.drop_callback = callback
    def update(self):
        if self.is_dropping:
            self.drop_speed += self.gravity; self.pos_y += self.drop_speed
            if self.pos_y >= self.target_y_for_drop: self.pos_y = self.target_y_for_drop; self.is_dropping = False; self.is_bouncing = True
            self.rect.centery = int(self.pos_y)
        elif self.is_bouncing:
            self.pos_y += self.bounce_speed; self.bounce_speed += self.gravity
            if self.pos_y >= self.target_y_for_drop:
                self.pos_y = self.target_y_for_drop; self.is_bouncing = False
                if self.drop_callback: cb = self.drop_callback; self.drop_callback = None; cb()
            self.rect.centery = int(self.pos_y)
        elif self.is_moving:
            dx = self.target_x - self.pos_x; dy = self.target_y - self.pos_y
            if (dx**2 + dy**2)**0.5 < MIN_SPEED:
                self.pos_x, self.pos_y = self.target_x, self.target_y; self.is_moving = False
                if self.on_finish_callback: cb = self.on_finish_callback; self.on_finish_callback = None; cb()
            else: self.pos_x += dx * LERP_FACTOR; self.pos_y += dy * LERP_FACTOR
            self.rect.center = (int(self.pos_x), int(self.pos_y))
        self.image = self.original_image

# --- LOGIC LAYER (Unchanged) ---
class Node:
    def __init__(self, label): self.label = label; self.next = None
class LinkedListManager:
    def __init__(self, capacity=10): self.head = None; self.size = 0; self.capacity = capacity
    def is_full(self): return self.size >= self.capacity
    def insert_at(self, index, label):
        if self.is_full(): return {"type": "ERROR", "message": "CONVEYOR FULL"}
        if index < 0 or index > self.size: return {"type": "ERROR", "message": "INVALID INDEX"}
        new_node = Node(label)
        if index == 0: new_node.next = self.head; self.head = new_node
        else:
            current = self.head
            for _ in range(index - 1): current = current.next
            new_node.next = current.next; current.next = new_node
        self.size += 1; return {"type": "INSERT", "label": label, "index": index}
    def remove_box(self, label):
        if not self.head: return [{"type": "ERROR", "message": "CONVEYOR EMPTY"}]
        if self.head.label == label:
            self.head = self.head.next; self.size -= 1
            return [{"type": "REMOVE", "label": label, "index": 0}]
        current = self.head; index = 0
        while current.next and current.next.label != label: current = current.next; index += 1
        if current.next:
            removed_node = current.next; current.next = removed_node.next; self.size -= 1
            return [{"type": "REMOVE", "label": removed_node.label, "index": index + 1}]
        return [{"type": "ERROR", "message": "NOT FOUND"}]
    def find_box(self, label):
        current = self.head
        while current:
            if current.label == label: return True
            current = current.next
        return False

# --- VISUALIZATION LAYER ---
class ConveyorSimulation:
    def __init__(self, screen):
        self.screen = screen; self.logic = LinkedListManager(capacity=10)
        self.all_sprites = pygame.sprite.Group(); self.crates_group = pygame.sprite.Group()
        self.placement_mode = False; self.label_to_place = ""; self.placement_markers = []
        self.ui_x = 750; self.ui_w = 250
        self.chassis = HandheldChassis(self.ui_x + 10, 20, self.ui_w - 20, SCREEN_HEIGHT - 40)
        self.lcd = LCDDisplay(self.ui_x + 35, 80, self.ui_w - 70, 100)
        self.lcd.update_status("CONVEYOR OPS")
        btn_cx = self.ui_x + self.ui_w // 2
        self.btn_append = RoundButton(btn_cx, 260, 40, BTN_GREEN_BASE, BTN_GREEN_LIGHT, "APPEND", self.action_append)
        self.btn_insert = RoundButton(btn_cx, 350, 40, BTN_BLUE_BASE, BTN_BLUE_LIGHT, "INSERT AT", self.action_insert_at)
        self.btn_remove = RoundButton(btn_cx, 440, 40, BTN_RED_BASE, BTN_RED_LIGHT, "REMOVE", self.action_remove)
        self.visual_list = []; self.is_animating = False; self.animation_lock_count = 0
        self.BELT_Y = SCREEN_HEIGHT - 100; self.SIMULATION_WIDTH = 750
        self.HOPPER_X = self.SIMULATION_WIDTH / 2; self.HOPPER_Y = -100
        self.DESPAWN_POINT = (-100, self.BELT_Y); self.belt_pattern_offset = 0
        self.background = self._generate_static_background()

    def _draw_shelf_unit(self, surf, x, y, w, h, rows):
        shadow_offset = 8
        pygame.draw.rect(surf, STATIC_SHADOW_COLOR, (x + shadow_offset, y + shadow_offset, w, h))
        for r in range(rows + 1):
            ry = y + (r * (h / rows))
            pygame.draw.line(surf, (80,80,85), (x, ry), (x + w, ry), 2)
            pygame.draw.line(surf, (120,120,125), (x, ry-1), (x + w, ry-1), 1)
        pygame.draw.line(surf, (80,80,85), (x, y), (x, y + h), 2)
        pygame.draw.line(surf, (80,80,85), (x+w, y), (x+w, y + h), 2)
        for _ in range(rows * 3):
            bx = x + random.randint(5, w - 25)
            by = y + (random.randrange(rows) * (h/rows)) + 5
            bw = random.randint(10, 20); bh = random.randint(5, 10)
            pygame.draw.rect(surf, BOX_COLOR_2, (bx, by, bw, bh))

    def _generate_static_background(self):
        # --- DEFINITIVE FIX: Use a separate layer for transparent effects ---
        # 1. Create the opaque base layer
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg.fill(FLOOR_COLOR)
        for _ in range(15000):
            color = random.choice([CONCRETE_NOISE_1, CONCRETE_NOISE_2])
            bg.set_at((random.randint(0, SCREEN_WIDTH-1), random.randint(100, SCREEN_HEIGHT-1)), color)
        for _ in range(20):
            points = []
            px, py = random.randint(0, self.SIMULATION_WIDTH-1), random.randint(200, SCREEN_HEIGHT-1)
            for _ in range(random.randint(3, 6)):
                points.append((px, py))
                px += random.randint(-20, 20); py += random.randint(-20, 20)
            if len(points) > 1: pygame.draw.lines(bg, (100,103,107), False, points, 1)
        wall_rect = pygame.Rect(0, 0, SCREEN_WIDTH, self.BELT_Y - 80)
        bg.fill(WALL_BASE_COLOR, wall_rect)
        for y in range(0, wall_rect.height, 15):
            pygame.draw.line(bg, WALL_LINE_COLOR, (0, y), (SCREEN_WIDTH, y), 1)
        pygame.draw.line(bg, (0,0,0, 100), (0, wall_rect.bottom), (SCREEN_WIDTH, wall_rect.bottom), 2)
        self._draw_shelf_unit(bg, 50, 250, 200, 250, 5)
        self._draw_shelf_unit(bg, 500, 250, 200, 250, 5)
        pygame.draw.rect(bg, (40, 45, 50), (0, 0, SCREEN_WIDTH, 80))
        
        # 2. Create a separate transparent layer for lights
        light_layer = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        light_positions = []
        for i in range(0, SCREEN_WIDTH, 100):
            light_positions.append((i + 40, 38))
            pygame.draw.rect(bg, (30,35,40), (i, 30, 80, 15))
            pygame.draw.rect(bg, (220,220,200), (i+5, 32, 70, 11))
        for lx, ly in light_positions:
            points = [(lx - 20, ly), (lx + 20, ly), (lx + 80, SCREEN_HEIGHT), (lx - 80, SCREEN_HEIGHT)]
            pygame.draw.polygon(light_layer, LIGHT_RAY_COLOR, points)
        
        # 3. Composite the layers together
        bg.blit(light_layer, (0, 0))
        return bg

    def _calculate_layout_parameters(self):
        if not self.visual_list: return {'start_x': self.SIMULATION_WIDTH / 2, 'gap': 0}
        total_box_width = sum(sprite.width for sprite in self.visual_list)
        total_gap_space = self.SIMULATION_WIDTH - total_box_width
        gap_size = total_gap_space / (len(self.visual_list) + 1)
        start_x = gap_size
        return {'start_x': start_x, 'gap': gap_size}

    def _calculate_target_positions(self):
        layout = self._calculate_layout_parameters()
        positions = []; current_x = layout['start_x']
        for sprite in self.visual_list:
            target_x = current_x + sprite.width / 2
            positions.append(target_x)
            current_x += sprite.width + layout['gap']
        return positions

    def draw_environment(self):
        self.screen.blit(self.background, (0, 0))
        belt_height = 40; belt_rect = pygame.Rect(0, self.BELT_Y - belt_height//2, self.SIMULATION_WIDTH, belt_height)
        pygame.draw.rect(self.screen, (20,20,20), belt_rect)
        self.belt_pattern_offset = (self.belt_pattern_offset + 3) % 20
        for x in range(self.belt_pattern_offset, self.SIMULATION_WIDTH, 20):
            pygame.draw.circle(self.screen, (30,30,35), (x, self.BELT_Y), 15)
            pygame.draw.circle(self.screen, (60,60,65), (x, self.BELT_Y), 12)
        hopper_shadow_poly = [(self.HOPPER_X - 80, self.BELT_Y - 120), (self.HOPPER_X + 80, self.BELT_Y - 120), (self.HOPPER_X, self.BELT_Y - 60)]
        pygame.draw.polygon(self.screen, STATIC_SHADOW_COLOR, [(p[0]+8, p[1]+8) for p in hopper_shadow_poly])
        pygame.draw.polygon(self.screen, (120,125,130), [(self.HOPPER_X - 40, 0), (self.HOPPER_X + 40, 0), (self.HOPPER_X + 80, self.BELT_Y - 120), (self.HOPPER_X - 80, self.BELT_Y - 120)])
        pygame.draw.polygon(self.screen, (100,105,110), hopper_shadow_poly)

    def draw_placement_markers(self):
        if not self.placement_mode: return
        self.placement_markers.clear(); mouse_pos = pygame.mouse.get_pos()
        layout = self._calculate_layout_parameters()
        x_coords = [layout['start_x'] / 2]
        current_x = layout['start_x']
        for sprite in self.visual_list:
            current_x += sprite.width; x_coords.append(current_x + layout['gap'] / 2); current_x += layout['gap']
        for i, pos_x in enumerate(x_coords):
            marker_rect = pygame.Rect(pos_x - 20, self.BELT_Y - 35, 40, 70)
            self.placement_markers.append((marker_rect, i))
            color = STRIPE_YELLOW
            if marker_rect.collidepoint(mouse_pos): color = BTN_GREEN_LIGHT
            pygame.draw.rect(self.screen, color, marker_rect, 3, border_radius=6)

    def on_animation_complete(self):
        self.animation_lock_count -= 1
        if self.animation_lock_count <= 0: self.is_animating = False; self.lcd.update_status("READY")

    def animate_to_positions(self):
        self.is_animating = True
        target_positions = self._calculate_target_positions()
        if not self.visual_list: self.is_animating = False; self.lcd.update_status("READY"); return
        self.animation_lock_count = len(self.visual_list)
        for i, sprite in enumerate(self.visual_list): sprite.move_to((target_positions[i], self.BELT_Y), self.on_animation_complete)

    def execute_insertion(self, label, index):
        receipt = self.logic.insert_at(index, label)
        if receipt['type'] == 'ERROR': self.lcd.update_status(f"ERR: {receipt['message']}"); return
        self.lcd.update_status(f"INSERT {label}@{index}"); self.lcd.text = ""
        self.is_animating = True
        size_type = random.choice(list(BOX_SIZES.keys()))
        new_box = BoxSprite(self.HOPPER_X, self.HOPPER_Y, label, size_type)
        self.all_sprites.add(new_box); self.crates_group.add(new_box)
        self.visual_list.insert(index, new_box)
        def stage2_slide_into_place(): self.animate_to_positions()
        new_box.drop_to(self.BELT_Y, callback=stage2_slide_into_place)

    def action_append(self):
        if self.is_animating or self.placement_mode: return
        label = self.lcd.text.upper()
        if not label: self.lcd.update_status("ERR: NO INPUT"); return
        if self.logic.find_box(label): self.lcd.update_status("ERR: DUPLICATE"); return
        self.execute_insertion(label, len(self.visual_list))

    def action_insert_at(self):
        if self.is_animating: return
        if self.placement_mode: self.placement_mode = False; self.lcd.update_status("CANCELED"); return
        label = self.lcd.text.upper()
        if not label: self.lcd.update_status("ERR: NO LABEL"); return
        if self.logic.find_box(label): self.lcd.update_status("ERR: DUPLICATE"); return
        if self.logic.is_full(): self.lcd.update_status("ERR: CONVEYOR FULL"); return
        self.placement_mode = True; self.label_to_place = label; self.lcd.update_status("CLICK A SLOT...")

    def action_remove(self):
        if self.is_animating or self.placement_mode: return
        label = self.lcd.text.upper()
        if not label: self.lcd.update_status("ERR: NO INPUT"); return
        receipt = self.logic.remove_box(label)[0]
        if receipt['type'] == 'ERROR': self.lcd.update_status(f"ERR: {receipt['message']}"); return
        self.lcd.update_status(f"OUT: {label}"); self.lcd.text = ""
        sprite_to_remove = next((s for s in self.visual_list if s.plate == label), None)
        if sprite_to_remove:
            self.is_animating = True; self.visual_list.remove(sprite_to_remove)
            self.animation_lock_count = 1
            sprite_to_remove.move_to(self.DESPAWN_POINT, callback=lambda: [sprite_to_remove.kill(), self.on_animation_complete()])
            self.animate_to_positions()

    def handle_mouse_click_for_insertion(self, event):
        if self.placement_mode and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for marker_rect, index in self.placement_markers:
                if marker_rect.collidepoint(event.pos):
                    self.placement_mode = False; self.execute_insertion(self.label_to_place, index); return True
            self.placement_mode = False; self.lcd.update_status("CANCELED"); return True
        return False

    def handle_events(self, event):
        if self.handle_mouse_click_for_insertion(event): return
        if self.placement_mode: return
        self.lcd.handle_event(event); self.btn_append.handle_event(event)
        self.btn_insert.handle_event(event); self.btn_remove.handle_event(event)

    def update(self):
        self.all_sprites.update(); self.lcd.update()

    def draw(self):
        self.draw_environment(); self.all_sprites.draw(self.screen)
        self.draw_placement_markers(); self.chassis.draw(self.screen)
        self.lcd.draw(self.screen); self.btn_append.draw(self.screen)
        self.btn_insert.draw(self.screen); self.btn_remove.draw(self.screen)