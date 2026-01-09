import pygame
import math
from settings import *
from core.sprites import CrateSprite
from core.ui import HandheldChassis, LCDDisplay, RoundButton

# --- LOGIC LAYER ---

class BSTNode:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None
        self.x = 0  # Visual coordinate (calculated later)
        self.y = 0

class BSTManager:
    def __init__(self):
        self.root = None
        self.nodes_count = 0
        self.max_depth = 4 # Limit depth to fit screen

    def insert(self, value):
        if self.root is None:
            self.root = BSTNode(value)
            self.nodes_count += 1
            return {"type": "ROOT", "node": self.root}
        
        current = self.root
        depth = 0
        path = [] # List of coordinates to travel [(x,y), (x,y)...]
        
        while True:
            path.append((current.x, current.y))
            
            if value == current.value:
                return {"type": "ERROR", "message": "DUPLICATE ID"}
            
            if depth >= self.max_depth:
                return {"type": "ERROR", "message": "SYSTEM FULL"}

            if value < current.value:
                if current.left is None:
                    current.left = BSTNode(value)
                    self.nodes_count += 1
                    return {
                        "type": "INSERT", 
                        "node": current.left, 
                        "parent": current, 
                        "direction": "LEFT",
                        "path": path
                    }
                current = current.left
            else:
                if current.right is None:
                    current.right = BSTNode(value)
                    self.nodes_count += 1
                    return {
                        "type": "INSERT", 
                        "node": current.right, 
                        "parent": current, 
                        "direction": "RIGHT",
                        "path": path
                    }
                current = current.right
            depth += 1

    def clear(self):
        self.root = None
        self.nodes_count = 0

# --- VISUALIZATION LAYER ---

class PackageSprite(pygame.sprite.Sprite):
    def __init__(self, x, y, value):
        super().__init__()
        self.value = value
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.target_x = float(x)
        self.target_y = float(y)
        self.is_moving = False
        self.path_queue = [] # List of targets
        self.on_finish_callback = None
        
        # Generate Surface
        self.image = pygame.Surface((30, 30))
        self.image.fill(BOX_COLOR_1)
        pygame.draw.rect(self.image, (50, 30, 10), (0,0,30,30), 2)
        pygame.draw.line(self.image, BOX_TAPE, (15, 0), (15, 30), 4)
        pygame.draw.line(self.image, BOX_TAPE, (0, 15), (30, 15), 4)
        
        # Text
        font = pygame.font.SysFont("Arial", 10, bold=True)
        txt = font.render(str(value), True, (255, 255, 255))
        self.image.blit(txt, (15 - txt.get_width()//2, 15 - txt.get_height()//2))
        
        self.rect = self.image.get_rect(center=(x, y))

    def add_path(self, points):
        for p in points:
            self.path_queue.append(p)

    def move_to(self, target, callback=None):
        self.target_x, self.target_y = target
        self.on_finish_callback = callback
        self.is_moving = True

    def update(self):
        if not self.is_moving:
            if self.path_queue:
                next_target = self.path_queue.pop(0)
                self.move_to(next_target)
            return

        dx = self.target_x - self.pos_x
        dy = self.target_y - self.pos_y
        dist = math.sqrt(dx**2 + dy**2)
        
        speed = 6.0 # Fast conveyor speed
        
        if dist < speed:
            self.pos_x = self.target_x
            self.pos_y = self.target_y
            self.is_moving = False
            if self.on_finish_callback:
                cb = self.on_finish_callback
                self.on_finish_callback = None
                cb()
        else:
            angle = math.atan2(dy, dx)
            self.pos_x += math.cos(angle) * speed
            self.pos_y += math.sin(angle) * speed
            
        self.rect.center = (int(self.pos_x), int(self.pos_y))

class RouterTreeSimulation:
    def __init__(self, screen):
        self.screen = screen
        self.logic = BSTManager()
        self.all_sprites = pygame.sprite.Group()
        self.packages_group = pygame.sprite.Group()
        
        # UI Setup
        self.ui_x = 750
        self.ui_w = 250
        self.chassis = HandheldChassis(self.ui_x + 10, 20, self.ui_w - 20, SCREEN_HEIGHT - 40)
        self.lcd = LCDDisplay(self.ui_x + 35, 80, self.ui_w - 70, 100)
        self.lcd.update_status("ROUTING SYSTEM")
        
        btn_cx = self.ui_x + self.ui_w // 2
        self.btn_insert = RoundButton(btn_cx, 280, 45, BTN_GREEN_BASE, BTN_GREEN_LIGHT, "INJECT", self.action_insert)
        self.btn_reset = RoundButton(btn_cx, 390, 45, BTN_RED_BASE, BTN_RED_LIGHT, "FLUSH", self.action_reset)
        
        self.is_animating = False
        self.ROOT_X = 375
        self.ROOT_Y = 100
        self.LEVEL_HEIGHT = 100
        
        # Pre-render background
        self.bg_surface = self._generate_background()

    def _generate_background(self):
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        surf.fill((40, 42, 45)) # Dark industrial floor
        
        # Grid lines
        for x in range(0, 750, 50):
            pygame.draw.line(surf, (50, 52, 55), (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, 50):
            pygame.draw.line(surf, (50, 52, 55), (0, y), (750, y), 1)
            
        # Hazard area at top
        pygame.draw.rect(surf, (20, 20, 20), (0, 0, 750, 80))
        pygame.draw.line(surf, STRIPE_YELLOW, (0, 80), (750, 80), 3)
        
        return surf

    def _recalculate_layout(self, node, x, y, level, width_spread):
        if node is None: return
        node.x = x
        node.y = y
        
        # Calculate children positions
        # As we go deeper, the spread decreases
        next_spread = width_spread / 2
        
        self._recalculate_layout(node.left, x - next_spread, y + self.LEVEL_HEIGHT, level + 1, next_spread)
        self._recalculate_layout(node.right, x + next_spread, y + self.LEVEL_HEIGHT, level + 1, next_spread)

    def draw_conveyor_line(self, start, end):
        # Draw the belt
        pygame.draw.line(self.screen, (20, 20, 20), start, end, 10) # Outline
        pygame.draw.line(self.screen, (60, 60, 65), start, end, 6)  # Belt
        
        # Draw moving arrows (simulated)
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        pygame.draw.circle(self.screen, (100, 100, 100), (int(mid_x), int(mid_y)), 2)

    def draw_diverter_node(self, node):
        if node is None: return
        
        # Draw connections first (so they are under the node)
        if node.left:
            self.draw_conveyor_line((node.x, node.y), (node.left.x, node.left.y))
            self.draw_diverter_node(node.left)
        if node.right:
            self.draw_conveyor_line((node.x, node.y), (node.right.x, node.right.y))
            self.draw_diverter_node(node.right)
            
        # Draw the machine itself
        rect = pygame.Rect(0, 0, 50, 50)
        rect.center = (node.x, node.y)
        
        # Shadow
        pygame.draw.rect(self.screen, SHADOW_COLOR, rect.move(4, 4), border_radius=5)
        
        # Body
        pygame.draw.rect(self.screen, (80, 85, 90), rect, border_radius=5)
        pygame.draw.rect(self.screen, (150, 155, 160), rect.inflate(-10, -10), border_radius=2)
        
        # Value Display
        font = pygame.font.SysFont("Impact", 16)
        txt = font.render(str(node.value), True, (20, 20, 20))
        self.screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))
        
        # Status Light (Green = Active)
        pygame.draw.circle(self.screen, (50, 255, 50), (rect.right - 6, rect.top + 6), 3)

    def action_insert(self):
        if self.is_animating: return
        
        text = self.lcd.text
        if not text.isdigit():
            self.lcd.update_status("ERR: INTEGERS ONLY")
            return
            
        val = int(text)
        if val > 999: 
            self.lcd.update_status("ERR: MAX 999")
            return

        receipt = self.logic.insert(val)
        
        if receipt['type'] == 'ERROR':
            self.lcd.update_status(f"ERR: {receipt['message']}")
            return
            
        self.lcd.update_status(f"ROUTING: {val}")
        self.lcd.text = ""
        self.is_animating = True
        
        # Recalculate positions for the whole tree (in case layout shifts, though static here)
        self._recalculate_layout(self.logic.root, self.ROOT_X, self.ROOT_Y, 0, 180)
        
        # Spawn Package
        pkg = PackageSprite(self.ROOT_X, 20, val) # Start above root
        self.all_sprites.add(pkg)
        self.packages_group.add(pkg)
        
        if receipt['type'] == 'ROOT':
            # Just drop to root
            pkg.move_to((self.ROOT_X, self.ROOT_Y), callback=self.on_animation_complete)
        else:
            # Follow path
            path = receipt['path'] # List of (x,y) visited
            final_node = receipt['node']
            
            # 1. Move to Root
            pkg.add_path([(self.ROOT_X, self.ROOT_Y)])
            
            # 2. Traverse existing nodes
            # Note: path contains coordinates of parents visited
            for coord in path[1:]: # Skip root as we added it
                pkg.add_path([coord])
                
            # 3. Move to final new position
            pkg.move_to((final_node.x, final_node.y), callback=self.on_animation_complete)

    def action_reset(self):
        self.logic.clear()
        self.all_sprites.empty()
        self.packages_group.empty()
        self.lcd.update_status("SYSTEM FLUSHED")

    def on_animation_complete(self):
        self.is_animating = False
        self.lcd.update_status("READY")
        # Keep the package there as part of the "Machine"
        # In a real sim, it might disappear into a chute, but here we want to see the tree structure.

    def handle_events(self, event):
        self.lcd.handle_event(event)
        self.btn_insert.handle_event(event)
        self.btn_reset.handle_event(event)

    def update(self):
        self.all_sprites.update()
        self.lcd.update()

    def draw(self):
        self.screen.blit(self.bg_surface, (0, 0))
        
        # Draw the Tree Structure (Conveyors and Nodes)
        # We draw this every frame because nodes might be added
        self._recalculate_layout(self.logic.root, self.ROOT_X, self.ROOT_Y, 0, 180)
        self.draw_diverter_node(self.logic.root)
        
        # Draw moving packages on top
        self.all_sprites.draw(self.screen)
        
        # UI
        self.chassis.draw(self.screen)
        self.lcd.draw(self.screen)
        self.btn_insert.draw(self.screen)
        self.btn_reset.draw(self.screen)