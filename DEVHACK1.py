import tkinter as tk
from tkinter import messagebox
import math
import heapq
import random
import time

# ============================================================
# WAREX 3D-STYLE MULTI-AMR WAREHOUSE SIMULATION
# Central WAREX Brain + 6 AMRs + path planning + obstacles
# ============================================================

BG = "#081018"
FLOOR = "#111c25"
GRID = "#263743"
TEXT = "#eef5f7"
WHITE = "#ffffff"
MUTED = "#8fa6b3"
CYAN = "#23d6d0"
GREEN = "#39d98a"
BLUE = "#4da3ff"
ORANGE = "#ffb648"
RED = "#ff5d65"
PURPLE = "#ad7aff"
YELLOW = "#ffe066"
DARK = "#0b141b"

SHELVES = {
    "S01": (2, 2), "S02": (5, 2), "S03": (8, 2),
    "S04": (2, 5), "S05": (5, 5), "S06": (8, 5),
    "S07": (2, 8), "S08": (5, 8), "S09": (8, 8),
    "S10": (2, 11), "S11": (5, 11), "S12": (8, 11),
}

# AMRs stop in the aisle directly in front of each shelf.
# They never drive through the shelf rack.
PICK_POINTS = {
    "S01": (2, 3), "S02": (5, 3), "S03": (8, 3),
    "S04": (2, 6), "S05": (5, 6), "S06": (8, 6),
    "S07": (2, 9), "S08": (5, 9), "S09": (8, 9),
    "S10": (2, 12), "S11": (5, 12), "S12": (8, 12),
}

RECEIVE = {"R01": (13, 3), "R02": (13, 7), "R03": (13, 11)}
DELIVERY = {"D01": (16, 3), "D02": (16, 7), "D03": (16, 11)}
CHARGERS = {"C01": (2, 14), "C02": (5, 14), "C03": (8, 14),
            "C04": (11, 14), "C05": (14, 14), "C06": (17, 14)}

TASKS = [
    ("ORDER-001", "S01", "R01", 3),
    ("ORDER-002", "S05", "R02", 2),
    ("ORDER-003", "S08", "D01", 3),
    ("ORDER-004", "S10", "D02", 2),
    ("ORDER-005", "S03", "R03", 1),
    ("ORDER-006", "S12", "D03", 3),
    ("ORDER-007", "S07", "R01", 2),
    ("ORDER-008", "S02", "D02", 1),
    ("ORDER-009", "S11", "R03", 3),
    ("ORDER-010", "S06", "D01", 2),
    ("ORDER-011", "S09", "R02", 1),
    ("ORDER-012", "S04", "D03", 3),
]

# Static blocked cells: walls/obstacles placed in aisles.
OBSTACLES = set()  # Start with NO obstacles; user can add/remove them manually.

GRID_W, GRID_H = 19, 16
CELL = 46
CANVAS_W = GRID_W * CELL
CANVAS_H = GRID_H * CELL

# Wide AMR roads directly in front of every shelf row.
ROAD_ROWS = {3, 6, 9, 12}
ROAD_CELLS = {(x, y) for y in ROAD_ROWS for x in range(1, 18)}

# AMRs are allowed to drive ONLY on this navigation network.
# Vertical connectors join the horizontal roads and reach the station/charger area.
ROAD_CONNECTOR_X = {1, 4, 7, 10, 13, 16, 17}
ROAD_NETWORK = set(ROAD_CELLS)
for _x in ROAD_CONNECTOR_X:
    for _y in range(3, 15):
        ROAD_NETWORK.add((_x, _y))

# Short access cells for the charging row.
for _x in (2, 5, 8, 11, 14, 17):
    ROAD_NETWORK.add((_x, 13))
    ROAD_NETWORK.add((_x, 14))


def euclidean(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def world_to_px(p):
    return p[0] * CELL + CELL / 2, p[1] * CELL + CELL / 2


def px_to_world(x, y):
    return int(x // CELL), int(y // CELL)


def neighbors(node):
    x, y = node
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        n = (x + dx, y + dy)
        if 0 <= n[0] < GRID_W and 0 <= n[1] < GRID_H:
            yield n


def astar(start, goal, blocked):
    """Road-only A*: AMRs can never cut through shelf/rack cells."""
    if start == goal:
        return [start]

    blocked = set(blocked)
    blocked.discard(start)
    blocked.discard(goal)

    # Only cells belonging to the warehouse road network may be traversed.
    allowed = set(ROAD_NETWORK)
    allowed.add(start)
    allowed.add(goal)

    open_heap = [(0, start)]
    came = {}
    g = {start: 0}

    while open_heap:
        _, current = heapq.heappop(open_heap)
        if current == goal:
            path = [current]
            while current in came:
                current = came[current]
                path.append(current)
            return list(reversed(path))

        for nxt in neighbors(current):
            if nxt not in allowed or nxt in blocked:
                continue
            tentative = g[current] + 1
            if tentative < g.get(nxt, 10**9):
                g[nxt] = tentative
                h = abs(nxt[0] - goal[0]) + abs(nxt[1] - goal[1])
                heapq.heappush(open_heap, (tentative + h, nxt))
                came[nxt] = current

    return [start]


class AMR:
    def __init__(self, name, grid_pos, color):
        self.name = name
        self.gx, self.gy = grid_pos
        self.x, self.y = world_to_px(grid_pos)
        self.color = color
        self.battery = 100.0
        self.status = "IDLE"
        self.task = None
        self.phase = None
        self.path = []
        self.path_index = 0
        self.target_name = None
        self.busy = False
        self.speed = 4.8
        self.distance = 0.0
        self.battery_used = 0.0
        self.wait_ticks = 0
        self.last_score = None
        self.reassigned = False

    def cell(self):
        return self.gx, self.gy

    def reset(self, pos):
        self.gx, self.gy = pos
        self.x, self.y = world_to_px(pos)
        self.battery = 100.0
        self.status = "IDLE"
        self.task = None
        self.phase = None
        self.path = []
        self.path_index = 0
        self.target_name = None
        self.busy = False
        self.distance = 0.0
        self.battery_used = 0.0
        self.wait_ticks = 0
        self.last_score = None
        self.reassigned = False


class SimpleMLModel:
    """Synthetic learned KNN-style model used by ML mode only."""

    def __init__(self):
        random.seed(42)
        self.data = []
        for _ in range(1800):
            dist = random.uniform(5, 100)
            battery = random.uniform(15, 100)
            priority = random.randint(1, 3)
            workload = random.uniform(0, 6)
            target = (
                12
                + dist * 0.70
                + (100 - battery) * 0.12
                + workload * 2.4
                - priority * 2.5
                + random.gauss(0, 1.5)
            )
            self.data.append((dist, battery, priority, workload, target))

    def predict(self, dist, battery, priority, workload):
        ranked = []
        for d, b, p, w, target in self.data:
            metric = (
                ((dist - d) / 100.0) ** 2
                + ((battery - b) / 100.0) ** 2
                + ((priority - p) / 3.0) ** 2
                + ((workload - w) / 6.0) ** 2
            )
            ranked.append((metric, target))
        ranked.sort(key=lambda item: item[0])
        nearest = ranked[:10]
        return sum(v for _, v in nearest) / len(nearest)


class WAREX3D:
    def __init__(self, root):
        self.root = root
        self.root.title("WAREX AI Brain — 3D Warehouse Digital Twin")
        try:
            self.root.state("zoomed")
        except tk.TclError:
            self.root.geometry("1600x950")
        self.root.configure(bg=BG)

        self.colors = [CYAN, GREEN, BLUE, ORANGE, PURPLE, YELLOW]
        starts = [(1, 13), (4, 13), (7, 13), (10, 13), (13, 13), (16, 13)]
        self.amrs = [
            AMR(f"AMR-{i+1:02d}", starts[i], self.colors[i])
            for i in range(6)
        ]

        self.running = False
        self.mode = None
        self.ml_model = SimpleMLModel()
        self.completed = 0
        self.pending = list(TASKS)
        self.active_order = None
        self.start_time = None
        self.events = []
        self.command_windows = []
        self.route_history = {}
        self.assignment_count = 0
        self.total_reassignments = 0
        self.obstacle_hits = 0
        self.simulation_finished = False
        self.obstacles = set()
        self.obstacle_mode = False

        self.build_ui()
        self.reset()

    # --------------------------- UI ---------------------------
    def build_ui(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=18, pady=(12, 6))

        tk.Label(
            header, text="WAREX AI BRAIN",
            bg=BG, fg=CYAN,
            font=("Segoe UI", 27, "bold")
        ).pack(side="left")

        tk.Label(
            header,
            text="3D DIGITAL TWIN  •  MULTI-AMR AUTONOMOUS WAREHOUSE",
            bg=BG, fg=MUTED,
            font=("Segoe UI", 10, "bold")
        ).pack(side="left", padx=22, pady=(9, 0))

        self.mode_label = tk.Label(
            header, text="● SYSTEM READY",
            bg=BG, fg=GREEN,
            font=("Segoe UI", 11, "bold")
        )
        self.mode_label.pack(side="right", pady=(8, 0))

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=18, pady=6)

        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True)

        self.canvas = tk.Canvas(
            left,
            width=CANVAS_W,
            height=CANVAS_H,
            bg=FLOOR,
            highlightthickness=1,
            highlightbackground="#324754",
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.canvas_click)

        right = tk.Frame(body, bg="#101b24", width=390)
        right.pack(side="right", fill="y", padx=(12, 0))
        right.pack_propagate(False)

        tk.Label(
            right, text="WAREX BRAIN",
            bg="#101b24", fg=CYAN,
            font=("Segoe UI", 16, "bold")
        ).pack(pady=(15, 4))

        tk.Label(
            right,
            text="Central task allocation • scoring • path planning",
            bg="#101b24", fg=MUTED,
            font=("Segoe UI", 8)
        ).pack(pady=(0, 10))

        btns = tk.Frame(right, bg="#101b24")
        btns.pack(fill="x", padx=15)

        self.ai_btn = tk.Button(
            btns, text="▶ RUN AI SIMULATION",
            command=lambda: self.start("AI"),
            bg=GREEN, fg="#06130d",
            font=("Segoe UI", 10, "bold"),
            relief="flat", height=2
        )
        self.ai_btn.pack(fill="x", pady=3)

        self.ml_btn = tk.Button(
            btns, text="▶ RUN ML SIMULATION",
            command=lambda: self.start("ML"),
            bg=BLUE, fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat", height=2
        )
        self.ml_btn.pack(fill="x", pady=3)

        self.obstacle_btn = tk.Button(
            btns, text="🧱 ADD / REMOVE OBSTACLE",
            command=self.toggle_obstacle_mode,
            bg="#6b3440", fg=TEXT,
            font=("Segoe UI", 9, "bold"),
            relief="flat", height=2
        )
        self.obstacle_btn.pack(fill="x", pady=3)

        self.clear_obstacles_btn = tk.Button(
            btns, text="CLEAR MY OBSTACLES",
            command=self.clear_user_obstacles,
            bg="#263845", fg=TEXT,
            font=("Segoe UI", 9, "bold"),
            relief="flat", height=2
        )
        self.clear_obstacles_btn.pack(fill="x", pady=3)

        tk.Button(
            btns, text="↻ RESET SIMULATION",
            command=self.reset,
            bg="#263845", fg=TEXT,
            font=("Segoe UI", 10, "bold"),
            relief="flat", height=2
        ).pack(fill="x", pady=3)

        self.metrics = tk.Label(
            right, text="", justify="left",
            bg="#101b24", fg=TEXT,
            font=("Consolas", 9)
        )
        self.metrics.pack(anchor="w", padx=15, pady=8)

        self.obstacle_help = tk.Label(
            right,
            text="Obstacle mode: click an aisle cell to add/remove a red obstacle.",
            bg="#101b24", fg=MUTED, wraplength=350,
            justify="left", font=("Segoe UI", 8)
        )
        self.obstacle_help.pack(anchor="w", padx=15, pady=(0, 8))

        tk.Label(
            right, text="AI MANAGER • NOTIFICATIONS",
            bg="#101b24", fg=CYAN,
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", padx=15, pady=(4, 0))

        self.notifications = tk.Text(
            right, height=7, bg="#0b151c", fg="#d9e7ed",
            font=("Consolas", 7), relief="flat",
            wrap="word", state="disabled"
        )
        self.notifications.pack(fill="x", padx=15, pady=(3, 6))

        tk.Label(
            right, text="LIVE FLEET",
            bg="#101b24", fg=CYAN,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=15)

        self.fleet = tk.Text(
            right, height=12, bg=DARK, fg=TEXT,
            font=("Consolas", 8), relief="flat",
            state="disabled"
        )
        self.fleet.pack(fill="x", padx=15, pady=5)

        tk.Label(
            right, text="BRAIN DECISIONS / EVENTS",
            bg="#101b24", fg=CYAN,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=15, pady=(7, 0))

        self.log = tk.Text(
            right, height=18, bg=DARK, fg="#d9e7ed",
            font=("Consolas", 8), relief="flat",
            state="disabled"
        )
        self.log.pack(fill="both", expand=True, padx=15, pady=5)

        footer = tk.Label(
            self.root,
            text="BLUE = shelf mission   •   ORANGE = delivery   •   PURPLE = charging   •   RED = obstacle / reassignment",
            bg=BG, fg=MUTED, font=("Segoe UI", 8)
        )
        footer.pack(pady=(3, 9))

    # ------------------------ drawing -------------------------
    def draw(self):
        c = self.canvas
        c.delete("all")

        # 2.5D warehouse floor
        for y in range(GRID_H):
            for x in range(GRID_W):
                x0, y0 = x * CELL, y * CELL
                x1, y1 = x0 + CELL, y0 + CELL
                fill = "#16242d" if (x + y) % 2 == 0 else "#122029"
                c.create_rectangle(
                    x0, y0, x1, y1,
                    fill=fill, outline="#22353f"
                )

        # Wide dedicated AMR roads in front of shelf rows.
        for row in sorted(ROAD_ROWS):
            y0 = row * CELL + 4
            y1 = (row + 1) * CELL - 4

            # Raised road bed / shadow
            c.create_rectangle(
                CELL - 2, y0 + 7, 18 * CELL + 2, y1 + 7,
                fill="#070d12", outline=""
            )
            c.create_rectangle(
                CELL, y0, 18 * CELL, y1,
                fill="#26343d", outline="#52656f", width=2
            )

            # Road edge lines
            c.create_line(
                CELL, y0 + 5, 18 * CELL, y0 + 5,
                fill="#6d7f87", width=2
            )
            c.create_line(
                CELL, y1 - 5, 18 * CELL, y1 - 5,
                fill="#0a1116", width=3
            )

            # Center lane markings
            cy = row * CELL + CELL / 2
            for xx in range(CELL + 8, 18 * CELL - 8, 38):
                c.create_line(
                    xx, cy, xx + 20, cy,
                    fill="#e0c34f", width=2
                )

            # Direction arrows
            for xx in range(CELL + 30, 18 * CELL - 30, 120):
                c.create_line(
                    xx, cy, xx + 18, cy,
                    fill="#d9e4e8", width=2
                )
                c.create_polygon(
                    xx + 18, cy,
                    xx + 10, cy - 4,
                    xx + 10, cy + 4,
                    fill="#d9e4e8", outline=""
                )

        # Vertical connector roads between horizontal shelf roads.
        for col in (1, 4, 7, 10, 13, 16, 17):
            x0 = col * CELL + 10
            x1 = (col + 1) * CELL - 10
            c.create_rectangle(
                x0, CELL, x1, 13 * CELL,
                fill="#202e37", outline="#40535f", width=1
            )

        # 2.5D warehouse roof/header.
        c.create_polygon(
            8, 8, CANVAS_W - 8, 8,
            CANVAS_W - 26, 28, 26, 28,
            fill="#263d49", outline="#5b7380"
        )
        c.create_text(
            CANVAS_W / 2, 18,
            text="WAREX AUTONOMOUS FULFILLMENT FLOOR",
            fill=TEXT, font=("Segoe UI", 9, "bold")
        )

        # Obstacles
        for ox, oy in self.obstacles:
            x, y = ox * CELL, oy * CELL
            c.create_rectangle(
                x + 5, y + 5, x + CELL - 5, y + CELL - 5,
                fill="#51262b", outline=RED, width=2
            )
            c.create_polygon(
                x + 10, y + CELL - 10,
                x + CELL - 10, y + CELL - 10,
                x + CELL - 15, y + 10,
                x + 15, y + 10,
                fill="#6c3137", outline=RED
            )
            c.create_text(x + CELL/2, y + CELL/2, text="⚠",
                          fill=YELLOW, font=("Segoe UI", 15, "bold"))

        # Shelf racks with pseudo-3D depth
        for name, (gx, gy) in SHELVES.items():
            x, y = world_to_px((gx, gy))
            self.draw_shelf_3d(x, y, name)

        # Front-of-shelf pickup points / aisle stopping zones
        for shelf_name, pos in PICK_POINTS.items():
            px, py = world_to_px(pos)
            c.create_oval(
                px - 10, py - 10, px + 10, py + 10,
                outline=CYAN, width=2, dash=(3, 2)
            )
            c.create_text(
                px, py + 14, text="▶ PICK",
                fill=CYAN, font=("Segoe UI", 5, "bold")
            )

        # Stations
        for name, pos in RECEIVE.items():
            self.draw_station(*world_to_px(pos), name, "RECEIVE", GREEN)
        for name, pos in DELIVERY.items():
            self.draw_station(*world_to_px(pos), name, "DELIVERY", ORANGE)
        for name, pos in CHARGERS.items():
            self.draw_charger(*world_to_px(pos), name)

        # Brain hub
        bx, by = world_to_px((10, 1))
        c.create_rectangle(bx - 130, by - 24, bx + 130, by + 24,
                           fill="#10323b", outline=CYAN, width=2)
        c.create_text(bx, by - 3, text="◉  WAREX AI BRAIN",
                      fill=CYAN, font=("Segoe UI", 13, "bold"))
        c.create_text(bx, by + 13, text="TASK MANAGER • PATH PLANNER",
                      fill=TEXT, font=("Segoe UI", 7))

        # Active routes
        for amr in self.amrs:
            if len(amr.path) >= 2:
                pts = []
                for cell in amr.path:
                    pts.extend(world_to_px(cell))
                c.create_line(
                    *pts,
                    fill=amr.color,
                    width=2,
                    dash=(7, 4),
                    smooth=False,
                    tags="route"
                )

        # AMRs
        for amr in self.amrs:
            self.draw_amr(amr)

    def show_notification(self, message, level="INFO"):
        """Compact floating notification beside the delivery stations."""
        try:
            if hasattr(self, "notification_window") and self.notification_window.winfo_exists():
                self.notification_window.destroy()
        except Exception:
            pass
        try:
            x = self.grid_x(14.1)
            y = self.grid_y(4.8)
        except Exception:
            x, y = 820, 300
        self.notification_window = tk.Frame(
            self.canvas, bg="#172033",
            highlightbackground="#4b5d78", highlightthickness=1, bd=0
        )
        self.notification_window.place(x=x, y=y, anchor="nw", width=205, height=82)
        tk.Label(
            self.notification_window, text="WAREX • " + str(level).upper(),
            bg="#172033", fg="#7dd3fc", font=("Segoe UI", 8, "bold"),
            anchor="w"
        ).place(x=9, y=6, width=187, height=16)
        tk.Label(
            self.notification_window, text=str(message), bg="#172033",
            fg="#f3f4f6", font=("Segoe UI", 8), justify="left",
            anchor="nw", wraplength=187
        ).place(x=9, y=25, width=187, height=48)
        try:
            self.after(2800, self._hide_notification)
        except Exception:
            pass

    def _hide_notification(self):
        try:
            if hasattr(self, "notification_window") and self.notification_window.winfo_exists():
                self.notification_window.destroy()
        except Exception:
            pass

    def draw_shelf_3d(self, x, y, name):
        c = self.canvas
        w, h = 34, 25
        depth = 10
        # Raised top face
        c.create_polygon(
            x-w, y-h, x+w, y-h,
            x+w+depth, y-h-depth,
            x-w+depth, y-h-depth,
            fill="#425c6b", outline="#78919e"
        )
        # Lower shadow face
        c.create_polygon(
            x-w, y+h, x+w, y+h,
            x+w+depth, y+h-depth,
            x-w+depth, y+h-depth,
            fill="#17252e", outline="#304550"
        )
        c.create_rectangle(
            x-w, y-h, x+w, y+h,
            fill="#243744", outline=BLUE, width=2
        )
        c.create_polygon(
            x+w, y-h, x+w+depth, y-h-depth,
            x+w+depth, y+h-depth,
            x+w, y+h,
            fill="#1b2c36", outline=BLUE
        )
        for yy in (-8, 4, 16):
            c.create_line(x-w+4, y+yy, x+w-4, y+yy,
                          fill="#5b7382", width=2)
        c.create_text(x, y-2, text=name, fill=WHITE,
                      font=("Segoe UI", 9, "bold"))
        c.create_text(x, y+15, text="RACK", fill="#91aab7",
                      font=("Segoe UI", 6))

    def draw_station(self, x, y, name, kind, color):
        c = self.canvas
        c.create_oval(x-32, y-21, x+32, y+21,
                      fill="#18322f" if kind == "RECEIVE" else "#3b3020",
                      outline=color, width=2)
        c.create_text(x, y-3, text=name, fill=WHITE,
                      font=("Segoe UI", 10, "bold"))
        c.create_text(x, y+11, text=kind, fill=color,
                      font=("Segoe UI", 6, "bold"))

    def draw_charger(self, x, y, name):
        c = self.canvas
        c.create_rectangle(x-30, y-20, x+30, y+20,
                           fill="#302540", outline=PURPLE, width=2)
        c.create_text(x, y-3, text=name, fill=WHITE,
                      font=("Segoe UI", 9, "bold"))
        c.create_text(x, y+11, text="⚡ CHARGE", fill=PURPLE,
                      font=("Segoe UI", 6, "bold"))

    def draw_amr(self, amr):
        c = self.canvas
        x, y = amr.x, amr.y

        if amr.status == "IDLE":
            col = GREEN
        elif "CHARGE" in amr.status:
            col = PURPLE
        elif "OBSTACLE" in amr.status:
            col = RED
        elif "SHELF" in amr.status or "PICK" in amr.status:
            col = BLUE
        else:
            col = ORANGE

        # Ground shadow
        c.create_oval(x-23, y+12, x+23, y+25,
                      fill="#05090c", outline="", tags="amr")

        # 3D body
        c.create_polygon(
            x-20, y-12, x+13, y-12,
            x+21, y-4, x+14, y+13,
            x-18, y+13, x-25, y+4,
            fill="#263945", outline=col, width=2, tags="amr"
        )
        c.create_polygon(
            x-20, y-12, x-12, y-20,
            x+21, y-20, x+13, y-12,
            fill="#3c5664", outline=col, tags="amr"
        )

        c.create_oval(x-7, y-15, x+7, y-1,
                      fill=col, outline=WHITE, width=1, tags="amr")
        c.create_text(x, y+3, text=amr.name[-2:],
                      fill=WHITE, font=("Segoe UI", 7, "bold"), tags="amr")

        # Battery bar
        bar_w = 46
        c.create_rectangle(x-bar_w/2, y-34, x+bar_w/2, y-29,
                           fill="#27343d", outline="", tags="amr")
        bw = bar_w * max(0, min(100, amr.battery)) / 100
        bcol = GREEN if amr.battery > 40 else ORANGE if amr.battery > 20 else RED
        c.create_rectangle(x-bar_w/2, y-34, x-bar_w/2+bw, y-29,
                           fill=bcol, outline="", tags="amr")

        c.create_text(
            x, y-43,
            text=f"{amr.name}  {amr.battery:.0f}%",
            fill=WHITE, font=("Segoe UI", 7, "bold"), tags="amr"
        )

        c.create_text(
            x, y+30,
            text=amr.status,
            fill=col, font=("Segoe UI", 6, "bold"), tags="amr"
        )

    # ---------------------- task brain ------------------------
    def ai_score(self, amr, task):
        order, shelf, dest, priority = task
        pickup = PICK_POINTS[shelf]
        destination = RECEIVE.get(dest, DELIVERY.get(dest))
        p1 = astar(amr.cell(), pickup, self.obstacles)
        p2 = astar(pickup, destination, self.obstacles)
        path_len = len(p1) + len(p2)
        battery_penalty = max(0, 35 - amr.battery) * 2.5
        priority_bonus = priority * 12
        score = path_len + battery_penalty - priority_bonus
        return score, path_len

    def ml_score(self, amr, task):
        order, shelf, dest, priority = task
        pickup = PICK_POINTS[shelf]
        destination = RECEIVE.get(dest, DELIVERY.get(dest))
        p1 = astar(amr.cell(), pickup, self.obstacles)
        p2 = astar(pickup, destination, self.obstacles)
        path_len = len(p1) + len(p2)
        workload = sum(1 for a in self.amrs if a.busy)
        predicted = self.ml_model.predict(
            path_len, amr.battery, priority, workload
        )
        return predicted, path_len

    def choose_amr(self, task):
        idle = [a for a in self.amrs if not a.busy and a.status == "IDLE"]
        if not idle:
            return None

        ranked = []
        for amr in idle:
            if self.mode == "ML":
                score, path_len = self.ml_score(amr, task)
            else:
                score, path_len = self.ai_score(amr, task)
            ranked.append((score, amr, path_len))

        ranked.sort(key=lambda item: item[0])
        return ranked[0]

    def assign_next_tasks(self):
        while self.pending:
            task = self.pending[0]
            chosen = self.choose_amr(task)
            if chosen is None:
                return

            score, amr, path_len = chosen
            self.pending.pop(0)
            self.assign(amr, task, score, path_len)

    def assign(self, amr, task, score, path_len):
        order, shelf, dest, priority = task
        amr.task = task
        amr.busy = True
        amr.phase = "SHELF"
        amr.status = "GO TO SHELF FRONT"
        amr.target_name = shelf

        # IMPORTANT: route to the aisle pickup point, not the shelf geometry.
        amr.path = astar(amr.cell(), PICK_POINTS[shelf], self.obstacles)
        amr.path_index = 1 if len(amr.path) > 1 else 0
        amr.last_score = score
        self.assignment_count += 1

        self.notify(
            f"{self.mode} ASSIGN",
            f"{amr.name} → {order} | {shelf} FRONT → {dest} | score {score:.1f} | {path_len} cells | {amr.battery:.0f}%",
            CYAN if self.mode == "AI" else BLUE,
        )

        self.event(
            f"{self.mode} BRAIN → {amr.name}: {order} | "
            f"{shelf} front → {dest} | score={score:.1f}"
        )

    # --------------------- movement ---------------------------
    def tick(self):
        if not self.running:
            return

        moving = False

        for amr in self.amrs:
            if not amr.busy and amr.phase != "CHARGE":
                continue

            # Battery protection and dynamic reassignment
            if amr.busy and amr.phase in ("SHELF", "DESTINATION") and amr.battery < 16:
                self.send_to_charge(amr)
                moving = True
                continue

            if amr.phase == "CHARGE" and amr.path:
                moving = True
                self.move_amr(amr)
                continue

            if amr.path:
                moving = True
                self.move_amr(amr)

        self.update()
        self.draw()

        if self.completed >= len(TASKS):
            self.finish()
            return

        self.root.after(45, self.tick)

    def move_amr(self, amr):
        if amr.path_index >= len(amr.path):
            self.arrival(amr)
            return

        target_cell = amr.path[amr.path_index]
        tx, ty = world_to_px(target_cell)

        dx, dy = tx - amr.x, ty - amr.y
        d = math.hypot(dx, dy)

        if d <= amr.speed:
            step = d
            amr.x, amr.y = tx, ty
            amr.gx, amr.gy = target_cell
            amr.path_index += 1
        else:
            step = amr.speed
            amr.x += amr.speed * dx / d
            amr.y += amr.speed * dy / d

        amr.distance += step
        used = step * 0.010
        amr.battery = max(0, amr.battery - used)
        amr.battery_used += used

    def arrival(self, amr):
        if amr.phase == "CHARGE":
            amr.battery = 100
            amr.status = "IDLE"
            amr.busy = False
            amr.phase = None
            amr.target_name = None
            amr.path = []
            self.event(f"{amr.name} recharged to 100%.")
            self.assign_next_tasks()
            return

        if amr.phase == "SHELF":
            order, shelf, dest, priority = amr.task
            amr.status = "PICK ORDER"
            self.event(f"{amr.name} reached {shelf} and picked {order}.")

            destination = RECEIVE.get(dest, DELIVERY.get(dest))
            amr.path = astar(amr.cell(), destination, self.obstacles)
            amr.path_index = 1 if len(amr.path) > 1 else 0
            amr.phase = "DESTINATION"
            amr.target_name = dest
            amr.status = "GO TO " + dest

            self.notify(
                "PICKED",
                f"{amr.name} picked {order} at {shelf} FRONT → A* to {dest}",
                BLUE,
            )

        elif amr.phase == "DESTINATION":
            order, shelf, dest, priority = amr.task
            self.completed += 1
            self.event(f"{amr.name} delivered {order} to {dest}.")

            self.notify(
                "COMPLETED",
                f"{amr.name} delivered {order} {shelf} → {dest} | {amr.distance:.1f} dist | {amr.battery:.0f}%",
                GREEN,
            )

            amr.status = "IDLE"
            amr.busy = False
            amr.task = None
            amr.phase = None
            amr.path = []
            amr.target_name = None

            self.assign_next_tasks()

    def send_to_charge(self, amr):
        if amr.phase == "CHARGE":
            return

        old_task = amr.task
        if old_task and old_task not in self.pending:
            self.pending.insert(0, old_task)

        self.total_reassignments += 1
        self.event(
            f"LOW BATTERY: {amr.name} → task returned to queue; "
            f"reassigning to another AMR after charge."
        )

        charger_name, charger_pos = min(
            CHARGERS.items(),
            key=lambda kv: euclidean(amr.cell(), kv[1])
        )

        amr.busy = False
        amr.phase = "CHARGE"
        amr.status = "GO TO CHARGER"
        amr.target_name = charger_name
        amr.path = astar(amr.cell(), charger_pos, self.obstacles)
        amr.path_index = 1 if len(amr.path) > 1 else 0
        amr.task = None

        self.notify(
            "REASSIGN",
            f"{amr.name} low battery {amr.battery:.0f}% → CHARGE {charger_name}; task returned to queue",
            RED,
        )
        self.assign_next_tasks()

    # -------------------- user obstacles ---------------------
    def toggle_obstacle_mode(self):
        self.obstacle_mode = not self.obstacle_mode
        if self.obstacle_mode:
            self.obstacle_btn.config(
                text="🧱 OBSTACLE MODE: ON",
                bg=RED
            )
            self.obstacle_help.config(
                text="OBSTACLE MODE ON: click an aisle cell to add/remove a red obstacle.",
                fg=RED
            )
            self.event("Manual obstacle mode enabled.")
        else:
            self.obstacle_btn.config(
                text="🧱 ADD / REMOVE OBSTACLE",
                bg="#6b3440"
            )
            self.obstacle_help.config(
                text="Obstacle mode: click an aisle cell to add/remove a red obstacle.",
                fg=MUTED
            )

    def canvas_click(self, event):
        if not self.obstacle_mode or self.running:
            return

        cell = px_to_world(event.x, event.y)
        x, y = cell

        if not (0 <= x < GRID_W and 0 <= y < GRID_H):
            return

        protected = set(SHELVES.values()) | set(PICK_POINTS.values())
        protected |= set(RECEIVE.values()) | set(DELIVERY.values()) | set(CHARGERS.values())

        if cell in protected:
            self.event("Obstacle rejected: station/shelf/pickup cell is protected.")
            return

        if cell in self.obstacles:
            self.obstacles.remove(cell)
            self.event(f"Manual obstacle REMOVED at cell {cell}.")
        else:
            self.obstacles.add(cell)
            self.event(f"Manual obstacle CREATED at cell {cell}.")

        self.draw()
        self.update()

    def clear_user_obstacles(self):
        if self.running:
            return
        self.obstacles = set()
        self.event("All manual obstacles cleared. Warehouse is now obstacle-free.")
        self.draw()
        self.update()

    # ----------------------- start/reset ----------------------
    def start(self, mode):
        if self.running:
            return

        if self.simulation_finished:
            self.reset()

        self.mode = mode
        self.running = True
        self.simulation_finished = False
        self.start_time = time.time()
        self.mode_label.config(text=f"● {self.mode} MODE RUNNING", fg=GREEN if self.mode == "AI" else BLUE)
        self.event(f"WAREX Brain online. {self.mode} mode selected. Scanning orders, fleet and obstacles.")
        self.assign_next_tasks()
        self.tick()

    def reset(self):
        self.running = False
        self.mode = None
        self.completed = 0
        self.pending = list(TASKS)
        self.start_time = None
        self.simulation_finished = False
        self.obstacles = set()
        self.obstacle_mode = False
        self.total_reassignments = 0
        self.assignment_count = 0

        starts = [(1, 13), (4, 13), (7, 13), (10, 13), (13, 13), (16, 13)]
        for i, amr in enumerate(self.amrs):
            amr.reset(starts[i])

        self.mode_label.config(text="● SYSTEM READY", fg=GREEN)

        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")
        self.notifications.config(state="normal")
        self.notifications.delete("1.0", "end")
        self.notifications.config(state="disabled")

        self.event("System reset. 6 AMRs ready. 12 orders queued.")
        self.notify("SYSTEM", "6 AMRs ready • 12 orders queued", GREEN)
        self.update()
        self.draw()

    def finish(self):
        if self.simulation_finished:
            return

        self.running = False
        self.simulation_finished = True
        elapsed = time.time() - self.start_time if self.start_time else 0
        self.mode_label.config(text="● ALL TASKS COMPLETE", fg=GREEN)
        self.update()

        self.notify(
            "RUN COMPLETE",
            f"All {self.completed}/{len(TASKS)} orders complete | {elapsed:.1f}s | reassignments {self.total_reassignments}",
            GREEN,
        )

    # ------------------------- info ---------------------------
    def event(self, text):
        stamp = time.strftime("%H:%M:%S")
        self.log.config(state="normal")
        self.log.insert("end", f"[{stamp}] {text}\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def notify(self, title, message, accent):
        """Compact notification displayed inside the AI Manager panel."""
        stamp = time.strftime("%H:%M:%S")
        self.notifications.config(state="normal")
        self.notifications.insert("end", f"[{stamp}] {title}: {message}\n")
        # Color the latest line without opening a separate popup window.
        line = self.notifications.index("end-2l linestart")
        end_line = self.notifications.index("end-2l lineend")
        tag = f"note_{stamp}_{self.assignment_count}_{self.completed}"
        self.notifications.tag_add(tag, line, end_line)
        self.notifications.tag_config(tag, foreground=accent)
        # Keep only the latest 8 notifications so the manager stays compact.
        line_count = int(self.notifications.index("end-1c").split(".")[0])
        while line_count > 9:
            self.notifications.delete("1.0", "2.0")
            line_count -= 1
        self.notifications.see("end")
        self.notifications.config(state="disabled")

    def update(self):
        elapsed = time.time() - self.start_time if self.start_time else 0
        total_dist = sum(a.distance for a in self.amrs)
        total_bat = sum(a.battery_used for a in self.amrs)

        self.metrics.config(
            text=(
                f"MODE                {self.mode or "READY"}\n"
                f"ORDERS              {self.completed:02d} / {len(TASKS):02d}\n"
                f"PENDING             {len(self.pending):02d}\n"
                f"ELAPSED             {elapsed:6.1f} s\n"
                f"FLEET DISTANCE      {total_dist:7.1f}\n"
                f"BATTERY CONSUMED    {total_bat:7.1f}%\n"
                f"REASSIGNMENTS       {self.total_reassignments:02d}\n"
                f"OBSTACLES           {len(self.obstacles):02d}\n"
            )
        )

        lines = []
        for a in self.amrs:
            order = a.task[0] if a.task else "-"
            lines.append(
                f"{a.name}  {a.battery:5.1f}%  "
                f"{a.status[:18]:18}  {order}"
            )

        self.fleet.config(state="normal")
        self.fleet.delete("1.0", "end")
        self.fleet.insert("1.0", "\n".join(lines))
        self.fleet.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = WAREX3D(root)
    root.mainloop()
