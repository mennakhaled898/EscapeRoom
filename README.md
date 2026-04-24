# EscapeRoom
# LOCKDOWN — AI-Powered Escape Room
> **A sophisticated simulation demonstrating competitive AI search strategies through high-stakes logical challenges.**

---

##  Table of Contents
*  [About the Project](#-about-the-project).
* [ Game Chambers & AI Logic](#-about-the-project)
* [ Technical Stack](#-technical-stack)
* [ Credits](#-credits)

---

##  About the Project
**LOCKDOWN** is an immersive technical challenge. You aren't just playing; you are competing against two distinct **AI Agents** to see who can escape first. This project visualizes how different algorithms "think", "prune", and "search" in real-time.

---

##  Game Chambers & AI Logic

###  Room 1: Color Sort Protocol
| Agent | Algorithm | Strategy |
| :--- | :--- | :--- |
| **Agent 1** | **Greedy BFS** | Prioritizes moves based on local entropy and immediate tube alignment. |
| **Agent 2** | **A* Search** | Evaluates the total distance of all colors to target tubes for the **most efficient path**. |

###  Room 2: Mastermind Cipher
| Agent | Algorithm | Strategy |
| :--- | :--- | :--- |
| **Agent 1** | **CBRS** | Prunes the search space by eliminating impossible combinations based on feedback. |
| **Agent 2** | **Minimax** | Implements **Knuth’s strategy** to solve the code by evaluating "worst-case" scenarios. |

###  Room 3: Crate Maze (Pathfinding)
| Agent | Algorithm | Strategy |
| :--- | :--- | :--- |
| **Agent 1** | **BFS** | Performs an exhaustive scan to **guarantee the shortest path** in any map. |
| **Agent 2** | **A* Search** | Uses **Manhattan Distance** heuristics to "aim" toward the target, reducing explored nodes. |

###  Room 4: 8-Puzzle Cipher
| Agent | Algorithm | Strategy |
| :--- | :--- | :--- |
| **Agent 1** | **A* Search** | Employs standard Manhattan distance heuristics to guide tiles to their goals. |
| **Agent 2** | **IDA*** | Uses **Linear Conflict** heuristics to prune branches and solve complex states faster. |

---

##  Technical Stack
* **Language:** `Python 3.10+`
* **Library:** `Pygame`
* **Visuals:** Dark Industrial / Silver Network Theme with real-time AI path visualization.

---

##  Installation & Setup
```bash
# Clone the repository
git clone [https://github.com/mennakhaled898/EscapeRoom.git](https://github.com/mennakhaled898/EscapeRoom.git)

# Install the required graphics library
pip install pygame

# Run the simulation
python main.py
```
---
## Credits
 **Development Team**
 
Merna Magdy

Menna Khaled

Nour Abodeif

 **Supervision**
 
Dr. Sara El-Metwally
