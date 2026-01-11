import pygame
import math
import random
from settings import *
from core.sprites import CrateSprite
from core.ui import HandheldChassis, LCDDisplay, RoundButton, Button

class BSTNode:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None
        self.x = 0; self.y = 0
        self.target_x = 0; self.target_y = 0
        self.push_arm_state = 'idle'
        self.push_arm_timer = 0
class BSTManager:
    def __init__(self):
        self.root = None
        self.nodes_count = 0
        self.max_allowed_depth = 5
        self.current_depth = 0
    def insert(self, value):
        if self.root is None:
            self.root = BSTNode(value)
            self.nodes_count += 1
            self.current_depth = 0
            return {"type": "ROOT", "node": self.root}
        current = self.root
        depth = 0
        path_nodes = []
        while True:
            path_nodes.append(current)
            if depth >= self.max_allowed_depth:
                return {"type": "ERROR", "message": "MAX DEPTH"}
            if value <= current.value:
                if current.left is None:
                    current.left = BSTNode(value)
                    self.nodes_count += 1
                    self.current_depth = max(self.current_depth, depth + 1)
                    return {
                        "type": "INSERT", "node": current.left, "parent": current,
                        "direction": "LEFT", "path_nodes": path_nodes
                    }
                current = current.left
            else:
                if current.right is None:
                    current.right = BSTNode(value)
                    self.nodes_count += 1
                    self.current_depth = max(self.current_depth, depth + 1)
                    return {
                        "type": "INSERT", "node": current.right, "parent": current,
                        "direction": "RIGHT", "path_nodes": path_nodes
                    }
                current = current.right
            depth += 1
    def clear(self):
        self.root = None
        self.nodes_count = 0
        self.current_depth = 0
    def in_order(self):
        result = []
        self._in_order_recursive(self.root, result)
        return result
    def _in_order_recursive(self, node, result):
        if node:
            self._in_order_recursive(node.left, result)
            result.append(node)
            self._in_order_recursive(node.right, result)
    def pre_order(self):
        result = []
        self._pre_order_recursive(self.root, result)
        return result
    def _pre_order_recursive(self, node, result):
        if node:
            result.append(node)
            self._pre_order_recursive(node.left, result)
            self._pre_order_recursive(node.right, result)
    def post_order(self):
        result = []
        self._post_order_recursive(self.root, result)
        return result
    def _post_order_recursive(self, node, result):
        if node:
            self._post_order_recursive(node.left, result)
            self._post_order_recursive(node.right, result)
            result.append(node)
class PackageSprite(pygame.sprite.Sprite):
    def __init__(self, start_x, start_y, value, size=30):
        super().__init__()
        self.value = value
        self.pos_x = float(start_x)
        self.pos_y = float(start_y)
        self.target_node = None
        self.path_queue = []
        self.final_callback = None
        self.is_moving = False
        self.image = None
        self.current_size = 0
        self.attached_node = None
        self.resize(size)
        self.rect = self.image.get_rect(center=(start_x, start_y))
    def resize(self, size):
        s = int(size)
        if s < 10: s = 10
        if abs(s - self.current_size) < 1 and self.image is not None:
            return
        self.current_size = s
        self.image = pygame.Surface((s, s), pygame.SRCALPHA)
        shadow_rect = pygame.Rect(2, 2, s, s)
        pygame.draw.rect(self.image, (0,0,0,80), shadow_rect, border_radius=3)
        main_rect = pygame.Rect(0, 0, s, s)
        pygame.draw.rect(self.image, BOX_COLOR_1, main_rect, border_radius=3)
        pygame.draw.rect(self.image, (50, 30, 10, 150), main_rect, 2, border_radius=3)
        half = s // 2
        tape_w = max(1, int(s * 0.15))
        pygame.draw.line(self.image, BOX_TAPE, (half, 0), (half, s), tape_w)
        pygame.draw.line(self.image, BOX_TAPE, (0, half), (s, half), tape_w)
        self.rect = self.image.get_rect(center=(int(self.pos_x), int(self.pos_y)))
    def add_path(self, nodes):
        self.path_queue.extend(nodes)
        if not self.is_moving and self.path_queue:
            self._start_next_leg()
    def _start_next_leg(self):
        if not self.path_queue: return
        self.target_node = self.path_queue.pop(0)
        self.is_moving = True
    def update(self):
        if self.attached_node:
            self.pos_x = self.attached_node.x
            self.pos_y = self.attached_node.y
            self.rect.center = (int(self.pos_x), int(self.pos_y))
            return
        if not self.is_moving or not self.target_node: return
        tx, ty = self.target_node.x, self.target_node.y
        dx = tx - self.pos_x
        dy = ty - self.pos_y
        dist = math.sqrt(dx**2 + dy**2)
        if dist < MIN_SPEED:
            self.pos_x, self.pos_y = tx, ty
            if self.path_queue:
                if self.target_node.left or self.target_node.right:
                    next_node = self.path_queue[0]
                    if next_node.value <= self.target_node.value:
                        self.target_node.push_arm_state = 'left'
                    else:
                        self.target_node.push_arm_state = 'right'
                    self.target_node.push_arm_timer = 15
                self._start_next_leg()
            else:
                self.is_moving = False
                self.attached_node = self.target_node
                self.target_node = None
                if self.final_callback:
                    cb = self.final_callback
                    self.final_callback = None
                    cb()
        else:
            self.pos_x += dx * LERP_FACTOR
            self.pos_y += dy * LERP_FACTOR
        self.rect.center = (int(self.pos_x), int(self.pos_y))
class DroneSprite(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.pos_x = float(x); self.pos_y = float(y)
        self.target_x = float(x); self.target_y = float(y)
        self.is_moving = False; self.on_finish_callback = None
        self.rotor_angle = 0
        self.current_size = 0
        self.original_image = None
        self.rotor_image = None
        self.image = pygame.Surface((1,1))
        self.rect = self.image.get_rect(center=(x,y))
        self.resize(40)
    def resize(self, size):
        s = int(size)
        if s < 15: s = 15
        if self.current_size == s: return
        self.current_size = s
        self.original_image = pygame.Surface((s, s), pygame.SRCALPHA)
        center = s // 2
        chassis_radius = s * 0.25
        arm_length = s * 0.5
        rotor_radius = s * 0.12
        arm_color = (80, 85, 90)
        pygame.draw.line(self.original_image, arm_color, (center, center), (center - arm_length, center - arm_length), 3)
        pygame.draw.line(self.original_image, arm_color, (center, center), (center + arm_length, center - arm_length), 3)
        pygame.draw.line(self.original_image, arm_color, (center, center), (center - arm_length, center + arm_length), 3)
        pygame.draw.line(self.original_image, arm_color, (center, center), (center + arm_length, center + arm_length), 3)
        pod_color = (50, 55, 60)
        pygame.draw.circle(self.original_image, pod_color, (center - arm_length, center - arm_length), rotor_radius)
        pygame.draw.circle(self.original_image, pod_color, (center + arm_length, center - arm_length), rotor_radius)
        pygame.draw.circle(self.original_image, pod_color, (center - arm_length, center + arm_length), rotor_radius)
        pygame.draw.circle(self.original_image, pod_color, (center + arm_length, center + arm_length), rotor_radius)
        pygame.draw.circle(self.original_image, (0,0,0,80), (center+2, center+2), chassis_radius)
        pygame.draw.circle(self.original_image, (180,185,190), (center, center), chassis_radius)
        pygame.draw.circle(self.original_image, (100,105,110), (center, center), chassis_radius, 1)
        pygame.draw.circle(self.original_image, (255, 80, 80), (center, center), chassis_radius * 0.5)
        pygame.draw.circle(self.original_image, (255, 150, 150), (center-1, center-1), chassis_radius * 0.2)
        self.rotor_image = pygame.Surface((s,s), pygame.SRCALPHA)
        blade_color = (50,55,60,180)
        blade_length = rotor_radius * 1.5
        for angle in [45, 135, 225, 315]:
            rad = math.radians(angle)
            end_x = center + math.cos(rad) * arm_length
            end_y = center + math.sin(rad) * arm_length
            pygame.draw.line(self.rotor_image, blade_color, (end_x - blade_length, end_y), (end_x + blade_length, end_y), 2)
    def move_to(self, target_pos, callback=None):
        self.target_x, self.target_y = target_pos
        self.on_finish_callback = callback
        self.is_moving = True
    def update(self):
        self.rotor_angle = (self.rotor_angle + 45) % 360
        if self.is_moving:
            dx = self.target_x - self.pos_x; dy = self.target_y - self.pos_y
            dist = math.sqrt(dx**2 + dy**2)
            if dist < 3.0:
                self.pos_x, self.pos_y = self.target_x, self.target_y
                self.is_moving = False
                if self.on_finish_callback:
                    cb = self.on_finish_callback; self.on_finish_callback = None; cb()
            else:
                self.pos_x += dx * 0.15; self.pos_y += dy * 0.15
        self.image = self.original_image.copy()
        rotated_rotors = pygame.transform.rotate(self.rotor_image, self.rotor_angle)
        rotor_rect = rotated_rotors.get_rect(center=self.image.get_rect().center)
        self.image.blit(rotated_rotors, rotor_rect)
        self.rect = self.image.get_rect(center=(int(self.pos_x), int(self.pos_y)))
class RouterTreeSimulation:
    def __init__(self, screen):
        self.screen = screen
        self.logic = BSTManager()
        self.packages_group = pygame.sprite.Group()
        self.drone = DroneSprite(-50, -50)
        self.drone_group = pygame.sprite.GroupSingle(self.drone)
        self.ui_x = 750; self.ui_w = 250
        self.chassis = HandheldChassis(self.ui_x + 10, 20, self.ui_w - 20, SCREEN_HEIGHT - 40)
        self.lcd = LCDDisplay(self.ui_x + 35, 80, self.ui_w - 70, 100)
        self.lcd.update_status("ROUTING SYSTEM")
        btn_cx = self.ui_x + self.ui_w // 2
        self.btn_insert = RoundButton(btn_cx, 280, 45, BTN_GREEN_BASE, BTN_GREEN_LIGHT, "INJECT", self.action_insert)
        self.btn_reset = RoundButton(btn_cx, 390, 45, BTN_RED_BASE, BTN_RED_LIGHT, "CLEAR", self.action_reset)
        self.btn_scan = RoundButton(btn_cx, 500, 45, BTN_BLUE_BASE, BTN_BLUE_LIGHT, "TRAVERSE", self.action_open_traversal_menu)
        self.is_animating = False
        self.SIM_WIDTH = 750; self.TOP_MARGIN = 120; self.BOTTOM_MARGIN = 50
        self.ROOT_X = self.SIM_WIDTH // 2
        self.target_node_size = 80; self.current_node_size = 80; self.belt_offset = 0
        self.bg_surface = self._generate_background()
        self.show_traversal_menu = False; self.traversal_result_data = None; self.pending_report_data = None
        menu_btn_w, menu_btn_h = 200, 40; menu_cx = self.SIM_WIDTH // 2; menu_start_y = 250
        self.menu_btn_in = Button(menu_cx - menu_btn_w//2, menu_start_y, menu_btn_w, menu_btn_h, "In-Order Traversal", lambda: self.action_traverse("IN"))
        self.menu_btn_pre = Button(menu_cx - menu_btn_w//2, menu_start_y + 50, menu_btn_w, menu_btn_h, "Pre-Order Traversal", lambda: self.action_traverse("PRE"))
        self.menu_btn_post = Button(menu_cx - menu_btn_w//2, menu_start_y + 100, menu_btn_w, menu_btn_h, "Post-Order Traversal", lambda: self.action_traverse("POST"))
        self.is_traversing = False; self.traversal_path = []; self.traversal_index = 0
        self.highlighted_node = None; self.highlight_timer = 0

    def _generate_background(self):
        # --- CHANGE: Draw across the full SCREEN_WIDTH ---
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg.fill(WALL_BASE_COLOR)
        
        # Far background shelves
        self._draw_shelf_unit(bg, 0, 100, SCREEN_WIDTH, SCREEN_HEIGHT / 2, 8, 25)
        
        # Pillars for depth
        for i in range(7):
            self._draw_pillar(bg, 50 + i * 150, 0, 20, SCREEN_HEIGHT)

        # Floor
        floor_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        floor_surf.set_colorkey((0,0,0)) # Make black transparent
        for _ in range(15000):
            color = random.choice([CONCRETE_NOISE_1, CONCRETE_NOISE_2])
            floor_surf.set_at((random.randint(0, SCREEN_WIDTH - 1), random.randint(0, SCREEN_HEIGHT - 1)), color)
        bg.blit(floor_surf, (0, 0))
        
        # Ceiling and lights
        pygame.draw.rect(bg, (40,45,50), (0,0,SCREEN_WIDTH, 80))
        light_fixtures = []
        for i in range(0, SCREEN_WIDTH, 150):
            pygame.draw.rect(bg, (20,22,25), (i, 30, 100, 10))
            pygame.draw.rect(bg, FLUORESCENT_LIGHT, (i+2, 32, 96, 6))
            light_fixtures.append((i+50, 40))

        # Bay Door
        door_w, door_h = 150, 30; door_x = self.SIM_WIDTH // 2 - door_w // 2
        pygame.draw.rect(bg, (40,40,40), (door_x, 0, door_w, door_h))
        for i in range(0, door_w, 15):
            pygame.draw.line(bg, (60,60,60), (door_x + i, 0), (door_x + i, door_h), 1)
        pygame.draw.rect(bg, STRIPE_YELLOW, (door_x, 0, door_w, door_h), 3)

        # Lighting overlay for atmosphere
        light_layer = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for lx, ly in light_fixtures:
            points = [(lx - 30, ly), (lx + 30, ly), (lx + 100, SCREEN_HEIGHT), (lx - 100, SCREEN_HEIGHT)]
            pygame.draw.polygon(light_layer, LIGHT_RAY_COLOR, points)
        bg.blit(light_layer, (0,0))
        return bg

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

    def _recalculate_layout(self, node, x, y, level, width_spread):
        if node is None: return
        node.target_x = x; node.target_y = y
        depth = self.logic.current_depth
        level_height = (SCREEN_HEIGHT - self.TOP_MARGIN - self.BOTTOM_MARGIN) / max(1, depth) if depth > 0 else 0
        next_spread = width_spread / 2
        self._recalculate_layout(node.left, x - next_spread, y + level_height, level + 1, next_spread)
        self._recalculate_layout(node.right, x + next_spread, y + level_height, level + 1, next_spread)
    def _update_node_positions(self, node):
        if node is None: return
        dx = node.target_x - node.x; dy = node.target_y - node.y
        if abs(dx) > 0.1 or abs(dy) > 0.1:
            node.x += dx * 0.1; node.y += dy * 0.1
        else:
            node.x, node.y = node.target_x, node.target_y
        if node.push_arm_timer > 0:
            node.push_arm_timer -= 1
            if node.push_arm_timer == 0:
                node.push_arm_state = 'idle'
        self._update_node_positions(node.left); self._update_node_positions(node.right)
    def draw_conveyor_line(self, start, end):
        dist = math.hypot(end[0]-start[0], end[1]-start[1])
        if dist == 0: return
        angle = math.atan2(end[1]-start[1], end[0]-start[0]); perp_angle = angle + math.pi / 2
        w = self.current_node_size * 0.4
        dx, dy = math.cos(perp_angle) * w/2, math.sin(perp_angle) * w/2
        points = [(start[0] - dx, start[1] - dy), (start[0] + dx, start[1] + dy),
                  (end[0] + dx, end[1] + dy), (end[0] - dx, end[1] - dy)]
        pygame.draw.polygon(self.screen, (40,40,45), points)
        num_stripes = int(dist / 20)
        if num_stripes > 0:
            for i in range(num_stripes + 2):
                t = (i - self.belt_offset / 20) / num_stripes
                if 0 <= t <= 1:
                    px1 = start[0] + (end[0]-start[0]) * t; py1 = start[1] + (end[1]-start[1]) * t
                    pygame.draw.line(self.screen, (60,60,65), (px1 - dx, py1 - dy), (px1 + dx, py1 + dy), 2)
        pygame.draw.line(self.screen, (90,95,100), points[0], points[3], 5)
        pygame.draw.line(self.screen, (90,95,100), points[1], points[2], 5)
    def draw_tree_nodes_and_labels(self, node):
        if node is None: return
        if node.left:
            self.draw_conveyor_line((node.x, node.y), (node.left.x, node.left.y)); self.draw_tree_nodes_and_labels(node.left)
        if node.right:
            self.draw_conveyor_line((node.x, node.y), (node.right.x, node.right.y)); self.draw_tree_nodes_and_labels(node.right)
        s = int(self.current_node_size); rect = pygame.Rect(0, 0, s, s); rect.center = (node.x, node.y)
        base_rect = rect.inflate(s*0.2, s*0.2)
        pygame.draw.rect(self.screen, (30,30,35), base_rect.move(3,3), border_radius=5)
        pygame.draw.rect(self.screen, (80,85,90), base_rect, border_radius=5)
        arm_w, arm_h = s * 0.8, s * 0.2; arm_rect = pygame.Rect(0,0, arm_w, arm_h); arm_rect.centery = base_rect.centery
        if node.push_arm_state == 'left': arm_rect.right = base_rect.centerx - 5
        elif node.push_arm_state == 'right': arm_rect.left = base_rect.centerx + 5
        else: arm_rect.centerx = base_rect.centerx
        pygame.draw.rect(self.screen, (255, 200, 0), arm_rect); pygame.draw.rect(self.screen, (180, 140, 0), arm_rect, 2)
        pygame.draw.rect(self.screen, (150,155,160), rect, border_radius=3)
        if self.highlighted_node == node and self.highlight_timer > 0:
            pygame.draw.rect(self.screen, (255, 255, 0), base_rect, 3, border_radius=5)
        font_size = max(14, int(s * 0.5)); font = pygame.font.SysFont("Impact", font_size)
        txt = font.render(str(node.value), True, (20, 20, 20))
        self.screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))
    def action_insert(self):
        if self.is_animating or self.is_traversing: return
        text = self.lcd.text
        if not text.isdigit(): self.lcd.update_status("ERR: INTEGERS ONLY"); return
        val = int(text)
        if val > 999: self.lcd.update_status("ERR: MAX 999"); return
        receipt = self.logic.insert(val)
        if receipt['type'] == 'ERROR': self.lcd.update_status(f"ERR: {receipt['message']}"); return
        self.lcd.update_status(f"ROUTING: {val}"); self.lcd.text = ""
        self.is_animating = True
        if receipt['type'] != 'ROOT':
            new_node = receipt['node']; parent = receipt['parent']
            new_node.x, new_node.y = parent.x, parent.y
        pkg = PackageSprite(self.ROOT_X, 40, val, size=self.current_node_size * 0.7)
        self.packages_group.add(pkg)
        hopper_node = BSTNode(0); hopper_node.x = self.ROOT_X; hopper_node.y = self.TOP_MARGIN
        path_nodes = [hopper_node]
        if receipt['type'] != 'ROOT':
            path_nodes.extend(receipt['path_nodes']); path_nodes.append(receipt['node'])
        pkg.final_callback = self.on_animation_complete; pkg.add_path(path_nodes)
    def action_reset(self):
        if self.is_traversing: return
        self.logic.clear(); self.packages_group.empty()
        self.drone.move_to((-50, -50))
        self.is_animating = False; self.lcd.update_status("SYSTEM FLUSHED")
    def on_animation_complete(self):
        self.is_animating = False; self.lcd.update_status("READY")
    def action_open_traversal_menu(self):
        if self.is_animating or self.is_traversing or not self.logic.root: return
        self.show_traversal_menu = True
    def action_traverse(self, order_type):
        self.show_traversal_menu = False
        path = []; title = ""
        if order_type == "IN": path = self.logic.in_order(); title = "IN-ORDER SCAN MANIFEST"
        elif order_type == "PRE": path = self.logic.pre_order(); title = "PRE-ORDER SCAN MANIFEST"
        elif order_type == "POST": path = self.logic.post_order(); title = "POST-ORDER SCAN MANIFEST"
        self.traversal_path = path
        self.pending_report_data = {"title": title, "path": " ".join([str(node.value) for node in path])}
        self.is_traversing = True; self.traversal_index = 0
        self.drone.pos_x, self.drone.pos_y = self.ROOT_X, 20
        self.lcd.update_status("SCANNING..."); self.process_next_traversal_step()
    def process_next_traversal_step(self):
        if self.traversal_index >= len(self.traversal_path):
            self.on_traversal_complete(); return
        node_to_visit = self.traversal_path[self.traversal_index]
        self.drone.move_to((node_to_visit.x, node_to_visit.y), callback=self.on_drone_arrival)
    def on_drone_arrival(self):
        node = self.traversal_path[self.traversal_index]
        self.highlighted_node = node; self.highlight_timer = 20
        self.traversal_index += 1; self.process_next_traversal_step()
    def on_traversal_complete(self):
        self.is_traversing = False; self.traversal_path = []; self.traversal_index = 0
        self.drone.move_to((-50, -50)); self.lcd.update_status("SCAN COMPLETE")
        self.traversal_result_data = self.pending_report_data; self.pending_report_data = None
    def handle_events(self, event):
        if self.show_traversal_menu:
            self.menu_btn_in.handle_event(event); self.menu_btn_pre.handle_event(event); self.menu_btn_post.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN and not (self.menu_btn_in.is_hovered or self.menu_btn_pre.is_hovered or self.menu_btn_post.is_hovered):
                self.show_traversal_menu = False
            return
        if self.traversal_result_data and not self.is_traversing:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.traversal_result_data = None; self.lcd.update_status("READY")
            return
        self.lcd.handle_event(event); self.btn_insert.handle_event(event)
        self.btn_reset.handle_event(event); self.btn_scan.handle_event(event)
    def update(self):
        if self.show_traversal_menu: return
        self.belt_offset = (self.belt_offset + 1) % 20
        if self.highlight_timer > 0:
            self.highlight_timer -= 1
            if self.highlight_timer == 0: self.highlighted_node = None
        depth = self.logic.current_depth
        slot_width = self.SIM_WIDTH / max(1, 2 ** depth)
        target_node_size = int(slot_width * 0.50)
        if target_node_size > 80: target_node_size = 80
        if target_node_size < 20: target_node_size = 20
        size_diff = target_node_size - self.current_node_size
        if abs(size_diff) > 0.1: self.current_node_size += size_diff * 0.1
        else: self.current_node_size = target_node_size
        initial_spread = self.SIM_WIDTH / 2
        self._recalculate_layout(self.logic.root, self.ROOT_X, self.TOP_MARGIN, 0, initial_spread)
        self._update_node_positions(self.logic.root)
        current_pkg_size = self.current_node_size * 0.8
        for pkg in self.packages_group:
            pkg.resize(current_pkg_size)
        self.drone.resize(self.current_node_size * 0.8)
        self.packages_group.update()
        self.drone_group.update()
        self.lcd.update()
    def draw_traversal_menu(self):
        overlay = pygame.Surface((self.SIM_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        font_title = pygame.font.SysFont("Impact", 30)
        title_surf = font_title.render("SELECT TRAVERSAL METHOD", True, WHITE)
        self.screen.blit(title_surf, (self.SIM_WIDTH//2 - title_surf.get_width()//2, 180))
        self.menu_btn_in.draw(self.screen); self.menu_btn_pre.draw(self.screen); self.menu_btn_post.draw(self.screen)
    def draw_traversal_result(self):
        overlay = pygame.Surface((self.SIM_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        w, h = 500, 220; x, y = (self.SIM_WIDTH - w) // 2, (SCREEN_HEIGHT - h) // 2
        pygame.draw.rect(self.screen, (0,0,0,80), (x+5, y+5, w, h), border_radius=3)
        pygame.draw.rect(self.screen, (230, 230, 220), (x, y, w, h), border_radius=3)
        pygame.draw.rect(self.screen, (100,100,100), (x,y,w,h), 1, border_radius=3)
        font_header = pygame.font.SysFont("Courier New", 18, bold=True)
        header_surf = font_header.render(self.traversal_result_data["title"], True, (30,30,30))
        self.screen.blit(header_surf, (x + w//2 - header_surf.get_width()//2, y + 20))
        pygame.draw.line(self.screen, (180,180,170), (x+20, y+50), (x+w-20, y+50), 1)
        font_result = pygame.font.SysFont("Consolas", 24, bold=True)
        words = self.traversal_result_data["path"].split(' ')
        lines = []; current_line = ""
        for word in words:
            test_line = current_line + word + " "
            if font_result.size(test_line)[0] < w - 40:
                current_line = test_line
            else:
                lines.append(current_line); current_line = word + " "
        lines.append(current_line)
        line_y = y + 80
        for line in lines:
            result_surf = font_result.render(line, True, (20, 20, 20))
            self.screen.blit(result_surf, (x + 20, line_y)); line_y += 30
        if not self.is_traversing:
            font_prompt = pygame.font.SysFont("Arial", 12)
            prompt_surf = font_prompt.render("Click anywhere to dismiss", True, (100, 100, 100))
            self.screen.blit(prompt_surf, (x + w - prompt_surf.get_width() - 10, y + h - prompt_surf.get_height() - 10))
    def draw(self):
        self.screen.blit(self.bg_surface, (0, 0))
        self.draw_tree_nodes_and_labels(self.logic.root)
        self.packages_group.draw(self.screen)
        for pkg in self.packages_group:
            font_size = max(12, int(pkg.current_size * 0.5))
            font = pygame.font.SysFont("Arial", font_size, bold=True)
            shadow = font.render(str(pkg.value), True, (0,0,0,100))
            self.screen.blit(shadow, (pkg.rect.centerx - shadow.get_width()//2 + 1, pkg.rect.centery - shadow.get_height()//2 + 1))
            label = font.render(str(pkg.value), True, (255, 255, 255))
            self.screen.blit(label, (pkg.rect.centerx - label.get_width()//2, pkg.rect.centery - label.get_height()//2))
        self.drone_group.draw(self.screen)
        self.chassis.draw(self.screen); self.lcd.draw(self.screen)
        self.btn_insert.draw(self.screen); self.btn_reset.draw(self.screen); self.btn_scan.draw(self.screen)
        if self.show_traversal_menu: self.draw_traversal_menu()
        elif self.traversal_result_data: self.draw_traversal_result()