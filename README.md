# EscapeRoom

#  LOCKDOWN — AI-Powered Escape Room
> **An immersive technical challenge where AI search strategies meet classic logic puzzles.**

---

##  Table of Contents
* [ About the Project](#-about-the-project)
* [ Game Mechanics & AI Logic](#-game-mechanics--ai-logic)
* [ Technical Stack](#-technical-stack)
* [ Credits](#-credits)

---

##  About the Project
**LOCKDOWN** is a high-stakes simulation game. You aren't just playing; you are competing against two distinct **AI Agents** to see who can escape first. The project visualizes how different algorithms "think" and "search" in real-time.

---

##  Game Mechanics & AI Logic

###  Room 1: Color Sort Protocol
* **The Mission:** Sort colors into matching tubes.
* **AI Brain:** `Breadth-First Search (BFS)`
* **Why?** It explores every possible move to ensure the **shortest solution** is found.

###  Room 2: Mastermind Codebreaker
* **The Mission:** Crack a 4-digit hidden code.
* **AI Brain:** `Minimax` & `Constraint-Based Search`
* **Why?** To demonstrate how AI prunes impossible options to zero in on the truth.

###  Room 3: Search & Find
* **The Mission:** Locate a hidden key in a grid of crates.
* **AI Brain:** `A* Search (Manhattan Distance)`
* **Why?** Efficient pathfinding that avoids obstacles while heading straight for the target.

###  Room 4: The 8-Puzzle (Sliding Tiles)
* **The Mission:** Arrange tiles 1-8 in the correct order.
* **The AI Showdown:**
    | Feature | Agent 1 (Greedy) | Agent 2 (A*) |
    | :--- | :--- | :--- |
    | **Strategy** | Best-First (Heuristic only) | A* (Cost + Heuristic) |
    | **Speed** |  Fast computation |  Slower but precise |
    | **Solution** | May take more steps | **Optimal (Shortest path)** |

---

##  Technical Stack
* **Language:** `Python 3.10+`
* **Framework:** `Pygame`
* **UI Theme:** Dark Industrial / Cybernetic Silver.

---

##  How to Run
```bash
# Clone the repository
git clone [https://github.com/mennakhaled898/EscapeRoom.git](https://github.com/mennakhaled898/EscapeRoom.git)

# Install dependencies
pip install pygame

# Launch the game
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
