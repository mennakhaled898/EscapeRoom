import pygame
import sys
import random
import time
import heapq
import math
from collections import deque

pygame.init()
pygame.mixer.init()

# ── DISPLAY ──────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 1280, 800
HALF = WIDTH // 2
GRID_SIZE = 10
CELL = 38
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("LOCKDOWN — Escape Room")

# ── PALETTE ──────────────────────────────────────────────────────────────────
# Industrial thriller: near-black steel, acid amber, blood red, toxic green
C_BG = (8,   9,  11)
C_PANEL = (14,  16,  20)
C_PANEL_LT = (20,  23,  29)
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
C_BLUE_DIM = (14,  55,  90)
C_YELLOW = (255, 220,  20)
C_CYAN = (0, 220, 200)
C_WHITE = (230, 235, 240)
C_GRAY = (80,  90, 105)
C_DARK = (18,  20,  25)
C_ORANGE = (255, 120,  20)
C_PURPLE = (170,  50, 230)
C_HAZARD_Y = (230, 200,   0)
C_HAZARD_B = (18,  20,  25)
C_LASER = (200,  15,  15)
C_LASER_GLOW = (255,  50,  50)
C_CRATE = (90,  60,  20)
C_CRATE_LT = (140,  95,  35)
C_KEY_CRATE = (20, 160,  80)

COLOR_KEYS = ["R", "G", "B", "Y"]
COLOR_MAP = {"R": C_RED_BRIGHT, "G": C_GREEN, "B": C_BLUE, "Y": C_YELLOW}
COLOR_NAMES = {"R": "RED", "G": "GRN", "B": "BLU", "Y": "YLW"}

# ── FONTS ─────────────────────────────────────────────────────────────────────
try:
    F_TITLE = pygame.font.SysFont("impact",        54, bold=False)
    F_HEAD = pygame.font.SysFont("impact",        32)
    F_LABEL = pygame.font.SysFont("couriernew",    16, bold=True)
    F_MONO = pygame.font.SysFont("couriernew",    14, bold=True)
    F_SMALL = pygame.font.SysFont("couriernew",    12)
    F_HUGE = pygame.font.SysFont("impact",        80)
    F_NUM = pygame.font.SysFont("impact",        42)
    F_MENU_T = pygame.font.SysFont("impact",        72)
    F_MENU_S = pygame.font.SysFont("impact",        28)
    F_MENU_B = pygame.font.SysFont("couriernew",    17, bold=True)
except:
    F_TITLE = F_HEAD = F_LABEL = F_MONO = F_SMALL = F_HUGE = F_NUM = F_MENU_T = F_MENU_S = F_MENU_B = pygame.font.SysFont(
        None, 24)

# ── NOISE TEXTURE SURFACE ─────────────────────────────────────────────────────
_noise_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
_noise_surf.fill((0, 0, 0, 0))
rng = random.Random(42)
for _ in range(18000):
    x = rng.randint(0, WIDTH-1)
    y = rng.randint(0, HEIGHT-1)
    v = rng.randint(0, 40)
    _noise_surf.set_at((x, y), (v, v, v, rng.randint(20, 80)))

# ── SCANLINE SURFACE ──────────────────────────────────────────────────────────
_scan_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
for y in range(0, HEIGHT, 3):
    pygame.draw.line(_scan_surf, (0, 0, 0, 38), (0, y), (WIDTH, y))

# ── HELPERS ───────────────────────────────────────────────────────────────────


def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i]-a[i])*t) for i in range(3))


def draw_panel(surf, rect, col=C_PANEL, border=C_STEEL, radius=6, bw=2):
    pygame.draw.rect(surf, col, rect, border_radius=radius)
    pygame.draw.rect(surf, border, rect, bw, border_radius=radius)


def draw_rivets(surf, rect, col=C_RIVET, r=4):
    for ox, oy in [(10, 10), (-10, 10), (10, -10), (-10, -10)]:
        cx = rect.x + (rect.width//2 + ox) if ox > 0 else rect.x + \
            (rect.width//2 + ox)
        cx = rect.left + (10 if ox > 0 else rect.width-10)
        cy = rect.top + (10 if oy > 0 else rect.height-10)
        pygame.draw.circle(surf, col, (cx, cy), r)
        pygame.draw.circle(surf, lerp_color(
            col, C_WHITE, 0.3), (cx-1, cy-1), r//2)


def draw_hazard_stripe(surf, rect, w=12):
    """Draw diagonal hazard stripes inside rect."""
    clip = surf.get_clip()
    surf.set_clip(rect)
    step = w * 2
    for x in range(rect.left - rect.height, rect.right + step, step):
        pts = [
            (x,            rect.top),
            (x + w,        rect.top),
            (x + w + rect.height, rect.bottom),
            (x + rect.height, rect.bottom),
        ]
        pygame.draw.polygon(surf, C_HAZARD_Y, pts)
        pts2 = [
            (x + w,               rect.top),
            (x + w*2,             rect.top),
            (x + w*2+rect.height, rect.bottom),
            (x + w + rect.height, rect.bottom),
        ]
        pygame.draw.polygon(surf, C_HAZARD_B, pts2)
    surf.set_clip(clip)


def draw_glow_circle(surf, pos, radius, col, alpha=80):
    glow = pygame.Surface((radius*4, radius*4), pygame.SRCALPHA)
    for r2 in range(radius*2, 0, -2):
        a2 = int(alpha * (1 - r2/(radius*2)))
        pygame.draw.circle(glow, (*col, a2), (radius*2, radius*2), r2)
    surf.blit(glow, (pos[0]-radius*2, pos[1]-radius*2))


def draw_glow_rect(surf, rect, col, alpha=60, pad=6):
    gr = rect.inflate(pad*2, pad*2)
    glow = pygame.Surface((gr.width, gr.height), pygame.SRCALPHA)
    for i in range(pad, 0, -1):
        a2 = int(alpha * (1 - i/pad))
        r2 = pygame.Rect(i, i, gr.width-i*2, gr.height-i*2)
        pygame.draw.rect(glow, (*col, a2), r2, 1)
    surf.blit(glow, gr.topleft)


def blit_text_shadow(surf, text_surf, pos, shadow_col=(0, 0, 0), offset=2):
    sh = text_surf.copy()
    sh.fill((*shadow_col, 180), special_flags=pygame.BLEND_RGBA_MULT)
    surf.blit(sh, (pos[0]+offset, pos[1]+offset))
    surf.blit(text_surf, pos)


def render_text(font, text, color, shadow=True):
    return font.render(text, True, color)


def draw_separator(surf, x, y1, y2, col=C_STEEL):
    pygame.draw.line(surf, col, (x, y1), (x, y2), 2)
    for yi in [y1, y2]:
        pygame.draw.circle(surf, C_RIVET, (x, yi), 5)
        pygame.draw.circle(surf, C_STEEL_LT, (x-1, yi-1), 2)


def draw_corner_marks(surf, rect, col=C_AMBER, size=14, w=2):
    x, y, W, H = rect.x, rect.y, rect.width, rect.height
    corners = [(x, y), (x+W, y), (x, y+H), (x+W, y+H)]
    dirs = [(1, 1), (-1, 1), (1, -1), (-1, -1)]
    for (cx, cy), (dx, dy) in zip(corners, dirs):
        pygame.draw.line(surf, col, (cx, cy), (cx+dx*size, cy), w)
        pygame.draw.line(surf, col, (cx, cy), (cx, cy+dy*size), w)


def pulse(t, speed=2.0, lo=0.4, hi=1.0):
    return lo + (hi-lo) * (0.5 + 0.5*math.sin(t*speed))


def flicker(t, seed=0):
    return 0.85 + 0.15 * math.sin(t*17.3 + seed) * math.sin(t*5.1 + seed*2)

# ── PATHFINDING ───────────────────────────────────────────────────────────────


def heuristic(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])


def astar_full(start, goal, obstacles):
    open_set = []
    heapq.heappush(open_set, (0, tuple(start)))
    came_from = {}
    g_score = {tuple(start): 0}
    closed = set()
    while open_set:
        _, current = heapq.heappop(open_set)
        if list(current) == goal:
            path = []
            while current in came_from:
                path.append(list(current))
                current = came_from[current]
            path.reverse()
            return path
        if current in closed:
            continue
        closed.add(current)
        r, c = current
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r+dr, c+dc
            nb = (nr, nc)
            if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                if [nr, nc] in obstacles and [nr, nc] != goal:
                    continue
                tg = g_score.get(current, 1e9) + 1
                if tg < g_score.get(nb, 1e9):
                    came_from[nb] = current
                    g_score[nb] = tg
                    heapq.heappush(
                        open_set, (tg+heuristic(list(nb), goal), nb))
    return []

# ── STATE ─────────────────────────────────────────────────────────────────────


def gen_obstacles(n, gs=GRID_SIZE):
    obs, protected = [], [[0, 0], [0, 1], [1, 0],
                          [gs-1, gs-1], [gs-2, gs-1], [gs-1, gs-2]]
    att = 0
    while len(obs) < n and att < 20000:
        att += 1
        r, c = random.randint(0, gs-1), random.randint(0, gs-1)
        if [r, c] not in obs and [r, c] not in protected:
            obs.append([r, c])
    return obs


def gen_state():
    r3 = gen_obstacles(10)
    r4 = gen_obstacles(20)
    return {
        "room": 1, "pos": [0, 0], "input": [],
        "secret_code": [random.choice(COLOR_KEYS) for _ in range(4)],
        "target_num": random.randint(100, 999), "hint": "ENTER CODE 100-999",
        "crates": r3, "key_loc": random.choice(r3) if r3 else [5, 5],
        "lasers": r4, "wrong_crates": [], "finished": False,
        "start_time": time.time(), "end_time": None,
        "path_queue": [], "frontier": [], "final_path_visual": [],
        "reset_timer": 0,
        # AI1
        "ai_low": 100, "ai_high": 999, "ai_target_guess": "", "ai_move_timer": 0,
        "ai_known_slots": [None]*4, "ai_tried_per_slot": [set() for _ in range(4)],
        "bfs_queue": deque(), "bfs_visited": set(), "bfs_active": False, "bfs_target": None,
        "timer_ms": 0,
        # AI2
        "bt_partial": [], "bt_domains": [list(COLOR_KEYS) for _ in range(4)],
        "inf_low": 100, "inf_high": 999, "inf_guess": "",
        "astar_active": False, "astar_target": None, "astar_path": [],
        # Visual
        "flash_timer": 0, "flash_col": C_RED,
    }

# ── GRID DRAWING ──────────────────────────────────────────────────────────────


def draw_grid(surf, data, ox, oy, agent_col, path_col, t):
    gw = GRID_SIZE*CELL
    # Grid background
    grid_rect = pygame.Rect(ox-4, oy-4, gw+8, gw+8)
    draw_panel(surf, grid_rect, C_DARK, C_STEEL_LT, 4, 2)
    draw_corner_marks(surf, grid_rect, agent_col, 12, 2)

    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            rx = ox + c*CELL
            ry = oy + r*CELL
            cell_rect = pygame.Rect(rx, ry, CELL, CELL)

            # Frontier highlight (BFS)
            if [r, c] in data['frontier']:
                pygame.draw.rect(surf, (30, 45, 30), cell_rect)

            # Base cell
            pygame.draw.rect(surf, C_STEEL, cell_rect, 1)

    # Path line
    vis = data['final_path_visual']
    if len(vis) > 1:
        pts = [(ox+p[1]*CELL+CELL//2, oy+p[0]*CELL+CELL//2) for p in vis]
        # Glow
        for i in range(4, 0, -1):
            pc = (*path_col[:3], 20*i)
            ps = pygame.Surface((gw, gw), pygame.SRCALPHA)
            if len(pts) > 1:
                local = [(p[0]-ox, p[1]-oy) for p in pts]
                pygame.draw.lines(ps, (*path_col, 15*i), False, local, i*3)
            surf.blit(ps, (ox, oy))
        pygame.draw.lines(surf, path_col, False, pts, 3)

    # Crates / lasers
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            rx = ox + c*CELL
            ry = oy + r*CELL
            cr = pygame.Rect(rx+2, ry+2, CELL-4, CELL-4)

            if data['room'] == 3 and [r, c] in data['crates']:
                is_wrong = [r, c] in data['wrong_crates']
                if is_wrong:
                    col = C_RED_DIM
                    pygame.draw.rect(surf, col, cr, border_radius=3)
                    pygame.draw.rect(surf, C_RED, cr, 2, border_radius=3)
                    # X mark
                    pygame.draw.line(surf, C_RED, (rx+6, ry+6),
                                     (rx+CELL-6, ry+CELL-6), 2)
                    pygame.draw.line(
                        surf, C_RED, (rx+CELL-6, ry+6), (rx+6, ry+CELL-6), 2)
                else:
                    pygame.draw.rect(surf, C_CRATE, cr, border_radius=3)
                    pygame.draw.rect(surf, C_CRATE_LT, cr, 1, border_radius=3)
                    # Crate planks
                    pygame.draw.line(
                        surf, C_CRATE_LT, (rx+CELL//2, ry+3), (rx+CELL//2, ry+CELL-3), 1)
                    pygame.draw.line(
                        surf, C_CRATE_LT, (rx+3, ry+CELL//2), (rx+CELL-3, ry+CELL//2), 1)

            if data['room'] == 4:
                if [r, c] in data['lasers']:
                    p2 = pulse(t, 4.0, 0.5, 1.0)
                    lc = lerp_color(C_RED_DIM, C_LASER_GLOW, p2-0.5)
                    pygame.draw.rect(surf, lc, cr, border_radius=2)
                    pygame.draw.rect(surf, C_LASER_GLOW,
                                     cr, 1, border_radius=2)
                if [r, c] == [0, 0]:
                    pygame.draw.rect(surf, C_GREEN_DIM, cr, border_radius=3)
                    pygame.draw.rect(surf, C_GREEN, cr, 2, border_radius=3)
                    lbl = F_SMALL.render("START", True, C_GREEN)
                    surf.blit(lbl, (rx+CELL//2-lbl.get_width() //
                              2, ry+CELL//2-lbl.get_height()//2))
                if [r, c] == [GRID_SIZE-1, GRID_SIZE-1]:
                    p2 = pulse(t, 1.5)
                    ec = lerp_color(C_AMBER_DIM, C_AMBER, p2)
                    pygame.draw.rect(surf, ec, cr, border_radius=3)
                    pygame.draw.rect(surf, C_AMBER, cr, 2, border_radius=3)
                    lbl = F_SMALL.render("EXIT", True, C_AMBER)
                    surf.blit(lbl, (rx+CELL//2-lbl.get_width() //
                              2, ry+CELL//2-lbl.get_height()//2))

    # Player dot
    pr, pc2 = data['pos']
    px = ox + pc2*CELL + CELL//2
    py = oy + pr*CELL + CELL//2
    draw_glow_circle(surf, (px, py), CELL//3+4, agent_col, 80)
    pygame.draw.circle(surf, lerp_color(
        agent_col, C_WHITE, 0.3), (px, py), CELL//3)
    pygame.draw.circle(surf, agent_col, (px, py), CELL//3, 2)

# ── SIDE PANEL ────────────────────────────────────────────────────────────────


def draw_side(surf, data, ox, label, agent_col, path_col, algo_labels, is_human, t, winner=None):
    """Draw one complete side panel."""
    W = HALF
    # Main panel background
    panel = pygame.Rect(ox, 0, W, HEIGHT)
    pygame.draw.rect(surf, C_PANEL, panel)

    # Top hazard stripe bar
    haz_rect = pygame.Rect(ox, 0, W, 8)
    draw_hazard_stripe(surf, haz_rect, 10)

    # Header area
    hdr = pygame.Rect(ox+10, 14, W-20, 68)
    draw_panel(surf, hdr, C_DARK, agent_col, 4, 2)
    draw_rivets(surf, hdr, C_STEEL_LT, 3)

    # Agent name
    fl = flicker(t, hash(label) % 100)
    nc = lerp_color(C_DARK, agent_col, fl)
    name_surf = F_TITLE.render(label, True, agent_col)
    blit_text_shadow(surf, name_surf, (ox+22, 18))

    # Room badge
    room_str = f"ROOM {data['room']}/4"
    rb_surf = F_HEAD.render(
        room_str, True, C_AMBER if not data['finished'] else C_GREEN)
    surf.blit(rb_surf, (ox+W-rb_surf.get_width()-22, 26))

    # Timer strip
    elapsed = (data['end_time'] if data['finished']
               else time.time()) - data['start_time']
    tmr_rect = pygame.Rect(ox+10, 88, W-20, 32)
    draw_panel(surf, tmr_rect, C_DARK, C_STEEL, 3, 1)
    tmr_col = C_GREEN if data['finished'] else C_AMBER
    tmr_str = f"▶  ELAPSED  {elapsed:08.3f}s"
    tmr_surf = F_LABEL.render(tmr_str, True, tmr_col)
    surf.blit(tmr_surf, (ox+20, 95))
    # Blinking dot
    if not data['finished'] and int(t*2) % 2 == 0:
        pygame.draw.circle(surf, C_RED_BRIGHT, (ox+W-30, 104), 6)
    else:
        pygame.draw.circle(surf, C_RED_DIM, (ox+W-30, 104), 6)

    # Algorithm tag
    algo_str = algo_labels.get(data['room'], "")
    alg_rect = pygame.Rect(ox+10, 126, W-20, 24)
    draw_panel(surf, alg_rect, C_DARK, C_STEEL, 2, 1)
    alg_surf = F_MONO.render(f"  ALGO: {algo_str}", True, C_GRAY)
    surf.blit(alg_surf, (ox+14, 129))

    # ── ROOM CONTENT ──

    if data['room'] == 1:
        draw_room1(surf, data, ox, W, t, agent_col, is_human)
    elif data['room'] == 2:
        draw_room2(surf, data, ox, W, t, agent_col, is_human)
    elif data['room'] in [3, 4]:
        grid_x = ox + (W - GRID_SIZE*CELL)//2
        grid_y = 175
        draw_room_label(surf, ox, W, data['room'], t)
        draw_grid(surf, data, grid_x, grid_y, agent_col, path_col, t)
        if data['room'] == 3:
            info = F_MONO.render(
                f"CRATES: {len([c for c in data['crates'] if c not in data['wrong_crates']])} REMAIN  |  WRONG: {len(data['wrong_crates'])}", True, C_GRAY)
            surf.blit(info, (ox+10, HEIGHT-36))
        else:
            info = F_MONO.render(
                "AVOID LASER GRIDS  ·  REACH EXIT [9,9]", True, C_GRAY)
            surf.blit(info, (ox+10, HEIGHT-36))

    # ── ESCAPED OVERLAY ──
    if data['finished']:
        ov = pygame.Surface((W, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 30, 0, 60))
        surf.blit(ov, (ox, 0))
        esc_surf = F_HUGE.render("ESCAPED", True, C_GREEN)
        p2 = pulse(t, 1.8)
        sc = lerp_color(C_GREEN_DIM, C_GREEN, p2)
        esc_surf2 = F_HUGE.render("ESCAPED", True, sc)
        ex = ox + W//2 - esc_surf.get_width()//2
        ey = HEIGHT//2 - esc_surf.get_height()//2
        draw_glow_rect(surf, pygame.Rect(
            ex-10, ey-6, esc_surf.get_width()+20, esc_surf.get_height()+12), C_GREEN, 100, 12)
        surf.blit(esc_surf2, (ex, ey))
        t_surf = F_LABEL.render(f"FINAL TIME:  {elapsed:.3f}s", True, C_WHITE)
        surf.blit(t_surf, (ox+W//2-t_surf.get_width() //
                  2, ey+esc_surf.get_height()+10))

        if winner:
            w_surf = F_HEAD.render(winner, True, C_AMBER)
            surf.blit(w_surf, (ox+W//2-w_surf.get_width() //
                      2, ey+esc_surf.get_height()+42))

    # Bottom hazard stripe
    haz2 = pygame.Rect(ox, HEIGHT-8, W, 8)
    draw_hazard_stripe(surf, haz2, 10)


def draw_room_label(surf, ox, W, room, t):
    labels = {3: "CARGO BAY — FIND THE KEY CRATE",
              4: "LASER GRID — REACH THE EXIT"}
    lbl = F_LABEL.render(labels.get(room, ""), True, C_GRAY)
    surf.blit(lbl, (ox + W//2 - lbl.get_width()//2, 158))


def draw_room1(surf, data, ox, W, t, agent_col, is_human):
    # Background panel
    area = pygame.Rect(ox+15, 162, W-30, 380)
    draw_panel(surf, area, C_DARK, C_STEEL, 6, 2)
    draw_corner_marks(surf, area, agent_col)

    title = F_HEAD.render("ACCESS CODE ENTRY", True, agent_col)
    surf.blit(title, (ox+W//2-title.get_width()//2, 172))

    # Instruction
    instr = F_MONO.render("MATCH THE 4-COLOR SECURITY CODE", True, C_GRAY)
    surf.blit(instr, (ox+W//2-instr.get_width()//2, 210))

    # Code slots
    slot_w, slot_h = 72, 72
    total_w = 4*slot_w + 3*10
    sx = ox + W//2 - total_w//2
    sy = 248

    for i in range(4):
        sr = pygame.Rect(sx + i*(slot_w+10), sy, slot_w, slot_h)
        filled = i < len(data['input'])
        correct = len(
            data['input']) == 4 and data['input'][i] == data['secret_code'][i]
        wrong = len(
            data['input']) == 4 and data['input'][i] != data['secret_code'][i]

        if filled:
            fc = COLOR_MAP[data['input'][i]]
            dark_fc = lerp_color(fc, C_DARK, 0.6)
            pygame.draw.rect(surf, dark_fc, sr, border_radius=6)
            pygame.draw.rect(surf, fc, sr, 3, border_radius=6)
            if correct:
                draw_glow_rect(surf, sr, C_GREEN, 120, 8)
                lbl = F_HEAD.render("✓", True, C_GREEN)
            elif wrong:
                lbl = F_HEAD.render(data['input'][i], True, fc)
            else:
                lbl = F_HEAD.render(data['input'][i], True, fc)
            surf.blit(lbl, (sr.centerx-lbl.get_width() //
                      2, sr.centery-lbl.get_height()//2))
        else:
            pygame.draw.rect(surf, C_STEEL, sr, border_radius=6)
            pygame.draw.rect(surf, C_STEEL_LT, sr, 2, border_radius=6)
            # Blinking cursor for next slot
            if i == len(data['input']) and int(t*2) % 2 == 0:
                cur = pygame.Rect(sr.centerx-3, sr.bottom-14, 6, 8)
                pygame.draw.rect(surf, agent_col, cur, border_radius=2)

        # Slot number
        n_surf = F_SMALL.render(f"[{i+1}]", True, C_GRAY)
        surf.blit(n_surf, (sr.x+2, sr.y+2))

    # Color buttons (only for human, decorative for AI)
    btn_y = sy + slot_h + 30
    for i, (key, col) in enumerate(COLOR_MAP.items()):
        br = pygame.Rect(sx + i*(slot_w+10), btn_y, slot_w, slot_h)

        if is_human:
            mx, my = pygame.mouse.get_pos()
            hovered = br.collidepoint(mx, my)
            dark_col = lerp_color(col, C_DARK, 0.55 if not hovered else 0.35)
            pygame.draw.rect(surf, dark_col, br, border_radius=8)
            pygame.draw.rect(
                surf, col, br, 3 if not hovered else 4, border_radius=8)
            if hovered:
                draw_glow_rect(surf, br, col, 80, 6)
        else:
            dark_col = lerp_color(col, C_DARK, 0.7)
            pygame.draw.rect(surf, dark_col, br, border_radius=8)
            pygame.draw.rect(surf, lerp_color(
                col, C_DARK, 0.3), br, 2, border_radius=8)

        k_surf = F_HEAD.render(COLOR_NAMES[key], True, col)
        surf.blit(k_surf, (br.centerx-k_surf.get_width() //
                  2, br.centery-k_surf.get_height()//2))

    # Status message
    if len(data['input']) == 4:
        if data['input'] == data['secret_code']:
            msg = F_LABEL.render(
                "▶  CODE ACCEPTED  ▶  PROCEEDING...", True, C_GREEN)
        else:
            msg = F_LABEL.render(
                "✖  INCORRECT CODE — RETRYING", True, C_RED_BRIGHT)
        surf.blit(msg, (ox+W//2-msg.get_width()//2, btn_y+slot_h+16))
    else:
        msg = F_LABEL.render(
            f"ENTERED: {len(data['input'])}/4 COLORS", True, C_GRAY)
        surf.blit(msg, (ox+W//2-msg.get_width()//2, btn_y+slot_h+16))


def draw_room2(surf, data, ox, W, t, agent_col, is_human):
    area = pygame.Rect(ox+15, 162, W-30, 380)
    draw_panel(surf, area, C_DARK, C_STEEL, 6, 2)
    draw_corner_marks(surf, area, agent_col)

    title = F_HEAD.render("NUMERIC KEYPAD OVERRIDE", True, agent_col)
    surf.blit(title, (ox+W//2-title.get_width()//2, 172))

    # Hint display
    hint_col = C_RED_BRIGHT if "HIGHER" in data['hint'] or "LOWER" in data['hint'] else C_GRAY
    if "HIGHER" in data['hint']:
        hint_col = C_GREEN
        arrow = "▲ NUMBER IS HIGHER"
    elif "LOWER" in data['hint']:
        hint_col = C_RED_BRIGHT
        arrow = "▼ NUMBER IS LOWER"
    else:
        arrow = data['hint']

    hint_rect = pygame.Rect(ox+30, 215, W-60, 42)
    draw_panel(surf, hint_rect, C_DARK, hint_col, 4, 2)
    h_surf = F_LABEL.render(arrow, True, hint_col)
    surf.blit(h_surf, (hint_rect.centerx-h_surf.get_width() //
              2, hint_rect.centery-h_surf.get_height()//2))

    # Number display
    num_str = "".join(data['input']) + ("_" if int(t*2) % 2 == 0 else " ")
    if not data['input']:
        num_str = "---"
    num_rect = pygame.Rect(ox+60, 275, W-120, 90)
    draw_panel(surf, num_rect, C_DARK, agent_col, 6, 2)
    draw_glow_rect(surf, num_rect, agent_col, 40, 6)
    n_surf = F_NUM.render(num_str, True, agent_col)
    surf.blit(n_surf, (num_rect.centerx-n_surf.get_width() //
              2, num_rect.centery-n_surf.get_height()//2))

    # Range indicator
    rng_str = f"RANGE:  {data.get('ai_low', data.get('inf_low', 100))}  —  {data.get('ai_high', data.get('inf_high', 999))}"
    if not is_human:
        rng_surf = F_MONO.render(rng_str, True, C_GRAY)
        surf.blit(rng_surf, (ox+W//2-rng_surf.get_width()//2, 380))

    if is_human:
        instr = F_MONO.render(
            "TYPE NUMBER  ·  ENTER TO CONFIRM  ·  BACKSPACE", True, C_GRAY)
        surf.blit(instr, (ox+W//2-instr.get_width()//2, 384))

    # Keypad graphic (decorative)
    kp_x = ox + W//2 - 90
    kp_y = 415
    digits = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "⌫", "0", "↵"]
    for i, d in enumerate(digits):
        kr = pygame.Rect(kp_x + (i % 3)*62, kp_y + (i//3)*46, 56, 40)
        is_special = d in ["⌫", "↵"]
        bc = C_STEEL_LT if not is_special else (
            C_RED_DIM if d == "⌫" else C_GREEN_DIM)
        fc = C_RED_BRIGHT if d == "⌫" else (C_GREEN if d == "↵" else C_WHITE)
        pygame.draw.rect(surf, bc, kr, border_radius=4)
        pygame.draw.rect(surf, C_STEEL, kr, 1, border_radius=4)
        ds = F_LABEL.render(d, True, fc)
        surf.blit(ds, (kr.centerx-ds.get_width() //
                  2, kr.centery-ds.get_height()//2))


# ── MENU ──────────────────────────────────────────────────────────────────────

def draw_menu(surf, t):
    surf.fill(C_BG)
    surf.blit(_noise_surf, (0, 0))
    surf.blit(_scan_surf, (0, 0))

    # Background grid pattern
    for x in range(0, WIDTH, 60):
        pygame.draw.line(surf, (18, 22, 28), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, 60):
        pygame.draw.line(surf, (18, 22, 28), (0, y), (WIDTH, y))

    # Center glow blob
    gb = pygame.Surface((600, 400), pygame.SRCALPHA)
    for r2 in range(200, 0, -10):
        a2 = int(8*(1-r2/200))
        pygame.draw.circle(gb, (20, 60, 20, a2), (300, 200), r2)
    surf.blit(gb, (WIDTH//2-300, HEIGHT//2-200))

    # Title plate
    tp = pygame.Rect(WIDTH//2-380, 40, 760, 110)
    draw_panel(surf, tp, (10, 14, 12), C_GREEN, 8, 3)
    draw_hazard_stripe(surf, pygame.Rect(WIDTH//2-380, 40, 760, 14), 14)
    draw_hazard_stripe(surf, pygame.Rect(WIDTH//2-380, 136, 760, 14), 14)
    draw_rivets(surf, tp, C_STEEL_LT, 5)

    p2 = pulse(t, 1.2)
    tc = lerp_color(C_GREEN_DIM, C_GREEN, p2)
    t1 = F_MENU_T.render("LOCKDOWN", True, tc)
    blit_text_shadow(surf, t1, (WIDTH//2-t1.get_width()//2, 52), C_BG, 3)

    # Divider
    pygame.draw.line(surf, C_STEEL, (100, 170), (WIDTH-100, 170), 1)

    # Warning text
    warn = F_MONO.render("▶  SELECT OPERATION MODE  ◀", True, C_AMBER)
    surf.blit(warn, (WIDTH//2-warn.get_width()//2, 182))

    mx, my = pygame.mouse.get_pos()

    # Button 1: Human vs AI
    b1 = pygame.Rect(WIDTH//2-340, 220, 680, 160)
    h1 = b1.collidepoint(mx, my)
    draw_panel(surf, b1, (12, 18, 28) if not h1 else (16, 28, 48),
               C_BLUE if h1 else C_STEEL, 8, 2 if not h1 else 3)
    if h1:
        draw_glow_rect(surf, b1, C_BLUE, 80, 10)
        draw_corner_marks(surf, b1, C_BLUE, 18, 3)
    else:
        draw_corner_marks(surf, b1, C_STEEL_LT, 14, 1)

    draw_hazard_stripe(surf, pygame.Rect(b1.x, b1.y, b1.width, 10), 10)
    b1t = F_MENU_S.render("MODE 01  ·  HUMAN  vs  AI",
                          True, C_BLUE if h1 else C_WHITE)
    surf.blit(b1t, (b1.centerx-b1t.get_width()//2, b1.y+20))
    pygame.draw.line(surf, C_STEEL, (b1.x+20, b1.y+62),
                     (b1.right-20, b1.y+62), 1)
    d1a = F_MENU_B.render(
        "You navigate the escape rooms using keyboard & mouse", True, C_GRAY)
    d1b = F_MENU_B.render(
        "Race against AI Agent using BFS · Binary Search · Greedy", True, C_GRAY)
    surf.blit(d1a, (b1.centerx-d1a.get_width()//2, b1.y+76))
    surf.blit(d1b, (b1.centerx-d1b.get_width()//2, b1.y+100))
    press1 = F_MONO.render("[ CLICK TO START ]" if h1 else "", True, C_BLUE)
    surf.blit(press1, (b1.centerx-press1.get_width()//2, b1.y+132))

    # Button 2: AI vs AI
    b2 = pygame.Rect(WIDTH//2-340, 408, 680, 180)
    h2 = b2.collidepoint(mx, my)
    draw_panel(surf, b2, (18, 12, 10) if not h2 else (30, 16, 12),
               C_RED if h2 else C_STEEL, 8, 2 if not h2 else 3)
    if h2:
        draw_glow_rect(surf, b2, C_RED, 80, 10)
        draw_corner_marks(surf, b2, C_RED, 18, 3)
    else:
        draw_corner_marks(surf, b2, C_STEEL_LT, 14, 1)

    draw_hazard_stripe(surf, pygame.Rect(b2.x, b2.y, b2.width, 10), 10)
    b2t = F_MENU_S.render("MODE 02  ·  AI  vs  AI",
                          True, C_RED if h2 else C_WHITE)
    surf.blit(b2t, (b2.centerx-b2t.get_width()//2, b2.y+20))
    pygame.draw.line(surf, C_STEEL, (b2.x+20, b2.y+62),
                     (b2.right-20, b2.y+62), 1)
    d2a = F_MENU_B.render(
        "AGENT 1  ·  BFS ·  Gaussian Binary Search  ·  Slot Elimination", True, C_GRAY)
    d2b = F_MENU_B.render(
        "AGENT 2  ·  A* ·  Informed Search  ·  Backtracking + Pruning", True, C_GRAY)
    d2c = F_MENU_B.render(
        "Watch two AI algorithms race through all 4 rooms", True, C_GRAY)
    surf.blit(d2a, (b2.centerx-d2a.get_width()//2, b2.y+76))
    surf.blit(d2b, (b2.centerx-d2b.get_width()//2, b2.y+104))
    surf.blit(d2c, (b2.centerx-d2c.get_width()//2, b2.y+140))
    press2 = F_MONO.render("[ CLICK TO START ]" if h2 else "", True, C_RED)
    surf.blit(press2, (b2.centerx-press2.get_width()//2, b2.y+158))

    # Footer
    pygame.draw.line(surf, C_STEEL, (100, 608), (WIDTH-100, 608), 1)
    f1 = F_MONO.render("ESC  ·  RETURN TO MENU FROM GAME", True, C_GRAY)
    f2 = F_MONO.render(
        "ARROW KEYS  ·  MOVEMENT      ENTER  ·  CONFIRM      BACKSPACE  ·  DELETE", True, (45, 50, 60))
    surf.blit(f1, (WIDTH//2-f1.get_width()//2, 620))
    surf.blit(f2, (WIDTH//2-f2.get_width()//2, 646))

    # Status bar
    sb = pygame.Rect(0, HEIGHT-30, WIDTH, 30)
    pygame.draw.rect(surf, C_DARK, sb)
    pygame.draw.line(surf, C_STEEL, (0, HEIGHT-30), (WIDTH, HEIGHT-30), 1)
    ts = F_SMALL.render(
        f"SYS: ONLINE  ·  {time.strftime('%H:%M:%S')}  ·  LOCKDOWN ESCAPE FACILITY  ·  AUTHORIZED PERSONNEL ONLY", True, C_GRAY)
    surf.blit(ts, (20, HEIGHT-22))

    surf.blit(_scan_surf, (0, 0))
    pygame.display.flip()
    return b1, b2


# ── MAIN RENDER ───────────────────────────────────────────────────────────────

AI1_ALGOS = {1: "Slot Elimination", 2: "Gaussian BinSearch",
             3: "BFS + Greedy", 4: "BFS + Greedy"}
AI2_ALGOS = {1: "Backtrack + Prune",
             2: "Informed Search", 3: "A* Search", 4: "A* Search"}
HUMAN_ALGOS = {1: "Manual Input", 2: "Manual Input",
               3: "Manual Navigation", 4: "Manual Navigation"}


def render_game(left, right, lname, rname, lcol, rcol, lalgos, ralgos, l_is_human, t, winner_msg=None):
    screen.fill(C_BG)
    screen.blit(_noise_surf, (0, 0))

    draw_side(screen, left,  0,     lname, lcol, (0, 140, 255) if lcol == C_BLUE else (
        255, 100, 0), lalgos, l_is_human, t, winner_msg if left['finished'] else None)
    draw_side(screen, right, HALF,  rname, rcol, (255, 80, 0) if rcol == C_ORANGE else (
        0, 200, 100), ralgos, False,     t, winner_msg if right['finished'] else None)

    # Center divider
    draw_separator(screen, HALF, 0, HEIGHT, C_STEEL)
    draw_hazard_stripe(screen, pygame.Rect(HALF-4, 0, 8, HEIGHT), 12)
    pygame.draw.line(screen, (0, 0, 0), (HALF-1, 0), (HALF-1, HEIGHT), 2)
    pygame.draw.line(screen, (0, 0, 0), (HALF+1, 0), (HALF+1, HEIGHT), 2)

    # VS badge
    vs_r = pygame.Rect(HALF-28, HEIGHT//2-28, 56, 56)
    pygame.draw.rect(screen, C_DARK, vs_r, border_radius=28)
    pygame.draw.rect(screen, C_AMBER, vs_r, 2, border_radius=28)
    vs = F_HEAD.render("VS", True, C_AMBER)
    screen.blit(vs, (HALF-vs.get_width()//2, HEIGHT//2-vs.get_height()//2))

    # Status bar
    sb = pygame.Rect(0, HEIGHT-30, WIDTH, 30)
    pygame.draw.rect(screen, C_DARK, sb)
    pygame.draw.line(screen, C_STEEL, (0, HEIGHT-30), (WIDTH, HEIGHT-30), 1)
    ts = F_SMALL.render(
        f"SYS: ACTIVE  ·  {time.strftime('%H:%M:%S')}  ·  PRESS ESC TO RETURN TO MENU", True, C_GRAY)
    screen.blit(ts, (WIDTH//2-ts.get_width()//2, HEIGHT-22))

    screen.blit(_scan_surf, (0, 0))
    pygame.display.flip()


# ── AI AGENTS ─────────────────────────────────────────────────────────────────

def tick_ai1(a, now):
    if a['finished']:
        return
    if a['room'] == 1 and now-a['timer_ms'] > 150:
        if len(a['input']) == 4:
            if a['input'] == a['secret_code']:
                a['room'], a['input'] = 2, []
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
        a['timer_ms'] = now
    elif a['room'] == 2 and now-a['timer_ms'] > 150:
        if not a['ai_target_guess']:
            span = a['ai_high']-a['ai_low']
            mu = (a['ai_low']+a['ai_high'])/2
            a['ai_target_guess'] = str(max(a['ai_low'], min(
                a['ai_high'], int(random.gauss(mu, span/6 if span > 0 else 1)))))
        if len(a['input']) < len(a['ai_target_guess']):
            a['input'].append(a['ai_target_guess'][len(a['input'])])
        else:
            g = int(a['ai_target_guess'])
            if g == a['target_num']:
                a['room'], a['pos'], a['input'] = 3, [0, 0], []
            else:
                if g < a['target_num']:
                    a['ai_low'] = g+1
                    a['hint'] = "HIGHER"
                else:
                    a['ai_high'] = g-1
                    a['hint'] = "LOWER"
                a['ai_target_guess'] = ""
                a['input'] = []
        a['timer_ms'] = now
    elif a['room'] in [3, 4]:
        if not a['bfs_active'] and not a['path_queue']:
            if a['room'] == 4:
                a['bfs_target'] = [9, 9]
            else:
                avail = [c for c in a['crates'] if c not in a['wrong_crates']]
                a['bfs_target'] = min(avail, key=lambda c: abs(
                    c[0]-a['pos'][0])+abs(c[1]-a['pos'][1])) if avail else [9, 9]
            a['bfs_queue'] = deque([(a['pos'], [])])
            a['bfs_visited'] = {tuple(a['pos'])}
            a['frontier'], a['final_path_visual'], a['bfs_active'] = [], [], True
        if a['bfs_active'] and now-a['timer_ms'] > 15:
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
                                a['bfs_queue'].append(
                                    ([nr2, nc2], path+[[nr2, nc2]]))
            else:
                a['bfs_active'] = False
            a['timer_ms'] = now
        elif not a['bfs_active'] and a['path_queue'] and now-a['ai_move_timer'] > 150:
            step = a['path_queue'].pop(0)
            if a['room'] == 3 and step in a['crates']:
                if step == a['key_loc']:
                    a['room'], a['pos'] = 4, [0, 0]
                else:
                    a['wrong_crates'].append(step)
                a['path_queue'], a['frontier'], a['final_path_visual'] = [], [], []
            else:
                a['pos'] = step
                if a['final_path_visual']:
                    a['final_path_visual'].pop(0)
                if a['room'] == 4 and a['pos'] == [9, 9]:
                    a['finished'], a['end_time'] = True, time.time()
            a['ai_move_timer'] = now


def tick_ai2(a, now):
    if a['finished']:
        return
    if a['room'] == 1 and now-a['timer_ms'] > 180:
        bt = a['bt_partial']
        domains = a['bt_domains']
        if len(bt) == 4:
            if bt == a['secret_code']:
                a['room'] = 2
                a['input'] = []
                a['bt_partial'] = []
                a['bt_domains'] = [list(COLOR_KEYS) for _ in range(4)]
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
            chosen = domains[idx][0] if domains[idx] else COLOR_KEYS[0]
            bt.append(chosen)
            a['input'] = list(bt)
        a['timer_ms'] = now
    elif a['room'] == 2 and now-a['timer_ms'] > 180:
        if not a['inf_guess']:
            a['inf_guess'] = str((a['inf_low']+a['inf_high'])//2)
            a['input'] = []
        if len(a['input']) < len(a['inf_guess']):
            a['input'].append(a['inf_guess'][len(a['input'])])
        else:
            g = int(a['inf_guess'])
            if g == a['target_num']:
                a['room'], a['pos'], a['input'] = 3, [0, 0], []
                a['inf_low'], a['inf_high'], a['inf_guess'] = 100, 999, ""
            else:
                if g < a['target_num']:
                    a['inf_low'] = g+1
                    a['hint'] = "HIGHER"
                else:
                    a['inf_high'] = g-1
                    a['hint'] = "LOWER"
                a['inf_guess'] = ""
                a['input'] = []
        a['timer_ms'] = now
    elif a['room'] in [3, 4]:
        if not a['path_queue']:
            if a['room'] == 4:
                target = [9, 9]
            else:
                avail = [c for c in a['crates'] if c not in a['wrong_crates']]
                target = min(avail, key=lambda c: heuristic(
                    c, a['pos'])) if avail else [9, 9]
            obs = a['lasers'] if a['room'] == 4 else a['crates']
            path = astar_full(a['pos'], target, obs)
            if path:
                a['path_queue'] = path
                a['final_path_visual'] = [list(a['pos'])]+path
        if a['path_queue'] and now-a['ai_move_timer'] > 120:
            step = a['path_queue'].pop(0)
            if a['room'] == 3 and step in a['crates']:
                if step == a['key_loc']:
                    a['room'], a['pos'] = 4, [0, 0]
                else:
                    a['wrong_crates'].append(step)
                a['path_queue'], a['frontier'], a['final_path_visual'] = [], [], []
            else:
                a['pos'] = step
                if a['final_path_visual']:
                    a['final_path_visual'].pop(0)
                if a['room'] == 4 and a['pos'] == [9, 9]:
                    a['finished'], a['end_time'] = True, time.time()
            a['ai_move_timer'] = now


def handle_human(h, events, now):
    if h['reset_timer'] > 0 and now > h['reset_timer']:
        h['input'], h['reset_timer'] = [], 0
    for e in events:
        if h['finished']:
            continue
        if e.type == pygame.MOUSEBUTTONDOWN and h['room'] == 1 and h['reset_timer'] == 0:
            mx, my = pygame.mouse.get_pos()
            slot_w, slot_h = 72, 72
            total_w = 4*slot_w+3*10
            sx = HALF//2-total_w//2
            btn_y = 248+slot_h+30
            for i, key in enumerate(COLOR_KEYS):
                br = pygame.Rect(sx+i*(slot_w+10), btn_y, slot_w, slot_h)
                if br.collidepoint(mx, my):
                    h['input'].append(key)
                    if len(h['input']) == 4:
                        if h['input'] == h['secret_code']:
                            h['room'], h['input'] = 2, []
                        else:
                            h['reset_timer'] = now+900
        if e.type == pygame.KEYDOWN:
            if h['room'] == 2:
                if e.key == pygame.K_RETURN:
                    v = "".join(h['input'])
                    val = int(v) if v.isdigit() else 0
                    if val == h['target_num']:
                        h['room'], h['pos'], h['input'] = 3, [0, 0], []
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
                            h['room'], h['pos'] = 4, [0, 0]
                        else:
                            h['wrong_crates'].append([nr, nc])
                    elif h['room'] == 4 and [nr, nc] in h['lasers']:
                        h['pos'] = [0, 0]
                    else:
                        h['pos'] = [nr, nc]
                    if h['room'] == 4 and h['pos'] == [GRID_SIZE-1, GRID_SIZE-1]:
                        h['finished'], h['end_time'] = True, time.time()


# ── MAIN LOOP ─────────────────────────────────────────────────────────────────

clock = pygame.time.Clock()
game_mode = "menu"
h = gen_state()
a = gen_state()
winner_msg = None

while True:
    t = time.time()
    now = pygame.time.get_ticks()
    events = pygame.event.get()

    for e in events:
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE and game_mode != "menu":
            game_mode = "menu"
            h = gen_state()
            a = gen_state()
            winner_msg = None

    if game_mode == "menu":
        b1, b2 = draw_menu(screen, t)
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                if b1.collidepoint(e.pos):
                    game_mode = "human_vs_ai"
                    h = gen_state()
                    a = gen_state()
                    winner_msg = None
                elif b2.collidepoint(e.pos):
                    game_mode = "ai_vs_ai"
                    h = gen_state()
                    a = gen_state()
                    winner_msg = None
        clock.tick(60)
        continue

    if game_mode == "human_vs_ai":
        handle_human(h, events, now)
        tick_ai1(a, now)
        if h['finished'] and not winner_msg and not a['finished']:
            winner_msg = "🏆 WINNER"
        elif a['finished'] and not winner_msg and not h['finished']:
            winner_msg = "🏆 WINNER"
        render_game(h, a, "HUMAN", "AI AGENT", C_BLUE, C_RED,
                    HUMAN_ALGOS, AI1_ALGOS, True, t, winner_msg)

    elif game_mode == "ai_vs_ai":
        tick_ai1(h, now)
        tick_ai2(a, now)
        if h['finished'] and not winner_msg and not a['finished']:
            winner_msg = "🏆 WINNER"
        elif a['finished'] and not winner_msg and not h['finished']:
            winner_msg = "🏆 WINNER"
        render_game(h, a, "AGENT 1 — BFS", "AGENT 2 — A*", C_BLUE, C_ORANGE,
                    AI1_ALGOS, AI2_ALGOS, False, t, winner_msg)

    clock.tick(30)
