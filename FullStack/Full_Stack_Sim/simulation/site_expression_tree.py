import pygame
import math
import random
from settings import *
from core.ui import HandheldChassis, LCDDisplay, RoundButton, Button
class Node:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None
        self.x = 0; self.y = 0
        self.target_x = 0; self.target_y = 0
class ExpressionTreeManager:
    def __init__(self):
        self.root = None
        self.current_depth = 0
        self.precedence = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3}
    def _is_operator(self, char):
        return char in "+-*/^"
    def _infix_to_postfix(self, expression):
        stack = []; output = []
        for char in expression:
            if char.isalnum():
                output.append(char)
            elif char == '(':
                stack.append(char)
            elif char == ')':
                while stack and stack[-1] != '(':
                    output.append(stack.pop())
                if stack and stack[-1] == '(':
                    stack.pop()
            elif self._is_operator(char):
                while (stack and self._is_operator(stack[-1])):
                    p_stack = self.precedence.get(stack[-1], 0)
                    p_char = self.precedence.get(char, 0)
                    is_right_assoc = char == '^'
                    if (p_stack > p_char) or (p_stack == p_char and not is_right_assoc):
                        output.append(stack.pop())
                    else:
                        break
                stack.append(char)
        while stack:
            output.append(stack.pop())
        return output
    def build_from_expression(self, expression):
        expression = "".join(filter(lambda x: not x.isspace(), expression))
        if not expression: return False
        try:
            postfix = self._infix_to_postfix(expression)
            stack = []
            for char in postfix:
                if char.isalnum():
                    stack.append(Node(char))
                elif self._is_operator(char):
                    if len(stack) < 2: return False
                    node = Node(char)
                    node.right = stack.pop()
                    node.left = stack.pop()
                    stack.append(node)
            if len(stack) != 1: return False
            self.root = stack[0]
            self.current_depth = 0
            self._calculate_depth(self.root, 0)
            return True
        except (IndexError, Exception):
            return False
    def _get_label_from_index(self, n):
        label = ""
        if n < 0: return ""
        while True:
            label = chr(n % 26 + ord('A')) + label
            n = n // 26 - 1
            if n < 0:
                break
        return label
    def build_from_levels(self, num_levels):
        if not 1 <= num_levels <= 5: return False
        node_index = 0
        self.root = Node(self._get_label_from_index(node_index))
        node_index += 1
        queue = [self.root]
        for level in range(num_levels - 1):
            for _ in range(len(queue)):
                current = queue.pop(0)
                current.left = Node(self._get_label_from_index(node_index))
                node_index += 1
                queue.append(current.left)
                current.right = Node(self._get_label_from_index(node_index))
                node_index += 1
                queue.append(current.right)
        self.current_depth = num_levels - 1
        return True
    def _calculate_depth(self, node, depth):
        if node is None: return
        self.current_depth = max(self.current_depth, depth)
        self._calculate_depth(node.left, depth + 1)
        self._calculate_depth(node.right, depth + 1)
    def get_traversals(self):
        return {
            "TLR": self._get_pre_order(self.root),
            "LTR": self._get_in_order(self.root),
            "LRT": self._get_post_order(self.root)
        }
    def _get_pre_order(self, node):
        if not node: return []
        return [node] + self._get_pre_order(node.left) + self._get_pre_order(node.right)
    def _get_in_order(self, node):
        if not node: return []
        return self._get_in_order(node.left) + [node] + self._get_in_order(node.right)
    def _get_post_order(self, node):
        if not node: return []
        return self._get_post_order(node.left) + self._get_post_order(node.right) + [node]
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
class ExpressionTreeSimulation:
    def __init__(self, screen):
        self.screen = screen
        self.logic = ExpressionTreeManager()
        self.all_sprites = pygame.sprite.Group()
        self.ui_x = 750; self.ui_w = 250
        self.chassis = HandheldChassis(self.ui_x + 10, 20, self.ui_w - 20, SCREEN_HEIGHT - 40)
        self.lcd = LCDDisplay(self.ui_x + 35, 80, self.ui_w - 70, 100)
        self.lcd.update_status("EXPRESSION PARSER")
        btn_cx = self.ui_x + self.ui_w // 2
        gen_y = 280; btn_radius = 40; h_gap = 15
        self.btn_gen_levels = RoundButton(btn_cx - btn_radius - h_gap, gen_y, btn_radius, BTN_GREEN_BASE, BTN_GREEN_LIGHT, "LEVELS", self.action_gen_levels)
        self.btn_gen_expr = RoundButton(btn_cx + btn_radius + h_gap, gen_y, btn_radius, BTN_ALT_GREEN_BASE, BTN_ALT_GREEN_LIGHT, "EXPR", self.action_gen_expr)
        self.btn_analyze = RoundButton(btn_cx, 390, 40, BTN_BLUE_BASE, BTN_BLUE_LIGHT, "TRAVERSE", self.action_open_analysis_menu)
        self.btn_clear = RoundButton(btn_cx, 490, 40, BTN_RED_BASE, BTN_RED_LIGHT, "CLEAR", self.action_clear)
        self.SIM_WIDTH = 750; self.TOP_MARGIN = 120; self.BOTTOM_MARGIN = 50
        self.ROOT_X = self.SIM_WIDTH // 2; self.current_node_size = 80; self.belt_offset = 0
        self.show_analysis_menu = False; self.manifest_data = None; self.pending_report_data = None
        menu_btn_w, menu_btn_h = 200, 40; menu_cx = self.SIM_WIDTH // 2; menu_start_y = 250
        self.menu_btn_tlr = Button(menu_cx - menu_btn_w//2, menu_start_y, menu_btn_w, menu_btn_h, "TLR (Pre-Order)", lambda: self.action_traverse("TLR"))
        self.menu_btn_ltr = Button(menu_cx - menu_btn_w//2, menu_start_y + 50, menu_btn_w, menu_btn_h, "LTR (In-Order)", lambda: self.action_traverse("LTR"))
        self.menu_btn_lrt = Button(menu_cx - menu_btn_w//2, menu_start_y + 100, menu_btn_w, menu_btn_h, "LRT (Post-Order)", lambda: self.action_traverse("LRT"))
        self.is_traversing = False; self.traversal_path = []; self.traversal_index = 0
        self.highlighted_node = None; self.highlight_timer = 0
        self.drone = DroneSprite(-50, -50); self.all_sprites.add(self.drone)
        self.bg_surface = self._generate_background()

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
    def draw_tree(self, node):
        if node is None: return
        if node.left:
            self.draw_conveyor_line((node.x, node.y), (node.left.x, node.left.y)); self.draw_tree(node.left)
        if node.right:
            self.draw_conveyor_line((node.x, node.y), (node.right.x, node.right.y)); self.draw_tree(node.right)
        s = int(self.current_node_size); rect = pygame.Rect(0, 0, s, s); rect.center = (node.x, node.y)
        pygame.draw.rect(self.screen, (30,30,35), rect.move(3,3), border_radius=5)
        pygame.draw.rect(self.screen, (80,85,90), rect, border_radius=5)
        is_op = not node.value.isalnum()
        screen_color = (255, 200, 0) if is_op else (150,155,160)
        pygame.draw.rect(self.screen, screen_color, rect.inflate(-10, -10), border_radius=3)
        if self.highlighted_node == node and self.highlight_timer > 0:
            pygame.draw.rect(self.screen, (50, 255, 200), rect, 3, border_radius=5)
        font_size = max(14, int(s * 0.5)); font = pygame.font.SysFont("Impact", font_size)
        txt = font.render(str(node.value), True, (20, 20, 20))
        self.screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))
    def action_gen_levels(self):
        text = self.lcd.text
        if not text.isdigit() or not (1 <= int(text) <= 5):
            self.lcd.update_status("ERR: LVL 1-5 ONLY"); return
        if self.logic.build_from_levels(int(text)):
            self.manifest_data = None; self.lcd.update_status("TREE GENERATED"); self.lcd.text = ""
    def action_gen_expr(self):
        text = self.lcd.text.upper()
        if not text: self.lcd.update_status("ERR: NO INPUT"); return
        if self.logic.build_from_expression(text):
            self.manifest_data = None; self.lcd.update_status("EXPR PARSED"); self.lcd.text = ""
        else:
            self.lcd.update_status("ERR: INVALID EXPR")
    def action_clear(self):
        self.logic.root = None; self.manifest_data = None
        self.lcd.update_status("SYSTEM CLEARED"); self.lcd.text = ""
    def action_open_analysis_menu(self):
        if self.is_traversing or not self.logic.root: return
        self.show_analysis_menu = True
    def action_traverse(self, order_type):
        self.show_analysis_menu = False
        all_traversals = self.logic.get_traversals()
        self.traversal_path = all_traversals[order_type]
        self.pending_report_data = {
            "title": f"{order_type} (Post-Order)" if order_type == "LRT" else f"{order_type} (Pre-Order)" if order_type == "TLR" else f"{order_type} (In-Order)",
            "path": " ".join([node.value for node in self.traversal_path])
        }
        self.is_traversing = True; self.traversal_index = 0
        self.drone.pos_x, self.drone.pos_y = self.ROOT_X, 20
        self.lcd.update_status("ANALYZING..."); self.process_next_traversal_step()
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
        self.drone.move_to((-50, -50)); self.lcd.update_status("ANALYSIS DONE")
        self.manifest_data = self.pending_report_data; self.pending_report_data = None
    def handle_events(self, event):
        if self.show_analysis_menu:
            self.menu_btn_tlr.handle_event(event); self.menu_btn_ltr.handle_event(event); self.menu_btn_lrt.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN and not (self.menu_btn_tlr.is_hovered or self.menu_btn_ltr.is_hovered or self.menu_btn_lrt.is_hovered):
                self.show_analysis_menu = False
            return
        if self.manifest_data and not self.is_traversing:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.manifest_data = None; self.lcd.update_status("READY")
            return
        self.lcd.handle_event(event); self.btn_gen_levels.handle_event(event)
        self.btn_gen_expr.handle_event(event); self.btn_analyze.handle_event(event); self.btn_clear.handle_event(event)
    def update(self):
        if self.show_analysis_menu: return
        self.belt_offset = (self.belt_offset + 2) % 20
        if self.highlight_timer > 0:
            self.highlight_timer -= 1
            if self.highlight_timer == 0: self.highlighted_node = None
        if self.logic.root:
            depth = self.logic.current_depth
            slot_width = self.SIM_WIDTH / max(1, 2 ** depth)
            target_node_size = int(slot_width * 0.50)
            if target_node_size > 80: target_node_size = 80
            if target_node_size < 30: target_node_size = 30
            size_diff = target_node_size - self.current_node_size
            if abs(size_diff) > 0.1: self.current_node_size += size_diff * 0.1
            else: self.current_node_size = target_node_size
            self._recalculate_layout(self.logic.root, self.ROOT_X, self.TOP_MARGIN, 0, self.SIM_WIDTH / 2)
            self._update_node_positions(self.logic.root)
            self.drone.resize(self.current_node_size * 0.8)
        self.all_sprites.update(); self.lcd.update()
    def draw_analysis_menu(self):
        overlay = pygame.Surface((self.SIM_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        font_title = pygame.font.SysFont("Impact", 30)
        title_surf = font_title.render("SELECT ANALYSIS METHOD", True, WHITE)
        self.screen.blit(title_surf, (self.SIM_WIDTH//2 - title_surf.get_width()//2, 180))
        self.menu_btn_tlr.draw(self.screen); self.menu_btn_ltr.draw(self.screen); self.menu_btn_lrt.draw(self.screen)
    def draw_manifest(self):
        overlay = pygame.Surface((self.SIM_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        w, h = 500, 220; x, y = (self.SIM_WIDTH - w) // 2, (SCREEN_HEIGHT - h) // 2
        pygame.draw.rect(self.screen, (0,0,0,80), (x+5, y+5, w, h), border_radius=3)
        pygame.draw.rect(self.screen, (230, 230, 220), (x, y, w, h), border_radius=3)
        pygame.draw.rect(self.screen, (100,100,100), (x,y,w,h), 1, border_radius=3)
        font_header = pygame.font.SysFont("Courier New", 18, bold=True)
        header_surf = font_header.render("ANALYSIS MANIFEST", True, (30,30,30))
        self.screen.blit(header_surf, (x + w//2 - header_surf.get_width()//2, y + 20))
        pygame.draw.line(self.screen, (180,180,170), (x+20, y+50), (x+w-20, y+50), 1)
        font_label = pygame.font.SysFont("Courier New", 16, bold=True)
        font_result = pygame.font.SysFont("Courier New", 20)
        label_surf = font_label.render(self.manifest_data['title'] + ":", True, (80,80,80))
        self.screen.blit(label_surf, (x+20, y + 70))
        words = self.manifest_data["path"].split(' ')
        lines = []; current_line = ""
        for word in words:
            test_line = current_line + word + " "
            if font_result.size(test_line)[0] < w - 40:
                current_line = test_line
            else:
                lines.append(current_line); current_line = word + " "
        lines.append(current_line)
        line_y = y + 100
        for line in lines:
            result_surf = font_result.render(line, True, (40, 40, 40))
            self.screen.blit(result_surf, (x + 25, line_y)); line_y += 25
        font_prompt = pygame.font.SysFont("Arial", 12)
        prompt_surf = font_prompt.render("Click anywhere to dismiss", True, (150, 150, 150))
        self.screen.blit(prompt_surf, (x + w - prompt_surf.get_width() - 10, y + h - prompt_surf.get_height() - 10))
    def draw(self):
        self.screen.blit(self.bg_surface, (0, 0))
        self.draw_tree(self.logic.root)
        self.all_sprites.draw(self.screen)
        self.chassis.draw(self.screen); self.lcd.draw(self.screen)
        self.btn_gen_levels.draw(self.screen); self.btn_gen_expr.draw(self.screen)
        self.btn_analyze.draw(self.screen); self.btn_clear.draw(self.screen)
        if self.show_analysis_menu: self.draw_analysis_menu()
        elif self.manifest_data: self.draw_manifest()