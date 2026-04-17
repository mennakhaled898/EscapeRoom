import pygame
import sys
import random
import time
import heapq
import math
from collections import deque

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

COLOR_KEYS = ["R", "G", "B", "Y"]
COLOR_MAP = {"R": C_RED_BRIGHT, "G": C_GREEN, "B": C_BLUE, "Y": C_YELLOW}
COLOR_NAMES = {"R": "RED",        "G": "GRN",   "B": "BLU",  "Y": "YLW"}

# ── FONTS ─────────────────────────────────────────────────────────────────────
try:
    F_TITLE = pygame.font.SysFont("impact", 54)
    F_HEAD = pygame.font.SysFont("impact", 32)
    F_LABEL = pygame.font.SysFont("couriernew", 16, bold=True)
    F_MONO = pygame.font.SysFont("couriernew", 14, bold=True)
    F_SMALL = pygame.font.SysFont("couriernew", 12)
    F_HUGE = pygame.font.SysFont("impact", 80)
    F_NUM = pygame.font.SysFont("impact", 42)
    F_MENU_T = pygame.font.SysFont("impact", 72)
    F_MENU_S = pygame.font.SysFont("impact", 28)
    F_MENU_B = pygame.font.SysFont("couriernew", 17, bold=True)
    F_RPT_T = pygame.font.SysFont("impact", 38)
    F_RPT_S = pygame.font.SysFont("couriernew", 15, bold=True)
except Exception:
    _fb = pygame.font.SysFont(None, 24)
    F_TITLE = F_HEAD = F_LABEL = F_MONO = F_SMALL = F_HUGE = F_NUM = F_MENU_T = F_MENU_S = F_MENU_B = F_RPT_T = F_RPT_S = _fb

# ── STATIC TEXTURES ───────────────────────────────────────────────────────────
_noise = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
_rng = random.Random(42)
for _ in range(18000):
    _noise.set_at((_rng.randint(0, WIDTH-1), _rng.randint(0, HEIGHT-1)),
                  (_rng.randint(0, 40),)*3 + (_rng.randint(20, 80),))

_scan = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
for _y in range(0, HEIGHT, 3):
    pygame.draw.line(_scan, (0, 0, 0, 38), (0, _y), (WIDTH, _y))

# ── MATH / COLOUR HELPERS ─────────────────────────────────────────────────────


def lerp(a, b, t):
    return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))


def pulse(t, speed=2.0, lo=0.4, hi=1.0):
    return lo+(hi-lo)*(0.5+0.5*math.sin(t*speed))


def flicker(t, seed=0):
    return 0.85+0.15*math.sin(t*17.3+seed)*math.sin(t*5.1+seed*2)

# ── DRAW PRIMITIVES ───────────────────────────────────────────────────────────


def dpanel(s, r, col=C_PANEL, bdr=C_STEEL, rad=6, bw=2):
    pygame.draw.rect(s, col, r, border_radius=rad)
    pygame.draw.rect(s, bdr, r, bw, border_radius=rad)


def drivets(s, r, col=C_RIVET, rad=4):
    for ox, oy in [(10, 10), (-10, 10), (10, -10), (-10, -10)]:
        cx = r.left+(10 if ox > 0 else r.width-10)
        cy = r.top + (10 if oy > 0 else r.height-10)
        pygame.draw.circle(s, col, (cx, cy), rad)
        pygame.draw.circle(s, lerp(col, C_WHITE, 0.3), (cx-1, cy-1), rad//2)


def dhazard(s, r, w=12):
    clip = s.get_clip()
    s.set_clip(r)
    step = w*2
    for x in range(r.left-r.height, r.right+step, step):
        pygame.draw.polygon(s, C_HAZARD_Y,
                            [(x, r.top), (x+w, r.top), (x+w+r.height, r.bottom), (x+r.height, r.bottom)])
        pygame.draw.polygon(s, C_HAZARD_B,
                            [(x+w, r.top), (x+w*2, r.top), (x+w*2+r.height, r.bottom), (x+w+r.height, r.bottom)])
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
    for (cx, cy), (dx, dy) in zip(
        [(r.x, r.y), (r.right, r.y), (r.x, r.bottom), (r.right, r.bottom)],
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

# ── PATHFINDING ───────────────────────────────────────────────────────────────


def heuristic(a, b):
    return abs(a[0]-b[0])+abs(a[1]-b[1])


def bfs_path(start, goal, obstacles, gs=GRID_SIZE):
    """BFS — returns path list (excl. start) or []."""
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


def astar_path(start, goal, obstacles, gs=GRID_SIZE):
    """A* — returns path list (excl. start) or []."""
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
            return path
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
    return []


def is_solvable(start, goal, obstacles, gs=GRID_SIZE):
    return len(bfs_path(start, goal, obstacles, gs)) > 0 or start == goal

# ── STATE GENERATION ──────────────────────────────────────────────────────────


def gen_obstacles_validated(n, gs=GRID_SIZE):
    """Generate n obstacles, guaranteed BFS-solvable from (0,0)→(gs-1,gs-1)."""
    protected = [[0, 0], [0, 1], [1, 0], [
        gs-1, gs-1], [gs-2, gs-1], [gs-1, gs-2]]
    for _ in range(200):          # retry up to 200 times
        obs = []
        attempts = 0
        while len(obs) < n and attempts < 20000:
            attempts += 1
            r, c = random.randint(0, gs-1), random.randint(0, gs-1)
            if [r, c] not in obs and [r, c] not in protected:
                obs.append([r, c])
        if is_solvable([0, 0], [gs-1, gs-1], obs, gs):
            return obs
    # Fallback: empty grid (always solvable)
    return []


def gen_state():
    r3 = gen_obstacles_validated(10)   # Room 3: crates
    r4 = gen_obstacles_validated(20)   # Room 4: lasers — guaranteed solvable
    return {
        # Core
        "room": 1, "pos": [0, 0], "input": [],
        "secret_code": [random.choice(COLOR_KEYS) for _ in range(4)],
        "target_num": random.randint(100, 999), "hint": "ENTER CODE 100-999",
        "crates": r3, "key_loc": random.choice(r3) if r3 else [5, 5],
        "lasers": r4, "wrong_crates": [], "finished": False,
        "start_time": time.time(), "end_time": None,
        "path_queue": [], "frontier": [], "final_path_visual": [],
        "reset_timer": 0,
        # Per-room timing stats
        "room_times": {1: None, 2: None, 3: None, 4: None},
        "room_entry": {1: time.time(), 2: None, 3: None, 4: None},
        "color_guesses": 0, "number_guesses": 0, "wrong_crates_count": 0,
        # AI1 fields
        "ai_low": 100, "ai_high": 999, "ai_target_guess": "",
        "ai_known_slots": [None]*4, "ai_tried_per_slot": [set() for _ in range(4)],
        "bfs_queue": deque(), "bfs_visited": set(), "bfs_active": False, "bfs_target": None,
        # AI2 fields
        "bt_partial": [], "bt_domains": [list(COLOR_KEYS) for _ in range(4)],
        "inf_low": 100, "inf_high": 999, "inf_guess": "",
        # Shared tick timers — one per agent, no shared state
        "tick_r1": 0, "tick_r2": 0, "tick_move": 0, "tick_bfs": 0,
    }


# ── AI AGENT 1: BFS / Gaussian Binary Search / Slot Elimination ───────────────
TICK_AI = 150   # ms between AI decisions — identical for both agents


def tick_ai1(a, now):
    if a['finished']:
        return

    if a['room'] == 1:
        if now-a['tick_r1'] < TICK_AI:
            return
        if len(a['input']) == 4:
            a['color_guesses'] += 1
            if a['input'] == a['secret_code']:
                _advance_room(a, 2)
            else:
                for i in range(4):
                    if a['input'][i] == a['secret_code'][i]:
                        a['ai_known_slots'][i] = a['input'][i]
                    else:
                        a['ai_tried_per_slot'][i].add(a['input'][i])
                a['input'] = []
        else:
            idx = len(a['input'])
            if a['ai_known_slots'][idx]:
                a['input'].append(a['ai_known_slots'][idx])
            else:
                poss = [
                    c for c in COLOR_KEYS if c not in a['ai_tried_per_slot'][idx]]
                a['input'].append(random.choice(
                    poss) if poss else random.choice(COLOR_KEYS))
        a['tick_r1'] = now

    elif a['room'] == 2:
        if now-a['tick_r2'] < TICK_AI:
            return
        if not a['ai_target_guess']:
            span = a['ai_high']-a['ai_low']
            mu = (a['ai_low']+a['ai_high'])/2
            a['ai_target_guess'] = str(max(a['ai_low'], min(a['ai_high'],
                                                            int(random.gauss(mu, span/6 if span > 0 else 1)))))
            a['input'] = []
        elif len(a['input']) < len(a['ai_target_guess']):
            a['input'].append(a['ai_target_guess'][len(a['input'])])
        else:
            a['number_guesses'] += 1
            g = int(a['ai_target_guess'])
            if g == a['target_num']:
                _advance_room(a, 3)
            else:
                if g < a['target_num']:
                    a['ai_low'] = g+1
                    a['hint'] = "HIGHER"
                else:
                    a['ai_high'] = g-1
                    a['hint'] = "LOWER"
                a['ai_target_guess'] = ""
                a['input'] = []
        a['tick_r2'] = now

    elif a['room'] in [3, 4]:
        # BFS planning phase
        if not a['bfs_active'] and not a['path_queue']:
            _ai1_plan_bfs(a)
        if a['bfs_active'] and now-a['tick_bfs'] > 15:
            _ai1_step_bfs(a)
            a['tick_bfs'] = now
        elif not a['bfs_active'] and a['path_queue'] and now-a['tick_move'] > TICK_AI:
            _ai_move(a, a['path_queue'].pop(0))
            a['tick_move'] = now


def _ai1_plan_bfs(a):
    target = _pick_target(a)
    a['bfs_target'] = target
    a['bfs_queue'] = deque([(a['pos'], [])])
    a['bfs_visited'] = {tuple(a['pos'])}
    a['frontier'] = []
    a['final_path_visual'] = []
    a['bfs_active'] = True


def _ai1_step_bfs(a):
    if a['bfs_queue']:
        (r, c), path = a['bfs_queue'].popleft()
        a['frontier'].append([r, c])
        if [r, c] == a['bfs_target']:
            a['path_queue'] = path
            a['final_path_visual'] = [list(a['pos'])]+list(path)
            a['bfs_active'] = False
        else:
            obs = a['lasers'] if a['room'] == 4 else a['crates']
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr2, nc2 = r+dr, c+dc
                if 0 <= nr2 < GRID_SIZE and 0 <= nc2 < GRID_SIZE and (nr2, nc2) not in a['bfs_visited']:
                    if [nr2, nc2] not in obs or [nr2, nc2] == a['bfs_target']:
                        a['bfs_visited'].add((nr2, nc2))
                        a['bfs_queue'].append(([nr2, nc2], path+[[nr2, nc2]]))
    else:
        a['bfs_active'] = False

# ── AI AGENT 2: A* / Pure Binary Search / Backtracking + Pruning ─────────────


def tick_ai2(a, now):
    if a['finished']:
        return

    if a['room'] == 1:
        if now-a['tick_r1'] < TICK_AI:
            return
        bt = a['bt_partial']
        domains = a['bt_domains']
        if len(bt) == 4:
            a['color_guesses'] += 1
            if bt == a['secret_code']:
                _advance_room(a, 2)
            else:
                for i in range(4):
                    if bt[i] == a['secret_code'][i]:
                        domains[i] = [bt[i]]
                    else:
                        if bt[i] in domains[i]:
                            domains[i].remove(bt[i])
                        if not domains[i]:
                            domains[i] = list(COLOR_KEYS)
                a['bt_partial'] = []
                a['input'] = []
        else:
            idx = len(bt)
            bt.append(domains[idx][0] if domains[idx] else COLOR_KEYS[0])
            a['input'] = list(bt)
        a['tick_r1'] = now

    elif a['room'] == 2:
        if now-a['tick_r2'] < TICK_AI:
            return
        if not a['inf_guess']:
            a['inf_guess'] = str((a['inf_low']+a['inf_high'])//2)
            a['input'] = []
        elif len(a['input']) < len(a['inf_guess']):
            a['input'].append(a['inf_guess'][len(a['input'])])
        else:
            a['number_guesses'] += 1
            g = int(a['inf_guess'])
            if g == a['target_num']:
                _advance_room(a, 3)
            else:
                if g < a['target_num']:
                    a['inf_low'] = g+1
                    a['hint'] = "HIGHER"
                else:
                    a['inf_high'] = g-1
                    a['hint'] = "LOWER"
                a['inf_guess'] = ""
                a['input'] = []
        a['tick_r2'] = now

    elif a['room'] in [3, 4]:
        if not a['path_queue'] and now-a['tick_bfs'] > 0:
            target = _pick_target(a)
            obs = a['lasers'] if a['room'] == 4 else a['crates']
            path = astar_path(a['pos'], target, obs)
            if path:
                a['path_queue'] = path
                a['final_path_visual'] = [list(a['pos'])]+path
            a['tick_bfs'] = now
        if a['path_queue'] and now-a['tick_move'] > TICK_AI:
            _ai_move(a, a['path_queue'].pop(0))
            a['tick_move'] = now

# ── SHARED AI HELPERS ─────────────────────────────────────────────────────────


def _pick_target(a):
    if a['room'] == 4:
        return [GRID_SIZE-1, GRID_SIZE-1]
    avail = [c for c in a['crates'] if c not in a['wrong_crates']]
    return min(avail, key=lambda c: heuristic(c, a['pos'])) if avail else [GRID_SIZE-1, GRID_SIZE-1]


def _ai_move(a, step):
    if a['room'] == 3 and step in a['crates']:
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
        if a['room'] == 4 and a['pos'] == [GRID_SIZE-1, GRID_SIZE-1]:
            a['finished'] = True
            a['end_time'] = time.time()
            _record_room_time(a, 4)


def _advance_room(a, to_room):
    _record_room_time(a, a['room'])
    a['room'] = to_room
    a['input'] = []
    a['pos'] = [0, 0]
    a['path_queue'] = []
    a['frontier'] = []
    a['final_path_visual'] = []
    a['bfs_active'] = False
    a['bfs_queue'] = deque()
    a['bfs_visited'] = set()
    a['room_entry'][to_room] = time.time()


def _record_room_time(a, room):
    entry = a['room_entry'].get(room)
    if entry:
        a['room_times'][room] = time.time()-entry

# ── HUMAN INPUT ───────────────────────────────────────────────────────────────


def handle_human(h, events, now):
    if h['reset_timer'] > 0 and now > h['reset_timer']:
        h['input'] = []
        h['reset_timer'] = 0
    for e in events:
        if h['finished']:
            continue
        if e.type == pygame.MOUSEBUTTONDOWN and h['room'] == 1 and h['reset_timer'] == 0:
            mx, my = pygame.mouse.get_pos()
            slot_w = 72
            total_w = 4*slot_w+3*10
            sx = HALF//2-total_w//2
            btn_y = 248+slot_w+30
            for i, key in enumerate(COLOR_KEYS):
                br = pygame.Rect(sx+i*(slot_w+10), btn_y, slot_w, slot_w)
                if br.collidepoint(mx, my):
                    h['input'].append(key)
                    if len(h['input']) == 4:
                        h['color_guesses'] += 1
                        if h['input'] == h['secret_code']:
                            _advance_room(h, 2)
                        else:
                            h['reset_timer'] = now+900
        if e.type == pygame.KEYDOWN:
            if h['room'] == 2:
                if e.key == pygame.K_RETURN:
                    v = "".join(h['input'])
                    val = int(v) if v.isdigit() else 0
                    h['number_guesses'] += 1
                    if val == h['target_num']:
                        _advance_room(h, 3)
                    else:
                        h['hint'] = "HIGHER" if val < h['target_num'] else "LOWER"
                        h['input'] = []
                elif e.key == pygame.K_BACKSPACE:
                    h['input'] = h['input'][:-1]
                elif e.unicode.isdigit():
                    h['input'].append(e.unicode)
            elif h['room'] in [3, 4]:
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
                    if h['room'] == 3 and [nr, nc] in h['crates']:
                        if [nr, nc] == h['key_loc']:
                            _advance_room(h, 4)
                        else:
                            h['wrong_crates'].append([nr, nc])
                            h['wrong_crates_count'] += 1
                    elif h['room'] == 4 and [nr, nc] in h['lasers']:
                        h['pos'] = [0, 0]
                    else:
                        h['pos'] = [nr, nc]
                    if h['room'] == 4 and h['pos'] == [GRID_SIZE-1, GRID_SIZE-1]:
                        h['finished'] = True
                        h['end_time'] = time.time()
                        _record_room_time(h, 4)

# ── DRAWING: GRID ─────────────────────────────────────────────────────────────


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
            if data['room'] == 3 and [r, c] in data['crates']:
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
            if data['room'] == 4:
                if [r, c] in data['lasers']:
                    p2 = pulse(t, 4.0, 0.5, 1.0)
                    pygame.draw.rect(surf, lerp(
                        C_RED_DIM, C_LASER_GLOW, p2-0.5), cr, border_radius=2)
                    pygame.draw.rect(surf, C_LASER_GLOW,
                                     cr, 1, border_radius=2)
                if [r, c] == [0, 0]:
                    pygame.draw.rect(surf, C_GREEN_DIM, cr, border_radius=3)
                    pygame.draw.rect(surf, C_GREEN, cr, 2, border_radius=3)
                    lbl = F_SMALL.render("START", True, C_GREEN)
                    surf.blit(lbl, (rx+CELL//2-lbl.get_width() //
                              2, ry+CELL//2-lbl.get_height()//2))
                if [r, c] == [GRID_SIZE-1, GRID_SIZE-1]:
                    ec = lerp(C_AMBER_DIM, C_AMBER, pulse(t, 1.5))
                    pygame.draw.rect(surf, ec, cr, border_radius=3)
                    pygame.draw.rect(surf, C_AMBER, cr, 2, border_radius=3)
                    lbl = F_SMALL.render("EXIT", True, C_AMBER)
                    surf.blit(lbl, (rx+CELL//2-lbl.get_width() //
                              2, ry+CELL//2-lbl.get_height()//2))
    pr, pc2 = data['pos']
    px = ox+pc2*CELL+CELL//2
    py = oy+pr*CELL+CELL//2
    dglow_circle(surf, (px, py), CELL//3+4, acol, 80)
    pygame.draw.circle(surf, lerp(acol, C_WHITE, 0.3), (px, py), CELL//3)
    pygame.draw.circle(surf, acol, (px, py), CELL//3, 2)

# ── DRAWING: ROOMS 1 & 2 ──────────────────────────────────────────────────────


def draw_room1(surf, data, ox, W, t, acol, is_human):
    area = pygame.Rect(ox+15, 162, W-30, 380)
    dpanel(surf, area, C_DARK, C_STEEL, 6, 2)
    dcorners(surf, area, acol)
    t1 = F_HEAD.render("ACCESS CODE ENTRY", True, acol)
    surf.blit(t1, (ox+W//2-t1.get_width()//2, 172))
    ins = F_MONO.render("MATCH THE 4-COLOR SECURITY CODE", True, C_GRAY)
    surf.blit(ins, (ox+W//2-ins.get_width()//2, 210))
    slot_w = 72
    total_w = 4*slot_w+3*10
    sx = ox+W//2-total_w//2
    sy = 248
    for i in range(4):
        sr = pygame.Rect(sx+i*(slot_w+10), sy, slot_w, slot_w)
        filled = i < len(data['input'])
        correct = len(
            data['input']) == 4 and data['input'][i] == data['secret_code'][i]
        if filled:
            fc = COLOR_MAP[data['input'][i]]
            pygame.draw.rect(surf, lerp(fc, C_DARK, 0.6), sr, border_radius=6)
            pygame.draw.rect(surf, fc, sr, 3, border_radius=6)
            if correct:
                dglow_rect(surf, sr, C_GREEN, 120, 8)
            lbl = F_HEAD.render(
                "✓" if correct else data['input'][i], True, C_GREEN if correct else fc)
            surf.blit(lbl, (sr.centerx-lbl.get_width() //
                      2, sr.centery-lbl.get_height()//2))
        else:
            pygame.draw.rect(surf, C_STEEL, sr, border_radius=6)
            pygame.draw.rect(surf, C_STEEL_LT, sr, 2, border_radius=6)
            if i == len(data['input']) and int(t*2) % 2 == 0:
                pygame.draw.rect(surf, acol, pygame.Rect(
                    sr.centerx-3, sr.bottom-14, 6, 8), border_radius=2)
        n = F_SMALL.render(f"[{i+1}]", True, C_GRAY)
        surf.blit(n, (sr.x+2, sr.y+2))
    btn_y = sy+slot_w+30
    for i, (key, col) in enumerate(COLOR_MAP.items()):
        br = pygame.Rect(sx+i*(slot_w+10), btn_y, slot_w, slot_w)
        if is_human:
            hov = br.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(surf, lerp(
                col, C_DARK, 0.35 if hov else 0.55), br, border_radius=8)
            pygame.draw.rect(surf, col, br, 4 if hov else 3, border_radius=8)
            if hov:
                dglow_rect(surf, br, col, 80, 6)
        else:
            pygame.draw.rect(surf, lerp(col, C_DARK, 0.7), br, border_radius=8)
            pygame.draw.rect(surf, lerp(col, C_DARK, 0.3),
                             br, 2, border_radius=8)
        ks = F_HEAD.render(COLOR_NAMES[key], True, col)
        surf.blit(ks, (br.centerx-ks.get_width() //
                  2, br.centery-ks.get_height()//2))
    if len(data['input']) == 4:
        msg = F_LABEL.render("▶  CODE ACCEPTED — PROCEEDING" if data['input'] == data['secret_code']
                             else "✖  INCORRECT CODE — RETRYING", True,
                             C_GREEN if data['input'] == data['secret_code'] else C_RED_BRIGHT)
    else:
        msg = F_LABEL.render(
            f"ENTERED: {len(data['input'])}/4 COLORS", True, C_GRAY)
    surf.blit(msg, (ox+W//2-msg.get_width()//2, btn_y+slot_w+16))


def draw_room2(surf, data, ox, W, t, acol, is_human):
    area = pygame.Rect(ox+15, 162, W-30, 380)
    dpanel(surf, area, C_DARK, C_STEEL, 6, 2)
    dcorners(surf, area, acol)
    tl = F_HEAD.render("NUMERIC KEYPAD OVERRIDE", True, acol)
    surf.blit(tl, (ox+W//2-tl.get_width()//2, 172))
    # Hint
    if "HIGHER" in data['hint']:
        arrow = "▲ NUMBER IS HIGHER"
        hcol = C_GREEN
    elif "LOWER" in data['hint']:
        arrow = "▼ NUMBER IS LOWER"
        hcol = C_RED_BRIGHT
    else:
        arrow = data['hint']
        hcol = C_GRAY
    hr = pygame.Rect(ox+30, 215, W-60, 42)
    dpanel(surf, hr, C_DARK, hcol, 4, 2)
    hs = F_LABEL.render(arrow, True, hcol)
    surf.blit(hs, (hr.centerx-hs.get_width() //
              2, hr.centery-hs.get_height()//2))
    # Number display
    num_str = "".join(data['input'])+("_" if int(t*2) % 2 == 0 else " ")
    if not data['input']:
        num_str = "---"
    nr2 = pygame.Rect(ox+60, 275, W-120, 90)
    dpanel(surf, nr2, C_DARK, acol, 6, 2)
    dglow_rect(surf, nr2, acol, 40, 6)
    ns = F_NUM.render(num_str, True, acol)
    surf.blit(ns, (nr2.centerx-ns.get_width() //
              2, nr2.centery-ns.get_height()//2))
    # ── Range indicator — shown for BOTH AI agents ──
    if not is_human:
        lo = data['ai_low'] if data.get(
            'ai_target_guess') is not None else data.get('inf_low', 100)
        hi = data['ai_high'] if data.get(
            'ai_target_guess') is not None else data.get('inf_high', 999)
        # Determine which agent this is: AI1 uses ai_low/ai_high, AI2 uses inf_low/inf_high
        # Both keys always present; show both:
        lo1, hi1 = data['ai_low'], data['ai_high']
        lo2, hi2 = data['inf_low'], data['inf_high']
        # Active range is whichever has been narrowed more
        act_lo = max(lo1, lo2)
        act_hi = min(hi1, hi2)
        # Just pick the right one: if inf_guess key in use (AI2) use inf_, else ai_
        if data['inf_guess'] or (data['inf_low'] != 100 or data['inf_high'] != 999):
            rng_str = f"SEARCH RANGE:  {data['inf_low']}  —  {data['inf_high']}"
        else:
            rng_str = f"SEARCH RANGE:  {data['ai_low']}  —  {data['ai_high']}"
        rng = F_MONO.render(rng_str, True, C_AMBER)
        rr = pygame.Rect(ox+30, 374, W-60, 26)
        dpanel(surf, rr, C_DARK, C_AMBER_DIM, 3, 1)
        surf.blit(rng, (rr.centerx-rng.get_width()//2, rr.y+5))
    else:
        ins = F_MONO.render(
            "TYPE NUMBER  ·  ENTER TO CONFIRM  ·  BACKSPACE", True, C_GRAY)
        surf.blit(ins, (ox+W//2-ins.get_width()//2, 384))
    # Keypad graphic
    kp_x = ox+W//2-90
    kp_y = 415
    for i, d in enumerate(["1", "2", "3", "4", "5", "6", "7", "8", "9", "⌫", "0", "↵"]):
        kr = pygame.Rect(kp_x+(i % 3)*62, kp_y+(i//3)*46, 56, 40)
        bc = C_RED_DIM if d == "⌫" else (
            C_GREEN_DIM if d == "↵" else C_STEEL_LT)
        fc = C_RED_BRIGHT if d == "⌫" else (C_GREEN if d == "↵" else C_WHITE)
        pygame.draw.rect(surf, bc, kr, border_radius=4)
        pygame.draw.rect(surf, C_STEEL, kr, 1, border_radius=4)
        ds = F_LABEL.render(d, True, fc)
        surf.blit(ds, (kr.centerx-ds.get_width() //
                  2, kr.centery-ds.get_height()//2))


# ── DRAWING: SIDE PANEL ───────────────────────────────────────────────────────
AI1_ALGOS = {1: "Slot Elimination", 2: "Gaussian BinSearch",
             3: "BFS + Greedy", 4: "BFS + Greedy"}
AI2_ALGOS = {1: "Backtrack+Prune", 2: "Informed Search",
             3: "A* Search",   4: "A* Search"}
HUMAN_ALGOS = {1: "Manual Input",    2: "Manual Input",
               3: "Manual Nav",  4: "Manual Nav"}


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
        f"ROOM {data['room']}/4", True, C_GREEN if data['finished'] else C_AMBER)
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
    # Room content
    if data['room'] == 1:
        draw_room1(surf, data, ox, W, t, acol, is_human)
    elif data['room'] == 2:
        draw_room2(surf, data, ox, W, t, acol, is_human)
    elif data['room'] in [3, 4]:
        lbl_txt = {3: "CARGO BAY — FIND THE KEY CRATE",
                   4: "LASER GRID — REACH THE EXIT"}
        ll = F_LABEL.render(lbl_txt.get(data['room'], ""), True, C_GRAY)
        surf.blit(ll, (ox+W//2-ll.get_width()//2, 158))
        draw_grid(surf, data, ox+(W-GRID_SIZE*CELL)//2, 175, acol, pcol, t)
        if data['room'] == 3:
            inf = F_MONO.render(
                f"CRATES REMAIN: {len([c for c in data['crates'] if c not in data['wrong_crates']])}  |  WRONG: {len(data['wrong_crates'])}", True, C_GRAY)
        else:
            inf = F_MONO.render(
                "AVOID LASER GRIDS  ·  REACH EXIT [9,9]", True, C_GRAY)
        surf.blit(inf, (ox+10, HEIGHT-36))
    # Escaped overlay
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

# ── DRAWING: PERFORMANCE REPORT ───────────────────────────────────────────────


def draw_report(surf, d1, d2, name1, name2, col1, col2, t):
    """Full-screen report shown after both agents finish (AI vs AI mode)."""
    surf.fill(C_BG)
    surf.blit(_noise, (0, 0))
    # Grid bg
    for x in range(0, WIDTH, 60):
        pygame.draw.line(surf, (18, 22, 28), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, 60):
        pygame.draw.line(surf, (18, 22, 28), (0, y), (WIDTH, y))

    # Title
    tp = pygame.Rect(WIDTH//2-380, 18, 760, 60)
    dpanel(surf, tp, C_DARK, C_AMBER, 6, 2)
    drivets(surf, tp, C_STEEL_LT, 4)
    dhazard(surf, pygame.Rect(tp.x, tp.y, tp.width, 10), 10)
    tls = F_RPT_T.render("PERFORMANCE ANALYSIS REPORT", True, C_AMBER)
    surf.blit(tls, (WIDTH//2-tls.get_width()//2, 30))

    el1 = (d1['end_time']-d1['start_time']) if d1['end_time'] else 999
    el2 = (d2['end_time']-d2['start_time']) if d2['end_time'] else 999
    winner_is_1 = el1 < el2

    # Column headers
    col_x = [200, 520, 830]   # label, agent1, agent2
    row_y = 110

    def hdr(txt, x, y, col): surf.blit(F_LABEL.render(txt, True, col), (x, y))
    def val(txt, x, y, col): surf.blit(F_RPT_S.render(txt, True, col), (x, y))

    hdr("METRIC",          col_x[0], row_y, C_GRAY)
    hdr(name1,             col_x[1], row_y, col1)
    hdr(name2,             col_x[2], row_y, col2)
    pygame.draw.line(surf, C_STEEL, (60, row_y+22), (WIDTH-60, row_y+22), 1)

    rows = [
        ("TOTAL TIME",
         f"{el1:.3f}s", f"{el2:.3f}s",
         col1 if winner_is_1 else C_GRAY, col2 if not winner_is_1 else C_GRAY),
        ("COLOR GUESSES",
         str(d1['color_guesses']), str(d2['color_guesses']),
         C_GREEN if d1['color_guesses'] <= d2['color_guesses'] else C_RED_BRIGHT,
         C_GREEN if d2['color_guesses'] <= d1['color_guesses'] else C_RED_BRIGHT),
        ("NUMBER GUESSES",
         str(d1['number_guesses']), str(d2['number_guesses']),
         C_GREEN if d1['number_guesses'] <= d2['number_guesses'] else C_RED_BRIGHT,
         C_GREEN if d2['number_guesses'] <= d1['number_guesses'] else C_RED_BRIGHT),
        ("WRONG CRATES",
         str(d1['wrong_crates_count']), str(d2['wrong_crates_count']),
         C_GREEN if d1['wrong_crates_count'] <= d2['wrong_crates_count'] else C_RED_BRIGHT,
         C_GREEN if d2['wrong_crates_count'] <= d1['wrong_crates_count'] else C_RED_BRIGHT),
    ]

    room_names = {1: "ROOM 1 (COLORS)", 2: "ROOM 2 (NUMBERS)",
                  3: "ROOM 3 (CRATES)", 4: "ROOM 4 (LASERS)"}
    for rm in [1, 2, 3, 4]:
        t1r = d1['room_times'].get(rm)
        t2r = d2['room_times'].get(rm)
        s1 = f"{t1r:.3f}s" if t1r else "—"
        s2 = f"{t2r:.3f}s" if t2r else "—"
        c1r = C_GREEN if (t1r and t2r and t1r <= t2r) else (
            C_AMBER if t1r else C_GRAY)
        c2r = C_GREEN if (t1r and t2r and t2r <= t1r) else (
            C_AMBER if t2r else C_GRAY)
        rows.append((room_names[rm], s1, s2, c1r, c2r))

    for i, (metric, v1, v2, vc1, vc2) in enumerate(rows):
        ry = row_y+40+i*38
        bg_col = (20, 22, 28) if i % 2 == 0 else (14, 16, 20)
        pygame.draw.rect(surf, bg_col, pygame.Rect(
            60, ry-4, WIDTH-120, 34), border_radius=4)
        hdr(metric,  col_x[0], ry, C_GRAY)
        val(v1,      col_x[1], ry, vc1)
        val(v2,      col_x[2], ry, vc2)

    # Verdict box
    vy = row_y+40+len(rows)*38+20
    vr = pygame.Rect(WIDTH//2-300, vy, 600, 80)
    winner_col = col1 if winner_is_1 else col2
    winner_name = name1 if winner_is_1 else name2
    diff = abs(el1-el2)
    dpanel(surf, vr, C_DARK, winner_col, 8, 3)
    dglow_rect(surf, vr, winner_col, 80, 10)
    dhazard(surf, pygame.Rect(vr.x, vr.y, vr.width, 10), 10)
    wl = F_RPT_T.render(f"🏆  WINNER:  {winner_name}", True, winner_col)
    surf.blit(wl, (WIDTH//2-wl.get_width()//2, vy+12))
    dl = F_LABEL.render(f"MARGIN OF VICTORY:  {diff:.3f}s  ({(diff/max(el1, el2)*100):.1f}% faster)",
                        True, C_WHITE)
    surf.blit(dl, (WIDTH//2-dl.get_width()//2, vy+50))

    # Footer
    foot = F_MONO.render("PRESS  ESC  TO RETURN TO MENU", True, C_GRAY)
    surf.blit(foot, (WIDTH//2-foot.get_width()//2, HEIGHT-30))

    surf.blit(_scan, (0, 0))
    pygame.display.flip()

# ── MENU ──────────────────────────────────────────────────────────────────────


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
    dshadow(surf, F_MENU_T.render("LOCKDOWN", True, tc), (WIDTH//2 -
            F_MENU_T.render("LOCKDOWN", True, tc).get_width()//2, 52), C_BG, 3)
    pygame.draw.line(surf, C_STEEL, (100, 170), (WIDTH-100, 170), 1)
    wn = F_MONO.render("▶  SELECT OPERATION MODE  ◀", True, C_AMBER)
    surf.blit(wn, (WIDTH//2-wn.get_width()//2, 182))
    mx, my = pygame.mouse.get_pos()
    # Button 1
    b1 = pygame.Rect(WIDTH//2-340, 220, 680, 160)
    h1 = b1.collidepoint(mx, my)
    dpanel(surf, b1, (16, 28, 48) if h1 else (12, 18, 28),
           C_BLUE if h1 else C_STEEL, 8, 2+(1 if h1 else 0))
    if h1:
        dglow_rect(surf, b1, C_BLUE, 80, 10)
        dcorners(surf, b1, C_BLUE, 18, 3)
    else:
        dcorners(surf, b1, C_STEEL_LT, 14, 1)
    dhazard(surf, pygame.Rect(b1.x, b1.y, b1.width, 10), 10)
    b1t = F_MENU_S.render("MODE 01  ·  HUMAN  vs  AI",
                          True, C_BLUE if h1 else C_WHITE)
    surf.blit(b1t, (b1.centerx-b1t.get_width()//2, b1.y+20))
    pygame.draw.line(surf, C_STEEL, (b1.x+20, b1.y+62),
                     (b1.right-20, b1.y+62), 1)
    for i, txt in enumerate(["You navigate the escape rooms using keyboard & mouse",
                            "Race against AI Agent using BFS · Binary Search · Greedy"]):
        s = F_MENU_B.render(txt, True, C_GRAY)
        surf.blit(s, (b1.centerx-s.get_width()//2, b1.y+76+i*24))
    if h1:
        cl = F_MONO.render("[ CLICK TO START ]", True, C_BLUE)
        surf.blit(cl, (b1.centerx-cl.get_width()//2, b1.y+132))
    # Button 2
    b2 = pygame.Rect(WIDTH//2-340, 408, 680, 180)
    h2 = b2.collidepoint(mx, my)
    dpanel(surf, b2, (30, 16, 12) if h2 else (18, 12, 10),
           C_RED if h2 else C_STEEL, 8, 2+(1 if h2 else 0))
    if h2:
        dglow_rect(surf, b2, C_RED, 80, 10)
        dcorners(surf, b2, C_RED, 18, 3)
    else:
        dcorners(surf, b2, C_STEEL_LT, 14, 1)
    dhazard(surf, pygame.Rect(b2.x, b2.y, b2.width, 10), 10)
    b2t = F_MENU_S.render("MODE 02  ·  AI  vs  AI",
                          True, C_RED if h2 else C_WHITE)
    surf.blit(b2t, (b2.centerx-b2t.get_width()//2, b2.y+20))
    pygame.draw.line(surf, C_STEEL, (b2.x+20, b2.y+62),
                     (b2.right-20, b2.y+62), 1)
    for i, (txt, col) in enumerate([
        ("AGENT 1  ·  BFS ·  Gaussian Binary Search  ·  Slot Elimination", C_GRAY),
        ("AGENT 2  ·  A* ·  Informed Search  ·  Backtracking + Pruning", C_GRAY),
            ("Watch two AI Agents race through all 4 rooms ", C_GRAY)]):
        s = F_MENU_B.render(txt, True, col)
        surf.blit(s, (b2.centerx-s.get_width()//2, b2.y+76+i*28))
    if h2:
        cl = F_MONO.render("[ CLICK TO START ]", True, C_RED)
        surf.blit(cl, (b2.centerx-cl.get_width()//2, b2.y+158))
    pygame.draw.line(surf, C_STEEL, (100, 608), (WIDTH-100, 608), 1)
    for i, (txt, col) in enumerate([
        ("ESC  ·  RETURN TO MENU FROM GAME", C_GRAY),
            ("ARROW KEYS  ·  MOVEMENT      ENTER  ·  CONFIRM      BACKSPACE  ·  DELETE", (45, 50, 60))]):
        s = F_MONO.render(txt, True, col)
        surf.blit(s, (WIDTH//2-s.get_width()//2, 620+i*26))
    sb = pygame.Rect(0, HEIGHT-30, WIDTH, 30)
    pygame.draw.rect(surf, C_DARK, sb)
    pygame.draw.line(surf, C_STEEL, (0, HEIGHT-30), (WIDTH, HEIGHT-30), 1)
    ts = F_SMALL.render(
        f"SYS: ONLINE  ·  {time.strftime('%H:%M:%S')}  ·  LOCKDOWN ESCAPE FACILITY  ·  AUTHORIZED PERSONNEL ONLY", True, C_GRAY)
    surf.blit(ts, (20, HEIGHT-22))
    surf.blit(_scan, (0, 0))
    pygame.display.flip()
    return b1, b2

# ── MAIN GAME RENDER ──────────────────────────────────────────────────────────


def render_game(left, right, lname, rname, lcol, rcol, lalgos, ralgos, l_is_human,
                t, l_win_tag, r_win_tag):
    screen.fill(C_BG)
    screen.blit(_noise, (0, 0))
    lpcol = (0, 140, 255) if lcol == C_BLUE else (255, 100, 0)
    rpcol = (255, 80, 0) if rcol == C_ORANGE else (0, 200, 100)
    draw_side(screen, left, 0,    lname, lcol, lpcol,
              lalgos, l_is_human, t, l_win_tag)
    draw_side(screen, right, HALF, rname, rcol,
              rpcol, ralgos, False,      t, r_win_tag)
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
    ts = F_SMALL.render(
        f"SYS: ACTIVE  ·  {time.strftime('%H:%M:%S')}  ·  PRESS ESC TO RETURN TO MENU", True, C_GRAY)
    screen.blit(ts, (WIDTH//2-ts.get_width()//2, HEIGHT-22))
    screen.blit(_scan, (0, 0))
    pygame.display.flip()

# ── WIN TAG LOGIC ─────────────────────────────────────────────────────────────


def compute_win_tags(d1, d2):
    """Return (tag_for_d1, tag_for_d2). Winner is strictly the faster finisher."""
    if d1['finished'] and d2['finished']:
        t1 = d1['end_time']-d1['start_time']
        t2 = d2['end_time']-d2['start_time']
        if t1 < t2:
            return "WINNER", "DEFEATED"
        elif t2 < t1:
            return "DEFEATED", "WINNER"
        else:
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

    # ── MENU ──
    if game_mode == "menu":
        b1, b2 = draw_menu(screen, t)
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                if b1.collidepoint(e.pos):
                    game_mode = "human_vs_ai"
                    h = gen_state()
                    a = gen_state()
                    show_report = False
                elif b2.collidepoint(e.pos):
                    game_mode = "ai_vs_ai"
                    h = gen_state()
                    a = gen_state()
                    show_report = False
        clock.tick(60)
        continue

    # ── AI vs AI REPORT ──
    if game_mode == "ai_vs_ai" and show_report:
        draw_report(screen, h, a, "AGENT 1",
                    "AGENT 2", C_BLUE, C_ORANGE, t)
        clock.tick(30)
        continue

    # ── HUMAN vs AI ──
    if game_mode == "human_vs_ai":
        handle_human(h, events, now)
        tick_ai1(a, now)
        lt, rt = compute_win_tags(h, a)
        render_game(h, a, "HUMAN", "AI AGENT", C_BLUE, C_RED,
                    HUMAN_ALGOS, AI1_ALGOS, True, t, lt, rt)

    # ── AI vs AI ──
    elif game_mode == "ai_vs_ai":
        tick_ai1(h, now)
        tick_ai2(a, now)
        # Trigger report once both done
        if h['finished'] and a['finished'] and not show_report:
            show_report = True
        lt, rt = compute_win_tags(h, a)
        render_game(h, a, "AGENT 1", "AGENT 2", C_BLUE, C_ORANGE,
                    AI1_ALGOS, AI2_ALGOS, False, t, lt, rt)

    clock.tick(30)
