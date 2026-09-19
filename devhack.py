import tkinter as tk
from tkinter import ttk, messagebox
import math
import random
import time

# ============================================================
# WAREX AI BRAIN - COMPLETE VIRTUAL WAREHOUSE SIMULATION
# ============================================================

WIDTH = 1180
HEIGHT = 850

BG = "#101820"
PANEL = "#18232d"
GRID = "#2b3945"
TEXT = "#f4f7f9"
GREEN = "#32d583"
BLUE = "#4da3ff"
ORANGE = "#ffb020"
RED = "#ff5c5c"
PURPLE = "#a970ff"
CYAN = "#28d7d0"
WHITE = "#ffffff"

SHELVES = {
    "S01": (120, 150), "S02": (300, 150), "S03": (480, 150),
    "S04": (120, 300), "S05": (300, 300), "S06": (480, 300),
    "S07": (120, 450), "S08": (300, 450), "S09": (480, 450),
    "S10": (120, 600), "S11": (300, 600), "S12": (480, 600),
}

RECEIVE_STATIONS = {
    "R01": (720, 180),
    "R02": (720, 380),
    "R03": (720, 580),
}

DELIVERY_STATIONS = {
    "D01": (930, 180),
    "D02": (930, 380),
    "D03": (930, 580),
}

CHARGING_STATIONS = {
    "C01": (150, 760), "C02": (300, 760), "C03": (450, 760),
    "C04": (600, 760), "C05": (750, 760), "C06": (900, 760),
}

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


def distance(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


class AMR:
    def __init__(self, name, x, y):
        self.name = name
        self.start_x = x
        self.start_y = y
        self.x = x
        self.y = y
        self.battery = 100.0
        self.status = "IDLE"
        self.task = None
        self.target_name = None
        self.target = None
        self.phase = None
        self.busy = False
        self.distance_travelled = 0.0
        self.battery_used = 0.0

    def get_position(self):
        return self.x, self.y

    def distance_to(self, x, y):
        return math.sqrt((self.x - x) ** 2 + (self.y - y) ** 2)

    def set_target(self, name, position, phase):
        self.target_name = name
        self.target = position
        self.phase = phase

    def move(self, speed=7.0):
        if self.target is None:
            return True

        dx = self.target[0] - self.x
        dy = self.target[1] - self.y
        d = math.sqrt(dx * dx + dy * dy)

        if d <= speed:
            travelled = d
            self.x, self.y = self.target
            self.distance_travelled += travelled
            self.consume_battery(travelled)
            return True

        self.x += speed * dx / d
        self.y += speed * dy / d
        self.distance_travelled += speed
        self.consume_battery(speed)
        return False

    def consume_battery(self, amount):
        used = amount * 0.012
        self.battery = max(0.0, self.battery - used)
        self.battery_used += used

    def reset(self):
        self.x = self.start_x
        self.y = self.start_y
        self.battery = 100.0
        self.status = "IDLE"
        self.task = None
        self.target_name = None
        self.target = None
        self.phase = None
        self.busy = False
        self.distance_travelled = 0.0
        self.battery_used = 0.0


class SimpleMLModel:
    """
    Lightweight learned model.
    It trains on synthetic historical warehouse records and predicts
    completion time using nearest-neighbour regression.
    """

    def __init__(self):
        random.seed(42)
        self.data = []
        self.train()

    def train(self):
        for _ in range(2500):
            dist = random.uniform(30, 1100)
            battery = random.uniform(20, 100)
            priority = random.randint(1, 3)
            workload = random.uniform(0, 8)

            target = (
                18
                + dist * 0.085
                + (100 - battery) * 0.18
                + workload * 2.7
                - priority * 4.0
                + random.gauss(0, 3)
            )
            self.data.append((dist, battery, priority, workload, target))

    def predict(self, distance_value, battery, priority, workload):
        query = (distance_value, battery, priority, workload)

        scored = []
        for row in self.data:
            d = (
                ((query[0] - row[0]) / 1000.0) ** 2
                + ((query[1] - row[1]) / 100.0) ** 2
                + ((query[2] - row[2]) / 3.0) ** 2
                + ((query[3] - row[3]) / 8.0) ** 2
            )
            scored.append((d, row[4]))

        scored.sort(key=lambda item: item[0])
        nearest = scored[:12]
        return sum(v for _, v in nearest) / len(nearest)


class WAREXApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WAREX AI Brain - Virtual Warehouse")
        self.root.geometry("1500x900")
        self.root.minsize(1250, 780)
        self.root.configure(bg=BG)
        self.root.resizable(True, True)
        try:
            self.root.state("zoomed")
        except tk.TclError:
            pass

        self.ml_model = SimpleMLModel()
        self.mode = None
        self.running = False
        self.paused = False
        self.start_time = None
        self.completed = 0
        self.total_distance = 0.0
        self.total_battery_used = 0.0
        self.pending_tasks = []
        self.results = {}
        self.popup_count = 0

        starts = [
            (560, 700), (600, 700), (640, 700),
            (680, 700), (720, 700), (760, 700),
        ]
        self.amrs = [
            AMR(f"AMR-{i + 1:02d}", starts[i][0], starts[i][1])
            for i in range(6)
        ]

        self.build_ui()
        self.reset()

    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------
    def build_ui(self):
        title = tk.Label(
            self.root,
            text="WAREX AI BRAIN",
            font=("Segoe UI", 24, "bold"),
            bg=BG,
            fg=CYAN,
        )
        title.pack(pady=(8, 2))

        subtitle = tk.Label(
            self.root,
            text="Central Intelligence Manager • 6 AMRs • 12 Shelves • Receive / Delivery / Charging",
            font=("Segoe UI", 10),
            bg=BG,
            fg=TEXT,
        )
        subtitle.pack(pady=(0, 6))

        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=8, pady=4)

        self.canvas = tk.Canvas(
            main,
            width=1000,
            height=800,
            bg="#0c141b",
            highlightthickness=1,
            highlightbackground=GRID,
        )
        self.canvas.pack(side="left", padx=(0, 8))

        side = tk.Frame(main, width=420, bg=PANEL)
        side.pack(side="right", fill="y")
        side.pack_propagate(False)

        tk.Label(
            side,
            text="WAREX BRAIN CONTROL",
            font=("Segoe UI", 14, "bold"),
            bg=PANEL,
            fg=CYAN,
        ).pack(pady=(12, 8))

        button_frame = tk.Frame(side, bg=PANEL)
        button_frame.pack(fill="x", padx=12)

        self.ai_btn = tk.Button(
            button_frame,
            text="▶ RUN AI SIMULATION",
            command=lambda: self.start("AI"),
            bg=GREEN,
            fg="#07110b",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            height=2,
        )
        self.ai_btn.pack(fill="x", pady=3)

        self.ml_btn = tk.Button(
            button_frame,
            text="▶ RUN ML SIMULATION",
            command=lambda: self.start("ML"),
            bg=BLUE,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            height=2,
        )
        self.ml_btn.pack(fill="x", pady=3)

        tk.Button(
            button_frame,
            text="📊 SHOW AI vs ML",
            command=self.show_comparison,
            bg=PURPLE,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            height=2,
        ).pack(fill="x", pady=3)

        tk.Button(
            button_frame,
            text="↻ RESET",
            command=self.reset,
            bg=ORANGE,
            fg="#181000",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            height=2,
        ).pack(fill="x", pady=3)

        self.mode_label = tk.Label(
            side,
            text="MODE: READY",
            font=("Segoe UI", 11, "bold"),
            bg=PANEL,
            fg=TEXT,
        )
        self.mode_label.pack(pady=(10, 4))

        self.metrics_label = tk.Label(
            side,
            text="",
            justify="left",
            anchor="w",
            font=("Consolas", 9),
            bg=PANEL,
            fg=TEXT,
        )
        self.metrics_label.pack(fill="x", padx=12, pady=5)

        tk.Label(
            side,
            text="LIVE AMR STATUS",
            font=("Segoe UI", 11, "bold"),
            bg=PANEL,
            fg=CYAN,
        ).pack(anchor="w", padx=12, pady=(8, 3))

        self.status_text = tk.Text(
            side,
            height=13,
            width=52,
            bg="#0c141b",
            fg=TEXT,
            font=("Consolas", 8),
            relief="flat",
            state="disabled",
        )
        self.status_text.pack(fill="x", padx=12)

        tk.Label(
            side,
            text="BRAIN EVENT LOG",
            font=("Segoe UI", 11, "bold"),
            bg=PANEL,
            fg=CYAN,
        ).pack(anchor="w", padx=12, pady=(8, 3))

        self.log_text = tk.Text(
            side,
            height=14,
            width=52,
            bg="#0c141b",
            fg="#dce7ee",
            font=("Consolas", 8),
            relief="flat",
            state="disabled",
        )
        self.log_text.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    # --------------------------------------------------------
    # Drawing
    # --------------------------------------------------------
    def draw_environment(self):
        self.canvas.delete("all")

        # Warehouse floor background and subtle grid
        self.canvas.create_rectangle(8, 8, 992, 792, fill="#0b151c", outline="#314451", width=2)
        for x in range(20, 1000, 40):
            self.canvas.create_line(x, 35, x, 790, fill="#13222b")
        for y in range(45, 791, 40):
            self.canvas.create_line(20, y, 990, y, fill="#13222b")

        # Aisles
        for x in (210, 390, 570):
            self.canvas.create_rectangle(x - 18, 110, x + 18, 690, fill="#101d25", outline="")
            self.canvas.create_text(x, 400, text="AISLE", fill="#3b5362", font=("Segoe UI", 7, "bold"), angle=90)

        # Operational zones
        self.canvas.create_rectangle(40, 95, 535, 660, outline="#244b5b", width=2, dash=(8, 5))
        self.canvas.create_text(65, 108, text="STORAGE / PICKING ZONE", anchor="w", fill="#4f7484", font=("Segoe UI", 9, "bold"))
        self.canvas.create_rectangle(680, 125, 985, 635, outline="#31543f", width=2, dash=(8, 5))
        self.canvas.create_text(700, 138, text="FULFILLMENT ZONE", anchor="w", fill="#6e9c7e", font=("Segoe UI", 9, "bold"))
        self.canvas.create_rectangle(70, 700, 970, 790, outline="#493c61", width=2, dash=(8, 5))
        self.canvas.create_text(90, 715, text="AMR CHARGING DOCKS", anchor="w", fill="#8b72a9", font=("Segoe UI", 9, "bold"))

        self.canvas.create_text(500, 22, text="WAREX VIRTUAL AUTONOMOUS WAREHOUSE", fill=TEXT, font=("Segoe UI", 15, "bold"))
        self.canvas.create_text(500, 43, text="Real-time fleet orchestration • task allocation • battery management", fill="#6f8795", font=("Segoe UI", 8))

        # Shelves
        for name, (x, y) in SHELVES.items():
            self.canvas.create_rectangle(
                x - 48, y - 28, x + 48, y + 28,
                fill="#273846",
                outline=BLUE,
                width=2,
            )
            self.canvas.create_text(
                x, y - 4,
                text=name,
                fill=WHITE,
                font=("Segoe UI", 10, "bold"),
            )
            self.canvas.create_text(
                x, y + 13,
                text="SHELF",
                fill="#9fb3c1",
                font=("Segoe UI", 7),
            )

        # Receive
        for name, (x, y) in RECEIVE_STATIONS.items():
            self.draw_station(x, y, name, "RECEIVE", GREEN)

        # Delivery
        for name, (x, y) in DELIVERY_STATIONS.items():
            self.draw_station(x, y, name, "DELIVERY", ORANGE)

        # Charging
        for name, (x, y) in CHARGING_STATIONS.items():
            self.canvas.create_rectangle(
                x - 32, y - 22, x + 32, y + 22,
                fill="#3a293f",
                outline=PURPLE,
                width=2,
            )
            self.canvas.create_text(
                x, y - 3,
                text=name,
                fill=WHITE,
                font=("Segoe UI", 9, "bold"),
            )
            self.canvas.create_text(
                x, y + 12,
                text="CHARGE",
                fill=PURPLE,
                font=("Segoe UI", 6),
            )

        # Legend
        legend = [(GREEN, "IDLE / READY"), (BLUE, "PICKING"), (ORANGE, "DELIVERING"), (PURPLE, "CHARGING"), (CYAN, "BRAIN")]
        lx, ly = 825, 675
        for i, (c, label) in enumerate(legend):
            xx = lx + (i % 2) * 105
            yy = ly + (i // 2) * 18
            self.canvas.create_rectangle(xx, yy, xx + 9, yy + 9, fill=c, outline="")
            self.canvas.create_text(xx + 14, yy + 4, text=label, anchor="w", fill="#a8bbc5", font=("Segoe UI", 6))

        # Brain
        self.canvas.create_rectangle(
            565, 60, 795, 105,
            fill="#102d35",
            outline=CYAN,
            width=2,
        )
        self.canvas.create_text(
            680, 79,
            text="●  WAREX AI BRAIN",
            fill=CYAN,
            font=("Segoe UI", 12, "bold"),
        )
        self.canvas.create_text(
            680, 96,
            text="DISPATCH • PREDICT • REASSIGN • OPTIMIZE",
            fill="#7daeb5",
            font=("Segoe UI", 6, "bold"),
        )

    def draw_station(self, x, y, name, kind, color):
        self.canvas.create_oval(
            x - 38, y - 25, x + 38, y + 25,
            fill="#24332d" if kind == "RECEIVE" else "#3a3020",
            outline=color,
            width=2,
        )
        self.canvas.create_text(
            x, y - 5,
            text=name,
            fill=WHITE,
            font=("Segoe UI", 9, "bold"),
        )
        self.canvas.create_text(
            x, y + 10,
            text=kind,
            fill=color,
            font=("Segoe UI", 6),
        )

    def draw_amrs(self):
        self.canvas.delete("amr")

        for amr in self.amrs:
            x, y = amr.get_position()

            if amr.status == "IDLE":
                color = GREEN
            elif "CHARGE" in amr.status:
                color = PURPLE
            elif "SHELF" in amr.status:
                color = BLUE
            elif "DESTINATION" in amr.status:
                color = ORANGE
            else:
                color = CYAN

            self.canvas.create_oval(
                x - 18, y - 18, x + 18, y + 18,
                fill=color,
                outline=WHITE,
                width=2,
                tags="amr",
            )
            self.canvas.create_text(
                x, y,
                text=amr.name[-2:],
                fill="#081016",
                font=("Segoe UI", 8, "bold"),
                tags="amr",
            )

            self.canvas.create_text(
                x, y - 29,
                text=f"{amr.battery:.0f}%",
                fill=WHITE,
                font=("Segoe UI", 7, "bold"),
                tags="amr",
            )
            bar_w = 42
            fill_w = bar_w * max(0, min(100, amr.battery)) / 100
            self.canvas.create_rectangle(x - 21, y + 22, x + 21, y + 27, fill="#263640", outline="", tags="amr")
            self.canvas.create_rectangle(x - 21, y + 22, x - 21 + fill_w, y + 27, fill=color, outline="", tags="amr")
            self.canvas.create_text(
                x, y + 39, text=amr.status, fill="#c8d6dd",
                font=("Segoe UI", 6, "bold"), tags="amr"
            )

            if amr.target_name:
                self.canvas.create_line(
                    x, y, amr.target[0], amr.target[1],
                    fill=color,
                    dash=(4, 3),
                    tags="amr",
                )

    # --------------------------------------------------------
    # Logging/status
    # --------------------------------------------------------
    def log(self, message):
        stamp = time.strftime("%H:%M:%S")
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"[{stamp}] {message}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def update_status(self):
        lines = []
        for amr in self.amrs:
            task = amr.task[0] if amr.task else "-"
            lines.append(
                f"{amr.name} | {amr.battery:5.1f}% | "
                f"{amr.status[:20]:20} | {task}"
            )

        self.status_text.config(state="normal")
        self.status_text.delete("1.0", "end")
        self.status_text.insert("1.0", "\n".join(lines))
        self.status_text.config(state="disabled")

        elapsed = 0 if self.start_time is None else time.time() - self.start_time

        self.metrics_label.config(
            text=(
                f"MODE              : {self.mode or 'READY'}\n"
                f"COMPLETED ORDERS  : {self.completed}/{len(TASKS)}\n"
                f"ELAPSED TIME      : {elapsed:6.1f} s\n"
                f"TOTAL DISTANCE    : {self.total_distance:6.1f}\n"
                f"BATTERY USED      : {self.total_battery_used:6.1f}%\n"
                f"PENDING TASKS     : {len(self.pending_tasks)}"
            )
        )

    # --------------------------------------------------------
    # Reset / start
    # --------------------------------------------------------
    def reset(self):
        self.running = False
        self.paused = False
        self.mode = None
        self.start_time = None
        self.completed = 0
        self.total_distance = 0.0
        self.total_battery_used = 0.0
        self.pending_tasks = list(TASKS)
        # Keep completed AI/ML results so the user can run:
        # AI -> RESET -> ML -> SHOW AI vs ML
        if not hasattr(self, "results"):
            self.results = {}

        for amr in self.amrs:
            amr.reset()

        self.mode_label.config(text="MODE: READY", fg=TEXT)

        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

        self.draw_environment()
        self.draw_amrs()
        self.update_status()

    def start(self, mode):
        if self.running:
            messagebox.showinfo(
                "WAREX",
                "A simulation is already running. Press RESET before starting another run."
            )
            return

        self.reset()
        self.mode = mode
        self.running = True
        self.start_time = time.time()
        self.mode_label.config(
            text=f"MODE: {mode} ACTIVE",
            fg=GREEN if mode == "AI" else BLUE,
        )

        self.log(
            f"WAREX Brain started {mode} simulation with "
            f"{len(self.amrs)} AMRs and {len(self.pending_tasks)} orders."
        )

        self.dispatch_tasks()
        self.loop()

    # --------------------------------------------------------
    # Decision engines
    # --------------------------------------------------------
    def ai_score(self, amr, task):
        _, shelf, destination, priority = task
        sx, sy = SHELVES[shelf]
        dx, dy = self.get_location(destination)

        travel = amr.distance_to(sx, sy) + distance((sx, sy), (dx, dy))
        battery_factor = max(0, 100 - amr.battery)
        priority_bonus = priority * 80

        return travel + battery_factor * 3 - priority_bonus

    def ml_score(self, amr, task):
        _, shelf, destination, priority = task
        sx, sy = SHELVES[shelf]
        dx, dy = self.get_location(destination)

        total_dist = (
            amr.distance_to(sx, sy)
            + distance((sx, sy), (dx, dy))
        )

        workload = sum(1 for a in self.amrs if a.busy)
        predicted = self.ml_model.predict(
            total_dist,
            amr.battery,
            priority,
            workload,
        )
        return predicted

    def choose_amr(self, task):
        candidates = [
            amr for amr in self.amrs
            if not amr.busy and amr.status == "IDLE"
        ]

        if not candidates:
            return None

        if self.mode == "AI":
            return min(candidates, key=lambda a: self.ai_score(a, task))

        return min(candidates, key=lambda a: self.ml_score(a, task))

    def dispatch_tasks(self):
        if not self.running:
            return

        while self.pending_tasks:
            task = self.pending_tasks[0]
            amr = self.choose_amr(task)

            if amr is None:
                break

            self.pending_tasks.pop(0)
            self.assign_task(amr, task)

    def assign_task(self, amr, task):
        order, shelf, destination, priority = task
        amr.task = task
        amr.busy = True
        amr.status = "GOING TO SHELF"

        shelf_pos = SHELVES[shelf]
        amr.set_target(shelf, shelf_pos, "SHELF")

        command = (
            f"{amr.name}\n"
            f"GO TO {shelf}\n"
            f"PICK {order}\n"
            f"DESTINATION: {destination}"
        )

        self.log(
            f"BRAIN → {amr.name}: GO TO {shelf} / PICK {order} / "
            f"DESTINATION: {destination}"
        )
        self.show_command_popup(amr.name, command)

    def get_location(self, name):
        if name in SHELVES:
            return SHELVES[name]
        if name in RECEIVE_STATIONS:
            return RECEIVE_STATIONS[name]
        if name in DELIVERY_STATIONS:
            return DELIVERY_STATIONS[name]
        return CHARGING_STATIONS[name]

    # --------------------------------------------------------
    # Movement / workflow
    # --------------------------------------------------------
    def loop(self):
        if not self.running:
            self.draw_amrs()
            self.update_status()
            return

        any_moving = False

        for amr in self.amrs:
            if not amr.busy and amr.status != "GOING TO CHARGE":
                continue

            # Low battery protection before continuing a task
            if (
                amr.busy
                and amr.phase in ("SHELF", "DESTINATION")
                and amr.battery <= 15
            ):
                self.reassign_for_charge(amr)
                any_moving = True
                continue

            if amr.target is None:
                continue

            any_moving = True
            arrived = amr.move(speed=8.0)

            if arrived:
                self.handle_arrival(amr)

        self.total_distance = sum(a.distance_travelled for a in self.amrs)
        self.total_battery_used = sum(a.battery_used for a in self.amrs)

        self.draw_amrs()
        self.update_status()

        if self.completed >= len(TASKS):
            self.finish_simulation()
            return

        if any_moving or self.pending_tasks:
            self.root.after(80, self.loop)
        else:
            self.root.after(100, self.loop)

    def handle_arrival(self, amr):
        if amr.phase == "CHARGE":
            amr.battery = 100.0
            amr.status = "IDLE"
            amr.target = None
            amr.target_name = None
            amr.phase = None

            self.log(f"{amr.name} reached charger and recharged to 100%.")
            self.dispatch_tasks()
            return

        if amr.phase == "SHELF":
            if not amr.task:
                return

            order, shelf, destination, priority = amr.task
            amr.status = "PICKING ORDER"
            self.log(
                f"{amr.name} picked {order} from {shelf}; "
                f"destination = {destination}."
            )

            dest_pos = self.get_location(destination)
            amr.set_target(destination, dest_pos, "DESTINATION")
            amr.status = "GOING TO DESTINATION"

            self.show_command_popup(
                amr.name,
                f"{amr.name}\n"
                f"ORDER PICKED: {order}\n"
                f"DELIVER TO: {destination}",
            )

        elif amr.phase == "DESTINATION":
            if not amr.task:
                return

            order, shelf, destination, priority = amr.task

            self.completed += 1
            self.log(
                f"{amr.name} completed {order} → {destination}."
            )

            amr.status = "IDLE"
            amr.busy = False
            amr.task = None
            amr.target = None
            amr.target_name = None
            amr.phase = None

            self.dispatch_tasks()

    def reassign_for_charge(self, amr):
        if not amr.task:
            return

        task = amr.task
        order = task[0]

        self.log(
            f"LOW BATTERY: {amr.name} has {amr.battery:.1f}%. "
            f"Reassigning {order} after charging."
        )

        amr.busy = False
        amr.status = "GOING TO CHARGE"
        amr.target = None
        amr.target_name = None
        amr.phase = "CHARGE"

        # Put task back into queue.
        if task not in self.pending_tasks:
            self.pending_tasks.insert(0, task)

        # Pick nearest charger.
        charger_name, charger_pos = min(
            CHARGING_STATIONS.items(),
            key=lambda item: distance(amr.get_position(), item[1]),
        )

        amr.set_target(charger_name, charger_pos, "CHARGE")

        self.show_command_popup(
            "WAREX BRAIN",
            f"{amr.name}\n"
            f"LOW BATTERY DETECTED\n"
            f"GO TO {charger_name}\n"
            f"RECHARGE → TASK REQUEUED",
        )

    # --------------------------------------------------------
    # Popups
    # --------------------------------------------------------
    def show_command_popup(self, title, message):
        self.popup_count += 1

        popup = tk.Toplevel(self.root)
        popup.title("WAREX BRAIN COMMAND")
        popup.geometry("360x190")
        popup.configure(bg="#101820")
        popup.resizable(False, False)

        tk.Label(
            popup,
            text="WAREX BRAIN COMMAND",
            font=("Segoe UI", 13, "bold"),
            bg="#101820",
            fg=CYAN,
        ).pack(pady=(15, 8))

        tk.Label(
            popup,
            text=message,
            font=("Consolas", 10, "bold"),
            justify="center",
            bg="#101820",
            fg=WHITE,
        ).pack(expand=True)

        tk.Button(
            popup,
            text="ACKNOWLEDGE",
            command=popup.destroy,
            bg=CYAN,
            fg="#061014",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
        ).pack(pady=10)

        # Automatically close after a short period.
        popup.after(2200, lambda: popup.destroy() if popup.winfo_exists() else None)

    # --------------------------------------------------------
    # Results / comparison
    # --------------------------------------------------------
    def finish_simulation(self):
        if not self.running:
            return

        self.running = False
        elapsed = time.time() - self.start_time if self.start_time else 0

        self.results[self.mode] = {
            "time": elapsed,
            "battery": self.total_battery_used,
            "distance": self.total_distance,
            "completed": self.completed,
        }

        self.mode_label.config(
            text=f"MODE: {self.mode} COMPLETE",
            fg=GREEN if self.mode == "AI" else BLUE,
        )

        self.log(
            f"{self.mode} simulation completed: "
            f"{elapsed:.1f}s, battery used {self.total_battery_used:.1f}%."
        )

        messagebox.showinfo(
            "WAREX Simulation Complete",
            f"{self.mode} simulation completed.\n\n"
            f"Orders: {self.completed}/{len(TASKS)}\n"
            f"Time: {elapsed:.1f} seconds\n"
            f"Battery used: {self.total_battery_used:.1f}%\n"
            f"Distance: {self.total_distance:.1f}",
        )

    def show_comparison(self):
        if "AI" not in self.results or "ML" not in self.results:
            messagebox.showinfo(
                "Comparison",
                "Run both AI and ML simulations first.\n\n"
                "1. RESET\n"
                "2. RUN AI SIMULATION\n"
                "3. RESET\n"
                "4. RUN ML SIMULATION\n"
                "5. SHOW AI vs ML",
            )
            return

        ai = self.results["AI"]
        ml = self.results["ML"]

        win = tk.Toplevel(self.root)
        win.title("WAREX AI vs ML Comparison")
        win.geometry("1000x760")
        win.configure(bg=BG)

        tk.Label(
            win,
            text="WAREX AI vs ML",
            font=("Segoe UI", 22, "bold"),
            bg=BG,
            fg=CYAN,
        ).pack(pady=12)

        tk.Label(
            win,
            text="Run AI → RESET → Run ML → SHOW AI vs ML",
            font=("Segoe UI", 10, "bold"),
            bg=BG, fg="#a9bdc8"
        ).pack(pady=(0, 8))

        table = ttk.Treeview(
            win,
            columns=("factor", "AI", "ML"),
            show="headings",
            height=5,
        )
        table.heading("factor", text="FACTOR")
        table.heading("AI", text="AI")
        table.heading("ML", text="ML")

        table.column("factor", width=250)
        table.column("AI", width=200)
        table.column("ML", width=200)

        table.insert(
            "",
            "end",
            values=("Completion Time (s)", f"{ai['time']:.1f}", f"{ml['time']:.1f}"),
        )
        table.insert(
            "",
            "end",
            values=("Battery Consumption (%)", f"{ai['battery']:.1f}", f"{ml['battery']:.1f}"),
        )
        table.insert(
            "",
            "end",
            values=("Distance Travelled", f"{ai['distance']:.1f}", f"{ml['distance']:.1f}"),
        )
        table.insert(
            "",
            "end",
            values=("Orders Completed", ai["completed"], ml["completed"]),
        )

        table.pack(pady=10)

        graph = tk.Canvas(
            win,
            width=780,
            height=350,
            bg="#0c141b",
            highlightthickness=0,
        )
        graph.pack(pady=10)

        factors = [
            ("Time", ai["time"], ml["time"]),
            ("Battery", ai["battery"], ml["battery"]),
        ]

        base_y = 285
        group_x = [230, 560]
        bar_width = 70

        for i, (label, v1, v2) in enumerate(factors):
            x = group_x[i]

            local_max = max(v1, v2, 1)
            h1 = 210 * v1 / local_max
            h2 = 210 * v2 / local_max

            graph.create_rectangle(
                x - 90,
                base_y - h1,
                x - 20,
                base_y,
                fill=GREEN,
                outline="",
            )
            graph.create_rectangle(
                x + 20,
                base_y - h2,
                x + 90,
                base_y,
                fill=BLUE,
                outline="",
            )

            graph.create_text(
                x - 55,
                base_y - h1 - 15,
                text=f"{v1:.1f}",
                fill=WHITE,
                font=("Segoe UI", 9, "bold"),
            )
            graph.create_text(
                x + 55,
                base_y - h2 - 15,
                text=f"{v2:.1f}",
                fill=WHITE,
                font=("Segoe UI", 9, "bold"),
            )

            graph.create_text(
                x,
                base_y + 25,
                text=label,
                fill=WHITE,
                font=("Segoe UI", 10, "bold"),
            )

        graph.create_text(
            250, 325,
            text="AI",
            fill=GREEN,
            font=("Segoe UI", 10, "bold"),
        )
        graph.create_text(
            580, 325,
            text="ML",
            fill=BLUE,
            font=("Segoe UI", 10, "bold"),
        )

        tk.Label(
            win,
            text=(
                "AI uses explicit decision logic based on distance, battery and priority.\n"
                "ML uses a learned nearest-neighbour model trained on synthetic historical data."
            ),
            font=("Segoe UI", 9),
            bg=BG,
            fg=TEXT,
            justify="center",
        ).pack(pady=5)


if __name__ == "__main__":
    root = tk.Tk()
    app = WAREXApp(root)
    root.mainloop()
