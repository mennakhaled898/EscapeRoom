# EscapeRoom
#  LOCKDOWN — AI-Powered Escape Room
> **A sophisticated simulation demonstrating competitive AI search strategies through high-stakes logical challenges.**

---

##  Game Rooms & AI Intelligence

###  Room 1: Color Sort Protocol
* **The Mission:** Sort disorganized colored balls into matching tubes.
* **AI Showdown:**
    * **Agent 1 (Greedy Best-First Search):** Prioritizes moves based on local entropy and immediate tube alignment to reduce disorganization quickly.
    * **Agent 2 (A* Search):** Calculates the optimal sequence by evaluating the total distance of all colors to their target tubes, ensuring the most efficient path.

###  Room 2: Mastermind Cipher
* **The Mission:** Decipher a hidden 4-digit code using logic and feedback.
* **AI Showdown:**
    * **Agent 1 (CBRS):** Selects candidates that satisfy constraints from previous feedback, pruning the search space by eliminating impossible combinations.
    * **Agent 2 (Minimax):** Implements Knuth’s strategy to evaluate the "worst-case" scenario for every potential guess, systematically narrowing down the correct code.

###  Room 3: Crate Maze (Grid Pathfinding)
* **The Mission:** Navigate a grid to find a hidden key within crates while avoiding obstacles.
* **AI Showdown:**
    * **Agent 1 (Breadth-First Search - BFS):** Performs an exhaustive scan of the grid to guarantee the shortest path, regardless of map complexity.
    * **Agent 2 (A* Search):** Utilizes ** Manhattan Distance** heuristics to "aim" toward the target, significantly reducing the number of nodes explored compared to BFS.

### Room 4: 8-Puzzle Cipher (The Final Challenge)
* **The Mission:** Solve the classic 3x3 sliding tile puzzle to reach the goal state.
* **AI Showdown:**
    * **Agent 1 (A* Search):** Employs standard Manhattan distance heuristics to guide tiles toward their goal positions.
    * **Agent 2 (IDA* - Iterative Deepening A*):** Uses an advanced **"Linear Conflict"** heuristic. This tighter estimation prunes unnecessary branches, solving complex configurations faster than standard A*.

---

##  Technical Implementation
* **Core Language:** `Python 3.10+`
* **Graphics Engine:** `Pygame`
* **Visual Aesthetics:** Dark Industrial / Silver Network Theme with real-time AI "Frontier" and "Path" visualization.

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
