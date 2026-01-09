PROJECT: Full Stack Logistics Simulator
THEME: Industrial Visualization of Data Structures (Warehouse Management System)
ENGINE: Python 3.x / Pygame

DESCRIPTION:
A visualization tool that represents computer science data structures as 
realistic logistics operations. The project uses a "Sim-Style" aesthetic,
rendering high-detail procedural assets (trucks, cargo, environment) entirely
via code.

The interface mimics a rugged industrial handheld scanner (WMS Unit), 
providing an immersive way to interact with the algorithms.

CURRENT MODULES:

1. LEVEL 1 - THE VERTICAL PARKING BAY (STACK)
   - Logic: LIFO (Last In, First Out).
   - Setting: A rugged maintenance hangar with textured asphalt floors.
   - Metaphor: A narrow bay where the last truck in blocks the exit.
   - Animation: Blocking trucks automatically "shuffle" to a holding zone to 
     release the target vehicle.
   - Feature: "Skip Animation" button instantly synchronizes the visual state
     with the logical data structure.

2. LEVEL 2 - THE WEIGH STATION (QUEUE)
   - Logic: FIFO (First In, First Out).
   - Setting: High-detail Industrial Yard (Asphalt, Fences, Shipping Containers).
   - Metaphor: A highway weigh station.
   - Animation: If a truck in the middle needs to leave, the trucks in front 
     drive out, take a "U-Turn Loopback Road," and rejoin the back of the line.
   - Logic Update: Trucks looping back count as a new Arrival and Departure.

3. LEVEL 3 - THE CONVEYOR BELT (LINKED LIST)
   - Logic: Singly Linked List (Insert/Remove at Index).
   - Setting: An atmospheric factory floor with an animated conveyor belt,
     textured concrete, and volumetric lighting effects ("god rays").
   - Metaphor: Boxes on a conveyor represent nodes, linked by a logical chain.
   - Animation: To insert a box, the user clicks a slot, subsequent boxes shift
     to create a gap, and the new box drops from a central hopper.

DIRECTORY STRUCTURE:
Full_Stack_Sim/
├── main.py                   # Entry Point (Main Menu & Scene Switcher)
├── settings.py               # Config, Palettes (Industrial/Retro LCD), Physics
├── assets/                   # (Optional) Folder for custom overrides
├── core/                     # Shared Engine Code
│   ├── sprites.py            # Procedural Asset Generators (Trucks, Boxes, Labels)
│   └── ui.py                 # Rugged UI System (Handheld Chassis, LCD, Round Buttons)
└── simulation/               # Level Logic
    ├── site_parking_stack.py # Level 1: Stack Logic (Interior)
    ├── site_parking_queue.py # Level 2: Queue Logic (Exterior Yard)
    └── site_conveyor_list.py # Level 3: Linked List Logic (Conveyor)

HOW TO RUN:
1. Ensure Python 3.x and Pygame are installed (`pip install pygame`).
2. Run: `python main.py`
3. Select a Module from the Main Menu.

CONTROLS (HANDHELD UNIT):
- LCD Screen: Type Label/ID (e.g., "TRK-123" or "BOX-A").
- GREEN BUTTON (APPEND/ARRIVE): Adds an item to the structure.
- BLUE BUTTON (INSERT AT): For Linked List, enters "Placement Mode".
- RED BUTTON (REMOVE/DEPART): Removes an item by its Label/ID.
- BLUE BUTTON (MANIFEST): Toggles the inventory report overlay.
- GRAY BUTTON (SKIP ANIM): Instantly finishes all active animations and snaps
  sprites to their logical positions.