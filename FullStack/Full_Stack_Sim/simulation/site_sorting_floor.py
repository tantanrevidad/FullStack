import pygame
import random
from settings import *
from core.ui import HandheldChassis, LCDDisplay, RoundButton, Button

class SortingManager:
    """
    Backend Logic for Sorting Algorithms.
    Generates step-by-step instructions for visualization.
    """
    def __init__(self):
        self.items = []
        self.original_items = []  # Store the initial state

    def generate_new_list(self, size=20):
        """Creates a new random list of integers."""
        self.size = size
        self.items = random.sample(range(10, 100), self.size)
        self.original_items = list(self.items)  # Backup the unsorted list

    def reset_to_original(self):
        """Restores the items list to its original unsorted state."""
        if self.original_items:
            self.items = list(self.original_items)

    def get_bubble_sort_steps(self):
        """Generates visualization steps for Bubble Sort."""
        steps = []
        items = list(self.items)
        n = len(items)
        for i in range(n):
            swapped = False
            for j in range(0, n - i - 1):
                steps.append({"type": "compare", "indices": (j, j + 1)})
                if items[j] > items[j + 1]:
                    items[j], items[j + 1] = items[j + 1], items[j]
                    swapped = True
                    steps.append({"type": "swap", "indices": (j, j + 1)})
            steps.append({"type": "lock", "index": n - 1 - i})
            if not swapped:
                for k in range(0, n - i - 1):
                    steps.append({"type": "lock", "index": k})
                break
        return steps

    def get_selection_sort_steps(self):
        """Generates visualization steps for Selection Sort."""
        steps = []
        items = list(self.items)
        n = len(items)
        for i in range(n):
            min_idx = i
            steps.append({"type": "highlight", "indices": [i]})
            for j in range(i + 1, n):
                steps.append({"type": "compare", "indices": (min_idx, j)})
                if items[j] < items[min_idx]:
                    min_idx = j
                    steps.append({"type": "highlight", "indices": [min_idx]})
            if min_idx != i:
                items[i], items[min_idx] = items[min_idx], items[i]
                steps.append({"type": "swap", "indices": (i, min_idx)})
            steps.append({"type": "lock", "index": i})
        return steps

    def get_insertion_sort_steps(self):
        """Generates visualization steps for Insertion Sort."""
        steps = []
        items = list(self.items)
        n = len(items)
        if n > 0:
            steps.append({"type": "lock", "index": 0})
        for i in range(1, n):
            key = items[i]
            j = i - 1
            steps.append({"type": "highlight", "indices": [i]})
            while j >= 0 and key < items[j]:
                steps.append({"type": "compare", "indices": (j, i if j == i-1 else j+1)})
                items[j + 1] = items[j]
                steps.append({"type": "swap", "indices": (j, j + 1)})
                j -= 1
            items[j + 1] = key
            steps.append({"type": "lock", "index": i})
        steps.append({"type": "lock_all"})
        return steps

    def get_merge_sort_steps(self):
        """Generates visualization steps for Merge Sort."""
        steps = []
        items = list(self.items)
        def merge_sort_recursive(arr, start, end):
            if start < end:
                mid = (start + end) // 2
                merge_sort_recursive(arr, start, mid)
                merge_sort_recursive(arr, mid + 1, end)
                steps.append({"type": "highlight", "indices": list(range(start, end + 1))})
                left = arr[start:mid+1]
                right = arr[mid+1:end+1]
                i = j = 0; k = start
                while i < len(left) and j < len(right):
                    if left[i] <= right[j]: arr[k] = left[i]; i += 1
                    else: arr[k] = right[j]; j += 1
                    k += 1
                while i < len(left): arr[k] = left[i]; i += 1; k += 1
                while j < len(right): arr[k] = right[j]; j += 1; k += 1
                new_order_slice = arr[start:end+1]
                steps.append({"type": "reorder", "indices": list(range(start, end + 1)), "values": new_order_slice})
        merge_sort_recursive(items, 0, len(items) - 1)
        steps.append({"type": "lock_all"})
        return steps

    def get_quick_sort_steps(self):
        """Generates visualization steps for Quick Sort."""
        steps = []
        items = list(self.items)
        def partition(arr, low, high):
            pivot = arr[high]; i = low - 1
            steps.append({"type": "set_pivot", "index": high})
            for j in range(low, high):
                steps.append({"type": "compare", "indices": (j, high)})
                if arr[j] < pivot:
                    i += 1
                    arr[i], arr[j] = arr[j], arr[i]
                    if i != j: steps.append({"type": "swap", "indices": (i, j)})
            arr[i + 1], arr[high] = arr[high], arr[i + 1]
            if (i + 1) != high: steps.append({"type": "swap", "indices": (i + 1, high)})
            steps.append({"type": "lock", "index": i + 1})
            return i + 1
        def quick_sort_recursive(arr, low, high):
            if low < high:
                pi = partition(arr, low, high)
                quick_sort_recursive(arr, low, pi - 1)
                quick_sort_recursive(arr, pi + 1, high)
        quick_sort_recursive(items, 0, len(items) - 1)
        steps.append({"type": "lock_all"})
        return steps

class ContainerSprite(pygame.sprite.Sprite):
    """
    Visual representation of a data element (container).
    Height corresponds to value.
    """
    def __init__(self, value, x, y, container_width, max_value):
        super().__init__()
        self.value = value
        self.pos_x, self.pos_y = float(x), float(y)
        self.target_x, self.target_y = float(x), float(y)
        self.is_moving = False
        self.on_finish_callback = None
        self.state = 'idle'
        self.width = int(container_width)
        self.height = int((value / max_value) * 200) + 50
        self.color_palette = [CONTAINER_BLUE, CONTAINER_RED, (180, 120, 40), (80, 80, 80)]
        self.base_color = random.choice(self.color_palette)
        self.image = self._create_surface()
        self.rect = self.image.get_rect(bottomleft=(x, y))

    def _create_surface(self):
        glow_padding = 15
        surf = pygame.Surface((self.width + glow_padding * 2, self.height + glow_padding * 2), pygame.SRCALPHA)
        self.container_body_rect = pygame.Rect(glow_padding, glow_padding, self.width, self.height)
        
        glow_color_map = {'comparing': (255, 80, 80), 'highlight': (255, 255, 100), 'pivot': (220, 100, 255)}
        if self.state in glow_color_map:
            glow_color = glow_color_map[self.state]
            for i in range(glow_padding // 2, 0, -1):
                glow_rect = self.container_body_rect.inflate(i * 2, i * 2)
                alpha = 120 - (i * 10)
                pygame.draw.rect(surf, (*glow_color, alpha), glow_rect, border_radius=i * 2)
        
        if self.state == 'sorted':
            main_color = CONTAINER_GREEN
            dark_color = (main_color[0] * 0.7, main_color[1] * 0.7, main_color[2] * 0.7)
        else:
            main_color = self.base_color
            dark_color = (main_color[0] * 0.7, main_color[1] * 0.7, main_color[2] * 0.7)
            
        pygame.draw.rect(surf, main_color, self.container_body_rect)
        for i in range(0, self.width, 6):
            pygame.draw.line(surf, dark_color, (self.container_body_rect.left + i, self.container_body_rect.top), (self.container_body_rect.left + i, self.container_body_rect.bottom), 1)
        
        pygame.draw.line(surf, (255,255,255,60), self.container_body_rect.topleft, self.container_body_rect.topright, 2)
        pygame.draw.rect(surf, (20, 20, 20), self.container_body_rect, 2)
        return surf

    def set_state(self, new_state):
        if self.state != new_state:
            self.state = new_state
            self.image = self._create_surface()

    def move_to(self, target_pos, callback=None):
        self.target_x, self.target_y = target_pos
        self.is_moving = True
        self.on_finish_callback = callback

    def update(self, speed_multiplier=1.0):
        if not self.is_moving: return
        dx = self.target_x - self.pos_x
        dy = self.target_y - self.pos_y
        effective_lerp = LERP_FACTOR * speed_multiplier
        effective_speed = MIN_SPEED * speed_multiplier
        
        if (dx**2 + dy**2) < effective_speed**2:
            self.pos_x, self.pos_y = self.target_x, self.target_y
            self.is_moving = False
            if self.on_finish_callback:
                cb = self.on_finish_callback
                self.on_finish_callback = None
                cb()
        else:
            self.pos_x += dx * effective_lerp
            self.pos_y += dy * effective_lerp
        self.rect.bottomleft = (int(self.pos_x), int(self.pos_y))

class GantryCraneSprite(pygame.sprite.Sprite):
    """
    Animated crane that moves above the containers to indicate comparisons.
    """
    def __init__(self, y_pos, rail_width):
        super().__init__()
        self.y_pos = y_pos
        self.rail_width = rail_width
        self.pos_x = rail_width / 2
        self.target_x = self.pos_x
        self.is_moving = False
        self.on_finish_callback = None
        self.image = self._create_surface()
        self.rect = self.image.get_rect(center=(self.pos_x, self.y_pos))

    def _create_surface(self):
        surf = pygame.Surface((120, 150), pygame.SRCALPHA)
        center_x = surf.get_width() // 2
        pygame.draw.line(surf, (30,30,30), (center_x - 15, 0), (center_x - 15, 100), 2)
        pygame.draw.line(surf, (30,30,30), (center_x + 15, 0), (center_x + 15, 100), 2)
        
        hoist_body = pygame.Rect(center_x - 30, 100, 60, 20)
        pygame.draw.rect(surf, (80, 85, 90), hoist_body)
        pygame.draw.rect(surf, (50, 55, 60), hoist_body, 2)
        
        pygame.draw.rect(surf, (60, 65, 70), (center_x - 25, 120, 50, 10))
        pygame.draw.polygon(surf, STRIPE_YELLOW, [(center_x - 25, 130), (center_x - 15, 140), (center_x - 5, 130)])
        pygame.draw.polygon(surf, STRIPE_YELLOW, [(center_x + 25, 130), (center_x + 15, 140), (center_x + 5, 130)])
        
        trolley_rect = pygame.Rect(0, 0, 120, 30)
        pygame.draw.rect(surf, (60, 65, 70), trolley_rect, border_radius=3)
        pygame.draw.rect(surf, (90, 95, 100), trolley_rect, 2, border_radius=3)
        pygame.draw.circle(surf, (40,40,40), (15, 15), 5)
        pygame.draw.circle(surf, (40,40,40), (105, 15), 5)
        return surf

    def move_to(self, target_x, callback=None):
        self.target_x = target_x
        self.is_moving = True
        self.on_finish_callback = callback

    def update(self, speed_multiplier=1.0):
        if not self.is_moving: return
        dx = self.target_x - self.pos_x
        effective_lerp = LERP_FACTOR * speed_multiplier
        effective_speed = MIN_SPEED * speed_multiplier
        
        if abs(dx) < effective_speed:
            self.pos_x = self.target_x
            self.is_moving = False
            if self.on_finish_callback:
                cb = self.on_finish_callback; self.on_finish_callback = None; cb()
        else:
            self.pos_x += dx * effective_lerp
        self.rect.centerx = int(self.pos_x)

class SortingSimulation:
    """
    Visualization for Sorting Module.
    Manages the sorting floor, containers, and gantry crane.
    """
    def __init__(self, screen):
        self.screen = screen
        self.logic = SortingManager()
        self.SIM_WIDTH = 750
        self.FLOOR_Y = SCREEN_HEIGHT - 80
        self.STAGING_Y = self.FLOOR_Y - 350
        
        self.all_sprites = pygame.sprite.Group()
        self.containers = pygame.sprite.Group()
        self.crane_group = pygame.sprite.Group()
        
        self.ui_x = 750
        self.ui_w = 250
        self.chassis = HandheldChassis(self.ui_x + 10, 20, self.ui_w - 20, SCREEN_HEIGHT - 40)
        self.lcd = LCDDisplay(self.ui_x + 35, 80, self.ui_w - 70, 100)
        self.lcd.update_status("SORTING FLOOR")
        
        btn_cx = self.ui_x + self.ui_w // 2
        self.btn_load = RoundButton(btn_cx, 280, 45, BTN_BLUE_BASE, BTN_BLUE_LIGHT, "LOAD", self.action_load_containers)
        self.btn_sort = RoundButton(btn_cx, 390, 45, BTN_GREEN_BASE, BTN_GREEN_LIGHT, "SORT", self.action_open_sort_menu)
        self.btn_reset = RoundButton(btn_cx, 500, 45, BTN_RED_BASE, BTN_RED_LIGHT, "RESET", self.action_reset)
        
        self.speed_levels = [0.5, 1.0, 2.0, 4.0, 8.0]
        self.speed_index = 1
        self.speed_multiplier = self.speed_levels[self.speed_index]
        
        speed_btn_y = self.chassis.rect.bottom - 60
        speed_btn_w = 80
        speed_btn_h = 30
        self.btn_speed_down = Button(btn_cx - speed_btn_w - 5, speed_btn_y, speed_btn_w, speed_btn_h, "Speed -", self.decrease_speed)
        self.btn_speed_up = Button(btn_cx + 5, speed_btn_y, speed_btn_w, speed_btn_h, "Speed +", self.increase_speed)
        
        self.is_sorting = False
        self.sort_steps = []
        self.visual_containers = []
        self.slot_positions = []
        
        self.gantry_crane = GantryCraneSprite(y_pos=180, rail_width=self.SIM_WIDTH)
        self.crane_group.add(self.gantry_crane)
        self.all_sprites.add(self.gantry_crane)
        
        self.background = self._generate_static_background()
        self.show_sort_menu = False
        self._init_sort_menu()
        
        self.action_load_containers()

    def _init_sort_menu(self):
        menu_btn_w, menu_btn_h = 220, 40
        menu_cx = self.SIM_WIDTH // 2
        start_y = 200
        self.menu_btn_bubble = Button(menu_cx - menu_btn_w//2, start_y, menu_btn_w, menu_btn_h, "Bubble Sort", lambda: self.action_begin_sort("bubble"))
        self.menu_btn_selection = Button(menu_cx - menu_btn_w//2, start_y + 50, menu_btn_w, menu_btn_h, "Selection Sort", lambda: self.action_begin_sort("selection"))
        self.menu_btn_insertion = Button(menu_cx - menu_btn_w//2, start_y + 100, menu_btn_w, menu_btn_h, "Insertion Sort", lambda: self.action_begin_sort("insertion"))
        self.menu_btn_merge = Button(menu_cx - menu_btn_w//2, start_y + 150, menu_btn_w, menu_btn_h, "Merge Sort", lambda: self.action_begin_sort("merge"))
        self.menu_btn_quick = Button(menu_cx - menu_btn_w//2, start_y + 200, menu_btn_w, menu_btn_h, "Quick Sort", lambda: self.action_begin_sort("quick"))
        self.sort_menu_buttons = [self.menu_btn_bubble, self.menu_btn_selection, self.menu_btn_insertion, self.menu_btn_merge, self.menu_btn_quick]

    def _draw_shelf_unit(self, surf, x, y, w, h, rows, cols):
        for r in range(rows):
            ry = y + r * (h/rows)
            for c in range(cols):
                cx = x + c * (w/cols)
                shelf_rect = pygame.Rect(cx, ry, w/cols, h/rows)
                pygame.draw.rect(surf, (40,45,50), shelf_rect, 1)
                if random.random() > 0.2:
                    box_w = random.randint(10, int(w/cols - 5))
                    box_h = random.randint(5, int(h/rows - 5))
                    box_x = cx + random.randint(2, int(w/cols - box_w - 2))
                    box_y = ry + int(h/rows - box_h - 2)
                    color = random.choice([BOX_COLOR_1, BOX_COLOR_2, (160, 110, 50)])
                    pygame.draw.rect(surf, color, (box_x, box_y, box_w, box_h))

    def _draw_pillar(self, surf, x, y, w, h):
        pygame.draw.rect(surf, (90, 95, 100), (x+w, y, 10, h))
        pygame.draw.rect(surf, (110, 115, 120), (x, y, w, h))

    def _generate_static_background(self):
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg.fill(WALL_BASE_COLOR)
        
        self._draw_shelf_unit(bg, 0, 100, SCREEN_WIDTH, SCREEN_HEIGHT/2, 8, 25)
        for i in range(7):
            self._draw_pillar(bg, 50 + i * 150, 0, 20, SCREEN_HEIGHT)
            
        floor_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - self.FLOOR_Y))
        floor_surf.fill(FLOOR_COLOR)
        for _ in range(8000):
            color = random.choice([CONCRETE_NOISE_1, CONCRETE_NOISE_2])
            floor_surf.set_at((random.randint(0, SCREEN_WIDTH - 1), random.randint(0, floor_surf.get_height() - 1)), color)
        bg.blit(floor_surf, (0, self.FLOOR_Y))
        
        pygame.draw.rect(bg, (30,30,30), (0, self.FLOOR_Y, SCREEN_WIDTH, 5))
        pygame.draw.line(bg, STRIPE_YELLOW, (0, self.FLOOR_Y + 10), (SCREEN_WIDTH, self.FLOOR_Y + 10), 3)
        
        pygame.draw.rect(bg, (40,45,50), (0,0,SCREEN_WIDTH, 80))
        light_fixtures = []
        for i in range(0, SCREEN_WIDTH, 150):
            pygame.draw.rect(bg, (20,22,25), (i, 30, 100, 10))
            pygame.draw.rect(bg, FLUORESCENT_LIGHT, (i+2, 32, 96, 6))
            light_fixtures.append((i+50, 40))
            
        rail_y = self.gantry_crane.y_pos - 30
        pygame.draw.rect(bg, (50, 55, 60), (0, rail_y, SCREEN_WIDTH, 25))
        pygame.draw.rect(bg, (80, 85, 90), (0, rail_y, SCREEN_WIDTH, 25), 2)
        
        light_layer = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for lx, ly in light_fixtures:
            points = [(lx - 30, ly), (lx + 30, ly), (lx + 100, SCREEN_HEIGHT), (lx - 100, SCREEN_HEIGHT)]
            pygame.draw.polygon(light_layer, LIGHT_RAY_COLOR, points)
        bg.blit(light_layer, (0,0))
        return bg

    def _rebuild_visuals(self):
        """Recreates all container sprites based on the current logic state."""
        for c in self.containers:
            c.kill()
        self.visual_containers.clear()
        self.slot_positions.clear()
        
        container_width = (self.SIM_WIDTH - 100) / self.logic.size
        start_x = 50
        
        for i, value in enumerate(self.logic.items):
            x = start_x + (i * container_width)
            self.slot_positions.append(x)
            c = ContainerSprite(value, x, self.FLOOR_Y, container_width - 4, 100)
            self.containers.add(c)
            self.all_sprites.add(c)
            self.visual_containers.append(c)

    def action_load_containers(self):
        if self.is_sorting: return
        size_text = self.lcd.text if self.lcd.text else "20"
        try:
            size = int(size_text)
            if not 10 <= size <= 30:
                self.lcd.update_status("ERR: SIZE 10-30")
                return
        except ValueError:
            self.lcd.update_status("ERR: NOT A NUMBER")
            return
            
        self.lcd.update_status("LOADING CARGO...")
        self.logic.generate_new_list(size=size)
        self._rebuild_visuals()
        self.lcd.update_status("READY TO SORT")

    def action_open_sort_menu(self):
        if self.is_sorting or not self.visual_containers: return
        self.show_sort_menu = True

    def action_begin_sort(self, sort_type):
        self.show_sort_menu = False
        if self.is_sorting: return
        
        # RESET PHASE: Ensure we are sorting the original unsorted data
        self.logic.reset_to_original()
        self._rebuild_visuals()
        
        self.is_sorting = True
        self.lcd.update_status(f"SORTING: {sort_type.upper()}")
        
        st_map = {
            "bubble": self.logic.get_bubble_sort_steps,
            "selection": self.logic.get_selection_sort_steps,
            "insertion": self.logic.get_insertion_sort_steps,
            "merge": self.logic.get_merge_sort_steps,
            "quick": self.logic.get_quick_sort_steps
        }
        
        self.sort_steps = st_map[sort_type]()
        self.process_next_step()

    def action_reset(self):
        for sprite in self.all_sprites:
            sprite.is_moving = False
            sprite.on_finish_callback = None
        self.is_sorting = False
        self.sort_steps.clear()
        self.show_sort_menu = False
        self.lcd.update_status("SYSTEM RESET")
        self.action_load_containers()

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

    def reset_container_states(self):
        for c in self.visual_containers:
            if c.state != 'sorted':
                c.set_state('idle')

    def on_reorder_complete(self, indices, values):
        value_map = {c.value: c for c in self.visual_containers}
        reordered_visual_slice = [value_map[v] for v in values]
        
        start, end = indices[0], indices[-1]
        self.visual_containers[start : end + 1] = reordered_visual_slice
        self.process_next_step()

    def process_next_step(self):
        if not self.sort_steps or not self.is_sorting:
            self.is_sorting = False
            self.lcd.update_status("SORT COMPLETE")
            self.reset_container_states()
            return
            
        step = self.sort_steps.pop(0)
        self.reset_container_states()
        
        step_type = step.get("type")
        
        if step_type == "compare":
            idx1, idx2 = step["indices"]
            c1 = self.visual_containers[idx1]
            c2 = self.visual_containers[idx2]
            c1.set_state('comparing')
            c2.set_state('comparing')
            target_crane_x = (c1.rect.centerx + c2.rect.centerx) / 2
            self.gantry_crane.move_to(target_crane_x, self.process_next_step)
            
        elif step_type == "swap":
            idx1, idx2 = step["indices"]
            c1 = self.visual_containers[idx1]
            c2 = self.visual_containers[idx2]
            
            self.visual_containers[idx1], self.visual_containers[idx2] = c2, c1
            
            pos1_x = self.slot_positions[idx1]
            pos2_x = self.slot_positions[idx2]
            
            c1.move_to((pos2_x, c1.pos_y))
            c2.move_to((pos1_x, c2.pos_y), self.process_next_step)
            
        elif step_type in ["lock", "set_pivot", "highlight"]:
            state = {
                "lock": "sorted",
                "set_pivot": "pivot",
                "highlight": "highlight"
            }[step_type]
            
            indices = step.get("indices", [step.get("index")])
            for idx in indices:
                if 0 <= idx < len(self.visual_containers):
                    self.visual_containers[idx].set_state(state)
            self.process_next_step()
            
        elif step_type == "reorder":
            indices = step["indices"]
            values = step["values"]
            
            value_map = {c.value: c for c in self.visual_containers}
            
            callback = lambda: self.on_reorder_complete(indices, values)
            
            for i, idx in enumerate(indices):
                cb = callback if i == len(indices) - 1 else None
                target_x = self.slot_positions[idx]
                sprite_to_move = value_map[values[i]]
                sprite_to_move.move_to((target_x, self.FLOOR_Y), cb)
                
        elif step_type == "lock_all":
            for c in self.visual_containers:
                c.set_state('sorted')
            self.process_next_step()

    def handle_events(self, event):
        if self.show_sort_menu:
            for btn in self.sort_menu_buttons:
                btn.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if not any(btn.rect.collidepoint(event.pos) for btn in self.sort_menu_buttons):
                    self.show_sort_menu = False
            return
            
        self.lcd.handle_event(event)
        self.btn_reset.handle_event(event)
        self.btn_speed_up.handle_event(event)
        self.btn_speed_down.handle_event(event)
        
        if not self.is_sorting:
            self.btn_load.handle_event(event)
            self.btn_sort.handle_event(event)

    def update(self):
        if self.show_sort_menu: return
        self.all_sprites.update(self.speed_multiplier)
        self.lcd.update()

    def draw_sort_menu(self):
        overlay = pygame.Surface((self.SIM_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        font_title = pygame.font.SysFont("Impact", 30)
        title_surf = font_title.render("SELECT SORTING ALGORITHM", True, WHITE)
        self.screen.blit(title_surf, (self.SIM_WIDTH//2 - title_surf.get_width()//2, 140))
        
        for btn in self.sort_menu_buttons:
            btn.draw(self.screen)

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.all_sprites.draw(self.screen)
        
        font = pygame.font.SysFont("Arial", 10, bold=True)
        for container in self.containers:
            text_surf = font.render(str(container.value), True, BLACK)
            padding = 3
            label_size = (text_surf.get_width() + padding * 2, text_surf.get_height() + padding * 2)
            label_surf = pygame.Surface(label_size)
            label_surf.fill(WHITE)
            pygame.draw.rect(label_surf, BLACK, label_surf.get_rect(), 1)
            label_surf.blit(text_surf, (padding, padding))
            
            visible_body_rect = pygame.Rect(
                container.rect.left + container.container_body_rect.left,
                container.rect.top + container.container_body_rect.top,
                container.container_body_rect.width,
                container.container_body_rect.height
            )
            
            label_rect = label_surf.get_rect(midbottom=visible_body_rect.midtop, y=visible_body_rect.top - 15)
            self.screen.blit(label_surf, label_rect)
            
        self.chassis.draw(self.screen)
        self.lcd.draw(self.screen)
        self.btn_load.draw(self.screen)
        self.btn_sort.draw(self.screen)
        self.btn_reset.draw(self.screen)
        self.btn_speed_up.draw(self.screen)
        self.btn_speed_down.draw(self.screen)
        
        if self.show_sort_menu:
            self.draw_sort_menu()