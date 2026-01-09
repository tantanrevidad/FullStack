import pygame
import random
import math
from settings import *
from core.sprites import CrateSprite
from core.ui import HandheldChassis, LCDDisplay, RoundButton

class Vehicle:
    def __init__(self, plate, arrival_count, departure_count):
        self.plate = plate
        self.arrival_count = arrival_count
        self.departure_count = departure_count

class QueueManager:
    def __init__(self, capacity=10):
        self.items = []
        self.capacity = capacity
        self.history = {}

    def _get_stats(self, plate):
        if plate not in self.history:
            self.history[plate] = {'arrivals': 0, 'departures': 0}
        return self.history[plate]

    def enqueue(self, plate):
        if len(self.items) >= self.capacity:
            return {"type": "OVERFLOW", "message": "LANE FULL"}
        
        # Check for duplicates in current queue
        for v in self.items:
            if v.plate == plate:
                return {"type": "DUPLICATE", "message": "ALREADY HERE"}
        
        stats = self._get_stats(plate)
        stats['arrivals'] += 1
        
        new_vehicle = Vehicle(plate, stats['arrivals'], stats['departures'])
        self.items.append(new_vehicle)
        
        return {
            "type": "ENQUEUE",
            "index": len(self.items) - 1,
            "data": new_vehicle
        }

    def remove_vehicle(self, plate):
        target_index = -1
        for i, v in enumerate(self.items):
            if v.plate == plate:
                target_index = i
                break
        
        if target_index == -1:
            return [{"type": "ERROR", "message": "NOT FOUND"}]

        events = []
        
        # Cycle the vehicles in front of the target
        for _ in range(target_index):
            cycling_vehicle = self.items.pop(0)
            
            # UPDATE: Cycling counts as a Departure AND an Arrival
            stats = self._get_stats(cycling_vehicle.plate)
            stats['departures'] += 1
            stats['arrivals'] += 1
            
            # Update the vehicle object to reflect new stats
            cycling_vehicle.arrival_count = stats['arrivals']
            cycling_vehicle.departure_count = stats['departures']
            
            self.items.append(cycling_vehicle)
            
            events.append({
                "type": "CYCLE",
                "data": cycling_vehicle,
                "new_index": len(self.items) - 1
            })

        # Remove the actual target
        target_vehicle = self.items.pop(0)
        stats = self._get_stats(target_vehicle.plate)
        stats['departures'] += 1
        
        events.append({
            "type": "DEPART",
            "data": target_vehicle,
            "stats": stats
        })
        
        return events

    def get_inventory_report(self):
        # Report based on history of all items currently in the queue
        report = []
        for v in self.items:
            stats = self.history[v.plate]
            report.append({
                "plate": v.plate,
                "arrivals": stats['arrivals'],
                "departures": stats['departures']
            })
        return report

class ParkingQueueSimulation:
    def __init__(self, screen):
        self.screen = screen
        self.logic = QueueManager(capacity=10)
        self.all_sprites = pygame.sprite.Group()
        self.crates_group = pygame.sprite.Group()
        
        # UI Setup
        self.ui_x = 750
        self.ui_y = 0
        self.ui_w = 250
        self.ui_h = SCREEN_HEIGHT
        
        self.chassis = HandheldChassis(self.ui_x + 10, 20, self.ui_w - 20, SCREEN_HEIGHT - 40)
        self.lcd = LCDDisplay(self.ui_x + 35, 80, self.ui_w - 70, 100)
        self.lcd.update_status("WEIGH STATION")
        
        btn_cx = self.ui_x + self.ui_w // 2
        self.btn_arrive = RoundButton(btn_cx, 280, 45, BTN_GREEN_BASE, BTN_GREEN_LIGHT, "ENQUEUE", self.action_arrive)
        self.btn_depart = RoundButton(btn_cx, 390, 45, BTN_RED_BASE, BTN_RED_LIGHT, "DEQUEUE", self.action_depart)
        self.btn_summary = RoundButton(btn_cx, 500, 45, BTN_BLUE_BASE, BTN_BLUE_LIGHT, "MANIFEST", self.action_summary)
        self.btn_skip = RoundButton(btn_cx, 590, 30, (100, 100, 100), (150, 150, 150), "SKIP", self.action_skip)
        
        self.visual_queue = []
        self.is_animating = False
        self.show_summary = False
        self.event_queue = []
        
        # Layout Constants
        self.LANE_Y = 320
        self.SCALE_FACTOR = 0.7
        self.SLOT_GAP = 72
        self.GATE_X = 700
        self.ENTRY_SPAWN = (-100, self.LANE_Y)
        self.EXIT_POINT = (SCREEN_WIDTH + 100, self.LANE_Y)
        
        # Loopback Road Coordinates
        self.LOOP_EXIT_X = self.GATE_X + 40
        self.LOOP_DOWN_Y = 580
        self.LOOP_BACK_X = 20
        
        # Pre-render background
        self.bg_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self._generate_static_environment()

    def draw_container(self, surf, x, y, color, angle=0):
        w, h = 120, 50
        c_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(surf, SHADOW_COLOR, (x+5, y+5, w, h))
        pygame.draw.rect(c_surf, color, (0, 0, w, h))
        pygame.draw.rect(c_surf, (30, 30, 30), (0, 0, w, h), 1)
        for i in range(0, w, 10):
            pygame.draw.line(c_surf, CONTAINER_RIB, (i, 0), (i, h), 2)
        pygame.draw.rect(c_surf, (200, 200, 200), (5, 5, 30, 10))
        if angle != 0:
            c_surf = pygame.transform.rotate(c_surf, angle)
        surf.blit(c_surf, (x, y))

    def draw_barrel_group(self, surf, x, y):
        positions = [(0,0), (15,5), (5, 15)]
        for dx, dy in positions:
            bx, by = x + dx, y + dy
            pygame.draw.circle(surf, SHADOW_COLOR, (bx+2, by+2), 7)
            pygame.draw.circle(surf, BARREL_BLUE, (bx, by), 7)
            pygame.draw.circle(surf, BARREL_RIM, (bx, by), 7, 1)
            pygame.draw.circle(surf, (20, 20, 30), (bx+2, by+2), 2)

    def draw_fence(self, surf, start, end):
        pygame.draw.line(surf, FENCE_SHADOW, (start[0]+2, start[1]+2), (end[0]+2, end[1]+2), 2)
        pygame.draw.line(surf, FENCE_COLOR, start, end, 2)
        dist = math.hypot(end[0]-start[0], end[1]-start[1])
        count = int(dist // 30)
        for i in range(count + 1):
            t = i / count if count > 0 else 0
            px = start[0] + (end[0] - start[0]) * t
            py = start[1] + (end[1] - start[1]) * t
            pygame.draw.circle(surf, (100, 100, 100), (int(px), int(py)), 3)

    def draw_drain(self, surf, x, y):
        pygame.draw.rect(surf, DRAIN_METAL, (x, y, 30, 30))
        pygame.draw.rect(surf, (30, 30, 30), (x, y, 30, 30), 2)
        for i in range(x+5, x+30, 5):
            pygame.draw.line(surf, (30, 30, 30), (i, y), (i, y+30), 2)

    def draw_crack(self, surf, x, y):
        points = [(x, y)]
        curr_x, curr_y = x, y
        for _ in range(4):
            curr_x += random.randint(-10, 10)
            curr_y += random.randint(-10, 10)
            points.append((curr_x, curr_y))
        pygame.draw.lines(surf, CRACK_COLOR, False, points, 1)

    def _generate_static_environment(self):
        surf = self.bg_surface
        surf.fill(YARD_CONCRETE)
        for _ in range(8000):
            x = random.randint(0, 750)
            y = random.randint(0, SCREEN_HEIGHT)
            color = random.choice([YARD_NOISE_1, YARD_NOISE_2])
            surf.set_at((x, y), color)
        for _ in range(20):
            self.draw_crack(surf, random.randint(0, 750), random.randint(0, 700))
        rw = 80
        def draw_road_rect(rect):
            pygame.draw.rect(surf, ASPHALT_BASE, rect)
            for _ in range(int(rect.width * rect.height * 0.005)):
                rx = random.randint(rect.left, rect.right-1)
                ry = random.randint(rect.top, rect.bottom-1)
                surf.set_at((rx, ry), ASPHALT_DARK)
        draw_road_rect(pygame.Rect(-100, self.LANE_Y - rw//2, 900, rw))
        draw_road_rect(pygame.Rect(self.LOOP_EXIT_X - rw//2, self.LANE_Y, rw, self.LOOP_DOWN_Y - self.LANE_Y))
        draw_road_rect(pygame.Rect(self.LOOP_BACK_X, self.LOOP_DOWN_Y - rw//2, self.LOOP_EXIT_X - self.LOOP_BACK_X, rw))
        draw_road_rect(pygame.Rect(self.LOOP_BACK_X - rw//2, self.LANE_Y, rw, self.LOOP_DOWN_Y - self.LANE_Y))
        for x in range(-100, 800, 60):
            pygame.draw.line(surf, ROAD_STRIPE, (x, self.LANE_Y), (x+30, self.LANE_Y), 2)
        pygame.draw.line(surf, (255, 255, 255), (self.GATE_X, self.LANE_Y - 35), (self.GATE_X, self.LANE_Y + 35), 6)
        self.draw_drain(surf, 200, 500)
        self.draw_drain(surf, 600, 500)
        oil_surf = pygame.Surface((60, 40), pygame.SRCALPHA)
        pygame.draw.ellipse(oil_surf, OIL_STAIN, (0,0,60,40))
        surf.blit(oil_surf, (self.GATE_X - 20, self.LANE_Y + 10))
        island_rect = pygame.Rect(self.LOOP_BACK_X + 40 + 10, self.LANE_Y + 40 + 10, 
                                  (self.LOOP_EXIT_X - self.LOOP_BACK_X) - 80 - 20,
                                  (self.LOOP_DOWN_Y - self.LANE_Y) - 80 - 20)
        pygame.draw.rect(surf, (125, 125, 130), island_rect)
        for i in range(island_rect.left, island_rect.right, 20):
            p1 = (i, island_rect.bottom)
            p2 = (i + 20, island_rect.top)
            if p2[0] < island_rect.right:
                pygame.draw.line(surf, (115, 115, 120), p1, p2, 2)
        self.draw_container(surf, island_rect.left + 20, island_rect.top + 20, CONTAINER_RED)
        self.draw_container(surf, island_rect.left + 40, island_rect.top + 10, CONTAINER_BLUE)
        self.draw_container(surf, island_rect.left + 160, island_rect.top + 30, CONTAINER_GREEN, angle=10)
        self.draw_barrel_group(surf, island_rect.right - 60, island_rect.bottom - 60)
        self.draw_barrel_group(surf, island_rect.right - 80, island_rect.bottom - 40)
        self._draw_static_pallet(surf, island_rect.right - 120, island_rect.bottom - 50)
        self._draw_static_pallet(surf, island_rect.right - 120, island_rect.bottom - 80)
        self.draw_fence(surf, (0, 180), (400, 180))
        self.draw_fence(surf, (400, 180), (400, 0))
        for i in range(3):
            for j in range(2):
                self._draw_static_pallet(surf, 50 + i*40, 100 + j*40)
        self.draw_container(surf, 100, 620, CONTAINER_BLUE)
        self.draw_container(surf, 230, 630, CONTAINER_RED, angle=-5)

    def _draw_static_pallet(self, surf, x, y):
        pygame.draw.rect(surf, SHADOW_COLOR, (x+5, y+5, 30, 30))
        pygame.draw.rect(surf, BOX_COLOR_2, (x, y, 30, 30))
        pygame.draw.line(surf, BOX_TAPE, (x, y+5), (x+30, y+5), 2)
        pygame.draw.line(surf, BOX_TAPE, (x, y+15), (x+30, y+15), 2)
        pygame.draw.line(surf, BOX_TAPE, (x, y+25), (x+30, y+25), 2)

    def draw_brick_building(self, x, y, w, h, label):
        pygame.draw.rect(self.screen, SHADOW_COLOR, (x+10, y+10, w, h))
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, BRICK_RED, rect)
        for by in range(y, y+h, 10):
            pygame.draw.line(self.screen, BRICK_DETAIL, (x, by), (x+w, by), 1)
            offset = 0 if (by//10)%2==0 else 10
            for bx in range(x + offset, x+w, 20):
                pygame.draw.line(self.screen, BRICK_DETAIL, (bx, by), (bx, by+10), 1)
        pygame.draw.rect(self.screen, (50, 30, 30), rect, 2)
        roof_h = h - 15
        roof_rect = pygame.Rect(x-4, y-4, w+8, roof_h)
        pygame.draw.rect(self.screen, ROOF_TAR, roof_rect)
        pygame.draw.rect(self.screen, (30, 30, 30), roof_rect, 2)
        font = pygame.font.SysFont("Arial", 10, bold=True)
        txt = font.render(label, True, (200, 200, 200))
        self.screen.blit(txt, (x + w//2 - txt.get_width()//2, y + roof_h//2))

    def draw_bollard(self, x, y):
        pygame.draw.circle(self.screen, SHADOW_COLOR, (x+3, y+3), 6)
        pygame.draw.circle(self.screen, (50, 50, 50), (x, y), 6)
        pygame.draw.circle(self.screen, BOLLARD_YELLOW, (x, y), 4)

    def draw_dynamic_environment(self):
        self.screen.blit(self.bg_surface, (0, 0))
        self.draw_brick_building(self.GATE_X + 20, self.LANE_Y - 130, 80, 60, "GUARD")
        wh_rect = pygame.Rect(450, 30, 250, 120)
        pygame.draw.rect(self.screen, SHADOW_COLOR, wh_rect.move(10, 10))
        pygame.draw.rect(self.screen, WAREHOUSE_WALL, wh_rect)
        for i in range(wh_rect.left, wh_rect.right, 10):
            pygame.draw.line(self.screen, (150, 155, 160), (i, wh_rect.top), (i, wh_rect.bottom), 1)
        pygame.draw.rect(self.screen, (100, 100, 100), wh_rect, 2)
        pygame.draw.rect(self.screen, WAREHOUSE_ROOF, (440, 20, 270, 100))
        pygame.draw.rect(self.screen, (80, 80, 80), (440, 20, 270, 100), 2)
        font = pygame.font.SysFont("Impact", 20)
        lbl = font.render("LOGISTICS HUB", True, (180, 180, 180))
        self.screen.blit(lbl, (575 - lbl.get_width()//2, 60))
        scale_rect = pygame.Rect(self.GATE_X - 80, self.LANE_Y - 35, 100, 70)
        pygame.draw.rect(self.screen, (50, 50, 50), scale_rect)
        pygame.draw.rect(self.screen, (180, 180, 180), scale_rect.inflate(-4, -4))
        pygame.draw.rect(self.screen, (100, 100, 100), scale_rect.inflate(-4, -4), 1)
        gate_pivot = (self.GATE_X + 25, self.LANE_Y - 40)
        pygame.draw.circle(self.screen, (200, 50, 50), gate_pivot, 6)
        pygame.draw.line(self.screen, (255, 255, 255), gate_pivot, (self.GATE_X + 25, self.LANE_Y + 40), 4)
        pygame.draw.line(self.screen, (200, 0, 0), gate_pivot, (self.GATE_X + 25, self.LANE_Y + 40), 4)
        island_rect = pygame.Rect(self.LOOP_BACK_X + 40 + 10, self.LANE_Y + 40 + 10, 
                                  (self.LOOP_EXIT_X - self.LOOP_BACK_X) - 80 - 20,
                                  (self.LOOP_DOWN_Y - self.LANE_Y) - 80 - 20)
        self.draw_bollard(island_rect.left, island_rect.top)
        self.draw_bollard(island_rect.right, island_rect.top)
        self.draw_bollard(island_rect.left, island_rect.bottom)
        self.draw_bollard(island_rect.right, island_rect.bottom)

    def _scale_sprite(self, sprite):
        w = int(sprite.original_image.get_width() * self.SCALE_FACTOR)
        h = int(sprite.original_image.get_height() * self.SCALE_FACTOR)
        sprite.original_image = pygame.transform.smoothscale(sprite.original_image, (w, h))
        sprite.image = sprite.original_image.copy()
        sprite.rect = sprite.image.get_rect(center=sprite.rect.center)

    def _force_orientation(self, sprite, angle):
        sprite.angle = angle
        sprite.image = pygame.transform.rotate(sprite.original_image, angle)
        sprite.rect = sprite.image.get_rect(center=(sprite.pos_x, sprite.pos_y))

    def _realign_queue(self, exclude_sprites=None):
        if exclude_sprites is None:
            exclude_sprites = []
        for i, sprite in enumerate(self.visual_queue):
            if sprite in exclude_sprites:
                continue
            target_x = self.GATE_X - (i * self.SLOT_GAP)
            if abs(sprite.pos_x - target_x) > 5:
                sprite.move_to((target_x, self.LANE_Y), callback=lambda s=sprite: self._force_orientation(s, 0))

    def action_arrive(self):
        if self.is_animating or self.show_summary: return
        plate = self.lcd.text.upper()
        if not plate:
            self.lcd.update_status("ERR: NO INPUT")
            return
        receipt = self.logic.enqueue(plate)
        if receipt['type'] in ['OVERFLOW', 'DUPLICATE']:
            self.lcd.update_status(f"ERR: {receipt['message']}")
            return
        self.lcd.update_status(f"IN: {plate}")
        self.lcd.text = ""
        new_crate = CrateSprite(self.ENTRY_SPAWN[0], self.ENTRY_SPAWN[1], receipt['data'].plate)
        self._scale_sprite(new_crate)
        self.all_sprites.add(new_crate)
        self.crates_group.add(new_crate)
        self.visual_queue.append(new_crate)
        target_x = self.GATE_X - (receipt['index'] * self.SLOT_GAP)
        self.is_animating = True
        new_crate.move_to((target_x, self.LANE_Y), callback=self.on_animation_complete)

    def action_depart(self):
        if self.is_animating or self.show_summary: return
        plate = self.lcd.text.upper()
        if not plate: return
        events = self.logic.remove_vehicle(plate)
        if events[0]['type'] == 'ERROR':
            self.lcd.update_status(f"ERR: {events[0]['message']}")
            return
        self.lcd.update_status(f"OUT: {plate}")
        self.lcd.text = ""
        self.is_animating = True
        self.event_queue = events
        self.process_next_event()

    def action_skip(self):
        if not self.is_animating: return
        
        # 1. Stop all movement
        for s in self.all_sprites:
            s.is_moving = False
            s.on_finish_callback = None
            
        # 2. Clear pending events
        self.event_queue = []
        
        # 3. Sync Visuals to Logic
        valid_plates = [v.plate for v in self.logic.items]
        
        # Kill sprites that shouldn't exist
        for sprite in self.crates_group:
            if sprite.plate not in valid_plates:
                sprite.kill()
                
        # Rebuild visual_queue to match logic order
        self.visual_queue = []
        for vehicle in self.logic.items:
            found_sprite = next((s for s in self.crates_group if s.plate == vehicle.plate), None)
            if found_sprite:
                self.visual_queue.append(found_sprite)
                
        # 4. Snap sprites to correct positions
        for i, sprite in enumerate(self.visual_queue):
            target_x = self.GATE_X - (i * self.SLOT_GAP)
            sprite.pos_x = target_x
            sprite.pos_y = self.LANE_Y
            sprite.rect.center = (int(sprite.pos_x), int(sprite.pos_y))
            self._force_orientation(sprite, 0)
            
        # 5. Reset State
        self.is_animating = False
        self.lcd.update_status("READY")

    def process_next_event(self):
        if not self.event_queue:
            self._realign_queue()
            self.on_animation_complete()
            return
        event = self.event_queue.pop(0)
        if event['type'] == 'CYCLE':
            sprite = self.visual_queue.pop(0)
            self.visual_queue.append(sprite)
            self._realign_queue(exclude_sprites=[sprite])
            final_slot_x = self.GATE_X - (event['new_index'] * self.SLOT_GAP)
            def step4_to_slot():
                sprite.move_to((final_slot_x, self.LANE_Y), callback=lambda: [self._force_orientation(sprite, 0), self.process_next_event()])
            def step3_up():
                self._force_orientation(sprite, 90)
                sprite.move_to((self.LOOP_BACK_X + 30, self.LANE_Y), callback=step4_to_slot)
            def step2_left():
                self._force_orientation(sprite, 180)
                sprite.move_to((self.LOOP_BACK_X + 30, self.LOOP_DOWN_Y + 30), callback=step3_up)
            def step1_down():
                self._force_orientation(sprite, 270)
                sprite.move_to((self.LOOP_EXIT_X, self.LOOP_DOWN_Y + 30), callback=step2_left)
            sprite.move_to((self.LOOP_EXIT_X, self.LANE_Y), callback=step1_down)
        elif event['type'] == 'DEPART':
            sprite = self.visual_queue.pop(0)
            def cleanup():
                sprite.kill()
                self._realign_queue()
                self.process_next_event()
            sprite.move_to(self.EXIT_POINT, callback=cleanup)

    def action_summary(self):
        self.show_summary = not self.show_summary

    def on_animation_complete(self):
        self.is_animating = False
        self._force_orientation_all()
        self.lcd.update_status("READY")

    def _force_orientation_all(self):
        for s in self.crates_group:
            s.angle = 0
            s.image = pygame.transform.rotate(s.original_image, 0)
            s.rect = s.image.get_rect(center=(s.pos_x, s.pos_y))

    def handle_events(self, event):
        if self.show_summary:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.show_summary = False
            return
        self.lcd.handle_event(event)
        self.btn_arrive.handle_event(event)
        self.btn_depart.handle_event(event)
        self.btn_summary.handle_event(event)
        self.btn_skip.handle_event(event)

    def update(self):
        if self.show_summary: return
        self.all_sprites.update()
        self.lcd.update()

    def draw_summary_overlay(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(230)
        overlay.fill((20, 25, 30))
        self.screen.blit(overlay, (0, 0))
        font_title = pygame.font.SysFont("Arial", 24, bold=True)
        font_mono = pygame.font.SysFont("Courier New", 14)
        pygame.draw.rect(self.screen, (255, 200, 50), (0, 40, SCREEN_WIDTH, 50))
        title = font_title.render("WEIGH STATION MANIFEST", True, (20, 20, 20))
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 55))
        headers = f"{'PLATE ID':<15} {'ARRIVALS':<10} {'DEPARTURES':<10}"
        self.screen.blit(font_mono.render(headers, True, (255, 200, 50)), (SCREEN_WIDTH//2 - 150, 120))
        pygame.draw.line(self.screen, (255, 200, 50), (SCREEN_WIDTH//2 - 160, 135), (SCREEN_WIDTH//2 + 160, 135), 1)
        report = self.logic.get_inventory_report()
        start_y = 150
        for i, item in enumerate(report):
            txt = f"{item['plate']:<15} {item['arrivals']:<10} {item['departures']:<10}"
            col = (255, 255, 255) if i % 2 == 0 else (200, 200, 210)
            self.screen.blit(font_mono.render(txt, True, col), (SCREEN_WIDTH//2 - 150, start_y + i*20))

    def draw(self):
        self.draw_dynamic_environment()
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