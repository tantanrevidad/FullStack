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
   - Animation: Blocking trucks automatically "shuffle" to a holding zone.

2. LEVEL 2 - THE WEIGH STATION (QUEUE)
   - Logic: FIFO (First In, First Out).
   - Setting: High-detail Industrial Yard (Asphalt, Fences, Shipping Containers).
   - Metaphor: A highway weigh station.
   - Animation: "Loopback" road for trucks cycling to the back of the line.

3. LEVEL 3 - THE CONVEYOR BELT (LINKED LIST)
   - Logic: Singly Linked List (Insert/Remove at Index).
   - Setting: Factory floor with volumetric lighting ("god rays").
   - Metaphor: Boxes on a conveyor represent nodes, linked by logical chains.
   - Interaction: "Click-to-Place" insertion mechanics.

4. LEVEL 4 - THE ROUTING FLOOR (BINARY SEARCH TREE)
   - Logic: Binary Search Tree (Insertion, In-Order, Pre-Order, Post-Order).
   - Setting: A high-detail, atmospheric warehouse with animated conveyors.
   - Metaphor: Packages travel a branching conveyor system based on ID value.
   - Features: 
     - Dynamic Layout Engine: The tree automatically resizes and "zooms out" 
       as it gets deeper to fit the screen.
     - Traversal Visualization: A "System Drone" animates the chosen traversal
       path (In-Order, Pre-Order, Post-Order) by visiting each node.
     - Scan Manifest: Traversal results are displayed on a thematic paper
       manifest popup after the drone scan is complete.

DIRECTORY STRUCTURE:
Full_Stack_Sim/
├── main.py                   # Entry Point (Main Menu & Scene Switcher)
├── settings.py               # Config, Palettes, Physics Constants
├── core/                     # Shared Engine Code
│   ├── sprites.py            # Procedural Asset Generators
│   └── ui.py                 # Rugged UI System
└── simulation/               # Level Logic
    ├── site_parking_stack.py # Level 1: Stack
    ├── site_parking_queue.py # Level 2: Queue
    ├── site_conveyor_list.py # Level 3: Linked List
    └── site_router_tree.py   # Level 4: BST

HOW TO RUN:
1. Ensure Python 3.x and Pygame are installed (`pip install pygame`).
2. Run: `python main.py`
3. Select a Module from the Main Menu.

CONTROLS (HANDHELD UNIT):
- LCD Screen: Type Label/ID (Integers for BST).
- GREEN BUTTON: Add Item (Append, Enqueue, or Inject).
- RED BUTTON: Remove Item (Depart, Dequeue, or Flush System).
- BLUE BUTTON: Context specific (Manifest/Scan).
- GRAY BUTTON: Skip Animation (Stack/Queue only).