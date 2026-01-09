import pygame
import sys
from settings import *
from core.ui import Button
from simulation.site_parking_stack import ParkingStackSimulation
from simulation.site_parking_queue import ParkingQueueSimulation
from simulation.site_conveyor_list import ConveyorSimulation
from simulation.site_router_tree import RouterTreeSimulation # <--- IMPORT

class MainMenu:
    def __init__(self, screen, switch_callback):
        self.screen = screen
        self.switch_callback = switch_callback
        self.title_font = pygame.font.SysFont("Impact", 60)
        self.sub_font = pygame.font.SysFont("Arial", 16)
        
        btn_w = 300
        btn_h = 50
        center_x = SCREEN_WIDTH // 2 - btn_w // 2
        start_y = 300
        gap = 70
        
        self.btn_stack = Button(center_x, start_y, btn_w, btn_h, "SITE A: MAINTENANCE BAY (STACK)",
                                lambda: self.switch_callback("STACK"))
        self.btn_queue = Button(center_x, start_y + gap, btn_w, btn_h, "SITE B: WEIGH STATION (QUEUE)",
                                lambda: self.switch_callback("QUEUE"))
        self.btn_conveyor = Button(center_x, start_y + gap*2, btn_w, btn_h, "SITE C: CONVEYOR BELT (LINKED LIST)",
                                lambda: self.switch_callback("CONVEYOR"))
        self.btn_tree = Button(center_x, start_y + gap*3, btn_w, btn_h, "SITE D: ROUTING FLOOR (BST)",
                                lambda: self.switch_callback("TREE")) # <--- NEW BUTTON
        self.btn_quit = Button(center_x, start_y + gap*4, btn_w, btn_h, "EXIT SYSTEM",
                               lambda: self.switch_callback("QUIT"))

    def handle_events(self, event):
        self.btn_stack.handle_event(event)
        self.btn_queue.handle_event(event)
        self.btn_conveyor.handle_event(event)
        self.btn_tree.handle_event(event) # <--- HANDLE
        self.btn_quit.handle_event(event)

    def update(self):
        pass

    def draw(self):
        self.screen.fill((20, 24, 28))
        
        # Title
        title_surf = self.title_font.render("FULL STACK LOGISTICS", True, (220, 220, 225))
        sub_surf = self.sub_font.render("DATA STRUCTURE VISUALIZATION SUITE", True, (100, 150, 200))
        self.screen.blit(title_surf, (SCREEN_WIDTH//2 - title_surf.get_width()//2, 150))
        self.screen.blit(sub_surf, (SCREEN_WIDTH//2 - sub_surf.get_width()//2, 220))
        
        # Buttons
        self.btn_stack.draw(self.screen)
        self.btn_queue.draw(self.screen)
        self.btn_conveyor.draw(self.screen)
        self.btn_tree.draw(self.screen) # <--- DRAW
        self.btn_quit.draw(self.screen)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Full Stack Logistics Simulator")
    clock = pygame.time.Clock()
    
    current_scene = None
    
    def switch_scene(scene_name):
        nonlocal current_scene
        if scene_name == "MENU":
            current_scene = MainMenu(screen, switch_scene)
        elif scene_name in ["STACK", "QUEUE", "CONVEYOR", "TREE"]:
            if scene_name == "STACK":
                current_scene = ParkingStackSimulation(screen)
            elif scene_name == "QUEUE":
                current_scene = ParkingQueueSimulation(screen)
            elif scene_name == "CONVEYOR":
                current_scene = ConveyorSimulation(screen)
            elif scene_name == "TREE":
                current_scene = RouterTreeSimulation(screen) # <--- INIT
            
            # Inject Back Button
            back_btn = Button(10, 10, 100, 30, "< MENU", lambda: switch_scene("MENU"))
            
            # Monkey patch handle/draw to include back button
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

    switch_scene("MENU")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
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