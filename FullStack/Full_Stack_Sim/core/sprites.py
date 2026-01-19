import pygame
import math
import random
from settings import *

class CrateSprite(pygame.sprite.Sprite):
    """
    Base class for moving entities (Trucks/Crates).
    Handles procedural drawing of the truck asset and linear interpolation movement.
    """
    def __init__(self, x, y, data_label):
        super().__init__()
        self.plate = str(data_label)
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.target_x = float(x)
        self.target_y = float(y)
        self.angle = 0
        self.is_moving = False
        self.on_finish_callback = None
        
        # Randomize cargo appearance
        self.cargo_layout = []
        for _ in range(6):
            if random.random() > 0.3:
                self.cargo_layout.append(random.choice([1, 2]))
            else:
                self.cargo_layout.append(0)
                
        self.original_image = self.generate_truck_surface()
        self.image = self.original_image.copy()
        self.label_surf = self.generate_label()
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def generate_truck_surface(self):
        """Draws the truck chassis, wheels, and cargo bed procedurally."""
        w, h = CRATE_HEIGHT, CRATE_WIDTH
        surf = pygame.Surface((w + 10, h + 10), pygame.SRCALPHA)
        ox, oy = 5, 5
        
        # Shadow
        shadow_rect = pygame.Rect(ox + 4, oy + 4, w, h)
        pygame.draw.rect(surf, (0, 0, 0, 60), shadow_rect, border_radius=4)
        
        # Tires
        tire_w, tire_h = 14, 6
        pygame.draw.rect(surf, TIRE_COLOR, (ox + w - 24, oy - 2, tire_w, tire_h))
        pygame.draw.rect(surf, TIRE_COLOR, (ox + w - 24, oy + h - 4, tire_w, tire_h))
        pygame.draw.rect(surf, TIRE_COLOR, (ox + 8, oy - 2, tire_w, tire_h))
        pygame.draw.rect(surf, TIRE_COLOR, (ox + 8, oy + h - 4, tire_w, tire_h))
        
        # Bed
        bed_length = w * 0.72
        bed_rect = pygame.Rect(ox, oy, bed_length, h)
        pygame.draw.rect(surf, TRUCK_CHASSIS, bed_rect, border_radius=2)
        pygame.draw.rect(surf, (70, 70, 75), (ox, oy + 2, bed_length, h-4), 1)
        
        # Cargo Boxes
        box_size = (h - 8) // 2
        start_x = ox + 2
        for i, box_type in enumerate(self.cargo_layout):
            if box_type == 0: continue
            col = i % 2
            row = i // 2
            bx = start_x + (row * (box_size + 2))
            by = oy + 4 + (col * box_size)
            color = BOX_COLOR_1 if box_type == 1 else BOX_COLOR_2
            box_rect = pygame.Rect(bx, by, box_size - 2, box_size - 2)
            pygame.draw.rect(surf, color, box_rect)
            pygame.draw.rect(surf, (0, 0, 0, 50), box_rect, 1)
            pygame.draw.line(surf, BOX_TAPE, box_rect.midleft, box_rect.midright, 2)
            
        # Hitch
        pygame.draw.rect(surf, (30, 30, 30), (ox + bed_length - 2, oy + h//2 - 3, 6, 6))
        
        # Cab
        cab_x = ox + bed_length + 2
        cab_w = w - bed_length - 2
        cab_rect = pygame.Rect(cab_x, oy, cab_w, h)
        pygame.draw.rect(surf, TRUCK_CAB_WHITE, cab_rect, border_radius=3)
        
        # Windshield
        ws_width = 10
        ws_height = h - 6
        ws_rect = pygame.Rect(cab_x + cab_w - 14, oy + 3, ws_width, ws_height)
        pygame.draw.rect(surf, WINDSHIELD, ws_rect, border_radius=2)
        pygame.draw.line(surf, (100, 120, 130), (ws_rect.right-2, ws_rect.top+2), (ws_rect.right-2, ws_rect.bottom-2), 1)
        
        # Mirrors
        pygame.draw.rect(surf, (20, 20, 20), (cab_x + cab_w - 12, oy - 2, 4, 3))
        pygame.draw.rect(surf, (20, 20, 20), (cab_x + cab_w - 12, oy + h - 1, 4, 3))
        
        # Headlights
        pygame.draw.rect(surf, (255, 200, 50), (ox + w - 2, oy + 2, 2, 4))
        pygame.draw.rect(surf, (255, 200, 50), (ox + w - 2, oy + h - 6, 2, 4))
        
        return surf

    def generate_label(self):
        """Generates the floating text label for the truck's plate ID."""
        font = pygame.font.SysFont("Arial", 10, bold=True)
        raw_text = font.render(self.plate, True, (20, 20, 20))
        padding_x, padding_y = 4, 2
        w = raw_text.get_width() + padding_x * 2
        h = raw_text.get_height() + padding_y * 2
        surf = pygame.Surface((w, h))
        surf.fill((255, 255, 255))
        pygame.draw.rect(surf, (0, 0, 0), surf.get_rect(), 1)
        surf.blit(raw_text, (padding_x, padding_y))
        return surf

    def move_to(self, target_pos, callback=None):
        """Sets a target position for the sprite to interpolate towards."""
        self.target_x, self.target_y = target_pos
        dx = self.target_x - self.pos_x
        dy = self.target_y - self.pos_y
        
        # Calculate rotation angle based on movement vector
        if abs(dx) > 1 or abs(dy) > 1:
            radians = math.atan2(-dy, dx)
            self.angle = math.degrees(radians)
            
        self.on_finish_callback = callback
        self.is_moving = True

    def update(self):
        """Updates position using Linear Interpolation (LERP)."""
        if not self.is_moving: return
        
        dx = self.target_x - self.pos_x
        dy = self.target_y - self.pos_y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist < MIN_SPEED:
            # Snap to target if close enough
            self.pos_x = self.target_x
            self.pos_y = self.target_y
            self.is_moving = False
            self.angle = round(self.angle / 90) * 90 # Snap angle to nearest 90
            if self.on_finish_callback:
                cb = self.on_finish_callback
                self.on_finish_callback = None
                cb()
        else:
            # Interpolate
            self.pos_x += dx * LERP_FACTOR
            self.pos_y += dy * LERP_FACTOR
            
            # Minimum movement threshold to prevent stalling
            if abs(dx * LERP_FACTOR) < 0.5 and abs(dx) > 0: self.pos_x += (dx/abs(dx)) * 0.5
            if abs(dy * LERP_FACTOR) < 0.5 and abs(dy) > 0: self.pos_y += (dy/abs(dy)) * 0.5
            
        self.rect.center = (int(self.pos_x), int(self.pos_y))
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)