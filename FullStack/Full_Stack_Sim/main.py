import pygame
import sys
import math
import random
from settings import *
from core.ui import Button

# Import simulations
from simulation.site_parking_stack import ParkingStackSimulation
from simulation.site_parking_queue import ParkingQueueSimulation
from simulation.site_conveyor_list import ConveyorSimulation
from simulation.site_router_tree import RouterTreeSimulation
from simulation.site_expression_tree import ExpressionTreeSimulation
from simulation.site_sorting_floor import SortingSimulation
from simulation.site_recursion_lab import RecursionSimulation
from simulation.site_warehouse_array import ArraySimulation

# --- INDUSTRIAL PALETTE ---
COLOR_CONCRETE_DARK = (30, 32, 35)
COLOR_CONCRETE_LIGHT = (50, 52, 55)
COLOR_ASPHALT = (20, 20, 22)
COLOR_MARKING = (200, 180, 50)
COLOR_WALL_DARK = (40, 45, 50)
COLOR_WALL_LIGHT = (60, 65, 70)
COLOR_ROOF_BASE = (30, 35, 40)

class IndustrialLabel:
    """A rugged, high-contrast label for facilities."""
    def __init__(self, x, y, title, subtitle):
        self.x = x
        self.y = y
        self.title = title.upper()
        self.subtitle = subtitle.upper()
        self.font_head = pygame.font.SysFont("Impact", 16)
        self.font_sub = pygame.font.SysFont("Arial", 10, bold=True)
        self.alpha = 0
        
    def draw(self, screen, hovered):
        # Animate opacity
        target = 255 if hovered else 150
        self.alpha += (target - self.alpha) * 0.1
        
        # Layout
        t_surf = self.font_head.render(self.title, True, (255, 255, 255))
        s_surf = self.font_sub.render(self.subtitle, True, (255, 200, 0))
        
        w = max(t_surf.get_width(), s_surf.get_width()) + 20
        h = 40
        
        # Background Plate (Metal look)
        bg_rect = pygame.Rect(self.x - w//2, self.y - h - 10, w, h)
        
        # Draw Shadow
        s_rect = bg_rect.copy()
        s_rect.y += 4
        s_surf_bg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s_surf_bg, (0, 0, 0, 100), s_surf_bg.get_rect(), border_radius=4)
        screen.blit(s_surf_bg, s_rect)

        # Draw Main Plate
        plate_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        plate_alpha = int(self.alpha)
        
        # Border/Fill
        pygame.draw.rect(plate_surf, (20, 25, 30, plate_alpha), (0, 0, w, h), border_radius=4)
        pygame.draw.rect(plate_surf, (100, 100, 100, plate_alpha), (0, 0, w, h), 1, border_radius=4)
        
        # Hazard Stripe on left
        pygame.draw.rect(plate_surf, (255, 200, 0, plate_alpha), (0, 0, 4, h), border_top_left_radius=4, border_bottom_left_radius=4)
        
        # Blit Text
        plate_surf.blit(t_surf, (10, 4))
        plate_surf.blit(s_surf, (10, 22))
        
        screen.blit(plate_surf, bg_rect)
        
        # Connecting Line
        if hovered:
            start = (self.x, self.y)
            end = (self.x, bg_rect.bottom)
            pygame.draw.line(screen, (255, 255, 255), start, end, 1)
            pygame.draw.circle(screen, (255, 255, 255), start, 2)

class Facility:
    def __init__(self, x, y, w, h, title, subtitle, type_id, callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.base_y = y
        self.title = title
        self.subtitle = subtitle
        self.type_id = type_id
        self.callback = callback
        self.hovered = False
        self.anim_timer = 0 # Start at 0
        self.label = IndustrialLabel(self.rect.centerx, self.rect.top - 5, title, subtitle)
        
        # Procedural Details
        self.wall_color = COLOR_WALL_DARK
        self.roof_color = COLOR_ROOF_BASE
        self.accent_color = (255, 100, 0) # Default Orange
        
        if type_id in ["STACK", "QUEUE"]: self.accent_color = (255, 200, 0) # Yellow
        if type_id in ["CONVEYOR", "SORTING"]: self.accent_color = (0, 150, 255) # Blue
        if type_id in ["TREE", "EXPR_TREE"]: self.accent_color = (0, 255, 100) # Green
        if type_id in ["RECURSION", "ARRAY"]: self.accent_color = (255, 50, 50) # Red

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        self.hovered = self.rect.collidepoint(mouse_pos)
        
        # Only animate if hovered
        if self.hovered:
            self.anim_timer += 1

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered:
                self.callback()

    def draw(self, screen):
        # 1. Drop Shadow (Perspective)
        shadow_offset = 15
        shadow_points = [
            self.rect.bottomleft,
            (self.rect.left + shadow_offset, self.rect.bottom - shadow_offset),
            (self.rect.right + shadow_offset, self.rect.bottom - shadow_offset),
            (self.rect.right + shadow_offset, self.rect.top - shadow_offset),
            self.rect.topright
        ]
        # Draw shadow with alpha
        shadow_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(shadow_surf, (0, 0, 0, 120), shadow_points)
        screen.blit(shadow_surf, (0,0))

        # 2. Concrete Base Pad
        pad_rect = self.rect.inflate(20, 20)
        pygame.draw.rect(screen, COLOR_CONCRETE_LIGHT, pad_rect, border_radius=4)
        pygame.draw.rect(screen, (20, 20, 20), pad_rect, 1, border_radius=4)

        # 3. Building Walls (2.5D Extrusion)
        depth = 10
        # Right Wall
        pygame.draw.polygon(screen, (30, 30, 35), [
            self.rect.topright,
            (self.rect.right + depth, self.rect.top - depth),
            (self.rect.right + depth, self.rect.bottom - depth),
            self.rect.bottomright
        ])
        # Top Wall (Roof Thickness)
        pygame.draw.polygon(screen, (50, 50, 55), [
            self.rect.topleft,
            (self.rect.left + depth, self.rect.top - depth),
            (self.rect.right + depth, self.rect.top - depth),
            self.rect.topright
        ])

        # 4. Main Roof Surface
        roof_rect = pygame.Rect(self.rect.left + depth, self.rect.top - depth, self.rect.width, self.rect.height)
        pygame.draw.rect(screen, self.roof_color, roof_rect)
        
        # Corrugated Texture
        for i in range(roof_rect.left, roof_rect.right, 10):
            pygame.draw.line(screen, (0, 0, 0, 50), (i, roof_rect.top), (i, roof_rect.bottom), 1)

        # 5. Mechanical Details & Animations
        self._draw_mechanics(screen, roof_rect)

        # 6. Lighting Effect (Soft Gradient Glow)
        if self.hovered:
            # Create a local surface for the glow to avoid full-screen blending issues
            glow_radius = 150
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            
            # Draw concentric circles with decreasing alpha to simulate a soft light
            num_layers = 15
            for i in range(num_layers):
                radius = int(glow_radius * (1 - i/num_layers))
                alpha = int(10 + (i * 2)) # Outer is faint, inner is stronger
                if alpha > 60: alpha = 60 # Cap alpha to prevent solid look
                
                pygame.draw.circle(glow_surf, (*self.accent_color, alpha), (glow_radius, glow_radius), radius)
            
            # Blit the glow centered on the building
            screen.blit(glow_surf, (roof_rect.centerx - glow_radius, roof_rect.centery - glow_radius))
            
            # Crisp Highlight Border
            pygame.draw.rect(screen, self.accent_color, roof_rect, 2)
            pygame.draw.rect(screen, (255, 255, 255), roof_rect, 1)

        # 7. Label
        self.label.draw(screen, self.hovered)

    def _draw_mechanics(self, screen, rect):
        # Draw specific details based on type
        cx, cy = rect.center
        
        if self.type_id == "STACK":
            # Elevator Shaft
            shaft_w = 30
            pygame.draw.rect(screen, (20, 20, 20), (cx - shaft_w//2, rect.top + 10, shaft_w, rect.height - 20))
            # Moving Platform
            offset = abs(math.sin(self.anim_timer * 0.05)) * (rect.height - 40)
            plat_y = rect.bottom - 20 - offset
            
            # Only color if hovered, else dark
            plat_color = self.accent_color if self.hovered else (40, 40, 40)
            pygame.draw.rect(screen, plat_color, (cx - 12, plat_y, 24, 8))
            
        elif self.type_id == "QUEUE":
            # Conveyor Lines
            for y in [rect.top + 20, rect.bottom - 20]:
                pygame.draw.line(screen, (50, 50, 50), (rect.left, y), (rect.right, y), 6)
                # Chasing Lights
                if self.hovered:
                    offset = (self.anim_timer * 2) % 20
                    for x in range(rect.left, rect.right, 20):
                        lx = x + offset
                        if lx < rect.right:
                            pygame.draw.circle(screen, self.accent_color, (lx, y), 2)

        elif self.type_id == "CONVEYOR":
            # Rotating Gears
            for gx in [cx - 30, cx, cx + 30]:
                pygame.draw.circle(screen, (60, 60, 60), (gx, cy), 12)
                if self.hovered:
                    angle = self.anim_timer * 0.1
                    end_x = gx + math.cos(angle) * 12
                    end_y = cy + math.sin(angle) * 12
                    pygame.draw.line(screen, (100, 100, 100), (gx, cy), (end_x, end_y), 2)

        elif self.type_id == "TREE":
            # Data Pipes
            pygame.draw.line(screen, (50, 50, 50), (cx, rect.top), (cx, rect.bottom), 4)
            pygame.draw.line(screen, (50, 50, 50), (rect.left, cy), (rect.right, cy), 4)
            # Pulses
            if self.hovered:
                offset = (self.anim_timer * 2) % (rect.height // 2)
                pygame.draw.circle(screen, self.accent_color, (cx, cy - offset), 3)
                pygame.draw.circle(screen, self.accent_color, (cx, cy + offset), 3)

        elif self.type_id == "EXPR_TREE":
            # Central Processor
            pygame.draw.rect(screen, (40, 40, 40), (cx - 20, cy - 20, 40, 40))
            pygame.draw.rect(screen, (20, 20, 20), (cx - 20, cy - 20, 40, 40), 2)
            
            if self.hovered:
                # Blinking Grid Pattern
                if (self.anim_timer // 10) % 2 == 0:
                    pygame.draw.rect(screen, self.accent_color, (cx - 15, cy - 15, 10, 10))
                    pygame.draw.rect(screen, self.accent_color, (cx + 5, cy + 5, 10, 10))
                else:
                    pygame.draw.rect(screen, self.accent_color, (cx + 5, cy - 15, 10, 10))
                    pygame.draw.rect(screen, self.accent_color, (cx - 15, cy + 5, 10, 10))
                
        elif self.type_id == "SORTING":
            # Gantry Crane Rails
            pygame.draw.line(screen, (80, 80, 80), (rect.left, rect.top + 10), (rect.right, rect.top + 10), 2)
            pygame.draw.line(screen, (80, 80, 80), (rect.left, rect.bottom - 10), (rect.right, rect.bottom - 10), 2)
            # Crane Body
            crane_x = rect.left + 10 + abs(math.sin(self.anim_timer * 0.05)) * (rect.width - 40)
            
            # Only color if hovered
            crane_color = self.accent_color if self.hovered else (40, 40, 40)
            pygame.draw.rect(screen, crane_color, (crane_x, rect.top + 5, 10, rect.height - 10))

        elif self.type_id == "ARRAY":
            # Storage Grid
            rows, cols = 3, 6
            cell_w = rect.width / cols
            cell_h = rect.height / rows
            for r in range(rows):
                for c in range(cols):
                    bx = rect.left + c * cell_w + 2
                    by = rect.top + r * cell_h + 2
                    pygame.draw.rect(screen, (40, 40, 45), (bx, by, cell_w - 4, cell_h - 4))
                    # Random filled slots
                    if (r * c + r) % 3 == 0:
                         pygame.draw.rect(screen, (60, 70, 80), (bx+2, by+2, cell_w - 8, cell_h - 8))
            # Scanner
            if self.hovered:
                scan_x = rect.left + abs(math.sin(self.anim_timer * 0.05)) * rect.width
                pygame.draw.line(screen, (255, 0, 0), (scan_x, rect.top), (scan_x, rect.bottom), 2)

        elif self.type_id == "RECURSION":
            # Concentric Circles
            pygame.draw.circle(screen, (40, 40, 40), (cx, cy), 25, 2)
            pygame.draw.circle(screen, (40, 40, 40), (cx, cy), 15, 2)
            if self.hovered:
                angle = self.anim_timer * 0.1
                ox = cx + math.cos(angle) * 25
                oy = cy + math.sin(angle) * 25
                pygame.draw.line(screen, self.accent_color, (cx, cy), (ox, oy), 2)

class MainMenu:
    def __init__(self, screen, switch_callback):
        self.screen = screen
        self.switch_callback = switch_callback
        self.bg_surface = self._generate_map_background()
        
        # Transition State
        self.transitioning = False
        self.transition_alpha = 0
        self.target_scene = None
        
        # Define Facilities
        # Shifted Y coordinates down by 50px to clear header
        self.facilities = [
            # Top Row
            Facility(80, 130, 80, 140, "Stack Tower", "LIFO Operations", "STACK", lambda: self.start_transition("STACK")),
            Facility(250, 150, 180, 80, "Weigh Station", "FIFO Queue", "QUEUE", lambda: self.start_transition("QUEUE")),
            Facility(520, 130, 150, 100, "Conveyor Belt", "Linked List", "CONVEYOR", lambda: self.start_transition("CONVEYOR")),
            
            # Middle Row
            Facility(120, 350, 120, 120, "Routing Hub", "Binary Search Tree", "TREE", lambda: self.start_transition("TREE")),
            Facility(450, 350, 120, 120, "Parser Lab", "Expression Tree", "EXPR_TREE", lambda: self.start_transition("EXPR_TREE")),
            
            # Bottom Row
            Facility(80, 550, 200, 100, "Sorting Yard", "Algorithms", "SORTING", lambda: self.start_transition("SORTING")),
            Facility(350, 570, 100, 80, "Recursion", "Hanoi Crane", "RECURSION", lambda: self.start_transition("RECURSION")),
            Facility(550, 550, 200, 80, "Smart Rack", "Array Storage", "ARRAY", lambda: self.start_transition("ARRAY")),
        ]
        
        self.exit_btn = Button(SCREEN_WIDTH - 120, SCREEN_HEIGHT - 50, 100, 30, "LOGOUT", lambda: self.switch_callback("QUIT"))

    def _generate_map_background(self):
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        surf.fill(COLOR_CONCRETE_DARK)
        
        # 1. Concrete Slabs (Base Layer)
        tile_w, tile_h = 100, 80
        for y in range(0, SCREEN_HEIGHT, tile_h):
            for x in range(0, SCREEN_WIDTH, tile_w):
                # Base color variation
                base_val = random.randint(28, 35)
                color = (base_val, base_val + 2, base_val + 5)
                pygame.draw.rect(surf, color, (x, y, tile_w, tile_h))
                
                # Expansion joints (Grid lines)
                pygame.draw.line(surf, (20, 22, 25), (x, y), (x + tile_w, y), 2)
                pygame.draw.line(surf, (20, 22, 25), (x, y), (x, y + tile_h), 2)
                
                # Cracks
                if random.random() > 0.8:
                    cx, cy = x + random.randint(20, 80), y + random.randint(20, 60)
                    points = [(cx, cy)]
                    for _ in range(3):
                        cx += random.randint(-10, 10)
                        cy += random.randint(-10, 10)
                        points.append((cx, cy))
                    pygame.draw.lines(surf, (25, 25, 25), False, points, 1)

        # 2. Oil Stains / Grime Patches
        for _ in range(20):
            sx = random.randint(0, SCREEN_WIDTH)
            sy = random.randint(0, SCREEN_HEIGHT)
            w = random.randint(30, 80)
            h = random.randint(20, 50)
            stain = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.ellipse(stain, (10, 10, 10, 30), (0, 0, w, h))
            surf.blit(stain, (sx, sy))

        # 3. Asphalt Roads (Keep existing logic but ensure it draws ON TOP of slabs)
        road_color = COLOR_ASPHALT
        
        # Draw Loop (Shifted down 50px)
        points = [(120, 270), (600, 270), (600, 530), (120, 530)]
        pygame.draw.lines(surf, road_color, True, points, 60)
        
        # Connectors (Shifted down 50px)
        connectors = [
            ((120, 270), (120, 200)), # Stack
            ((340, 270), (340, 200)), # Queue
            ((600, 270), (600, 200)), # Conveyor
            ((180, 270), (180, 350)), # Tree
            ((510, 270), (510, 350)), # Parser
            ((180, 530), (180, 600)), # Sorting
            ((400, 530), (400, 600)), # Recursion
            ((600, 530), (600, 600)), # Array
        ]
        for p1, p2 in connectors:
            pygame.draw.line(surf, road_color, p1, p2, 40)
            
        # 4. Road Markings (Hazard Yellow)
        for p1, p2 in connectors:
            pygame.draw.line(surf, COLOR_MARKING, p1, p2, 2)
            
        # 5. Noise / Grime (Keep existing)
        for _ in range(20000):
            x = random.randint(0, SCREEN_WIDTH-1)
            y = random.randint(0, SCREEN_HEIGHT-1)
            c = random.randint(0, 10)
            current = surf.get_at((x,y))
            new_c = (max(0, current.r - c), max(0, current.g - c), max(0, current.b - c))
            surf.set_at((x, y), new_c)
            
        # 6. Vignette (Keep existing)
        vig = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(vig, (0,0,0,0), vig.get_rect()) 
        for i in range(100):
            pygame.draw.rect(vig, (0,0,0, 2), (i*4, i*3, SCREEN_WIDTH - i*8, SCREEN_HEIGHT - i*6), 10)
        surf.blit(vig, (0,0))
            
        return surf

    def start_transition(self, scene_name):
        if not self.transitioning:
            self.transitioning = True
            self.target_scene = scene_name
            self.transition_alpha = 0

    def handle_events(self, event):
        if self.transitioning:
            return # Block input during transition
            
        for fac in self.facilities:
            fac.handle_event(event)
        self.exit_btn.handle_event(event)

    def update(self):
        for fac in self.facilities:
            fac.update()
            
        if self.transitioning:
            self.transition_alpha += 10
            if self.transition_alpha >= 255:
                self.transition_alpha = 255
                self.switch_callback(self.target_scene)

    def draw(self):
        self.screen.blit(self.bg_surface, (0, 0))
        
        # Draw Facilities
        for fac in self.facilities:
            fac.draw(self.screen)
            
        self.exit_btn.draw(self.screen)
        
        # Header
        pygame.draw.rect(self.screen, (0, 0, 0), (0, 0, SCREEN_WIDTH, 40))
        pygame.draw.line(self.screen, (255, 200, 0), (0, 40), (SCREEN_WIDTH, 40), 2)
        
        font = pygame.font.SysFont("Impact", 20)
        title = font.render("FULL STACK LOGISTICS // FACILITY OVERVIEW", True, (200, 200, 200))
        self.screen.blit(title, (20, 8))
        
        # Status Light
        pygame.draw.circle(self.screen, (0, 255, 0), (SCREEN_WIDTH - 30, 20), 5)
        status = pygame.font.SysFont("Arial", 10).render("LIVE FEED", True, (0, 255, 0))
        self.screen.blit(status, (SCREEN_WIDTH - 90, 15))
        
        # Fullscreen Hint
        hint = pygame.font.SysFont("Arial", 10).render("[F11] FULL SCREEN", True, (100, 100, 100))
        self.screen.blit(hint, (SCREEN_WIDTH - 180, 15))
        
        # Transition Overlay
        if self.transitioning:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(self.transition_alpha)
            self.screen.blit(overlay, (0, 0))
            
            if self.transition_alpha > 100:
                font_term = pygame.font.SysFont("Consolas", 24, bold=True)
                text = font_term.render(f"ESTABLISHING UPLINK TO {self.target_scene}...", True, (0, 255, 0))
                self.screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT//2))

def main():
    pygame.init()
    # Default to windowed, but use SCALED to allow resizing if the OS supports it
    flags = pygame.SCALED 
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
    pygame.display.set_caption("Full Stack Logistics Simulator")
    clock = pygame.time.Clock()

    current_scene = None
    is_fullscreen = False

    def switch_scene(scene_name):
        nonlocal current_scene
        if scene_name == "MENU":
            current_scene = MainMenu(screen, switch_scene)
        elif scene_name in ["STACK", "QUEUE", "CONVEYOR", "TREE", "EXPR_TREE", "SORTING", "RECURSION", "ARRAY"]:
            # Initialize specific simulation scenes
            if scene_name == "STACK":
                current_scene = ParkingStackSimulation(screen)
            elif scene_name == "QUEUE":
                current_scene = ParkingQueueSimulation(screen)
            elif scene_name == "CONVEYOR":
                current_scene = ConveyorSimulation(screen)
            elif scene_name == "TREE":
                current_scene = RouterTreeSimulation(screen)
            elif scene_name == "EXPR_TREE":
                current_scene = ExpressionTreeSimulation(screen)
            elif scene_name == "SORTING":
                current_scene = SortingSimulation(screen)
            elif scene_name == "RECURSION":
                current_scene = RecursionSimulation(screen)
            elif scene_name == "ARRAY":
                current_scene = ArraySimulation(screen)
            
            # Inject Back Button into the scene
            back_btn = Button(10, 10, 100, 30, "< MAP", lambda: switch_scene("MENU"))
            
            # Monkey-patch the handle_events and draw methods to include the back button
            original_handle = current_scene.handle_events
            original_draw = current_scene.draw
            
            def new_handle(event):
                back_btn.handle_event(event)
                original_handle(event)
            
            def new_draw():
                original_draw()
                back_btn.draw(screen)
                
            current_scene.handle_events = new_handle
            current_scene.draw = new_draw
            
        elif scene_name == "QUIT":
            pygame.quit()
            sys.exit()

    # Start at Menu
    switch_scene("MENU")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Toggle Fullscreen with F11
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    is_fullscreen = not is_fullscreen
                    if is_fullscreen:
                        # SCALED | FULLSCREEN scales the surface to the monitor size
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED | pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED)
                    
                    # Update the reference in the current scene
                    if current_scene:
                        current_scene.screen = screen

            if current_scene:
                current_scene.handle_events(event)

        if current_scene:
            current_scene.update()
            current_scene.draw()

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()