PROJECT: Full Stack Logistics Simulator
VERSION: 1.1 (Audio Update)
THEME: Industrial Visualization of Data Structures (Warehouse Management System)
ENGINE: Python 3.x / Pygame Community Edition

DESCRIPTION:
A high-fidelity visualization tool that represents computer science data structures 
as realistic logistics operations. The project uses a "Sim-Style" aesthetic, 
rendering procedural assets (trucks, cargo, environment, buildings) entirely via code.

The experience begins at the "Facility Overview," a dynamic, procedurally generated 
industrial park at night, featuring real-time lighting, mechanical animations, and 
an adaptive procedural soundtrack. Users "uplink" to specific facilities to interact 
with the underlying algorithms via a rugged handheld scanner interface.

CONTROLS:
- Mouse: Interact with UI, Select Slots, Hover over Facilities.
- Keyboard: Type values into the scanner.
- F11: Toggle Full Screen Mode.

MODULES (FACILITIES):

1. STACK TOWER (LIFO Operations)
   - Logic: Last-In, First-Out stack management.
   - Visuals: Vertical parking bay with hydraulic lifts and holding zones.

2. WEIGH STATION (FIFO Queue)
   - Logic: First-In, First-Out queue with loopback cycling.
   - Visuals: Industrial yard with animated conveyor lanes and traffic control.

3. CONVEYOR BELT (Linked List)
   - Logic: Singly Linked List (Insert/Remove at Index).
   - Visuals: Factory floor with volumetric lighting and animated belts.

4. ROUTING HUB (Binary Search Tree)
   - Logic: BST Insertion and Traversal (In/Pre/Post-order).
   - Visuals: Automated warehouse with drone-based package routing.

5. PARSER LAB (Expression Tree)
   - Logic: Shunting-yard algorithm for parsing mathematical expressions.
   - Visuals: High-tech analysis floor with processing grids.

6. SORTING YARD (Algorithms)
   - Logic: Bubble, Selection, Insertion, Merge, and Quick Sort.
   - Visuals: Large-scale gantry crane operations with container manipulation.

7. RECURSION LAB (Tower of Hanoi)
   - Logic: Recursive problem solving (Manual & Auto-Solve).
   - Visuals: Magnetic crane moving disks between platforms.

8. SMART RACK (Array Storage)
   - Logic: Fixed-size Array (O(1) Read vs O(n) Write).
   - Visuals: Multi-level pallet racking with industrial forklift physics.

DIRECTORY STRUCTURE:
Full_Stack_Sim/
├── main.py                      # Entry Point (Facility Overview & State Machine)
├── settings.py                  # Config, Palettes, Physics Constants
├── core/                        # Shared Engine Code
│   ├── sprites.py               # Procedural Asset Generators (Trucks, Crates)
│   ├── ui.py                    # Rugged UI System (Scanner, Buttons)
│   └── sound_engine.py          # Procedural Audio Synthesizer & Sequencer
└── simulation/                  # Level Logic & Visualization
    ├── site_parking_stack.py    # Stack Logic
    ├── site_parking_queue.py    # Queue Logic
    ├── site_conveyor_list.py    # Linked List Logic
    ├── site_router_tree.py      # BST Logic
    ├── site_expression_tree.py  # Expression Tree Logic
    ├── site_sorting_floor.py    # Sorting Logic
    ├── site_recursion_lab.py    # Recursion Logic
    └── site_warehouse_array.py  # Array Logic

HOW TO RUN:
1. Ensure Python 3.x and Pygame are installed (`pip install pygame`).
2. Run: `python main.py`