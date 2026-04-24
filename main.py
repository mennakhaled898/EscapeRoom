import pygame
import sys
import random
import time
import heapq
import math
import copy
from collections import deque, Counter
from itertools import product

pygame.init()

# ── DISPLAY ───────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 1280, 800
HALF = WIDTH // 2
GRID_SIZE = 10
CELL = 38
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("LOCKDOWN — Escape Room")

# ── PALETTE ───────────────────────────────────────────────────────────────────
C_BG = (8,   9,  11)
C_PANEL = (14,  16,  20)
C_STEEL = (32,  36,  44)
C_STEEL_LT = (50,  56,  68)
C_RIVET = (42,  46,  55)
C_AMBER = (255, 170,   0)
C_AMBER_DIM = (120,  80,   0)
C_RED = (220,  30,  30)
C_RED_DIM = (80,  15,  15)
C_RED_BRIGHT = (255,  55,  55)
C_GREEN = (20, 210,  80)
C_GREEN_DIM = (8,  70,  28)
C_BLUE = (40, 160, 255)
C_YELLOW = (255, 220,  20)
C_WHITE = (230, 235, 240)
C_GRAY = (80,  90, 105)
C_DARK = (18,  20,  25)
C_ORANGE = (255, 120,  20)
C_HAZARD_Y = (230, 200,   0)
C_HAZARD_B = (18,  20,  25)
C_LASER_GLOW = (255,  50,  50)
C_CRATE = (90,  60,  20)
C_CRATE_LT = (140,  95,  35)
C_PURPLE = (170,  60, 220)
C_TEAL = (0,  200, 180)

# ── MASTERMIND CONSTANTS ──────────────────────────────────────────────────────
MM_DIGITS = ["1", "2", "3", "4", "5", "6"]
MM_ALL = [list(p) for p in product(MM_DIGITS, repeat=4)]

# ── SORT GAME CONSTANTS ───────────────────────────────────────────────────────
SORT_COLORS = ["R", "G", "B", "Y"]
SORT_CMAP = {"R": C_RED_BRIGHT, "G": C_GREEN, "B": C_BLUE, "Y": C_YELLOW}
SORT_TUBES = 5
TUBE_CAP = 3

# ── 8-PUZZLE CONSTANTS ────────────────────────────────────────────────────────
P8_GOAL = (1, 2, 3, 4, 5, 6, 7, 8, 0)   # 0 = blank
P8_GOAL_IDX = {v: i for i, v in enumerate(P8_GOAL)}
P8_MOVES = [(-1, 0), (1, 0), (0, -1), (0, 1)]   # up, down, left, right

# ── 8-PUZZLE HELPERS ──────────────────────────────────────────────────────────


def p8_is_solvable(state):
    """Count inversions to determine solvability."""
    tiles = [t for t in state if t != 0]
    inv = 0
    for i in range(len(tiles)):
        for j in range(i+1, len(tiles)):
            if tiles[i] > tiles[j]:
                inv += 1
    return inv % 2 == 0


def p8_make_puzzle():
    """Generate a solvable, non-trivial 8-puzzle."""
    for _ in range(10000):
        s = list(P8_GOAL)
        random.shuffle(s)
        t = tuple(s)
        if t != P8_GOAL and p8_is_solvable(t):
            return t
    return P8_GOAL


def p8_neighbors(state):
    """Return list of (move_dir_label, new_state) from state."""
    idx = state.index(0)
    r, c = divmod(idx, 3)
    result = []
    for dr, dc in P8_MOVES:
        nr, nc = r+dr, c+dc
        if 0 <= nr < 3 and 0 <= nc < 3:
            ni = nr*3+nc
            lst = list(state)
            lst[idx], lst[ni] = lst[ni], lst[idx]
            result.append(tuple(lst))
    return result


def p8_manhattan(state):
    """Manhattan distance heuristic."""
    dist = 0
    for i, v in enumerate(state):
        if v == 0:
            continue
        gi = P8_GOAL_IDX[v]
        dist += abs(i//3 - gi//3) + abs(i % 3 - gi % 3)
    return dist


def p8_linear_conflict(state):
    """Manhattan + linear conflict heuristic (admissible, tighter)."""
    dist = p8_manhattan(state)
    lc = 0
    # Row conflicts
    for row in range(3):
        tiles_in_row = []
        for col in range(3):
            v = state[row*3 + col]
            if v != 0 and P8_GOAL_IDX[v] // 3 == row:
                tiles_in_row.append((v, col))
        for i in range(len(tiles_in_row)):
            for j in range(i+1, len(tiles_in_row)):
                vi, ci = tiles_in_row[i]
                vj, cj = tiles_in_row[j]
                gi = P8_GOAL_IDX[vi] % 3
                gj = P8_GOAL_IDX[vj] % 3
                if ci < cj and gi > gj:
                    lc += 2
                elif ci > cj and gi < gj:
                    lc += 2
    # Column conflicts
    for col in range(3):
        tiles_in_col = []
        for row in range(3):
            v = state[row*3 + col]
            if v != 0 and P8_GOAL_IDX[v] % 3 == col:
                tiles_in_col.append((v, row))
        for i in range(len(tiles_in_col)):
            for j in range(i+1, len(tiles_in_col)):
                vi, ri = tiles_in_col[i]
                vj, rj = tiles_in_col[j]
                gi = P8_GOAL_IDX[vi] // 3
                gj = P8_GOAL_IDX[vj] // 3
                if ri < rj and gi > gj:
                    lc += 2
                elif ri > rj and gi < gj:
                    lc += 2
    return dist + lc

# ── A* for 8-puzzle (Agent 1 Room 4) ─────────────────────────────────────────
# Uses basic Manhattan Distance. Simple, clean, fast in practice.


def p8_astar(start):
    """A* with Manhattan distance. Returns (path_of_states, nodes_explored)."""
    if start == P8_GOAL:
        return [start], 0
    open_set = [(p8_manhattan(start), 0, start, [start])]
    visited = {}
    nodes = 0
    while open_set:
        f, g, state, path = heapq.heappop(open_set)
        if state in visited and visited[state] <= g:
            continue
        visited[state] = g
        nodes += 1
        if state == P8_GOAL:
            return path, nodes
        for ns in p8_neighbors(state):
            ng = g + 1
            if ns not in visited or visited[ns] > ng:
                heapq.heappush(
                    open_set, (ng + p8_manhattan(ns), ng, ns, path + [ns]))
    return [], nodes

# ── IDA* for 8-puzzle (Agent 2 Room 4) ───────────────────────────────────────
# Uses Manhattan + Linear Conflict heuristic. Memory-efficient depth-first
# iterative deepening. Explores fewer unique states but revisits nodes.


def p8_idastar(start):
    """IDA* with Manhattan+LinearConflict. Returns (path_of_states, nodes_explored)."""
    if start == P8_GOAL:
        return [start], 0

    nodes_explored = [0]

    def search(path, g, bound):
        state = path[-1]
        f = g + p8_linear_conflict(state)
        if f > bound:
            return f, None
        if state == P8_GOAL:
            return -1, list(path)
        min_t = float('inf')
        prev = path[-2] if len(path) > 1 else None
        for ns in p8_neighbors(state):
            if ns == prev:
                continue
            nodes_explored[0] += 1
            path.append(ns)
            t, result = search(path, g+1, bound)
            if t == -1:
                return -1, result
            if t < min_t:
                min_t = t
            path.pop()
        return min_t, None

    bound = p8_linear_conflict(start)
    path = [start]
    while True:
        t, result = search(path, 0, bound)
        if t == -1:
            return result, nodes_explored[0]
        if t == float('inf'):
            return [], nodes_explored[0]
        bound = t

# ── MASTERMIND SCORE ──────────────────────────────────────────────────────────


def mm_score(guess, secret):
    exact = sum(g == s for g, s in zip(guess, secret))
    gc = Counter(guess)
    sc = Counter(secret)
    return (exact, sum(min(gc[d], sc[d]) for d in MM_DIGITS) - exact)


def mm_per_slot(guess, secret):
    result = [None]*4
    remaining = list(secret)
    for i in range(4):
        if guess[i] == secret[i]:
            result[i] = 'exact'
            remaining[i] = None
    for i in range(4):
        if result[i] is not None:
            continue
        if guess[i] in remaining:
            result[i] = 'misplaced'
            remaining[remaining.index(guess[i])] = None
        else:
            result[i] = 'wrong'
    return result


# ── FONTS ─────────────────────────────────────────────────────────────────────
try:
    F_TITLE = pygame.font.SysFont("impact", 54)
    F_HEAD = pygame.font.SysFont("impact", 32)
    F_LABEL = pygame.font.SysFont("couriernew", 16, bold=True)
    F_MONO = pygame.font.SysFont("couriernew", 14, bold=True)
    F_SMALL = pygame.font.SysFont("couriernew", 12)
    F_HUGE = pygame.font.SysFont("impact", 80)
    F_NUM = pygame.font.SysFont("impact", 38)
    F_MENU_T = pygame.font.SysFont("impact", 72)
    F_MENU_S = pygame.font.SysFont("impact", 28)
    F_MENU_B = pygame.font.SysFont("couriernew", 17, bold=True)
    F_RPT_T = pygame.font.SysFont("impact", 38)
    F_RPT_S = pygame.font.SysFont("couriernew", 15, bold=True)
    F_TILE = pygame.font.SysFont("impact", 40)
    F_TILE_S = pygame.font.SysFont("impact", 28)
except Exception:
    _fb = pygame.font.SysFont(None, 24)
    F_TITLE = F_HEAD = F_LABEL = F_MONO = F_SMALL = F_HUGE = F_NUM = \
        F_MENU_T = F_MENU_S = F_MENU_B = F_RPT_T = F_RPT_S = F_TILE = F_TILE_S = _fb

_noise = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
_rng = random.Random(42)
for _ in range(18000):
    _noise.set_at((_rng.randint(0, WIDTH-1), _rng.randint(0, HEIGHT-1)),
                  (_rng.randint(0, 40),)*3 + (_rng.randint(20, 80),))
_scan = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
for _y in range(0, HEIGHT, 3):
    pygame.draw.line(_scan, (0, 0, 0, 38), (0, _y), (WIDTH, _y))

# ── DRAW HELPERS ──────────────────────────────────────────────────────────────


def lerp(a, b, t):
    return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))


def pulse(t, speed=2.0, lo=0.4, hi=1.0):
    return lo+(hi-lo)*(0.5+0.5*math.sin(t*speed))


def flicker(t, seed=0):
    return 0.85+0.15*math.sin(t*17.3+seed)*math.sin(t*5.1+seed*2)


def dpanel(s, r, col=C_PANEL, bdr=C_STEEL, rad=6, bw=2):
    pygame.draw.rect(s, col, r, border_radius=rad)
    pygame.draw.rect(s, bdr, r, bw, border_radius=rad)


def drivets(s, r, col=C_RIVET, rad=4):
    for ox, oy in [(10, 10), (-10, 10), (10, -10), (-10, -10)]:
        cx = r.left+(10 if ox > 0 else r.width-10)
        cy = r.top+(10 if oy > 0 else r.height-10)
        pygame.draw.circle(s, col, (cx, cy), rad)
        pygame.draw.circle(s, lerp(col, C_WHITE, 0.3), (cx-1, cy-1), rad//2)


def dhazard(s, r, w=12):
    clip = s.get_clip()
    s.set_clip(r)
    step = w*2
    for x in range(r.left-r.height, r.right+step, step):
        pygame.draw.polygon(s, C_HAZARD_Y, [
                            (x, r.top), (x+w, r.top), (x+w+r.height, r.bottom), (x+r.height, r.bottom)])
        pygame.draw.polygon(s, C_HAZARD_B, [(
            x+w, r.top), (x+w*2, r.top), (x+w*2+r.height, r.bottom), (x+w+r.height, r.bottom)])
    s.set_clip(clip)


def dglow_circle(s, pos, rad, col, alpha=80):
    g = pygame.Surface((rad*4, rad*4), pygame.SRCALPHA)
    for r2 in range(rad*2, 0, -2):
        pygame.draw.circle(
            g, (*col, int(alpha*(1-r2/(rad*2)))), (rad*2, rad*2), r2)
    s.blit(g, (pos[0]-rad*2, pos[1]-rad*2))


def dglow_rect(s, r, col, alpha=60, pad=6):
    gr = r.inflate(pad*2, pad*2)
    g = pygame.Surface((gr.width, gr.height), pygame.SRCALPHA)
    for i in range(pad, 0, -1):
        pygame.draw.rect(g, (*col, int(alpha*(1-i/pad))),
                         pygame.Rect(i, i, gr.width-i*2, gr.height-i*2), 1)
    s.blit(g, gr.topleft)


def dcorners(s, r, col=C_AMBER, sz=14, w=2):
    for (cx, cy), (dx, dy) in zip([(r.x, r.y), (r.right, r.y), (r.x, r.bottom), (r.right, r.bottom)],
                                  [(1, 1), (-1, 1), (1, -1), (-1, -1)]):
        pygame.draw.line(s, col, (cx, cy), (cx+dx*sz, cy), w)
        pygame.draw.line(s, col, (cx, cy), (cx, cy+dy*sz), w)


def dshadow(s, surf, pos, shcol=(0, 0, 0), off=2):
    sh = surf.copy()
    sh.fill((*shcol, 180), special_flags=pygame.BLEND_RGBA_MULT)
    s.blit(sh, (pos[0]+off, pos[1]+off))
    s.blit(surf, pos)


def dsep(s, x, y1, y2, col=C_STEEL):
    pygame.draw.line(s, col, (x, y1), (x, y2), 2)
    for yi in [y1, y2]:
        pygame.draw.circle(s, C_RIVET, (x, yi), 5)
        pygame.draw.circle(s, C_STEEL_LT, (x-1, yi-1), 2)

# ── SORT HELPERS ───────────────────────────────────────────────────────────────


def greedy_sort(tubes):
    open_set = [(sort_score_h(tubes), tubes, [])]
    visited = set()
    while open_set:
        h, state, path = heapq.heappop(open_set)
        k = tubes_key(state)
        if k in visited:
            continue
        visited.add(k)
        if sort_solved(state):
            return path
        for s in range(SORT_TUBES):
            for d in range(SORT_TUBES):
                if not can_move(state, s, d):
                    continue
                ns = apply_move(state, s, d)
                heapq.heappush(open_set, (sort_score_h(ns), ns, path+[(s, d)]))
    return []


def astar_sort(tubes):
    start = tubes_key(tubes)
    g = {start: 0}
    open_set = [(sort_score_h(tubes), 0, tubes, [])]
    vis = set()
    while open_set:
        f, cost, state, path = heapq.heappop(open_set)
        k = tubes_key(state)
        if k in vis:
            continue
        vis.add(k)
        if sort_solved(state):
            return path
        for s in range(SORT_TUBES):
            for d in range(SORT_TUBES):
                if not can_move(state, s, d):
                    continue
                ns = apply_move(state, s, d)
                nk = tubes_key(ns)
                nc = cost+1
                if nc < g.get(nk, 9999):
                    g[nk] = nc
                    heapq.heappush(
                        open_set, (nc+sort_score_h(ns), nc, ns, path+[(s, d)]))
    return []


def make_sort_puzzle():
    for _ in range(2000):
        balls = []
        for c in SORT_COLORS:
            balls.extend([c]*TUBE_CAP)
        random.shuffle(balls)
        tubes = [list(balls[i*TUBE_CAP:(i+1)*TUBE_CAP])
                 for i in range(SORT_TUBES-1)]
        tubes.append([])
        if not sort_solved(tubes) and greedy_sort(tubes) is not None:
            return tubes
    return tubes


def sort_solved(tubes):
    for tube in tubes:
        if not tube:
            continue
        if len(tube) != TUBE_CAP or len(set(tube)) != 1:
            return False
    return True


def sort_score_h(tubes):
    miss = 0
    for tube in tubes:
        if not tube:
            continue
        maj = Counter(tube).most_common(1)[0][0]
        miss += sum(1 for b in tube if b != maj)
    return miss


def can_move(tubes, s, d):
    if s == d or not tubes[s] or len(tubes[d]) >= TUBE_CAP:
        return False
    if tubes[d]:
        return tubes[d][-1] == tubes[s][-1]
    return True


def apply_move(tubes, s, d):
    t = copy.deepcopy(tubes)
    t[d].append(t[s].pop())
    return t


def tubes_key(t): return tuple(tuple(x) for x in t)

# ── PATHFINDING  ──────────────────────────────────────────


def heuristic(a, b): return abs(a[0]-b[0])+abs(a[1]-b[1])


def bfs_path(start, goal, obstacles, gs=GRID_SIZE):
    q = deque([(start, [])])
    vis = {tuple(start)}
    while q:
        (r, c), path = q.popleft()
        if [r, c] == goal:
            return path
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < gs and 0 <= nc < gs and (nr, nc) not in vis:
                if [nr, nc] not in obstacles or [nr, nc] == goal:
                    vis.add((nr, nc))
                    q.append(([nr, nc], path+[[nr, nc]]))
    return []


# ── PATCHED: astar_path now returns (path, nodes_explored, frontier_cells) ───
# This mirrors what _ai1_bfs provides for BFS so Agent 2's Room 3 can show
# the same green "explored nodes" overlay that Agent 1 already displays.
def astar_path(start, goal, obstacles, gs=GRID_SIZE):
    open_set = []
    heapq.heappush(open_set, (0, tuple(start)))
    came_from = {}
    g_score = {tuple(start): 0}
    closed = set()
    while open_set:
        _, cur = heapq.heappop(open_set)
        if list(cur) == goal:
            path = []
            while cur in came_from:
                path.append(list(cur))
                cur = came_from[cur]
            path.reverse()
            return path, len(closed), [list(n) for n in closed]
        if cur in closed:
            continue
        closed.add(cur)
        r, c = cur
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r+dr, c+dc
            nb = (nr, nc)
            if 0 <= nr < gs and 0 <= nc < gs:
                if [nr, nc] in obstacles and [nr, nc] != goal:
                    continue
                tg = g_score.get(cur, 1e9)+1
                if tg < g_score.get(nb, 1e9):
                    came_from[nb] = cur
                    g_score[nb] = tg
                    heapq.heappush(
                        open_set, (tg+heuristic(list(nb), goal), nb))
    return [], len(closed), [list(n) for n in closed]


def is_solvable(s, g, obs, gs=GRID_SIZE):
    return len(bfs_path(s, g, obs, gs)) > 0 or s == g


def gen_obstacles_validated(n, gs=GRID_SIZE):
    protected = [[0, 0], [0, 1], [1, 0], [
        gs-1, gs-1], [gs-2, gs-1], [gs-1, gs-2]]
    for _ in range(200):
        obs = []
        att = 0
        while len(obs) < n and att < 20000:
            att += 1
            r, c = random.randint(0, gs-1), random.randint(0, gs-1)
            if [r, c] not in obs and [r, c] not in protected:
                obs.append([r, c])
        if is_solvable([0, 0], [gs-1, gs-1], obs, gs):
            return obs
    return []

# ── MASTERMIND AI ─────────────────────────────────────────────────────────────


def cbrs_consistent(code, history):
    for guess, fb in history:
        if mm_score(guess, code) != fb:
            return False
    return True


def cbrs_pick(history):
    consistent = [c for c in MM_ALL if cbrs_consistent(c, history)]
    return random.choice(consistent) if consistent else random.choice(MM_ALL)


def minimax_solve(secret):
    cands = list(MM_ALL)
    guess = ["1", "1", "2", "2"]
    sequence = []
    while True:
        sequence.append(list(guess))
        fb = mm_score(guess, secret)
        if fb == (4, 0):
            return sequence
        cands = [c for c in cands if mm_score(guess, c) == fb]
        if not cands:
            return sequence
        if len(cands) == 1:
            guess = cands[0]
            continue
        best = None
        bw = 999999
        for g in cands:
            bk = {}
            for c in cands:
                fb2 = mm_score(g, c)
                bk[fb2] = bk.get(fb2, 0)+1
            w = max(bk.values())
            if w < bw:
                bw = w
                best = g
        guess = best

# ── STATE GENERATION ──────────────────────────────────────────────────────────


def gen_shared_puzzles():
    r3 = gen_obstacles_validated(10)
    p8 = p8_make_puzzle()
    return {
        "sort_tubes": make_sort_puzzle(),
        "mm_secret":  random.choice(MM_ALL),
        "crates": r3,
        "key_loc": random.choice(r3) if r3 else [5, 5],
        "p8_start": p8,
    }


def gen_state(puzzles=None):
    if puzzles is None:
        r3 = gen_obstacles_validated(10)
        sort_tubes = make_sort_puzzle()
        mm_secret = random.choice(MM_ALL)
        crates = r3
        key_loc = random.choice(r3) if r3 else [5, 5]
        p8_start = p8_make_puzzle()
    else:
        sort_tubes = copy.deepcopy(puzzles["sort_tubes"])
        mm_secret = list(puzzles["mm_secret"])
        crates = copy.deepcopy(puzzles["crates"])
        key_loc = list(puzzles["key_loc"])
        p8_start = puzzles["p8_start"]

    return {
        "room": 1, "pos": [0, 0], "input": [],
        "finished": False, "start_time": time.time(), "end_time": None,
        "path_queue": [], "frontier": [], "final_path_visual": [], "reset_timer": 0,
        # Room 1
        "sort_tubes": sort_tubes, "sort_selected": None, "sort_moves": 0,
        "sort_invalid_flash": 0, "sort_history": [],
        # Room 2
        "mm_secret": mm_secret, "mm_input": [], "mm_history": [],
        "mm_guesses": 0, "mm_feedback_display": 0,
        # Room 3
        "crates": crates, "key_loc": key_loc,
        "wrong_crates": [], "wrong_crates_count": 0,
        # Room 4: 8-puzzle
        "p8_start":   p8_start,
        "p8_state":   p8_start,           # current board state (tuple of 9)
        "p8_plan":    [],                 # precomputed list of states
        "p8_step_idx": 0,                 # which step we're on
        "p8_nodes":   0,                  # nodes explored by solver
        "p8_solved":  False,
        # (tile_val, from_pos, to_pos, start_ms) for animation
        "p8_anim_tile": None,
        "p8_last_move_time": 0,           # for human: debounce
        # Stats
        "room_times": {1: None, 2: None, 3: None, 4: None},
        "room_entry": {1: time.time(), 2: None, 3: None, 4: None},
        "nodes_explored": 0, "sort_moves_total": 0,
        # AI1 (Greedy Sort, CBRS, BFS, A*-8puzzle)
        "ls_plan": [], "ga_history": [], "ga_current_guess": None, "ga_submitted": False,
        # AI2 (A* Sort, Minimax, A*, IDA*-8puzzle)
        "astar_plan": [], "mm_plan": [], "mm_plan_idx": 0, "mm_submitted": False,
        "mm_input": [], "mm_history": [],
        # Grid ticks
        "tick_r1": 0, "tick_r2": 0, "tick_move": 0, "tick_bfs": 0, "tick_r4": 0,
    }


TICK_AI = 200     # ms between AI moves for rooms 1-3
TICK_P8 = 180     # ms between 8-puzzle tile slides

# ── SORT AI ───────────────────────────────────────────────────────────────────


def ai1_sort_plan(a):
    plan = greedy_sort(a['sort_tubes'])
    a['ls_plan'] = list(plan) if plan else []


def ai2_sort_plan(a):
    plan = astar_sort(a['sort_tubes'])
    a['astar_plan'] = list(plan)

# ── AI TICK ───────────────────────────────────────────────────────────────────


def tick_ai1(a, now, puzzle_tubes):
    if a['finished']:
        return

    if a['room'] == 1:
        if now-a['tick_r1'] < TICK_AI:
            return
        if not a.get('ls_plan'):
            ai1_sort_plan(a)
        if a.get('ls_plan'):
            s2, d2 = a['ls_plan'].pop(0)
            a['sort_tubes'] = apply_move(a['sort_tubes'], s2, d2)
            a['sort_moves'] += 1
            if sort_solved(a['sort_tubes']):
                _advance_room(a, 2)
        else:
            _advance_room(a, 2)
        a['tick_r1'] = now

    elif a['room'] == 2:
        if now-a['tick_r2'] < TICK_AI:
            return
        guess = a['ga_current_guess']
        if guess is None:
            guess = ["1", "1", "2", "2"]
            a['ga_current_guess'] = guess
        if len(a['mm_input']) < 4:
            a['mm_input'].append(guess[len(a['mm_input'])])
        elif not a['ga_submitted']:
            a['ga_submitted'] = True
        else:
            a['mm_guesses'] += 1
            fb = mm_score(guess, a['mm_secret'])
            a['mm_history'].append((list(guess), fb))
            a['ga_history'].append((list(guess), fb))
            if fb == (4, 0):
                _advance_room(a, 3)
            else:
                a['ga_current_guess'] = cbrs_pick(a['ga_history'])
                a['mm_input'] = []
                a['ga_submitted'] = False
        a['tick_r2'] = now

    elif a['room'] == 3:
        if not a['path_queue']:
            _ai1_bfs(a)
        if a['path_queue'] and now-a['tick_move'] > TICK_AI:
            _ai_move_r3(a, a['path_queue'].pop(0))
            a['tick_move'] = now

    elif a['room'] == 4:
        # A* 8-puzzle solver for Agent 1
        if now - a['tick_r4'] < TICK_P8:
            return
        if not a['p8_plan']:
            plan, nodes = p8_astar(a['p8_start'])
            a['p8_plan'] = plan
            a['p8_nodes'] = nodes
            a['nodes_explored'] += nodes
            a['p8_step_idx'] = 0
        idx = a['p8_step_idx']
        if idx < len(a['p8_plan']):
            prev_state = a['p8_state']
            new_state = a['p8_plan'][idx]
            # Find which tile moved for animation
            for i in range(9):
                if prev_state[i] != new_state[i] and prev_state[i] != 0:
                    a['p8_anim_tile'] = (
                        prev_state[i], i, new_state.index(prev_state[i]), now)
                    break
            a['p8_state'] = new_state
            a['p8_step_idx'] = idx + 1
            if a['p8_state'] == P8_GOAL:
                a['p8_solved'] = True
                _advance_room(a, 5)  # 5 = finished
        a['tick_r4'] = now


def tick_ai2(a, now, puzzle_tubes):
    if a['finished']:
        return

    if a['room'] == 1:
        if now-a['tick_r1'] < TICK_AI:
            return
        if not a['astar_plan']:
            ai2_sort_plan(a)
        if a['astar_plan']:
            s2, d2 = a['astar_plan'].pop(0)
            a['sort_tubes'] = apply_move(a['sort_tubes'], s2, d2)
            a['sort_moves'] += 1
            if sort_solved(a['sort_tubes']):
                _advance_room(a, 2)
        else:
            _advance_room(a, 2)
        a['tick_r1'] = now

    elif a['room'] == 2:
        if now-a['tick_r2'] < TICK_AI:
            return
        if not a['mm_plan']:
            a['mm_plan'] = minimax_solve(a['mm_secret'])
            a['mm_plan_idx'] = 0
        if a['mm_plan_idx'] >= len(a['mm_plan']):
            _advance_room(a, 3)
            a['tick_r2'] = now
            return
        guess = a['mm_plan'][a['mm_plan_idx']]
        if len(a['mm_input']) < 4:
            a['mm_input'].append(guess[len(a['mm_input'])])
        elif not a['mm_submitted']:
            a['mm_submitted'] = True
        else:
            a['mm_guesses'] += 1
            fb = mm_score(guess, a['mm_secret'])
            a['mm_history'].append((list(guess), fb))
            if fb == (4, 0):
                _advance_room(a, 3)
            else:
                a['mm_plan_idx'] += 1
                a['mm_input'] = []
                a['mm_submitted'] = False
        a['tick_r2'] = now

    elif a['room'] == 3:
        if not a['path_queue'] and now-a['tick_bfs'] > 0:
            target = pick_target_ai2(a)
            obs = a['crates']
            path, n_exp, frontier = astar_path(a['pos'], target, obs)
            a['nodes_explored'] += n_exp
            # visualise explored nodes like BFS
            a['frontier'] = frontier
            if path:
                a['path_queue'] = path
                a['final_path_visual'] = [list(a['pos'])]+path
            a['tick_bfs'] = now
        if a['path_queue'] and now-a['tick_move'] > TICK_AI:
            _ai_move_r3(a, a['path_queue'].pop(0))
            a['tick_move'] = now

    elif a['room'] == 4:
        # IDA* 8-puzzle solver for Agent 2
        if now - a['tick_r4'] < TICK_P8:
            return
        if not a['p8_plan']:
            plan, nodes = p8_idastar(a['p8_start'])
            a['p8_plan'] = plan
            a['p8_nodes'] = nodes
            a['nodes_explored'] += nodes
            a['p8_step_idx'] = 0
        idx = a['p8_step_idx']
        if idx < len(a['p8_plan']):
            prev_state = a['p8_state']
            new_state = a['p8_plan'][idx]
            for i in range(9):
                if prev_state[i] != new_state[i] and prev_state[i] != 0:
                    a['p8_anim_tile'] = (
                        prev_state[i], i, new_state.index(prev_state[i]), now)
                    break
            a['p8_state'] = new_state
            a['p8_step_idx'] = idx + 1
            if a['p8_state'] == P8_GOAL:
                a['p8_solved'] = True
                _advance_room(a, 5)
        a['tick_r4'] = now

# ── SHARED HELPERS ─────────────────────────────────────────────────────────────


def pick_target_ai1(a):
    avail = [c for c in a['crates'] if c not in a['wrong_crates']]
    return avail[0] if avail else [GRID_SIZE-1, GRID_SIZE-1]


def pick_target_ai2(a):
    avail = [c for c in a['crates'] if c not in a['wrong_crates']]
    return min(avail, key=lambda c: heuristic(c, a['pos'])) if avail else [GRID_SIZE-1, GRID_SIZE-1]


def _ai1_bfs(a):
    target = pick_target_ai1(a)
    obs = a['crates']
    q = deque([(a['pos'], [])])
    vis = {tuple(a['pos'])}
    found = []
    while q:
        (r, c), path = q.popleft()
        if [r, c] == target:
            found = path
            break
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr2, nc2 = r+dr, c+dc
            if 0 <= nr2 < GRID_SIZE and 0 <= nc2 < GRID_SIZE and (nr2, nc2) not in vis:
                if [nr2, nc2] not in obs or [nr2, nc2] == target:
                    vis.add((nr2, nc2))
                    q.append(([nr2, nc2], path+[[nr2, nc2]]))
    a['frontier'] = [list(v) for v in vis]
    a['path_queue'] = found
    a['final_path_visual'] = [list(a['pos'])]+found
    a['nodes_explored'] += len(vis)


def _ai_move_r3(a, step):
    if step in a['crates']:
        if step == a['key_loc']:
            _advance_room(a, 4)
        else:
            a['wrong_crates'].append(step)
            a['wrong_crates_count'] += 1
        a['path_queue'] = []
        a['frontier'] = []
        a['final_path_visual'] = []
    else:
        a['pos'] = step
        if a['final_path_visual']:
            a['final_path_visual'].pop(0)


def _advance_room(a, to_room):
    _record_room_time(a, a['room'])
    if to_room == 5:           # sentinel: 8-puzzle finished → game over
        a['finished'] = True
        a['end_time'] = time.time()
        return
    a['room'] = to_room
    a['input'] = []
    a['pos'] = [0, 0]
    a['path_queue'] = []
    a['frontier'] = []
    a['final_path_visual'] = []
    a['ls_plan'] = []
    a['sort_history'] = []
    a['astar_plan'] = []
    a['ga_history'] = []
    a['ga_current_guess'] = None
    a['ga_submitted'] = False
    a['mm_plan'] = []
    a['mm_plan_idx'] = 0
    a['mm_submitted'] = False
    a['mm_input'] = []
    a['mm_history'] = []
    a['room_entry'][to_room] = time.time()
    # Reset 8-puzzle step index when entering room 4
    if to_room == 4:
        a['p8_step_idx'] = 0
        a['p8_plan'] = []


def _record_room_time(a, room):
    entry = a['room_entry'].get(room)
    if entry:
        a['room_times'][room] = time.time()-entry

# ── HUMAN INPUT ───────────────────────────────────────────────────────────────


def handle_human(h, events, now, ox):
    if h['reset_timer'] > 0 and now > h['reset_timer']:
        h['reset_timer'] = 0
    for e in events:
        if h['finished']:
            continue

        # Room 1: Color Sort
        if e.type == pygame.MOUSEBUTTONDOWN and h['room'] == 1:
            mx, my = pygame.mouse.get_pos()
            ti = _tube_hit(mx, my, ox)
            if ti is not None:
                if h['sort_selected'] is None:
                    if h['sort_tubes'][ti]:
                        h['sort_selected'] = ti
                else:
                    sel = h['sort_selected']
                    if ti == sel:
                        h['sort_selected'] = None
                    elif can_move(h['sort_tubes'], sel, ti):
                        h['sort_history'].append(
                            copy.deepcopy(h['sort_tubes']))
                        h['sort_tubes'] = apply_move(h['sort_tubes'], sel, ti)
                        h['sort_moves'] += 1
                        h['sort_selected'] = None
                        if sort_solved(h['sort_tubes']):
                            _advance_room(h, 2)
                    else:
                        h['sort_invalid_flash'] = now+400
                        if h['sort_tubes'][ti] and ti != sel:
                            h['sort_selected'] = ti
            else:
                h['sort_selected'] = None

        # Room 2: Mastermind
        if e.type == pygame.KEYDOWN and h['room'] == 2:
            if h['reset_timer'] > 0 and e.unicode in MM_DIGITS:
                h['mm_input'] = []
                h['reset_timer'] = 0
                h['mm_input'].append(e.unicode)
            elif h['reset_timer'] == 0:
                if e.key == pygame.K_RETURN and len(h['mm_input']) == 4:
                    h['mm_guesses'] += 1
                    fb = mm_score(h['mm_input'], h['mm_secret'])
                    h['mm_history'].append((list(h['mm_input']), fb))
                    if fb == (4, 0):
                        _advance_room(h, 3)
                    else:
                        h['reset_timer'] = now+2000
                elif e.key == pygame.K_BACKSPACE and h['mm_input']:
                    h['mm_input'].pop()
                elif e.unicode in MM_DIGITS and len(h['mm_input']) < 4:
                    h['mm_input'].append(e.unicode)

        # Room 1 undo
        if e.type == pygame.KEYDOWN and h['room'] == 1:
            if e.key == pygame.K_u and h['sort_history']:
                h['sort_tubes'] = h['sort_history'].pop()
                h['sort_moves'] = max(0, h['sort_moves']-1)
                h['sort_selected'] = None

        # Room 3: nav
        if e.type == pygame.KEYDOWN and h['room'] == 3:
            nr, nc = h['pos']
            if e.key == pygame.K_UP:
                nr -= 1
            elif e.key == pygame.K_DOWN:
                nr += 1
            elif e.key == pygame.K_LEFT:
                nc -= 1
            elif e.key == pygame.K_RIGHT:
                nc += 1
            if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                if [nr, nc] in h['crates']:
                    if [nr, nc] == h['key_loc']:
                        _advance_room(h, 4)
                    else:
                        h['wrong_crates'].append([nr, nc])
                        h['wrong_crates_count'] += 1
                else:
                    h['pos'] = [nr, nc]

        # Room 4: 8-puzzle — click tile adjacent to blank
        if e.type == pygame.MOUSEBUTTONDOWN and h['room'] == 4:
            mx, my = pygame.mouse.get_pos()
            tile_idx = _p8_tile_hit(mx, my, ox, HALF)
            if tile_idx is not None:
                state = h['p8_state']
                blank = state.index(0)
                br, bc2 = divmod(blank, 3)
                tr2, tc2 = divmod(tile_idx, 3)
                if abs(br-tr2)+abs(bc2-tc2) == 1:
                    lst = list(state)
                    lst[blank], lst[tile_idx] = lst[tile_idx], lst[blank]
                    tile_val = state[tile_idx]
                    h['p8_anim_tile'] = (tile_val, tile_idx, blank, now)
                    h['p8_state'] = tuple(lst)
                    if h['p8_state'] == P8_GOAL:
                        h['p8_solved'] = True
                        _advance_room(h, 5)


def _tube_hit(mx, my, ox):
    tw = 52
    th = 140
    gap = 12
    total = SORT_TUBES*tw+(SORT_TUBES-1)*gap
    sx = ox+HALF//2-total//2
    sy = 270
    for i in range(SORT_TUBES):
        tx = sx+i*(tw+gap)
        if tx <= mx <= tx+tw and sy <= my <= sy+th:
            return i
    return None


def _p8_tile_hit(mx, my, ox, W):
    """Return grid index 0-8 if click hits a tile, else None."""
    tile_sz = 110
    gap = 8
    board_w = 3*tile_sz + 2*gap
    bx = ox + W//2 - board_w//2
    by = 210
    for row in range(3):
        for col in range(3):
            tx = bx + col*(tile_sz+gap)
            ty = by + row*(tile_sz+gap)
            if tx <= mx <= tx+tile_sz and ty <= my <= ty+tile_sz:
                return row*3+col
    return None

# ── DRAWING ────────────────────────────────────────────────────────────────────


def draw_sort(surf, data, ox, W, t, acol, is_human):
    area = pygame.Rect(ox+15, 162, W-30, 400)
    dpanel(surf, area, C_DARK, C_STEEL, 6, 2)
    dcorners(surf, area, acol)
    tl = F_HEAD.render("COLOUR SORT PROTOCOL", True, acol)
    surf.blit(tl, (ox+W//2-tl.get_width()//2, 172))
    ins = F_MONO.render(
        "SORT BALLS BY COLOUR  ·  ONLY SAME-COLOUR OR EMPTY TUBE", True, C_GRAY)
    surf.blit(ins, (ox+W//2-ins.get_width()//2, 210))
    tubes = data['sort_tubes']
    tw = 52
    th = 140
    ball_r = 17
    gap = 12
    total = SORT_TUBES*tw+(SORT_TUBES-1)*gap
    sx = ox+W//2-total//2
    sy = 270
    now_ms = pygame.time.get_ticks()
    invalid_flash = (data.get('sort_invalid_flash', 0) > now_ms)
    for i, tube in enumerate(tubes):
        tx = sx+i*(tw+gap)
        sel = (is_human and data.get('sort_selected') == i)
        pure = (len(tube) == TUBE_CAP and len(set(tube)) == 1)
        if pure:
            border = C_GREEN
            bw = 3
        elif sel and invalid_flash:
            border = C_RED_BRIGHT
            bw = 3
        elif sel:
            border = acol
            bw = 3
        else:
            border = C_STEEL
            bw = 2
        is_valid_dest = (is_human and data.get('sort_selected') is not None and
                         not sel and can_move(tubes, data['sort_selected'], i))
        tr = pygame.Rect(tx, sy, tw, th)
        bg = lerp(C_DARK, C_GREEN_DIM, 0.3) if (
            is_valid_dest and not pure) else lerp(C_DARK, C_STEEL, 0.15)
        dpanel(surf, tr, bg, border, 6, bw)
        if sel:
            dglow_rect(surf, tr, acol, 60, 6)
        if is_valid_dest and not pure:
            dglow_rect(surf, tr, C_GREEN, 30, 4)
        for j, ball in enumerate(tube):
            bx2 = tx+tw//2
            by2 = sy+th-ball_r-4-(j*(ball_r*2+4))
            col = SORT_CMAP[ball]
            dglow_circle(surf, (bx2, by2), ball_r+3, col, 50)
            pygame.draw.circle(surf, lerp(
                col, C_DARK, 0.45), (bx2, by2), ball_r)
            pygame.draw.circle(surf, col, (bx2, by2), ball_r, 3)
            pygame.draw.circle(surf, lerp(
                col, C_WHITE, 0.55), (bx2-4, by2-5), 4)
        tn = F_SMALL.render(str(i+1), True, C_GRAY)
        surf.blit(tn, (tx+tw//2-tn.get_width()//2, sy+th+5))
    if sort_solved(tubes):
        msg = F_LABEL.render("▶  SORTED — PROCEEDING", True, C_GREEN)
        surf.blit(msg, (ox+W//2-msg.get_width()//2, sy+th+22))
    elif is_human:
        undo_hint = F_SMALL.render(
            f"[U] UNDO  |  MOVES: {data['sort_moves']}", True, C_GRAY)
        surf.blit(undo_hint, (ox+W//2-undo_hint.get_width()//2, sy+th+22))
    else:
        info = F_SMALL.render(f"MOVES: {data['sort_moves']}", True, C_GRAY)
        surf.blit(info, (ox+W//2-info.get_width()//2, sy+th+22))


def draw_mastermind(surf, data, ox, W, t, acol, is_human):
    area = pygame.Rect(ox+15, 162, W-30, 400)
    dpanel(surf, area, C_DARK, C_STEEL, 6, 2)
    dcorners(surf, area, acol)
    tl = F_HEAD.render("MASTERMIND CIPHER", True, acol)
    surf.blit(tl, (ox+W//2-tl.get_width()//2, 172))
    ins = F_MONO.render(
        "CRACK 4-DIGIT CODE (1-6)  |  GREEN=RIGHT POS  AMBER=WRONG POS  GRAY=NOT IN CODE", True, C_GRAY)
    surf.blit(ins, (ox+W//2-ins.get_width()//2, 210))
    hist = data['mm_history']
    max_show = 5
    start_h = max(0, len(hist)-max_show)
    shown = hist[start_h:]
    slot_w = 46
    slot_h = 30
    slot_gap = 10
    row_total = 4*slot_w+3*slot_gap
    gx = ox+W//2-row_total//2
    hy = 228
    for guess, fb in shown:
        per_slot = mm_per_slot(guess, data['mm_secret'])
        for pi in range(4):
            pr = pygame.Rect(gx+pi*(slot_w+slot_gap), hy, slot_w, slot_h)
            slot_fb = per_slot[pi]
            if slot_fb == 'exact':
                bg = lerp(C_GREEN_DIM, C_DARK, 0.3)
                border = C_GREEN
            elif slot_fb == 'misplaced':
                bg = lerp(C_AMBER_DIM, C_DARK, 0.3)
                border = C_AMBER
            else:
                bg = C_DARK
                border = C_GRAY
            pygame.draw.rect(surf, bg, pr, border_radius=5)
            pygame.draw.rect(surf, border, pr, 2, border_radius=5)
            ps = F_LABEL.render(guess[pi], True, C_WHITE)
            surf.blit(ps, (pr.centerx-ps.get_width() //
                      2, pr.centery-ps.get_height()//2))
        exact_n = per_slot.count('exact')
        misp_n = per_slot.count('misplaced')
        fx = gx+4*(slot_w+slot_gap)+4
        sm = F_SMALL.render(f"✓{exact_n} ~{misp_n}", True, C_GRAY)
        surf.blit(sm, (fx, hy+8))
        hy += slot_h+6
    iy = max(hy+8, 390)
    inp = data['mm_input']
    in_feedback = (data.get('reset_timer', 0) > 0 and len(inp) == 4
                   and bool(hist) and list(inp) == list(hist[-1][0]))
    slot_w2 = 54
    slot_h2 = 52
    slot_gap2 = 10
    row_total2 = 4*slot_w2+3*slot_gap2
    gx2 = ox+W//2-row_total2//2
    for pi in range(4):
        pr = pygame.Rect(gx2+pi*(slot_w2+slot_gap2), iy, slot_w2, slot_h2)
        if pi < len(inp):
            if in_feedback and hist:
                per_slot_cur = mm_per_slot(inp, data['mm_secret'])
                slot_fb = per_slot_cur[pi]
                if slot_fb == 'exact':
                    bg = lerp(C_GREEN_DIM, C_DARK, 0.3)
                    border = C_GREEN
                elif slot_fb == 'misplaced':
                    bg = lerp(C_AMBER_DIM, C_DARK, 0.3)
                    border = C_AMBER
                else:
                    bg = lerp(C_RED_DIM, C_DARK, 0.3)
                    border = C_GRAY
            else:
                bg = lerp(acol, C_DARK, 0.7)
                border = acol
            pygame.draw.rect(surf, bg, pr, border_radius=8)
            pygame.draw.rect(surf, border, pr, 3, border_radius=8)
            ps = F_NUM.render(inp[pi], True, C_WHITE)
            surf.blit(ps, (pr.centerx-ps.get_width() //
                      2, pr.centery-ps.get_height()//2))
        else:
            pygame.draw.rect(surf, C_STEEL, pr, border_radius=8)
            pygame.draw.rect(surf, C_STEEL_LT, pr, 2, border_radius=8)
            if pi == len(inp) and int(t*2) % 2 == 0 and not in_feedback:
                pygame.draw.rect(surf, acol, pygame.Rect(
                    pr.centerx-2, pr.bottom-10, 5, 7), border_radius=2)
        n = F_SMALL.render(f"[{pi+1}]", True, C_GRAY)
        surf.blit(n, (pr.x+2, pr.y+2))
    by2 = iy+slot_h2+10
    if is_human:
        if in_feedback and hist:
            per_slot_last = mm_per_slot(hist[-1][0], data['mm_secret'])
            exact_n = per_slot_last.count('exact')
            misp_n = per_slot_last.count('misplaced')
            fb_surf = F_LABEL.render(
                f"RESULT:  {exact_n} CORRECT POSITION  ·  {misp_n} WRONG POSITION", True, C_AMBER)
            surf.blit(fb_surf, (ox+W//2-fb_surf.get_width()//2, by2))
            nxt = F_MONO.render(
                "PRESS ANY DIGIT KEY (1-6) TO START NEXT GUESS", True, C_GRAY)
            surf.blit(nxt, (ox+W//2-nxt.get_width()//2, by2+20))
        else:
            hint1 = F_MONO.render(
                "TYPE DIGITS  1 – 6  TO FILL SLOTS  |  BACKSPACE = DELETE", True, C_GRAY)
            hint2 = F_MONO.render("ENTER = SUBMIT GUESS", True, C_GRAY)
            surf.blit(hint1, (ox+W//2-hint1.get_width()//2, by2))
            surf.blit(hint2, (ox+W//2-hint2.get_width()//2, by2+18))
            rdy = (len(inp) == 4)
            sbr = pygame.Rect(ox+W//2-90, by2+40, 180, 34)
            pygame.draw.rect(
                surf, C_GREEN_DIM if rdy else C_DARK, sbr, border_radius=7)
            pygame.draw.rect(surf, C_GREEN if rdy else C_STEEL,
                             sbr, 2, border_radius=7)
            if rdy:
                dglow_rect(surf, sbr, C_GREEN, 50, 4)
            ss = F_LABEL.render(
                "▶  PRESS ENTER" if rdy else f"{len(inp)}/4 DIGITS", True, C_GREEN if rdy else C_GRAY)
            surf.blit(ss, (sbr.centerx-ss.get_width() //
                      2, sbr.centery-ss.get_height()//2))
    gc = F_MONO.render(f"GUESSES: {data['mm_guesses']}", True, C_GRAY)
    surf.blit(gc, (ox+W//2-gc.get_width()//2, by2+(42 if is_human else 6)))


def draw_p8(surf, data, ox, W, t, acol, is_human, algo_label):
    """Draw the 8-puzzle (Room 4)."""
    now_ms = pygame.time.get_ticks()
    state = data['p8_state']

    # Panel background
    area = pygame.Rect(ox+15, 155, W-30, 440)
    dpanel(surf, area, C_DARK, C_STEEL, 6, 2)
    dcorners(surf, area, acol)

    # Title
    tl = F_HEAD.render("CIPHER LOCK — 8-PUZZLE", True, acol)
    surf.blit(tl, (ox+W//2-tl.get_width()//2, 163))

    # Sub-title
    sub = F_MONO.render(
        "SLIDE TILES INTO ORDER  ·  BLANK TILE = MOVE SPACE", True, C_GRAY)
    surf.blit(sub, (ox+W//2-sub.get_width()//2, 196))

    # Board geometry
    tile_sz = 110
    gap = 8
    board_w = 3*tile_sz + 2*gap
    board_h = 3*tile_sz + 2*gap
    bx = ox + W//2 - board_w//2
    by = 214

    # Board backing plate
    backing = pygame.Rect(bx-10, by-10, board_w+20, board_h+20)
    pygame.draw.rect(surf, (10, 12, 16), backing, border_radius=12)
    pygame.draw.rect(surf, C_STEEL_LT, backing, 2, border_radius=12)
    dhazard(surf, pygame.Rect(bx-10, by-10, board_w+20, 10), 10)

    # Goal positions ghosted in background
    goal_font = pygame.font.SysFont("impact", 28)
    for gi, gv in enumerate(P8_GOAL):
        if gv == 0:
            continue
        gr2, gc2 = divmod(gi, 3)
        gx2 = bx + gc2*(tile_sz+gap)
        gy2 = by + gr2*(tile_sz+gap)
        gs_surf = goal_font.render(str(gv), True, (28, 32, 40))
        surf.blit(gs_surf, (gx2+tile_sz//2-gs_surf.get_width() //
                  2, gy2+tile_sz//2-gs_surf.get_height()//2))

    # Tile colours — each number has a unique accent
    tile_cols = {
        1: (255,  80,  60),
        2: (255, 160,  20),
        3: (230, 220,  10),
        4: (40,  210,  80),
        5: (30,  170, 255),
        6: (130,  60, 255),
        7: (255,  60, 200),
        8: (0,   200, 180),
    }

    blank_idx = state.index(0)
    anim = data.get('p8_anim_tile')   # (tile_val, from_idx, to_idx, start_ms)

    for i, val in enumerate(state):
        row, col = divmod(i, 3)
        tx = bx + col*(tile_sz+gap)
        ty = by + row*(tile_sz+gap)

        if val == 0:
            # Draw blank slot with pulsing border
            slot_r = pygame.Rect(tx+3, ty+3, tile_sz-6, tile_sz-6)
            p = pulse(t, 2.0, 0.0, 0.3)
            pygame.draw.rect(surf, lerp((10, 12, 16), acol, p),
                             slot_r, border_radius=8)
            pygame.draw.rect(surf, lerp(C_STEEL, acol, p*0.5),
                             slot_r, 2, border_radius=8)
            if is_human:
                # Show arrows for valid moves
                br2, bc3 = divmod(blank_idx, 3)
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr2, nc2 = br2+dr, bc3+dc
                    if 0 <= nr2 < 3 and 0 <= nc2 < 3:
                        ax = tx+tile_sz//2 + dc*30
                        ay = ty+tile_sz//2 + dr*30
                        arrow_s = F_SMALL.render(
                            "◆", True, lerp(C_STEEL, acol, 0.4))
                        surf.blit(arrow_s, (ax-arrow_s.get_width() //
                                  2, ay-arrow_s.get_height()//2))
            continue

        # Animate the sliding tile
        draw_x, draw_y = tx, ty
        if anim and anim[0] == val:
            _, from_i, to_i, start_ms = anim
            elapsed_anim = now_ms - start_ms
            dur = TICK_P8 * 0.75
            if elapsed_anim < dur:
                prog = elapsed_anim / dur
                prog = 1 - (1-prog)**2  # ease-out
                fr_row, fr_col = divmod(from_i, 3)
                to_row, to_col = divmod(to_i, 3)
                draw_x = int((bx+fr_col*(tile_sz+gap)) + prog *
                             ((bx+to_col*(tile_sz+gap))-(bx+fr_col*(tile_sz+gap))))
                draw_y = int((by+fr_row*(tile_sz+gap)) + prog *
                             ((by+to_row*(tile_sz+gap))-(by+fr_row*(tile_sz+gap))))

        tcol = tile_cols.get(val, C_AMBER)
        in_place = (P8_GOAL_IDX[val] == i)

        # Tile shadow
        sh_r = pygame.Rect(draw_x+4, draw_y+5, tile_sz-6, tile_sz-6)
        pygame.draw.rect(surf, (0, 0, 0), sh_r, border_radius=10)

        # Tile face
        tile_r = pygame.Rect(draw_x+2, draw_y+2, tile_sz-4, tile_sz-4)
        bg_col = lerp(tcol, C_DARK, 0.72) if not in_place else lerp(
            tcol, C_DARK, 0.55)
        pygame.draw.rect(surf, bg_col, tile_r, border_radius=10)

        # Bevel top edge
        bevel_r = pygame.Rect(draw_x+2, draw_y+2, tile_sz-4, 6)
        pygame.draw.rect(surf, lerp(tcol, C_WHITE, 0.25),
                         bevel_r, border_radius=10)

        # Border — green glow if in place
        border_col = C_GREEN if in_place else tcol
        bw2 = 3 if in_place else 2
        pygame.draw.rect(surf, border_col, tile_r, bw2, border_radius=10)
        if in_place:
            dglow_rect(surf, tile_r, C_GREEN, 40, 5)

        # Number
        num_s = F_TILE.render(str(val), True, lerp(tcol, C_WHITE, 0.85))
        surf.blit(num_s, (draw_x+tile_sz//2-num_s.get_width() //
                  2, draw_y+tile_sz//2-num_s.get_height()//2))

        # Small position indicator dot (corner rivet)
        pygame.draw.circle(surf, lerp(tcol, C_DARK, 0.5),
                           (draw_x+tile_sz-10, draw_y+10), 4)

    # Stats bar below board
    stats_y = by + board_h + 16
    md = p8_manhattan(state)
    steps_done = data.get('p8_step_idx', 0)
    total_steps = len(data.get('p8_plan', [])) if data.get('p8_plan') else 0
    nodes_v = data.get('p8_nodes', 0)

    if data['p8_solved'] or state == P8_GOAL:
        sv = F_LABEL.render("▶  CIPHER UNLOCKED — ESCAPED!", True, C_GREEN)
        surf.blit(sv, (ox+W//2-sv.get_width()//2, stats_y))
    else:
        stat1 = F_MONO.render(
            f"DIST: {md:2d}  ·  NODES: {nodes_v}", True, C_GRAY)
        surf.blit(stat1, (ox+W//2-stat1.get_width()//2, stats_y))
        if not is_human and total_steps:
            prog_frac = steps_done / total_steps
            bar_w = W - 80
            bar_r = pygame.Rect(ox+40, stats_y+20, bar_w, 8)
            pygame.draw.rect(surf, C_STEEL, bar_r, border_radius=4)
            fill_r = pygame.Rect(ox+40, stats_y+20, int(bar_w*prog_frac), 8)
            pygame.draw.rect(surf, acol, fill_r, border_radius=4)
            pl = F_SMALL.render(
                f"STEP {steps_done}/{total_steps}  ·  ALGO: {algo_label}", True, C_GRAY)
            surf.blit(pl, (ox+W//2-pl.get_width()//2, stats_y+32))
        elif is_human:
            hint = F_SMALL.render(
                "CLICK A TILE NEXT TO THE BLANK TO SLIDE IT", True, C_GRAY)
            surf.blit(hint, (ox+W//2-hint.get_width()//2, stats_y+20))


def draw_grid(surf, data, ox, oy, acol, pcol, t):
    gw = GRID_SIZE*CELL
    dpanel(surf, pygame.Rect(ox-4, oy-4, gw+8, gw+8), C_DARK, C_STEEL_LT, 4, 2)
    dcorners(surf, pygame.Rect(ox-4, oy-4, gw+8, gw+8), acol, 12, 2)
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            rx = ox+c*CELL
            ry = oy+r*CELL
            if [r, c] in data['frontier']:
                pygame.draw.rect(surf, (30, 45, 30),
                                 pygame.Rect(rx, ry, CELL, CELL))
            pygame.draw.rect(surf, C_STEEL, pygame.Rect(rx, ry, CELL, CELL), 1)
    vis = data['final_path_visual']
    if len(vis) > 1:
        pts = [(ox+p[1]*CELL+CELL//2, oy+p[0]*CELL+CELL//2) for p in vis]
        ps = pygame.Surface((gw, gw), pygame.SRCALPHA)
        local = [(p[0]-ox, p[1]-oy) for p in pts]
        for i in range(4, 0, -1):
            if len(local) > 1:
                pygame.draw.lines(ps, (*pcol, 15*i), False, local, i*3)
        surf.blit(ps, (ox, oy))
        if len(pts) > 1:
            pygame.draw.lines(surf, pcol, False, pts, 3)
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            rx = ox+c*CELL
            ry = oy+r*CELL
            cr = pygame.Rect(rx+2, ry+2, CELL-4, CELL-4)
            if [r, c] in data['crates']:
                if [r, c] in data['wrong_crates']:
                    pygame.draw.rect(surf, C_RED_DIM, cr, border_radius=3)
                    pygame.draw.rect(surf, C_RED, cr, 2, border_radius=3)
                    pygame.draw.line(surf, C_RED, (rx+6, ry+6),
                                     (rx+CELL-6, ry+CELL-6), 2)
                    pygame.draw.line(
                        surf, C_RED, (rx+CELL-6, ry+6), (rx+6, ry+CELL-6), 2)
                else:
                    pygame.draw.rect(surf, C_CRATE, cr, border_radius=3)
                    pygame.draw.rect(surf, C_CRATE_LT, cr, 1, border_radius=3)
                    pygame.draw.line(
                        surf, C_CRATE_LT, (rx+CELL//2, ry+3), (rx+CELL//2, ry+CELL-3), 1)
                    pygame.draw.line(
                        surf, C_CRATE_LT, (rx+3, ry+CELL//2), (rx+CELL-3, ry+CELL//2), 1)
    pr, pc2 = data['pos']
    px = ox+pc2*CELL+CELL//2
    py = oy+pr*CELL+CELL//2
    dglow_circle(surf, (px, py), CELL//3+4, acol, 80)
    pygame.draw.circle(surf, lerp(acol, C_WHITE, 0.3), (px, py), CELL//3)
    pygame.draw.circle(surf, acol, (px, py), CELL//3, 2)


AI1_ALGOS = {1: "Greedy Sort", 2: "Constraint-Based Rnd Search",
             3: "BFS",    4: "A* (Manhattan)"}
AI2_ALGOS = {1: "A* Sort ",
             2: "Minimax (Knuth's)",          3: "A*",     4: "IDA* (Manhattan+LC)"}
HUMAN_ALGOS = {1: "Manual Sort", 2: "Manual Mastermind",
               3: "Manual Nav", 4: "Manual Slide"}


def draw_side(surf, data, ox, label, acol, pcol, algos, is_human, t, win_tag):
    W = HALF
    pygame.draw.rect(surf, C_PANEL, pygame.Rect(ox, 0, W, HEIGHT))
    dhazard(surf, pygame.Rect(ox, 0, W, 8), 10)
    hdr = pygame.Rect(ox+10, 14, W-20, 68)
    dpanel(surf, hdr, C_DARK, acol, 4, 2)
    drivets(surf, hdr, C_STEEL_LT, 3)
    fl = flicker(t, hash(label) % 100)
    dshadow(surf, F_TITLE.render(label, True, lerp(
        acol, C_WHITE, fl*0.2)), (ox+22, 18))
    rs = F_HEAD.render(
        f"ROOM {min(data['room'], 4)}/4", True, C_GREEN if data['finished'] else C_AMBER)
    surf.blit(rs, (ox+W-rs.get_width()-22, 26))
    elapsed = (data['end_time'] if data['finished']
               else time.time())-data['start_time']
    tr = pygame.Rect(ox+10, 88, W-20, 32)
    dpanel(surf, tr, C_DARK, C_STEEL, 3, 1)
    ts2 = F_LABEL.render(
        f"▶  ELAPSED  {elapsed:08.3f}s", True, C_GREEN if data['finished'] else C_AMBER)
    surf.blit(ts2, (ox+20, 95))
    dot_col = (C_RED_BRIGHT if not data['finished'] and int(
        t*2) % 2 == 0 else C_RED_DIM)
    pygame.draw.circle(surf, dot_col, (ox+W-30, 104), 6)
    algo_str = algos.get(data['room'], "")
    ar = pygame.Rect(ox+10, 126, W-20, 24)
    dpanel(surf, ar, C_DARK, C_STEEL, 2, 1)
    surf.blit(F_MONO.render(f"  ALGO: {algo_str}", True, C_GRAY), (ox+14, 129))

    if data['room'] == 1:
        draw_sort(surf, data, ox, W, t, acol, is_human)
    elif data['room'] == 2:
        draw_mastermind(surf, data, ox, W, t, acol, is_human)
    elif data['room'] == 3:
        ll = F_LABEL.render("CARGO BAY — FIND THE KEY CRATE", True, C_GRAY)
        surf.blit(ll, (ox+W//2-ll.get_width()//2, 158))
        draw_grid(surf, data, ox+(W-GRID_SIZE*CELL)//2, 175, acol, pcol, t)
        inf = F_MONO.render(
            f"CRATES REMAIN: {len([c for c in data['crates'] if c not in data['wrong_crates']])}  |  WRONG: {len(data['wrong_crates'])}", True, C_GRAY)
        surf.blit(inf, (ox+10, HEIGHT-36))
    elif data['room'] == 4:
        draw_p8(surf, data, ox, W, t, acol, is_human, algo_str)

    if data['finished']:
        ov = pygame.Surface((W, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 30, 0, 60))
        surf.blit(ov, (ox, 0))
        sc = lerp(C_GREEN_DIM, C_GREEN, pulse(t, 1.8))
        es = F_HUGE.render("ESCAPED", True, sc)
        ex = ox+W//2-es.get_width()//2
        ey = HEIGHT//2-es.get_height()//2
        dglow_rect(surf, pygame.Rect(ex-10, ey-6, es.get_width() +
                   20, es.get_height()+12), C_GREEN, 100, 12)
        surf.blit(es, (ex, ey))
        tf = F_LABEL.render(f"FINAL TIME:  {elapsed:.3f}s", True, C_WHITE)
        surf.blit(tf, (ox+W//2-tf.get_width()//2, ey+es.get_height()+10))
        if win_tag:
            wc = C_AMBER if win_tag == "WINNER" else C_GRAY
            ws = F_HEAD.render(
                f"🏆  {win_tag}" if win_tag == "WINNER" else win_tag, True, wc)
            surf.blit(ws, (ox+W//2-ws.get_width()//2, ey+es.get_height()+44))
    dhazard(surf, pygame.Rect(ox, HEIGHT-8, W, 8), 10)


def draw_report(surf, d1, d2, n1, n2, c1, c2, t):
    surf.fill(C_BG)
    surf.blit(_noise, (0, 0))
    for x in range(0, WIDTH, 60):
        pygame.draw.line(surf, (18, 22, 28), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, 60):
        pygame.draw.line(surf, (18, 22, 28), (0, y), (WIDTH, y))
    tp = pygame.Rect(WIDTH//2-380, 18, 760, 60)
    dpanel(surf, tp, C_DARK, C_AMBER, 6, 2)
    drivets(surf, tp, C_STEEL_LT, 4)
    dhazard(surf, pygame.Rect(tp.x, tp.y, tp.width, 10), 10)
    tls = F_RPT_T.render("PERFORMANCE ANALYSIS REPORT", True, C_AMBER)
    surf.blit(tls, (WIDTH//2-tls.get_width()//2, 30))
    el1 = (d1['end_time']-d1['start_time']) if d1['end_time'] else 999
    el2 = (d2['end_time']-d2['start_time']) if d2['end_time'] else 999
    win1 = el1 < el2
    cx = [60, 560, 900]
    ry = 95
    def hdr(tx, x, y, c): surf.blit(F_LABEL.render(tx, True, c), (x, y))
    def val(tx, x, y, c): surf.blit(F_RPT_S.render(tx, True, c), (x, y))
    def bc(v1, v2): return (C_GREEN, C_RED_BRIGHT) if v1 <= v2 else (
        C_RED_BRIGHT, C_GREEN)
    hdr("METRIC", cx[0], ry, C_GRAY)
    hdr(n1, cx[1], ry, c1)
    hdr(n2, cx[2], ry, c2)
    pygame.draw.line(surf, C_STEEL, (40, ry+22), (WIDTH-40, ry+22), 1)
    r4_n1 = d1['p8_nodes']
    r4_n2 = d2['p8_nodes']
    r4_steps1 = d1.get('p8_step_idx', 0)
    r4_steps2 = d2.get('p8_step_idx', 0)
    rows = [
        ("TOTAL TIME",    f"{el1:.3f}s",     f"{el2:.3f}s",
         c1 if win1 else C_GRAY, c2 if not win1 else C_GRAY),
        ("R1 ALGO",       "Greedy Sort",      "A* Sort",          C_GRAY, C_GRAY),
        ("R1 SORT MOVES", str(d1['sort_moves']), str(
            d2['sort_moves']), *bc(d1['sort_moves'], d2['sort_moves'])),
        ("R2 ALGO",       "CBRS",             "Minimax/Knuth",    C_GRAY, C_GRAY),
        ("R2 MM GUESSES", str(d1['mm_guesses']), str(
            d2['mm_guesses']), *bc(d1['mm_guesses'], d2['mm_guesses'])),
        ("R3 ALGO",       "BFS",              "A*",               C_GRAY, C_GRAY),
        ("R3 NODES",      str(d1['nodes_explored']-r4_n1), str(d2['nodes_explored']-r4_n2),
         *bc(d1['nodes_explored']-r4_n1, d2['nodes_explored']-r4_n2)),
        ("WRONG CRATES",  str(d1['wrong_crates_count']), str(
            d2['wrong_crates_count']), *bc(d1['wrong_crates_count'], d2['wrong_crates_count'])),
        ("R4 ALGO",       "A* (Manhattan)",
         "IDA* (Manhattan+LC)", C_GRAY, C_GRAY),
        ("R4 NODES",      str(r4_n1),         str(
            r4_n2),         *bc(r4_n1, r4_n2)),
        ("R4 MOVES",      str(r4_steps1),     str(
            r4_steps2),     *bc(r4_steps1, r4_steps2)),
    ]
    for rm, rn in [(1, "R1 TIME"), (2, "R2 TIME"), (3, "R3 TIME"), (4, "R4 TIME")]:
        t1r = d1['room_times'].get(rm)
        t2r = d2['room_times'].get(rm)
        s1 = f"{t1r:.3f}s" if t1r else "—"
        s2 = f"{t2r:.3f}s" if t2r else "—"
        cr1 = C_GREEN if (t1r and t2r and t1r <= t2r) else (
            C_AMBER if t1r else C_GRAY)
        cr2 = C_GREEN if (t1r and t2r and t2r <= t1r) else (
            C_AMBER if t2r else C_GRAY)
        rows.append((rn, s1, s2, cr1, cr2))
    for i, (metric, v1, v2, vc1, vc2) in enumerate(rows):
        row_y = ry+36+i*26
        pygame.draw.rect(surf, (20, 22, 28) if i % 2 == 0 else (
            14, 16, 20), pygame.Rect(40, row_y-4, WIDTH-80, 22), border_radius=4)
        hdr(metric, cx[0], row_y, C_GRAY)
        val(v1, cx[1], row_y, vc1)
        val(v2, cx[2], row_y, vc2)
    vy = ry+36+len(rows)*26+12
    vr = pygame.Rect(WIDTH//2-300, vy, 600, 76)
    wc = c1 if win1 else c2
    wn = n1 if win1 else n2
    dpanel(surf, vr, C_DARK, wc, 8, 3)
    dglow_rect(surf, vr, wc, 80, 10)
    dhazard(surf, pygame.Rect(vr.x, vr.y, vr.width, 10), 10)
    wl = F_RPT_T.render(f"WINNER:  {wn}", True, wc)
    surf.blit(wl, (WIDTH//2-wl.get_width()//2, vy+10))
    diff = abs(el1-el2)
    dl = F_LABEL.render(
        f"MARGIN:  {diff:.3f}s  ({diff/max(el1, el2)*100:.1f}% faster)", True, C_WHITE)
    surf.blit(dl, (WIDTH//2-dl.get_width()//2, vy+46))
    surf.blit(F_MONO.render("PRESS  ESC  TO RETURN TO MENU",
              True, C_GRAY), (WIDTH//2-120, HEIGHT-28))
    surf.blit(_scan, (0, 0))
    pygame.display.flip()


def draw_menu(surf, t):
    surf.fill(C_BG)
    surf.blit(_noise, (0, 0))
    surf.blit(_scan, (0, 0))
    for x in range(0, WIDTH, 60):
        pygame.draw.line(surf, (18, 22, 28), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, 60):
        pygame.draw.line(surf, (18, 22, 28), (0, y), (WIDTH, y))
    gb = pygame.Surface((600, 400), pygame.SRCALPHA)
    for r2 in range(200, 0, -10):
        pygame.draw.circle(gb, (20, 60, 20, int(8*(1-r2/200))), (300, 200), r2)
    surf.blit(gb, (WIDTH//2-300, HEIGHT//2-200))
    tp = pygame.Rect(WIDTH//2-380, 40, 760, 110)
    dpanel(surf, tp, (10, 14, 12), C_GREEN, 8, 3)
    dhazard(surf, pygame.Rect(tp.x, tp.y, tp.width, 14), 14)
    dhazard(surf, pygame.Rect(tp.x, tp.bottom-14, tp.width, 14), 14)
    drivets(surf, tp, C_STEEL_LT, 5)
    tc = lerp(C_GREEN_DIM, C_GREEN, pulse(t, 1.2))
    tmp = F_MENU_T.render("LOCKDOWN", True, tc)
    dshadow(surf, tmp, (WIDTH//2-tmp.get_width()//2, 52), C_BG, 3)
    pygame.draw.line(surf, C_STEEL, (100, 170), (WIDTH-100, 170), 1)
    surf.blit(F_MONO.render("▶  SELECT OPERATION MODE  ◀", True, C_AMBER),
              (WIDTH//2-F_MONO.render("▶  SELECT OPERATION MODE  ◀", True, C_AMBER).get_width()//2, 182))
    rd = F_SMALL.render(
        "R1: Colour Sort  ·  R2: Mastermind  ·  R3: Crate Maze  ·  R4: 8-Puzzle Cipher Lock", True, C_GRAY)
    surf.blit(rd, (WIDTH//2-rd.get_width()//2, 198))
    mx, my = pygame.mouse.get_pos()
    b1 = pygame.Rect(WIDTH//2-340, 222, 680, 150)
    h1 = b1.collidepoint(mx, my)
    dpanel(surf, b1, (16, 28, 48) if h1 else (12, 18, 28),
           C_BLUE if h1 else C_STEEL, 8, 2+(1 if h1 else 0))
    if h1:
        dglow_rect(surf, b1, C_BLUE, 80, 10)
        dcorners(surf, b1, C_BLUE, 18, 3)
    else:
        dcorners(surf, b1, C_STEEL_LT, 14, 1)
    dhazard(surf, pygame.Rect(b1.x, b1.y, b1.width, 10), 10)
    surf.blit(F_MENU_S.render("MODE 01  ·  HUMAN  vs  AI", True, C_BLUE if h1 else C_WHITE),
              (b1.centerx-F_MENU_S.render("MODE 01  ·  HUMAN  vs  AI", True, C_BLUE if h1 else C_WHITE).get_width()//2, b1.y+20))
    pygame.draw.line(surf, C_STEEL, (b1.x+20, b1.y+58),
                     (b1.right-20, b1.y+58), 1)
    for i, txt in enumerate(["Sort  ·  Mastermind  ·  Crate Maze  ·  8-Puzzle Cipher Lock",
                            "Race against AI Agent  ·  CLICK tiles to slide (Room 4)"]):
        s = F_MENU_B.render(txt, True, C_GRAY)
        surf.blit(s, (b1.centerx-s.get_width()//2, b1.y+70+i*24))
    if h1:
        cl = F_MONO.render("[ CLICK TO START ]", True, C_BLUE)
        surf.blit(cl, (b1.centerx-cl.get_width()//2, b1.y+122))
    b2 = pygame.Rect(WIDTH//2-340, 390, 680, 180)
    h2 = b2.collidepoint(mx, my)
    dpanel(surf, b2, (30, 16, 12) if h2 else (18, 12, 10),
           C_RED if h2 else C_STEEL, 8, 2+(1 if h2 else 0))
    if h2:
        dglow_rect(surf, b2, C_RED, 80, 10)
        dcorners(surf, b2, C_RED, 18, 3)
    else:
        dcorners(surf, b2, C_STEEL_LT, 14, 1)
    dhazard(surf, pygame.Rect(b2.x, b2.y, b2.width, 10), 10)
    surf.blit(F_MENU_S.render("MODE 02  ·  AI  vs  AI", True, C_RED if h2 else C_WHITE),
              (b2.centerx-F_MENU_S.render("MODE 02  ·  AI  vs  AI", True, C_RED if h2 else C_WHITE).get_width()//2, b2.y+20))
    pygame.draw.line(surf, C_STEEL, (b2.x+20, b2.y+58),
                     (b2.right-20, b2.y+58), 1)
    for i, (txt, col) in enumerate([
        ("AGENT 1 · Greedy Sort · CBRS · BFS · A* (Manhattan)", C_GRAY),
        ("AGENT 2 · A* Sort · Minimax (Knuth's) · A* · IDA* (Manhattan+LC)", C_GRAY),
            ("Identical puzzles · Full performance report at end", C_GRAY)]):
        s = F_MENU_B.render(txt, True, col)
        surf.blit(s, (b2.centerx-s.get_width()//2, b2.y+72+i*30))
    if h2:
        cl = F_MONO.render("[ CLICK TO START ]", True, C_RED)
        surf.blit(cl, (b2.centerx-cl.get_width()//2, b2.y+156))
    pygame.draw.line(surf, C_STEEL, (100, 590), (WIDTH-100, 590), 1)
    for i, (txt, col) in enumerate([
            ("ESC  ·  MENU    R1: CLICK TUBES    R2: TYPE 1-6 → ENTER    R3: ARROWS    R4: CLICK TILES", C_GRAY)]):
        s = F_MONO.render(txt, True, col)
        surf.blit(s, (WIDTH//2-s.get_width()//2, 602+i*22))
    sb = pygame.Rect(0, HEIGHT-30, WIDTH, 30)
    pygame.draw.rect(surf, C_DARK, sb)
    pygame.draw.line(surf, C_STEEL, (0, HEIGHT-30), (WIDTH, HEIGHT-30), 1)
    ts2 = F_SMALL.render(
        f"SYS: ONLINE  ·  {time.strftime('%H:%M:%S')}  ·  LOCKDOWN ESCAPE FACILITY", True, C_GRAY)
    surf.blit(ts2, (20, HEIGHT-22))
    surf.blit(_scan, (0, 0))
    pygame.display.flip()
    return b1, b2


def render_game(left, right, lname, rname, lcol, rcol, lalgos, ralgos, l_is_human, t, lt, rt):
    screen.fill(C_BG)
    screen.blit(_noise, (0, 0))
    lpcol = (0, 140, 255) if lcol == C_BLUE else (255, 100, 0)
    rpcol = (255, 80, 0) if rcol == C_ORANGE else (0, 200, 100)
    draw_side(screen, left, 0, lname, lcol, lpcol, lalgos, l_is_human, t, lt)
    draw_side(screen, right, HALF, rname, rcol, rpcol, ralgos, False, t, rt)
    dsep(screen, HALF, 0, HEIGHT, C_STEEL)
    dhazard(screen, pygame.Rect(HALF-4, 0, 8, HEIGHT), 12)
    pygame.draw.line(screen, (0, 0, 0), (HALF-1, 0), (HALF-1, HEIGHT), 2)
    pygame.draw.line(screen, (0, 0, 0), (HALF+1, 0), (HALF+1, HEIGHT), 2)
    vsr = pygame.Rect(HALF-28, HEIGHT//2-28, 56, 56)
    pygame.draw.rect(screen, C_DARK, vsr, border_radius=28)
    pygame.draw.rect(screen, C_AMBER, vsr, 2, border_radius=28)
    vs = F_HEAD.render("VS", True, C_AMBER)
    screen.blit(vs, (HALF-vs.get_width()//2, HEIGHT//2-vs.get_height()//2))
    sb = pygame.Rect(0, HEIGHT-30, WIDTH, 30)
    pygame.draw.rect(screen, C_DARK, sb)
    pygame.draw.line(screen, C_STEEL, (0, HEIGHT-30), (WIDTH, HEIGHT-30), 1)
    ts2 = F_SMALL.render(
        f"SYS: ACTIVE  ·  {time.strftime('%H:%M:%S')}  ·  ESC = MENU", True, C_GRAY)
    screen.blit(ts2, (WIDTH//2-ts2.get_width()//2, HEIGHT-22))
    screen.blit(_scan, (0, 0))
    pygame.display.flip()


def compute_win_tags(d1, d2):
    if d1['finished'] and d2['finished']:
        t1 = d1['end_time']-d1['start_time']
        t2 = d2['end_time']-d2['start_time']
        if t1 < t2:
            return "WINNER", "DEFEATED"
        elif t2 < t1:
            return "DEFEATED", "WINNER"
        return "DRAW", "DRAW"
    elif d1['finished']:
        return "LEADING", None
    elif d2['finished']:
        return None, "LEADING"
    return None, None


# ── MAIN LOOP ─────────────────────────────────────────────────────────────────
clock = pygame.time.Clock()
game_mode = "menu"
h = gen_state()
a = gen_state()
show_report = False
pt_shared = None

while True:
    t = time.time()
    now = pygame.time.get_ticks()
    events = pygame.event.get()
    for e in events:
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            game_mode = "menu"
            h = gen_state()
            a = gen_state()
            show_report = False
            pt_shared = None

    if game_mode == "menu":
        b1, b2 = draw_menu(screen, t)
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                if b1.collidepoint(e.pos):
                    game_mode = "human_vs_ai"
                    h = gen_state()
                    a = gen_state()
                    show_report = False
                    pt_shared = None
                elif b2.collidepoint(e.pos):
                    game_mode = "ai_vs_ai"
                    shared = gen_shared_puzzles()
                    pt_shared = copy.deepcopy(shared["sort_tubes"])
                    h = gen_state(shared)
                    a = gen_state(shared)
                    show_report = False
        clock.tick(60)
        continue

    if game_mode == "ai_vs_ai" and show_report:
        draw_report(screen, h, a, "AGENT 1", "AGENT 2", C_BLUE, C_ORANGE, t)
        clock.tick(30)
        continue

    if game_mode == "human_vs_ai":
        handle_human(h, events, now, 0)
        tick_ai1(a, now, a['sort_tubes'])
        lt, rt = compute_win_tags(h, a)
        render_game(h, a, "HUMAN", "AI", C_BLUE, C_RED,
                    HUMAN_ALGOS, AI1_ALGOS, True, t, lt, rt)

    elif game_mode == "ai_vs_ai":
        orig = pt_shared if pt_shared else h['sort_tubes']
        tick_ai1(h, now, orig)
        tick_ai2(a, now, orig)
        if h['finished'] and a['finished'] and not show_report:
            show_report = True
        lt, rt = compute_win_tags(h, a)
        render_game(h, a, "AGENT 1", "AGENT 2", C_BLUE, C_ORANGE,
                    AI1_ALGOS, AI2_ALGOS, False, t, lt, rt)

    clock.tick(30)
