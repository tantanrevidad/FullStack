import pygame
import random
import math
from settings import *
from core.ui import HandheldChassis, LCDDisplay, RoundButton, Button

class ArrayManager:
    """
    Backend Logic for Fixed-Size Array.
    Handles read/write operations and index validation.
    """
    def __init__(self, capacity=10):
        self.resize(capacity)

    def resize(self, capacity):
        """Resizes the array and clears data."""
        self.capacity = capacity
        self.data = [None] * capacity

    def write(self, index, value):
        """Writes a value to a specific index."""
        if index < 0 or index >= self.capacity: return {"type": "ERROR", "message": "INDEX OOB"}
        old_value = self.data[index]
        self.data[index] = value
        return {"type": "WRITE", "index": index, "value": value, "replaced": old_value is not None}

    def read(self, index):
        """Reads a value from a specific index."""
        if index < 0 or index >= self.capacity: return {"type": "ERROR", "message": "INDEX OOB"}
        value = self.data[index]
        if value is None: return {"type": "EMPTY", "index": index, "message": "SLOT EMPTY"}
        return {"type": "READ", "index": index, "value": value}

    def clear_slot(self, index):
        """Clears the value at a specific index."""
        if index < 0 or index >= self.capacity: return {"type": "ERROR", "message": "INDEX OOB"}
        if self.data[index] is None: return {"type": "ERROR", "message": "ALREADY EMPTY"}
        value = self.data[index]
        self.data[index] = None
        return {"type": "CLEAR", "index": index, "value": value}

    def get_manifest(self):
        return [{"index": i, "value": v} for i, v in enumerate(self.data)]

class PalletCrateSprite(pygame.sprite.Sprite):
    """Visual representation of a palletized crate."""
    def __init__(self, x, y, value):
        super().__init__()
        self.value = str(value)
        self.width = 40
        self.height = 40
        self.image = self._create_surface()
        self.rect = self.image.get_rect(midbottom=(x, y))

    def _create_surface(self):
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pallet_h = 6
        box_h = self.height - pallet_h
        pallet_color = (139, 105, 70)
        dark_wood = (100, 70, 40)
        pygame.draw.rect(surf, pallet_color, (0, self.height-pallet_h, self.width, pallet_h))
        for i in range(0, self.width, 4):
            pygame.draw.line(surf, dark_wood, (i, self.height-pallet_h), (i, self.height), 1)
        pygame.draw.rect(surf, (20, 20, 20), (0, self.height - pallet_h//2 - 1, self.width, 2))
        pygame.draw.rect(surf, pallet_color, (0, self.height-pallet_h, 4, pallet_h))
        pygame.draw.rect(surf, pallet_color, (self.width//2-2, self.height-pallet_h, 4, pallet_h))
        pygame.draw.rect(surf, pallet_color, (self.width-4, self.height-pallet_h, 4, pallet_h))
        box_rect = pygame.Rect(2, 0, self.width-4, box_h)
        pygame.draw.rect(surf, BOX_COLOR_1, box_rect)
        pygame.draw.rect(surf, (160, 110, 60), box_rect, 1)
        for i in range(box_rect.left + 4, box_rect.right, 4):
            pygame.draw.line(surf, (190, 125, 60), (i, box_rect.top), (i, box_rect.bottom), 1)
        tape_y = int(box_h * 0.25)
        pygame.draw.line(surf, BOX_TAPE, (2, tape_y), (self.width-2, tape_y), 4)
        label_w = self.width * 0.6
        label_h = box_h * 0.4
        label_x = (self.width - label_w) // 2
        label_y = (box_h - label_h) // 2 + 5
        pygame.draw.rect(surf, (240, 240, 240), (label_x, label_y, label_w, label_h))
        font = pygame.font.SysFont("Arial", 12, bold=True)
        txt = font.render(self.value, True, (20, 20, 20))
        surf.blit(txt, (self.width//2 - txt.get_width()//2, label_y + label_h//2 - txt.get_height()//2))
        pygame.draw.polygon(surf, (200, 50, 50), [
            (self.width - 8, 4), (self.width - 5, 8), (self.width - 11, 8)
        ])
        return surf

class ForkliftSprite(pygame.sprite.Sprite):
    """
    Animated forklift that moves horizontally and lifts forks vertically.
    """
    def __init__(self, x, y):
        super().__init__()
        self.home_x, self.home_y = float(x), float(y)
        self.pos_x, self.pos_y = self.home_x, self.home_y
        self.target_x = self.home_x
        self.is_moving = False
        self.state = 'IDLE'
        self.callback = None
        self.cargo_sprite = None
        self.fork_height = 0
        self.max_fork_height = 180
        self.width = 70
        self.height = 50
        self.facing_right = True
        self.original_image_right = self._create_surface(facing_right=True)
        self.original_image_left = self._create_surface(facing_right=False)
        self.image = self.original_image_right
        self.rect = self.image.get_rect(bottomleft=(int(self.pos_x), int(self.pos_y)))

    def _create_surface(self, facing_right):
        surf = pygame.Surface((self.width + 50, self.height + self.max_fork_height + 20), pygame.SRCALPHA)
        floor_y = surf.get_height() - 10
        direction = 1 if facing_right else -1
        body_x_start = 0 if facing_right else 40
        tire_radius = 14
        rear_tire_x = body_x_start + 15 if facing_right else body_x_start + self.width - 15
        front_tire_x = body_x_start + self.width - 15 if facing_right else body_x_start + 15
        for tx in [rear_tire_x, front_tire_x]:
            pygame.draw.circle(surf, (20, 20, 20), (tx, floor_y), tire_radius)
            pygame.draw.circle(surf, (50, 50, 50), (tx, floor_y), 6)
            for i in range(0, 360, 45):
                rad = math.radians(i)
                ox = tx + math.cos(rad) * (tire_radius - 2)
                oy = floor_y + math.sin(rad) * (tire_radius - 2)
                pygame.draw.circle(surf, (40, 40, 40), (int(ox), int(oy)), 2)
        chassis_h = 35
        chassis_rect = pygame.Rect(body_x_start, floor_y - chassis_h, self.width, chassis_h - 5)
        pygame.draw.rect(surf, (255, 200, 0), chassis_rect, border_radius=6)
        pygame.draw.rect(surf, (200, 150, 0), chassis_rect, 2, border_radius=6)
        pygame.draw.rect(surf, (30, 30, 30), (body_x_start, floor_y - 15, self.width, 10))
        vent_x = body_x_start + 10 if facing_right else body_x_start + self.width - 25
        for i in range(3):
            pygame.draw.line(surf, (50, 50, 50), (vent_x + i*5, floor_y - 25), (vent_x + i*5, floor_y - 18), 2)
        cab_w = 35
        cab_h = 45
        cab_x = body_x_start + 10 if facing_right else body_x_start + self.width - 10 - cab_w
        cab_rect = pygame.Rect(cab_x, floor_y - chassis_h - cab_h + 5, cab_w, cab_h)
        pygame.draw.rect(surf, (40, 40, 45), cab_rect, 3, border_radius=2)
        pygame.draw.rect(surf, (40, 40, 45), (cab_x - 2, cab_rect.top, cab_w + 4, 4))
        seat_x = cab_x + 5 if facing_right else cab_x + cab_w - 15
        pygame.draw.rect(surf, (60, 60, 60), (seat_x, floor_y - chassis_h - 10, 10, 15))
        pygame.draw.circle(surf, (255, 100, 0), (cab_x + cab_w//2, cab_rect.top - 2), 3)
        mast_x = body_x_start + self.width if facing_right else body_x_start
        mast_w = 8
        mast_h = self.height + self.max_fork_height - 20
        mast_rect = pygame.Rect(mast_x - 4, floor_y - mast_h, mast_w, mast_h)
        pygame.draw.rect(surf, (60, 65, 70), mast_rect)
        pygame.draw.rect(surf, (30, 35, 40), mast_rect, 1)
        pygame.draw.rect(surf, (180, 180, 190), (mast_x - 2, floor_y - mast_h + 5, 4, mast_h - 10))
        fork_y = floor_y - 5 - self.fork_height
        fork_len = 35
        fork_start_x = mast_x if facing_right else mast_x - fork_len
        pygame.draw.rect(surf, (40, 40, 40), (mast_x - 5, fork_y - 25, 10, 30))
        pygame.draw.rect(surf, (150, 150, 155), (fork_start_x, fork_y, fork_len, 4))
        return surf

    def move_to(self, target_x, callback=None):
        self.target_x = target_x; self.callback = callback; self.is_moving = True
        if self.target_x > self.pos_x: self.facing_right = True
        elif self.target_x < self.pos_x: self.facing_right = False
        self.image = self.original_image_right if self.facing_right else self.original_image_left

    def lift_forks(self, height, callback=None):
        self.target_fork_height = height; self.callback = callback
        self.state = 'LIFTING' if height > self.fork_height else 'LOWERING'

    def update(self):
        if self.is_moving:
            dx = self.target_x - self.pos_x
            if abs(dx) < MIN_SPEED * 2:
                self.pos_x = self.target_x; self.is_moving = False
                if self.callback: cb = self.callback; self.callback = None; cb()
            else:
                self.pos_x += dx * 0.08
                if abs(dx) > 1 and abs(dx * 0.08) < 1: self.pos_x += 1 if dx > 0 else -1
        if self.state in ['LIFTING', 'LOWERING']:
            dh = self.target_fork_height - self.fork_height
            if abs(dh) < 1:
                self.fork_height = self.target_fork_height; self.state = 'IDLE'
                self.image = self._create_surface(self.facing_right)
                if self.callback: cb = self.callback; self.callback = None; cb()
            else:
                self.fork_height += dh * 0.2
                self.image = self._create_surface(self.facing_right)
        if self.cargo_sprite:
            mast_offset = self.width if self.facing_right else 0
            fork_x = self.pos_x + mast_offset
            if not self.facing_right: fork_x -= 35
            fork_y = self.pos_y - 10 - self.fork_height
            self.cargo_sprite.rect.bottom = int(fork_y)
            self.cargo_sprite.rect.centerx = int(fork_x + 17.5)
        self.rect = self.image.get_rect(bottomleft=(int(self.pos_x), int(self.pos_y)))

class ArraySimulation:
    """
    Visualization for Array Module.
    Renders the rack system and manages forklift operations.
    """
    def __init__(self, screen):
        self.screen = screen
        self.logic = ArrayManager(capacity=10)
        self.all_sprites = pygame.sprite.Group()
        self.crates_group = pygame.sprite.Group()
        
        self.SIM_WIDTH = 750
        self.FLOOR_Y = SCREEN_HEIGHT - 100
        self.RACK_BASE_Y = self.FLOOR_Y - 100
        self.RACK_X_START = 110
        self.SLOT_WIDTH = 60
        self.LEVEL_HEIGHT = 70
        self.HOME_X = 20
        
        self.forklift = ForkliftSprite(self.HOME_X, self.FLOOR_Y)
        self.all_sprites.add(self.forklift)
        
        self.ui_x = 750; self.ui_w = 250
        self.chassis = HandheldChassis(self.ui_x + 10, 20, self.ui_w - 20, SCREEN_HEIGHT - 40)
        self.lcd = LCDDisplay(self.ui_x + 35, 80, self.ui_w - 70, 100)
        self.lcd.update_status("SELECT A SLOT")
        
        btn_cx = self.ui_x + self.ui_w // 2
        self.btn_write = RoundButton(btn_cx, 260, 45, BTN_GREEN_BASE, BTN_GREEN_LIGHT, "WRITE", self.action_write)
        self.btn_manifest = RoundButton(btn_cx, 480, 45, BTN_BLUE_BASE, BTN_BLUE_LIGHT, "SUMMARY", self.action_manifest)
        self.btn_clear = RoundButton(btn_cx, 590, 45, BTN_RED_BASE, BTN_RED_LIGHT, "CLEAR", self.action_clear)
        self.btn_resize = RoundButton(btn_cx, 370, 45, (200, 180, 50), (255, 230, 80), "RESIZE", self.action_resize_click)
        
        self.selected_index = None
        self.is_animating = False
        self.show_manifest = False
        self.manifest_scroll = 0
        self.scanner_active = False
        self.scanner_timer = 0
        self.input_mode = None
        
        self.recalculate_layout()
        self.bg_surface = self._generate_background()

    def recalculate_layout(self):
        self.slot_rects = []
        for i in range(self.logic.capacity):
            row = i // 10
            col = i % 10
            x = self.RACK_X_START + (col * self.SLOT_WIDTH)
            y = self.RACK_BASE_Y - (row * self.LEVEL_HEIGHT)
            rect = pygame.Rect(x, y - 50, self.SLOT_WIDTH, 60)
            self.slot_rects.append(rect)

    def _generate_background(self):
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg.fill(WALL_BASE_COLOR)
        floor_rect = pygame.Rect(0, self.FLOOR_Y, SCREEN_WIDTH, SCREEN_HEIGHT - self.FLOOR_Y)
        bg.fill(FLOOR_COLOR, floor_rect)
        for x in range(0, SCREEN_WIDTH, 20):
            color = (75, 80, 85) if (x // 20) % 2 == 0 else (85, 90, 95)
            pygame.draw.rect(bg, color, (x, 0, 20, self.FLOOR_Y))
        for _ in range(5000):
            color = random.choice([CONCRETE_NOISE_1, CONCRETE_NOISE_2])
            bg.set_at((random.randint(0, SCREEN_WIDTH-1), random.randint(self.FLOOR_Y, SCREEN_HEIGHT-1)), color)
        rack_zone_rect = pygame.Rect(self.RACK_X_START - 20, self.FLOOR_Y, (self.SLOT_WIDTH * 10) + 40, 40)
        pygame.draw.rect(bg, (40, 40, 40), rack_zone_rect)
        for i in range(0, rack_zone_rect.width, 30):
            p1 = (rack_zone_rect.left + i, rack_zone_rect.bottom)
            p2 = (rack_zone_rect.left + i + 15, rack_zone_rect.top)
            pygame.draw.line(bg, STRIPE_YELLOW, p1, p2, 3)
        pygame.draw.line(bg, (0,0,0), (0, self.FLOOR_Y), (SCREEN_WIDTH, self.FLOOR_Y), 3)
        num_rows = (self.logic.capacity - 1) // 10 + 1
        rack_w = self.SLOT_WIDTH * 10 + 20
        upright_color = (40, 60, 90)
        for i in range(11):
            x = self.RACK_X_START + (i * self.SLOT_WIDTH)
            top_y = self.RACK_BASE_Y - ((num_rows - 1) * self.LEVEL_HEIGHT) - 10
            pygame.draw.rect(bg, (30, 45, 70), (x+5, top_y, 4, self.FLOOR_Y - top_y))
            pygame.draw.rect(bg, upright_color, (x-2, top_y, 4, self.FLOOR_Y - top_y))
            pygame.draw.rect(bg, (30, 30, 30), (x-4, self.FLOOR_Y-2, 8, 2))
        beam_color = (220, 100, 40)
        beam_shadow = (180, 80, 30)
        for r in range(num_rows):
            y = self.RACK_BASE_Y - (r * self.LEVEL_HEIGHT)
            pygame.draw.rect(bg, beam_color, (self.RACK_X_START - 10, y, rack_w, 8))
            pygame.draw.rect(bg, beam_shadow, (self.RACK_X_START - 10, y+8, rack_w, 2))
            for c in range(10):
                idx = r * 10 + c
                if idx < self.logic.capacity:
                    x = self.RACK_X_START + (c * self.SLOT_WIDTH)
                    pygame.draw.rect(bg, (200, 200, 200), (x + self.SLOT_WIDTH//2 - 10, y + 12, 20, 14))
                    font = pygame.font.SysFont("Arial", 10, bold=True)
                    txt = font.render(str(idx), True, (20, 20, 20))
                    bg.blit(txt, (x + self.SLOT_WIDTH//2 - txt.get_width()//2, y + 13))
        light_layer = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for i in range(0, SCREEN_WIDTH, 200):
            pygame.draw.rect(bg, (20, 20, 20), (i, 0, 60, 20))
            pygame.draw.ellipse(bg, (200, 255, 255), (i+5, 15, 50, 10))
            points = [(i+10, 20), (i+50, 20), (i+150, self.FLOOR_Y), (i-80, self.FLOOR_Y)]
            pygame.draw.polygon(light_layer, (255, 255, 220, 15), points)
        bg.blit(light_layer, (0,0))
        return bg

    def get_slot_pos(self, index):
        row = index // 10
        col = index % 10
        x = self.RACK_X_START + (col * self.SLOT_WIDTH) + (self.SLOT_WIDTH // 2)
        y = self.RACK_BASE_Y - (row * self.LEVEL_HEIGHT)
        return x, y

    def handle_mouse_click(self, pos):
        if self.is_animating: return
        for i, rect in enumerate(self.slot_rects):
            if rect.collidepoint(pos):
                self.selected_index = i
                self.input_mode = 'VALUE'
                self.lcd.update_status(f"SLOT {i} SELECTED")
                self.lcd.text = ""
                return

    def action_resize_click(self):
        if self.is_animating: return
        if self.input_mode == 'SIZE':
            self.execute_resize()
        else:
            self.input_mode = 'SIZE'
            self.selected_index = None
            self.lcd.update_status("ENTER SIZE [10-30]")
            self.lcd.text = ""

    def execute_resize(self):
        text = self.lcd.text
        if not text.isdigit():
            self.lcd.update_status("ERR: NUMBERS ONLY")
            return
        size = int(text)
        if not 10 <= size <= 30:
            self.lcd.update_status("ERR: 10-30 ONLY")
            return
        self.logic.resize(size)
        for c in self.crates_group: c.kill()
        self.recalculate_layout()
        self.bg_surface = self._generate_background()
        self.forklift.move_to(self.HOME_X)
        self.lcd.update_status(f"RESIZED TO {size}")
        self.input_mode = None

    def action_write(self):
        if self.is_animating: return
        if self.selected_index is None:
            self.lcd.update_status("ERR: SELECT SLOT")
            return
        text = self.lcd.text
        if not text.isdigit():
            self.lcd.update_status("ERR: ENTER VALUE")
            return
        val = int(text)
        if val > 999:
            self.lcd.update_status("ERR: MAX 999")
            return
        receipt = self.logic.write(self.selected_index, val)
        self.is_animating = True
        self.lcd.update_status(f"WRITING {val}...")
        self.lcd.text = ""
        target_idx = self.selected_index
        self.selected_index = None
        self.input_mode = None
        existing_crate = next((c for c in self.crates_group if abs(c.rect.centerx - self.get_slot_pos(target_idx)[0]) < 10 and abs(c.rect.bottom - self.get_slot_pos(target_idx)[1]) < 10), None)
        if existing_crate:
            self.animate_removal(existing_crate, lambda: self.animate_insertion(target_idx, val))
        else:
            self.animate_insertion(target_idx, val)

    def action_manifest(self):
        if self.is_animating: return
        self.show_manifest = True
        self.manifest_scroll = 0
        self.selected_index = None
        self.input_mode = None
        self.lcd.update_status("MANIFEST OPEN")

    def action_clear(self):
        if self.is_animating: return
        if self.selected_index is None:
            self.lcd.update_status("ERR: SELECT SLOT")
            return
        receipt = self.logic.clear_slot(self.selected_index)
        target_idx = self.selected_index
        self.selected_index = None
        self.input_mode = None
        if receipt['type'] == 'ERROR':
            self.lcd.update_status(receipt['message'])
            return
        self.is_animating = True
        self.lcd.update_status("CLEARING SLOT...")
        target_crate = next((c for c in self.crates_group if abs(c.rect.centerx - self.get_slot_pos(target_idx)[0]) < 10 and abs(c.rect.bottom - self.get_slot_pos(target_idx)[1]) < 10), None)
        if target_crate:
            self.animate_removal(target_crate, self.on_animation_complete)
        else:
            self.on_animation_complete()

    def animate_insertion(self, index, value):
        crate = PalletCrateSprite(self.HOME_X, self.FLOOR_Y, value)
        self.all_sprites.add(crate); self.crates_group.add(crate)
        self.forklift.cargo_sprite = crate
        slot_x, slot_y = self.get_slot_pos(index)
        target_x = slot_x - 87
        shelf_lift = (self.FLOOR_Y - slot_y)
        clearance_lift = shelf_lift + 15
        def step5_return():
            self.forklift.move_to(self.HOME_X, self.on_animation_complete)
        def step4_lower_forks():
            self.forklift.lift_forks(0, step5_return)
        def step3_detach():
            self.forklift.cargo_sprite = None
            crate.rect.bottom = slot_y
            step4_lower_forks()
        def step2_lower_to_shelf():
            self.forklift.lift_forks(shelf_lift, step3_detach)
        def step1_move_in():
            self.forklift.move_to(target_x, step2_lower_to_shelf)
        def step0_lift():
            self.forklift.lift_forks(clearance_lift, step1_move_in)
        step0_lift()

    def animate_removal(self, crate, next_callback):
        target_x = crate.rect.centerx - 87
        slot_y = crate.rect.bottom
        shelf_lift = (self.FLOOR_Y - slot_y)
        clearance_lift = shelf_lift + 15
        def step5_destroy():
            crate.kill()
            self.forklift.cargo_sprite = None
            self.forklift.move_to(self.HOME_X, next_callback)
        def step4_lower_to_floor():
            self.forklift.lift_forks(0, step5_destroy)
        def step3_move_out():
            self.forklift.move_to(target_x - 20, step4_lower_to_floor)
        def step2_lift_off():
            self.forklift.cargo_sprite = crate
            self.forklift.lift_forks(clearance_lift, step3_move_out)
        def step1_raise_forks():
            self.forklift.lift_forks(shelf_lift, step2_lift_off)
        self.forklift.move_to(target_x, step1_raise_forks)

    def on_animation_complete(self):
        self.is_animating = False
        self.lcd.update_status("READY")

    def handle_events(self, event):
        if self.show_manifest:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button in [1, 3]:
                self.show_manifest = False
                self.lcd.update_status("READY")
            elif event.type == pygame.MOUSEWHEEL:
                self.manifest_scroll += event.y * 20
                max_scroll = 0
                min_scroll = -max(0, (len(self.logic.data) * 20) - 350)
                if self.manifest_scroll > max_scroll: self.manifest_scroll = max_scroll
                if self.manifest_scroll < min_scroll: self.manifest_scroll = min_scroll
            return
        self.lcd.handle_event(event)
        self.btn_write.handle_event(event)
        self.btn_manifest.handle_event(event)
        self.btn_clear.handle_event(event)
        self.btn_resize.handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.handle_mouse_click(event.pos)

    def update(self):
        if self.show_manifest: return
        self.all_sprites.update()
        self.lcd.update()

    def draw_manifest(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        w, h = 400, 500
        x, y = (SCREEN_WIDTH - w) // 2, (SCREEN_HEIGHT - h) // 2
        pygame.draw.rect(self.screen, (240, 240, 235), (x, y, w, h), border_radius=5)
        font_head = pygame.font.SysFont("Courier New", 24, bold=True)
        head = font_head.render("INVENTORY MANIFEST", True, (20, 20, 20))
        self.screen.blit(head, (x + w//2 - head.get_width()//2, y + 20))
        pygame.draw.line(self.screen, (50, 50, 50), (x+20, y+50), (x+w-20, y+50), 2)
        list_rect = pygame.Rect(x + 20, y + 60, w - 40, h - 100)
        self.screen.set_clip(list_rect)
        font_mono = pygame.font.SysFont("Courier New", 16)
        manifest = self.logic.get_manifest()
        col1_x = x + 40
        col2_x = x + 200
        self.screen.set_clip(None)
        pygame.draw.rect(self.screen, (240, 240, 235), (x+20, y+60, w-40, 30))
        self.screen.blit(font_mono.render("INDEX", True, (80, 80, 80)), (col1_x, y + 65))
        self.screen.blit(font_mono.render("VALUE", True, (80, 80, 80)), (col2_x, y + 65))
        pygame.draw.line(self.screen, (150, 150, 150), (x+20, y+85), (x+w-20, y+85), 1)
        content_rect = pygame.Rect(x + 20, y + 90, w - 40, h - 130)
        self.screen.set_clip(content_rect)
        start_y = y + 90 + self.manifest_scroll
        for item in manifest:
            idx_str = f"[{item['index']}]"
            val_str = str(item['value']) if item['value'] is not None else "---"
            color = (0, 0, 0) if item['value'] is not None else (150, 150, 150)
            self.screen.blit(font_mono.render(idx_str, True, (50, 50, 50)), (col1_x, start_y))
            self.screen.blit(font_mono.render(val_str, True, color), (col2_x, start_y))
            start_y += 20
        self.screen.set_clip(None)
        foot = font_mono.render("- CLICK TO CLOSE -", True, (100, 100, 100))
        self.screen.blit(foot, (x + w//2 - foot.get_width()//2, y + h - 30))

    def draw(self):
        self.screen.blit(self.bg_surface, (0, 0))
        if self.selected_index is not None:
            rect = self.slot_rects[self.selected_index]
            pygame.draw.rect(self.screen, (0, 255, 0), rect, 2, border_radius=4)
            if self.logic.data[self.selected_index] is None and not self.is_animating:
                ghost_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
                pygame.draw.rect(ghost_surf, (0, 255, 0, 50), (0, 0, 40, 40), border_radius=2)
                pygame.draw.rect(ghost_surf, (0, 255, 0), (0, 0, 40, 40), 1, border_radius=2)
                cx, cy = self.get_slot_pos(self.selected_index)
                self.screen.blit(ghost_surf, (cx - 20, cy - 40))
        for sprite in self.all_sprites:
            if isinstance(sprite, ForkliftSprite):
                s = pygame.Surface((sprite.width + 20, 20), pygame.SRCALPHA)
                pygame.draw.ellipse(s, (0,0,0,80), (0,0,sprite.width+20, 20))
                self.screen.blit(s, (sprite.rect.x - 10, sprite.rect.bottom - 10))
            elif isinstance(sprite, PalletCrateSprite) and sprite.rect.bottom == self.FLOOR_Y:
                if not self.forklift.cargo_sprite == sprite:
                    s = pygame.Surface((44, 10), pygame.SRCALPHA)
                    pygame.draw.ellipse(s, (0,0,0,60), (0,0,44,10))
                    self.screen.blit(s, (sprite.rect.x - 2, sprite.rect.bottom - 5))
        self.all_sprites.draw(self.screen)
        self.chassis.draw(self.screen)
        self.lcd.draw(self.screen)
        self.btn_write.draw(self.screen)
        self.btn_manifest.draw(self.screen)
        self.btn_clear.draw(self.screen)
        self.btn_resize.draw(self.screen)
        if self.show_manifest:
            self.draw_manifest()