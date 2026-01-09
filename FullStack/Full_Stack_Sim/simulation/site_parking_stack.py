import pygame
import random
from settings import *
from core.sprites import CrateSprite
from core.ui import HandheldChassis, LCDDisplay, RoundButton

class Vehicle:
    def __init__(self, plate, arrival_count, departure_count):
        self.plate = plate; self.arrival_count = arrival_count; self.departure_count = departure_count

class StackManager:
    def __init__(self, capacity=10):
        self.items = []; self.capacity = capacity; self.history = {}
    def _get_stats(self, plate):
        if plate not in self.history: self.history[plate] = {'arrivals': 0, 'departures': 0}
        return self.history[plate]
    def push(self, plate):
        if len(self.items) >= self.capacity: return {"type": "OVERFLOW", "message": "BAY FULL"}
        if any(v.plate == plate for v in self.items): return {"type": "DUPLICATE", "message": "ALREADY HERE"}
        stats = self._get_stats(plate); stats['arrivals'] += 1
        new_vehicle = Vehicle(plate, stats['arrivals'], stats['departures'])
        self.items.append(new_vehicle)
        return {"type": "PUSH", "index": len(self.items) - 1, "data": new_vehicle}
    def remove_vehicle(self, plate):
        target_index = -1
        for i, v in enumerate(self.items):
            if v.plate == plate: target_index = i; break
        if target_index == -1: return [{"type": "ERROR", "message": "NOT FOUND"}]
        events = []; current_top_index = len(self.items) - 1; temp_holding = []
        while len(self.items) > target_index + 1:
            v = self.items.pop(); temp_holding.append(v)
            stats = self._get_stats(v.plate); stats['departures'] += 1
            events.append({"type": "TEMP_POP", "data": v, "index": current_top_index})
            current_top_index -= 1
        target_vehicle = self.items.pop()
        stats = self._get_stats(target_vehicle.plate); stats['departures'] += 1
        events.append({"type": "FINAL_POP", "data": target_vehicle, "index": target_index, "stats": stats})
        for v in reversed(temp_holding):
            self.items.append(v)
            stats = self._get_stats(v.plate); stats['arrivals'] += 1
            events.append({"type": "RESTACK_PUSH", "data": v, "index": len(self.items) - 1})
        return events
    def get_inventory_report(self):
        report = []
        for v in self.items:
            stats = self.history[v.plate]
            report.append({"plate": v.plate, "arrivals": stats['arrivals'], "departures": stats['departures']})
        return report

class ParkingStackSimulation:
    def __init__(self, screen):
        self.screen = screen; self.logic = StackManager(capacity=10)
        self.all_sprites = pygame.sprite.Group(); self.crates_group = pygame.sprite.Group()
        self.ui_x = 750; self.ui_y = 0; self.ui_w = 250; self.ui_h = SCREEN_HEIGHT
        self.chassis = HandheldChassis(self.ui_x + 10, 20, self.ui_w - 20, SCREEN_HEIGHT - 40)
        self.lcd = LCDDisplay(self.ui_x + 35, 80, self.ui_w - 70, 100)
        self.lcd.update_status("MAINTENANCE BAY")
        
        btn_cx = self.ui_x + self.ui_w // 2
        self.btn_arrive = RoundButton(btn_cx, 280, 45, BTN_GREEN_BASE, BTN_GREEN_LIGHT, "ARRIVE", self.action_arrive)
        self.btn_depart = RoundButton(btn_cx, 390, 45, BTN_RED_BASE, BTN_RED_LIGHT, "DEPART", self.action_depart)
        self.btn_summary = RoundButton(btn_cx, 500, 35, BTN_BLUE_BASE, BTN_BLUE_LIGHT, "MANIFEST", self.action_summary)
        self.btn_skip = RoundButton(btn_cx, 580, 30, (100, 100, 100), (150, 150, 150), "SKIP ANIM", self.action_skip)
        
        self.visual_stack = []; self.holding_stack_height = 0
        self.last_receipt = None; self.event_queue = []
        self.is_animating = False; self.show_summary = False

    def draw_pallet(self, x, y, boxes=2):
        pygame.draw.rect(self.screen, (100, 80, 50), (x, y, 30, 20))
        pygame.draw.line(self.screen, (60, 40, 20), (x, y+10), (x+30, y+10), 2)
        for i in range(boxes):
            bx = x + 2 + (i*10); by = y - 10
            pygame.draw.rect(self.screen, BOX_COLOR_1, (bx, by, 12, 12))
            pygame.draw.rect(self.screen, (80, 60, 40), (bx, by, 12, 12), 1)

    def draw_vent(self, x, y):
        pygame.draw.rect(self.screen, (40, 40, 45), (x, y, 20, 20))
        for i in range(0, 20, 4):
            pygame.draw.line(self.screen, (30, 30, 35), (x, y+i), (x+20, y+i), 1)

    def draw_environment(self):
        self.screen.fill(ASPHALT_STACK_BASE)
        for _ in range(5000):
            color = ASPHALT_STACK_NOISE
            self.screen.set_at((random.randint(0, 749), random.randint(0, SCREEN_HEIGHT-1)), color)
        wall_h = 80
        for x in range(0, 750, 10):
            color = WALL_CORRUGATED_DARK if (x // 10) % 2 == 0 else WALL_CORRUGATED_LIGHT
            pygame.draw.rect(self.screen, color, (x, 0, 10, wall_h))
        pygame.draw.rect(self.screen, (20,22,25), (0, wall_h, 750, 10))
        office_rect = pygame.Rect(325, 20, 150, 60)
        pygame.draw.rect(self.screen, (30,35,40), office_rect, border_radius=5)
        glow_surf = pygame.Surface((130, 40), pygame.SRCALPHA)
        glow_surf.fill(CONTROL_ROOM_GLOW)
        self.screen.blit(glow_surf, (335, 30))
        pygame.draw.rect(self.screen, (100, 110, 120), office_rect, 2, border_radius=5)
        font = pygame.font.SysFont("Arial", 8); self.screen.blit(font.render("CONTROL", True, (150, 160, 170)), (375, 22))
        for x in [50, 150, 550, 650]:
            pygame.draw.rect(self.screen, (20, 22, 25), (x, 30, 60, 30))
            pygame.draw.rect(self.screen, (10, 12, 15), (x+5, 35, 50, 20))
        pygame.draw.line(self.screen, STRIPE_YELLOW, (250, 100), (250, SCREEN_HEIGHT), 2)
        pygame.draw.line(self.screen, STRIPE_YELLOW, (500, 100), (500, SCREEN_HEIGHT), 2)
        slot_height = CRATE_WIDTH + PARKING_GAP
        for i in range(10):
            y = STACK_ZONE_BASE_Y - (i * slot_height)
            slot_rect = pygame.Rect(STACK_ZONE_X - 10, y - CRATE_WIDTH//2, CRATE_HEIGHT + 20, CRATE_WIDTH + 10)
            c_len = 15; col = PARKING_LINE_COLOR
            pygame.draw.line(self.screen, col, slot_rect.topleft, (slot_rect.left + c_len, slot_rect.top), 2)
            pygame.draw.line(self.screen, col, slot_rect.topleft, (slot_rect.left, slot_rect.top + c_len), 2)
            pygame.draw.line(self.screen, col, (slot_rect.left, slot_rect.bottom - c_len), (slot_rect.left, slot_rect.bottom), 2)
            pygame.draw.line(self.screen, col, (slot_rect.left - c_len//2, slot_rect.bottom), (slot_rect.left + c_len//2, slot_rect.bottom), 2)
            pygame.draw.line(self.screen, col, slot_rect.topright, (slot_rect.right - c_len, slot_rect.top), 2)
            pygame.draw.line(self.screen, col, slot_rect.topright, (slot_rect.right, slot_rect.top + c_len), 2)
            pygame.draw.line(self.screen, col, (slot_rect.right, slot_rect.bottom - c_len), (slot_rect.right, slot_rect.bottom), 2)
            pygame.draw.line(self.screen, col, (slot_rect.right - c_len//2, slot_rect.bottom), (slot_rect.right + c_len//2, slot_rect.bottom), 2)
            num_font = pygame.font.SysFont("Arial", 10, bold=True)
            self.screen.blit(num_font.render(str(i+1), True, (150, 150, 160)), (slot_rect.right + 15, slot_rect.centery - 5))
        for i in range(10):
            y = HOLDING_ZONE_Y - (i * slot_height)
            slot_rect = pygame.Rect(HOLDING_ZONE_X - 10, y - CRATE_WIDTH//2, CRATE_HEIGHT + 20, CRATE_WIDTH + 10)
            pygame.draw.rect(self.screen, STRIPE_YELLOW, slot_rect, 1)
        font = pygame.font.SysFont("Impact", 18)
        text_surf = font.render("MAINTENANCE BAY", True, STENCIL_TEXT_COLOR)
        text_surf = pygame.transform.rotate(text_surf, 90)
        self.screen.blit(text_surf, (STACK_ZONE_X - 40, 350))
        text_surf = font.render("TEMP PARKING", True, STENCIL_TEXT_COLOR)
        text_surf = pygame.transform.rotate(text_surf, 90)
        self.screen.blit(text_surf, (HOLDING_ZONE_X + 130, 380))
        self.draw_pallet(20, 120, boxes=1); self.draw_pallet(60, 120, boxes=2)
        self.draw_pallet(20, 160, boxes=2); self.draw_vent(100, 130)
        self.draw_pallet(680, 120, boxes=2); self.draw_pallet(680, 160, boxes=1)
        self.draw_vent(640, 130)

    def _force_park_orientation(self, sprite):
        sprite.angle = 0
        sprite.image = pygame.transform.rotate(sprite.original_image, 0)
        self.process_next_event()

    def action_arrive(self):
        if self.is_animating or self.show_summary: return
        plate = self.lcd.text.upper()
        if not plate: self.lcd.update_status("ERR: NO INPUT"); return
        receipt = self.logic.push(plate)
        if receipt['type'] in ['OVERFLOW', 'DUPLICATE']: self.lcd.update_status(f"ERR: {receipt['message']}"); return
        self.lcd.update_status(f"IN: {plate}"); self.lcd.text = ""
        new_crate = CrateSprite(SPAWN_X, SPAWN_Y, receipt['data'].plate)
        self.all_sprites.add(new_crate); self.crates_group.add(new_crate)
        self.visual_stack.append(new_crate)
        slot_height = CRATE_WIDTH + PARKING_GAP
        stack_target_y = STACK_ZONE_BASE_Y - (receipt['index'] * slot_height)
        stack_target = (STACK_ZONE_X + CRATE_HEIGHT/2, stack_target_y)
        def drive_to_stack(): new_crate.move_to(stack_target, callback=lambda: self._force_park_orientation(new_crate))
        self.is_animating = True
        new_crate.move_to((RECEIVING_BAY_X, RECEIVING_BAY_Y), callback=drive_to_stack)

    def action_depart(self):
        if self.is_animating or self.show_summary: return
        plate = self.lcd.text.upper()
        if not plate: return
        events = self.logic.remove_vehicle(plate)
        if events[0]['type'] == 'ERROR': self.lcd.update_status(f"ERR: {events[0]['message']}"); return
        self.lcd.update_status(f"OUT: {plate}"); self.lcd.text = ""
        self.event_queue = events; self.is_animating = True
        self.process_next_event()

    def action_skip(self):
        if not self.is_animating: return
        
        # 1. Stop all movement and clear events
        self.event_queue = []
        
        # 2. HARD RESET: Clear all existing sprites to prevent duplication/clumping
        for s in self.crates_group:
            s.kill()
        self.visual_stack = []
        
        # 3. Regenerate sprites from Logic State (Source of Truth)
        slot_height = CRATE_WIDTH + PARKING_GAP
        
        for i, vehicle in enumerate(self.logic.items):
            # Create fresh sprite
            new_sprite = CrateSprite(0, 0, vehicle.plate)
            
            # Calculate exact position
            target_y = STACK_ZONE_BASE_Y - (i * slot_height)
            new_sprite.pos_x = STACK_ZONE_X + CRATE_HEIGHT/2
            new_sprite.pos_y = target_y
            
            # Force orientation and position
            new_sprite.rect.center = (int(new_sprite.pos_x), int(new_sprite.pos_y))
            new_sprite.angle = 0
            new_sprite.image = pygame.transform.rotate(new_sprite.original_image, 0)
            new_sprite.is_moving = False
            
            # Add to groups
            self.all_sprites.add(new_sprite)
            self.crates_group.add(new_sprite)
            self.visual_stack.append(new_sprite)
            
        # 4. Reset State
        self.holding_stack_height = 0
        self.is_animating = False
        self.lcd.update_status("READY")

    def process_next_event(self):
        if not self.event_queue: self.on_animation_complete(); return
        event = self.event_queue.pop(0)
        slot_height = CRATE_WIDTH + PARKING_GAP
        if event['type'] == 'TEMP_POP':
            if self.visual_stack:
                crate = self.visual_stack.pop()
                target_y = HOLDING_ZONE_Y - (self.holding_stack_height * slot_height)
                self.holding_stack_height += 1
                crate.move_to((HOLDING_ZONE_X + CRATE_HEIGHT/2, target_y), callback=lambda: self._force_park_orientation(crate))
            else: self.process_next_event()
        elif event['type'] == 'FINAL_POP':
            if self.visual_stack:
                crate = self.visual_stack.pop()
                self.last_receipt = event['stats']; self.last_receipt['plate'] = event['data'].plate
                def cleanup(): crate.kill(); self.process_next_event()
                crate.move_to((SHIPPING_BAY_X, SHIPPING_BAY_Y), callback=cleanup)
            else: self.process_next_event()
        elif event['type'] == 'RESTACK_PUSH':
            sprite_to_move = next((s for s in self.crates_group if hasattr(s, 'plate') and s.plate == event['data'].plate), None)
            if sprite_to_move:
                self.holding_stack_height -= 1
                target_y = STACK_ZONE_BASE_Y - (event['index'] * slot_height)
                self.visual_stack.append(sprite_to_move)
                sprite_to_move.move_to((STACK_ZONE_X + CRATE_HEIGHT/2, target_y), callback=lambda: self._force_park_orientation(sprite_to_move))
            else: self.process_next_event()

    def action_summary(self): self.show_summary = not self.show_summary
    def on_animation_complete(self): self.is_animating = False; self.lcd.update_status("READY")

    def handle_events(self, event):
        if self.show_summary:
            if event.type == pygame.MOUSEBUTTONDOWN: self.show_summary = False
            return
        self.lcd.handle_event(event); self.btn_arrive.handle_event(event)
        self.btn_depart.handle_event(event); self.btn_summary.handle_event(event)
        self.btn_skip.handle_event(event)

    def update(self):
        if self.show_summary: return
        self.all_sprites.update(); self.lcd.update()

    def draw_summary_overlay(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); overlay.set_alpha(230); overlay.fill((20, 25, 30))
        self.screen.blit(overlay, (0, 0))
        font_title = pygame.font.SysFont("Arial", 24, bold=True); font_mono = pygame.font.SysFont("Courier New", 14)
        pygame.draw.rect(self.screen, (50, 150, 250), (0, 40, SCREEN_WIDTH, 50))
        title = font_title.render("WAREHOUSE INVENTORY MANIFEST", True, (255, 255, 255))
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 55))
        headers = f"{'PLATE ID':<15} {'ARRIVALS':<10} {'DEPARTURES':<10}"
        self.screen.blit(font_mono.render(headers, True, (100, 200, 255)), (SCREEN_WIDTH//2 - 150, 120))
        pygame.draw.line(self.screen, (100, 200, 255), (SCREEN_WIDTH//2 - 160, 135), (SCREEN_WIDTH//2 + 160, 135), 1)
        report = self.logic.get_inventory_report(); start_y = 150
        for i, item in enumerate(report):
            txt = f"{item['plate']:<15} {item['arrivals']:<10} {item['departures']:<10}"
            col = (255, 255, 255) if i % 2 == 0 else (200, 200, 210)
            self.screen.blit(font_mono.render(txt, True, col), (SCREEN_WIDTH//2 - 150, start_y + i*20))

    def draw(self):
        self.draw_environment()
        self.all_sprites.draw(self.screen)
        for sprite in self.crates_group:
            label_x = sprite.rect.centerx - sprite.label_surf.get_width() // 2
            label_y = sprite.rect.centery - 35
            self.screen.blit(sprite.label_surf, (label_x, label_y))
        self.chassis.draw(self.screen)
        self.lcd.draw(self.screen)
        self.btn_arrive.draw(self.screen)
        self.btn_depart.draw(self.screen)
        self.btn_summary.draw(self.screen)
        self.btn_skip.draw(self.screen)
        if self.show_summary:
            self.draw_summary_overlay()