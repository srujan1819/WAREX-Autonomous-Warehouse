import pygame
import math
import heapq

pygame.init()

# ============================================================
# WINDOW
# ============================================================

WIDTH = 1000
HEIGHT = 700

screen = pygame.display.set_mode(
    (WIDTH, HEIGHT)
)

pygame.display.set_caption(
    "WAREX - Autonomous Warehouse Intelligence"
)

clock = pygame.time.Clock()


# ============================================================
# COLORS
# ============================================================

BACKGROUND = (25, 25, 25)
FLOOR = (65, 65, 65)
BORDER = (220, 220, 220)

PICKUP = (50, 150, 80)
DELIVERY = (50, 100, 180)
CHARGING = (180, 150, 50)
SHELF = (120, 90, 60)
OBSTACLE = (220, 70, 70)

WHITE = (255, 255, 255)
YELLOW = (230, 200, 50)
GREEN = (50, 220, 100)
FAIL_COLOR = (255, 80, 80)
AI_COLOR = (100, 200, 255)
PANEL_COLOR = (40, 40, 40)

ROBOT_COLORS = [
    (220, 60, 60),
    (60, 120, 220),
    (60, 200, 100),
    (220, 160, 40),
    (180, 70, 200)
]


# ============================================================
# WAREHOUSE
# ============================================================

WAREHOUSE_X = 30
WAREHOUSE_Y = 40
WAREHOUSE_WIDTH = 620
WAREHOUSE_HEIGHT = 600

GRID_SIZE = 20


# ============================================================
# SHELVES
# ============================================================

shelves = [

    (240, 210, 100, 50),
    (370, 210, 100, 50),

    (240, 300, 100, 50),
    (370, 300, 100, 50),

    (240, 390, 100, 50),
    (370, 390, 100, 50)

]


# ============================================================
# SHELF PICKUP POSITIONS
# ============================================================

shelf_pickup_positions = [

    # Pickup points are deliberately placed just OUTSIDE
    # the shelf rectangles so A* can always enter them.
    (220, 270),
    (350, 270),

    (220, 360),
    (350, 360),

    (220, 450),
    (350, 450)

]


# ============================================================
# PICKUP ZONE ORDER POSITIONS
# ============================================================

pickup_zone_positions = [
    (110, 155),
    (185, 155)
]


# ============================================================
# SHELF STORAGE POSITIONS
# ============================================================

shelf_storage_positions = [
    (230, 275),
    (360, 275),
    (230, 365),
    (360, 365),
    (230, 455),
    (360, 455)
]

# ============================================================
# DYNAMIC OBSTACLES
# ============================================================

dynamic_obstacles = []


# ============================================================
# AI EXPLANATION
# ============================================================

ai_explanation = (
    "AI: Monitoring warehouse conditions..."
)


def set_ai_explanation(message):

    global ai_explanation

    ai_explanation = message


# ============================================================
# AI DECISION LOG
# ============================================================

decision_log = []


def add_decision(message):

    decision_log.insert(
        0,
        message
    )

    if len(decision_log) > 6:

        decision_log.pop()


# ============================================================
# ROBOTS
# ============================================================

robots = [

    {
        "id": "R1",
        "x": 80,
        "y": 260,
        "battery": 95,
        "order": None,
        "status": "IDLE",
        "path": [],
        "failed": False,
        "parking_target": None,
        "resume_after_charge": False,
        "blocked_time": 0
    },

    {
        "id": "R2",
        "x": 80,
        "y": 330,
        "battery": 80,
        "order": None,
        "status": "IDLE",
        "path": [],
        "failed": False,
        "parking_target": None,
        "resume_after_charge": False,
        "blocked_time": 0
    },

    {
        "id": "R3",
        "x": 80,
        "y": 400,
        "battery": 65,
        "order": None,
        "status": "IDLE",
        "path": [],
        "failed": False,
        "parking_target": None,
        "resume_after_charge": False,
        "blocked_time": 0
    },

    {
        "id": "R4",
        "x": 120,
        "y": 470,
        "battery": 45,
        "order": None,
        "status": "IDLE",
        "path": [],
        "failed": False,
        "parking_target": None,
        "resume_after_charge": False,
        "blocked_time": 0
    },

    {
        "id": "R5",
        "x": 80,
        "y": 540,
        "battery": 25,
        "order": None,
        "status": "IDLE",
        "path": [],
        "failed": False,
        "parking_target": None,
        "resume_after_charge": False,
        "blocked_time": 0
    }

]


# ============================================================
# PARKING POSITIONS
# ============================================================

# ============================================================
# DELIVERY POSITIONS
# ============================================================

# Dedicated delivery bays inside the DELIVERY ZONE.
# These are separate from the parking slots.
delivery_positions = [
    (540, 130),
    (540, 160),
    (540, 190),
    (540, 220),
    (540, 250)
]


parking_positions = [

    # Dedicated parking slots, separated from the delivery zone.
    (310, 520),
    (350, 520),
    (390, 520),
    (310, 570),
    (350, 570)

]


def get_parking_position(robot):

    for index, current_robot in enumerate(robots):

        if current_robot["id"] == robot["id"]:

            return parking_positions[index]

    return parking_positions[0]


# ============================================================
# ORDERS
# ============================================================

orders = [

    {
        "id": "O1",
        "pickup": shelf_pickup_positions[0],
        "delivery": (540, 130),
        "priority": "HIGH",
        "assigned_robot": None,
        "status": "WAITING"
    },

    {
        "id": "O2",
        "pickup": shelf_pickup_positions[1],
        "delivery": (540, 160),
        "priority": "MEDIUM",
        "assigned_robot": None,
        "status": "WAITING"
    },

    {
        "id": "O3",
        "pickup": shelf_pickup_positions[2],
        "delivery": (540, 190),
        "priority": "HIGH",
        "assigned_robot": None,
        "status": "WAITING"
    },

    {
        "id": "O4",
        "pickup": shelf_pickup_positions[3],
        "delivery": (540, 220),
        "priority": "MEDIUM",
        "assigned_robot": None,
        "status": "WAITING"
    },

    {
        "id": "O5",
        "pickup": shelf_pickup_positions[4],
        "delivery": (540, 250),
        "priority": "LOW",
        "assigned_robot": None,
        "status": "WAITING"
    },

    {
        "id": "O6",
        "pickup": pickup_zone_positions[0],
        "delivery": shelf_storage_positions[4],
        "priority": "HIGH",
        "assigned_robot": None,
        "status": "WAITING",
        "destination_type": "SHELF"
    },

    {
        "id": "O7",
        "pickup": pickup_zone_positions[1],
        "delivery": shelf_storage_positions[5],
        "priority": "MEDIUM",
        "assigned_robot": None,
        "status": "WAITING",
        "destination_type": "SHELF"
    }


]


# ============================================================
# POSITION TO GRID
# ============================================================

def position_to_grid(x, y):

    return (

        int(
            (x - WAREHOUSE_X)
            / GRID_SIZE
        ),

        int(
            (y - WAREHOUSE_Y)
            / GRID_SIZE
        )

    )


# ============================================================
# GRID TO POSITION
# ============================================================

def grid_to_position(grid_x, grid_y):

    return (

        WAREHOUSE_X
        + grid_x * GRID_SIZE
        + GRID_SIZE // 2,

        WAREHOUSE_Y
        + grid_y * GRID_SIZE
        + GRID_SIZE // 2

    )


# ============================================================
# CHECK BLOCKED
# ============================================================

def is_blocked(grid_x, grid_y):

    x = (
        WAREHOUSE_X
        + grid_x * GRID_SIZE
    )

    y = (
        WAREHOUSE_Y
        + grid_y * GRID_SIZE
    )

    cell_rect = pygame.Rect(
        x,
        y,
        GRID_SIZE,
        GRID_SIZE
    )

    # --------------------------------------------------------
    # SHELVES
    # --------------------------------------------------------
    # A grid cell is blocked only when it actually overlaps
    # the shelf. Pickup points are outside these rectangles.
    # --------------------------------------------------------
    for shelf in shelves:

        shelf_rect = pygame.Rect(shelf)

        if cell_rect.colliderect(shelf_rect):

            return True

    # --------------------------------------------------------
    # DYNAMIC OBSTACLES
    # --------------------------------------------------------
    for obstacle in dynamic_obstacles:

        if cell_rect.colliderect(obstacle):

            return True

    return False


# ============================================================
# A* HEURISTIC
# ============================================================

def heuristic(a, b):

    return (

        abs(a[0] - b[0])

        +

        abs(a[1] - b[1])

    )


# ============================================================
# A* NEIGHBORS
# ============================================================

def get_neighbors(node):

    x, y = node

    neighbors = [

        (x + 1, y),
        (x - 1, y),
        (x, y + 1),
        (x, y - 1)

    ]

    valid_neighbors = []

    max_x = (
        WAREHOUSE_WIDTH
        // GRID_SIZE
    )

    max_y = (
        WAREHOUSE_HEIGHT
        // GRID_SIZE
    )

    for nx, ny in neighbors:

        if nx < 0 or nx >= max_x:

            continue

        if ny < 0 or ny >= max_y:

            continue

        if is_blocked(nx, ny):

            continue

        valid_neighbors.append(
            (nx, ny)
        )

    return valid_neighbors


# ============================================================
# A* PATHFINDING
# ============================================================

def a_star(start, goal):

    open_set = []

    heapq.heappush(
        open_set,
        (0, start)
    )

    came_from = {}

    cost_so_far = {
        start: 0
    }

    while open_set:

        current = heapq.heappop(
            open_set
        )[1]

        if current == goal:

            path = []

            while current in came_from:

                path.append(current)

                current = came_from[current]

            path.append(start)

            path.reverse()

            return path

        for neighbor in get_neighbors(
            current
        ):

            new_cost = (

                cost_so_far[current]

                +

                1

            )

            if (

                neighbor not in cost_so_far

                or

                new_cost
                <
                cost_so_far[neighbor]

            ):

                cost_so_far[neighbor] = (
                    new_cost
                )

                priority = (

                    new_cost

                    +

                    heuristic(
                        neighbor,
                        goal
                    )

                )

                heapq.heappush(

                    open_set,

                    (
                        priority,
                        neighbor
                    )

                )

                came_from[neighbor] = (
                    current
                )

    return []


# ============================================================
# CREATE ROBOT PATH
# ============================================================

def create_robot_path(
    robot,
    target
):

    start = position_to_grid(
        robot["x"],
        robot["y"]
    )

    goal = position_to_grid(
        target[0],
        target[1]
    )

    if is_blocked(
        goal[0],
        goal[1]
    ):

        robot["path"] = []

        return False

    path = a_star(
        start,
        goal
    )

    if len(path) == 0:

        robot["path"] = []

        return False

    screen_path = []

    for grid_position in path:

        screen_path.append(

            grid_to_position(
                grid_position[0],
                grid_position[1]
            )

        )

    if len(screen_path) > 0:

        screen_path[0] = (
            robot["x"],
            robot["y"]
        )

    if screen_path[-1] != target:

        screen_path.append(
            target
        )

    robot["path"] = screen_path

    return True


# ============================================================
# ROBOT-TO-ROBOT COLLISION AVOIDANCE
# ============================================================

# Robots are drawn with a radius of roughly 15-16 pixels.
# Keep a larger safety radius so their bodies never overlap.
ROBOT_SAFE_DISTANCE = 34


def robot_can_move_safely(robot, next_x, next_y):

    """Return True only when the robot's next position is safe.

    If two robots get close, the robot with the smaller number
    gets right-of-way. The other robot waits for a moment and
    automatically continues when the area is clear.
    """

    for other in robots:

        if other is robot:
            continue

        if other["failed"]:
            continue

        dx = next_x - other["x"]
        dy = next_y - other["y"]

        distance = math.sqrt(
            dx * dx + dy * dy
        )

        if distance < ROBOT_SAFE_DISTANCE:

            # Give right-of-way to the robot with the lower
            # robot number. This prevents two robots from
            # repeatedly stopping each other.
            try:
                robot_number = int(robot["id"][1:])
                other_number = int(other["id"][1:])
            except (ValueError, TypeError):
                robot_number = 999
                other_number = 999

            if other_number < robot_number:
                return False

    return True


# ============================================================
# MOVE ROBOT
# ============================================================

def move_robot(
    robot,
    target
):

    distance_to_target = math.sqrt(

        (
            robot["x"]
            - target[0]
        ) ** 2

        +

        (
            robot["y"]
            - target[1]
        ) ** 2

    )

    if distance_to_target < 5:

        robot["x"] = target[0]

        robot["y"] = target[1]

        robot["path"] = []

        robot["blocked_time"] = 0

        return True

    if len(robot["path"]) == 0:

        success = create_robot_path(
            robot,
            target
        )

        if not success:

            robot["blocked_time"] += 1

            robot["status"] = (
                "PATH BLOCKED"
            )

            return False

    waypoint = robot["path"][0]

    dx = (
        waypoint[0]
        - robot["x"]
    )

    dy = (
        waypoint[1]
        - robot["y"]
    )

    distance = math.sqrt(
        dx * dx
        +
        dy * dy
    )

    speed = 2

    # --------------------------------------------------------
    # PREDICT THE NEXT POSITION BEFORE MOVING.
    # --------------------------------------------------------

    if distance > 0:

        if distance <= speed:

            next_x = waypoint[0]
            next_y = waypoint[1]

        else:

            next_x = (
                robot["x"]
                + (dx / distance) * speed
            )

            next_y = (
                robot["y"]
                + (dy / distance) * speed
            )

        # ----------------------------------------------------
        # ROBOT COLLISION CHECK
        # ----------------------------------------------------

        if not robot_can_move_safely(
            robot,
            next_x,
            next_y
        ):

            # Do NOT count another robot as a permanent A* path
            # blockage. The robot simply waits and tries again.
            robot["status"] = "WAITING FOR ROBOT"

            return False

    if distance <= speed:

        if not robot_can_move_safely(
            robot,
            waypoint[0],
            waypoint[1]
        ):

            robot["status"] = "WAITING FOR ROBOT"

            return False

        robot["x"] = waypoint[0]

        robot["y"] = waypoint[1]

        robot["path"].pop(0)

    else:

        robot["x"] = next_x

        robot["y"] = next_y

    robot["blocked_time"] = 0

    # If the robot was waiting for another robot and can move
    # again, restore its normal movement status.
    if robot["status"] == "WAITING FOR ROBOT":

        if robot["order"] is not None:

            current_order = None

            for order in orders:

                if order["id"] == robot["order"]:
                    current_order = order
                    break

            if current_order is not None:

                if current_order["status"] == "PICKUP":
                    robot["status"] = "GOING TO PICKUP"

                elif current_order["status"] == "DELIVERY":
                    robot["status"] = "DELIVERING"

        elif robot["status"] == "WAITING FOR ROBOT":

            robot["status"] = "MOVING"

    distance_to_target = math.sqrt(

        (
            robot["x"]
            - target[0]
        ) ** 2

        +

        (
            robot["y"]
            - target[1]
        ) ** 2

    )

    if distance_to_target < 5:

        robot["x"] = target[0]

        robot["y"] = target[1]

        robot["path"] = []

        return True

    return False


# ============================================================
# PRIORITY VALUE
# ============================================================

def priority_value(priority):

    if priority == "HIGH":

        return 3

    if priority == "MEDIUM":

        return 2

    return 1


# ============================================================
# PRIORITY NAME
# ============================================================

def priority_name(value):

    if value == 3:

        return "HIGH"

    if value == 2:

        return "MEDIUM"

    return "LOW"


# ============================================================
# GET ROBOT FOR ORDER
# ============================================================

def get_order_robot(order):

    robot_id = order["assigned_robot"]

    if robot_id is None:

        return None

    for robot in robots:

        if robot["id"] == robot_id:

            return robot

    return None


# ============================================================
# DISTANCE
# ============================================================

def calculate_distance(
    robot,
    order
):

    return math.sqrt(

        (
            robot["x"]
            - order["pickup"][0]
        ) ** 2

        +

        (
            robot["y"]
            - order["pickup"][1]
        ) ** 2

    )


# ============================================================
# BATTERY RISK
# ============================================================

def predict_battery_risk(robot):

    if robot["battery"] <= 15:

        return "CRITICAL"

    if robot["battery"] <= 30:

        return "HIGH"

    if robot["battery"] <= 50:

        return "MEDIUM"

    return "LOW"


# ============================================================
# REMAINING DISTANCE
# ============================================================

def calculate_remaining_distance(order):

    robot = get_order_robot(
        order
    )

    if robot is None:

        return 0

    if order["status"] == "PICKUP":

        pickup_distance = math.sqrt(

            (
                robot["x"]
                - order["pickup"][0]
            ) ** 2

            +

            (
                robot["y"]
                - order["pickup"][1]
            ) ** 2

        )

        delivery_distance = math.sqrt(

            (
                order["pickup"][0]
                - order["delivery"][0]
            ) ** 2

            +

            (
                order["pickup"][1]
                - order["delivery"][1]
            ) ** 2

        )

        return (

            pickup_distance
            +
            delivery_distance

        )

    if order["status"] == "DELIVERY":

        return math.sqrt(

            (
                robot["x"]
                - order["delivery"][0]
            ) ** 2

            +

            (
                robot["y"]
                - order["delivery"][1]
            ) ** 2

        )

    return 0


# ============================================================
# DELAY RISK
# ============================================================

def predict_delay_risk(order):

    robot = get_order_robot(
        order
    )

    if robot is None:

        return "WAITING"

    risk_score = 0

    battery_risk = predict_battery_risk(
        robot
    )

    if battery_risk == "CRITICAL":

        risk_score += 4

    elif battery_risk == "HIGH":

        risk_score += 3

    elif battery_risk == "MEDIUM":

        risk_score += 1

    if len(dynamic_obstacles) >= 3:

        risk_score += 2

    elif len(dynamic_obstacles) >= 1:

        risk_score += 1

    distance = calculate_remaining_distance(
        order
    )

    if distance > 700:

        risk_score += 2

    elif distance > 400:

        risk_score += 1

    if risk_score >= 4:

        return "HIGH"

    if risk_score >= 2:

        return "MEDIUM"

    return "LOW"


# ============================================================
# ETA
# ============================================================

def calculate_eta(order):

    if order["status"] == "COMPLETED":

        return 0

    robot = get_order_robot(
        order
    )

    if robot is None:

        return 0

    distance = calculate_remaining_distance(
        order
    )

    speed_per_second = 120

    eta = (

        distance
        /
        speed_per_second

    )

    eta += (

        len(dynamic_obstacles)
        *
        0.5

    )

    if robot["battery"] <= 15:

        eta += 7

    elif robot["battery"] <= 30:

        eta += 3

    return eta


# ============================================================
# TASK ALLOCATION
# ============================================================

def assign_orders():

    available_robots = []

    for robot in robots:

        if robot["failed"]:

            continue

        if robot["status"] != "IDLE":

            continue

        if robot["order"] is not None:

            continue

        if robot["battery"] <= 30:

            continue

        available_robots.append(
            robot
        )

    waiting_orders = []

    for order in orders:

        if order["status"] == "WAITING":

            waiting_orders.append(
                order
            )

    # ========================================================
    # IMPORTANT PRIORITY SORT
    # ========================================================

    waiting_orders.sort(

        key=lambda order: (

            priority_value(
                order["priority"]
            ),

            -calculate_waiting_order_distance(
                order
            )

        ),

        reverse=True

    )

    for order in waiting_orders:

        if len(available_robots) == 0:

            break

        best_robot = None

        best_score = -999999

        for robot in available_robots:

            distance = calculate_distance(
                robot,
                order
            )

            battery = robot["battery"]

            priority = priority_value(
                order["priority"]
            )

            # =================================================
            # PRIORITY HAS STRONG INFLUENCE
            # =================================================

            priority_bonus = (
                priority * 200
            )

            battery_score = (
                battery * 2
            )

            distance_penalty = (
                distance * 0.5
            )

            score = (

                priority_bonus

                +

                battery_score

                -

                distance_penalty

            )

            if score > best_score:

                best_score = score

                best_robot = robot

        if best_robot is not None:

            order["assigned_robot"] = (
                best_robot["id"]
            )

            order["status"] = "PICKUP"

            best_robot["order"] = (
                order["id"]
            )

            best_robot["status"] = (
                "GOING TO PICKUP"
            )

            best_robot["path"] = []

            best_robot["blocked_time"] = 0

            available_robots.remove(
                best_robot
            )

            set_ai_explanation(

                "AI: "

                +

                order["priority"]

                +

                " priority "

                +

                order["id"]

                +

                " assigned to "

                +

                best_robot["id"]

                +

                "."

            )

            add_decision(

                "ASSIGN: "

                +

                order["id"]

                +

                " ["

                +

                order["priority"]

                +

                "] -> "

                +

                best_robot["id"]

            )


# ============================================================
# WAITING ORDER DISTANCE
# ============================================================

def calculate_waiting_order_distance(order):

    distances = []

    for robot in robots:

        if robot["failed"]:

            continue

        if robot["order"] is not None:

            continue

        if robot["status"] != "IDLE":

            continue

        if robot["battery"] <= 30:

            continue

        distance = math.sqrt(

            (
                robot["x"]
                - order["pickup"][0]
            ) ** 2

            +

            (
                robot["y"]
                - order["pickup"][1]
            ) ** 2

        )

        distances.append(
            distance
        )

    if len(distances) == 0:

        return 999999

    return min(distances)


# ============================================================
# PRIORITY CHANGE
# ============================================================

def cycle_priority(order):

    old_priority = order["priority"]

    if old_priority == "LOW":

        order["priority"] = "MEDIUM"

    elif old_priority == "MEDIUM":

        order["priority"] = "HIGH"

    else:

        order["priority"] = "LOW"

    new_priority = order["priority"]

    # ========================================================
    # WAITING ORDER
    # ========================================================

    if order["status"] == "WAITING":

        set_ai_explanation(

            "AI: "

            +

            order["id"]

            +

            " changed from "

            +

            old_priority

            +

            " to "

            +

            new_priority

            +

            ". Re-evaluating priority."

        )

        add_decision(

            "PRIORITY: "

            +

            order["id"]

            +

            " "

            +

            old_priority

            +

            " -> "

            +

            new_priority

        )

        assign_orders()

        return

    # ========================================================
    # ACTIVE PICKUP
    # ========================================================

    if order["status"] == "PICKUP":

        set_ai_explanation(

            "AI: "

            +

            order["id"]

            +

            " priority changed to "

            +

            new_priority

            +

            ". Current pickup continues."

        )

        add_decision(

            "PRIORITY: "

            +

            order["id"]

            +

            " -> "

            +

            new_priority

        )

        return

    # ========================================================
    # ACTIVE DELIVERY
    # ========================================================

    if order["status"] == "DELIVERY":

        set_ai_explanation(

            "AI: "

            +

            order["id"]

            +

            " priority changed to "

            +

            new_priority

            +

            ". Current delivery continues."

        )

        add_decision(

            "PRIORITY: "

            +

            order["id"]

            +

            " -> "

            +

            new_priority

        )

        return

    # ========================================================
    # COMPLETED
    # ========================================================

    if order["status"] == "COMPLETED":

        set_ai_explanation(

            "AI: "

            +

            order["id"]

            +

            " priority label changed to "

            +

            new_priority

            +

            ". Order already completed."

        )

        add_decision(

            "PRIORITY: "

            +

            order["id"]

            +

            " completed"

        )


# ============================================================
# ACTIVE TASK HANDOFF / DYNAMIC REASSIGNMENT
# ============================================================

def reassign_interrupted_order(robot, reason):

    if robot["order"] is None:

        return False

    interrupted_order = None

    for order in orders:

        if order["id"] == robot["order"]:

            interrupted_order = order

            break

    if interrupted_order is None:

        robot["order"] = None

        return False

    available_robots = []

    for candidate in robots:

        if candidate == robot:

            continue

        if candidate["failed"]:

            continue

        if candidate["order"] is not None:

            continue

        if candidate["status"] != "IDLE":

            continue

        if candidate["battery"] <= 30:

            continue

        available_robots.append(candidate)

    # Choose the best available robot using the same WAREX factors:
    # priority, battery and distance to the current stage.
    best_robot = None
    best_score = -999999

    target = interrupted_order["pickup"]

    if interrupted_order["status"] == "DELIVERY":

        target = interrupted_order["delivery"]

    for candidate in available_robots:

        distance = math.sqrt(

            (candidate["x"] - target[0]) ** 2

            +

            (candidate["y"] - target[1]) ** 2

        )

        priority = priority_value(
            interrupted_order["priority"]
        )

        score = (
            priority * 200
            +
            candidate["battery"] * 2
            -
            distance * 0.5
        )

        if score > best_score:

            best_score = score

            best_robot = candidate

    if best_robot is None:

        return False

    old_robot_id = robot["id"]
    new_robot_id = best_robot["id"]
    order_id = interrupted_order["id"]
    stage = interrupted_order["status"]

    best_robot["order"] = order_id
    best_robot["path"] = []
    best_robot["blocked_time"] = 0

    interrupted_order["assigned_robot"] = new_robot_id

    if stage == "PICKUP":

        best_robot["status"] = "GOING TO PICKUP"

    else:

        best_robot["status"] = "GOING TO DELIVERY"

    robot["order"] = None
    robot["path"] = []
    robot["blocked_time"] = 0

    if reason == "LOW BATTERY":

        robot["resume_after_charge"] = False
        robot["status"] = "GOING TO CHARGE"

    else:

        robot["resume_after_charge"] = False
        robot["status"] = "IDLE"

    set_ai_explanation(

        "AI: "
        + old_robot_id
        + " interrupted "
        + order_id
        + " ("
        + reason
        + "). Reassigned to "
        + new_robot_id
        + " to continue "
        + stage.lower()
        + "."

    )

    add_decision(

        "HANDOFF: "
        + order_id
        + " "
        + old_robot_id
        + " -> "
        + new_robot_id
        + " ("
        + reason
        + ")"

    )

    return True


# ============================================================
# SEND ROBOT TO CHARGE
# ============================================================

def send_robot_to_charge(robot):

    robot["path"] = []

    robot["blocked_time"] = 0

    robot["status"] = (
        "GOING TO CHARGE"
    )

    set_ai_explanation(

        "AI: "

        +

        robot["id"]

        +

        " battery low. Sending robot to charging."

    )

    add_decision(

        "BATTERY: "

        +

        robot["id"]

        +

        " -> CHARGE"

    )


# ============================================================
# PAUSE TASK FOR CHARGING
# ============================================================

def pause_task_for_charging(robot):

    if robot["order"] is None:

        send_robot_to_charge(
            robot
        )

        return

    robot["resume_after_charge"] = True

    robot["path"] = []

    robot["blocked_time"] = 0

    robot["status"] = (
        "GOING TO CHARGE"
    )

    set_ai_explanation(

        "AI: "

        +

        robot["id"]

        +

        " low battery. Task paused. "

        +

        "Charging before resuming."

    )

    add_decision(

        "RECOVERY: "

        +

        robot["id"]

        +

        " task paused"

    )


# ============================================================
# LOW BATTERY MANAGEMENT
# ============================================================

def send_low_battery_robots_to_charge():

    for robot in robots:

        if robot["failed"]:

            continue

        # ====================================================
        # ACTIVE TASK
        # ====================================================

        if (

            robot["order"] is not None

            and

            robot["battery"] <= 15

            and

            robot["status"]
            in
            [
                "GOING TO PICKUP",
                "GOING TO DELIVERY",
                "PATH BLOCKED"
            ]

        ):

            handed_off = reassign_interrupted_order(
                robot,
                "LOW BATTERY"
            )

            if not handed_off:

                pause_task_for_charging(
                    robot
                )

            continue

        # ====================================================
        # IDLE ROBOT
        # ====================================================

        if (

            robot["order"] is None

            and

            robot["battery"] <= 30

            and

            robot["status"] == "IDLE"

        ):

            send_robot_to_charge(
                robot
            )


# ============================================================
# RESUME TASK AFTER CHARGING
# ============================================================

def resume_task_after_charging(robot):

    if robot["order"] is None:

        robot["resume_after_charge"] = False

        # After charging, do NOT leave the robot IDLE.
        # First try to give it one waiting order.
        waiting_orders = [

            order

            for order in orders

            if order["status"] == "WAITING"

        ]

        if waiting_orders:

            waiting_orders.sort(

                key=lambda order: priority_value(
                    order["priority"]
                ),

                reverse=True

            )

            next_order = waiting_orders[0]

            next_order["assigned_robot"] = robot["id"]

            next_order["status"] = "PICKUP"

            robot["order"] = next_order["id"]

            robot["status"] = "GOING TO PICKUP"

            robot["path"] = []

            robot["blocked_time"] = 0

            set_ai_explanation(

                "AI: "
                + robot["id"]
                + " fully charged. Assigned "
                + next_order["id"]
                + " as the next task."

            )

            add_decision(

                "CHARGE COMPLETE: "
                + robot["id"]
                + " -> "
                + next_order["id"]

            )

        else:

            # No task is waiting, so physically move to parking.
            for i, current_robot in enumerate(robots):

                if current_robot is robot:

                    robot["parking_target"] = parking_positions[i]

                    break

            robot["status"] = "PARKING"

            robot["path"] = []

            robot["blocked_time"] = 0

            set_ai_explanation(

                "AI: "
                + robot["id"]
                + " fully charged. No task waiting. Moving to parking."

            )

            add_decision(

                "CHARGE COMPLETE: "
                + robot["id"]
                + " -> PARKING"

            )

        return

    order = None

    for current_order in orders:

        if (

            current_order["id"]
            ==
            robot["order"]

        ):

            order = current_order

            break

    if order is None:

        robot["order"] = None

        robot["resume_after_charge"] = False

        robot["status"] = "IDLE"

        assign_orders()

        return

    robot["resume_after_charge"] = False

    robot["path"] = []

    robot["blocked_time"] = 0

    if order["status"] == "PICKUP":

        robot["status"] = (
            "GOING TO PICKUP"
        )

        set_ai_explanation(

            "AI: "

            +

            robot["id"]

            +

            " charged. Resuming "

            +

            order["id"]

            +

            " pickup."

        )

        add_decision(

            "RESUME: "

            +

            robot["id"]

            +

            " -> "

            +

            order["id"]

        )

    elif order["status"] == "DELIVERY":

        robot["status"] = (
            "GOING TO DELIVERY"
        )

        set_ai_explanation(

            "AI: "

            +

            robot["id"]

            +

            " charged. Resuming "

            +

            order["id"]

            +

            " delivery."

        )

        add_decision(

            "RESUME: "

            +

            robot["id"]

            +

            " delivery"

        )


# ============================================================
# FAILURE RECOVERY
# ============================================================

def reassign_failed_order(
    failed_robot
):

    failed_order_id = (
        failed_robot["order"]
    )

    if failed_order_id is None:

        return

    failed_order = None

    for order in orders:

        if order["id"] == failed_order_id:

            failed_order = order

            break

    if failed_order is None:

        return

    failed_order["assigned_robot"] = None

    failed_order["status"] = "WAITING"

    failed_robot["order"] = None

    available_robots = []

    for robot in robots:

        if robot == failed_robot:

            continue

        if robot["failed"]:

            continue

        if robot["order"] is not None:

            continue

        if robot["status"] != "IDLE":

            continue

        if robot["battery"] <= 30:

            continue

        available_robots.append(
            robot
        )

    best_robot = None

    best_score = -999999

    for robot in available_robots:

        distance = math.sqrt(

            (
                robot["x"]
                - failed_order["pickup"][0]
            ) ** 2

            +

            (
                robot["y"]
                - failed_order["pickup"][1]
            ) ** 2

        )

        priority = priority_value(
            failed_order["priority"]
        )

        score = (

            priority * 200

            +

            robot["battery"] * 2

            -

            distance * 0.5

        )

        if score > best_score:

            best_score = score

            best_robot = robot

    if best_robot is not None:

        best_robot["order"] = (
            failed_order["id"]
        )

        best_robot["status"] = (
            "GOING TO PICKUP"
        )

        best_robot["path"] = []

        failed_order["assigned_robot"] = (
            best_robot["id"]
        )

        failed_order["status"] = "PICKUP"

        set_ai_explanation(

            "AI: "

            +

            failed_robot["id"]

            +

            " failed. "

            +

            failed_order["id"]

            +

            " reassigned to "

            +

            best_robot["id"]

            +

            "."

        )

        add_decision(

            "RECOVERY: "

            +

            failed_order["id"]

            +

            " -> "

            +

            best_robot["id"]

        )


# ============================================================
# MANUAL FAILURE
# ============================================================

def fail_robot(robot_number):

    robot = robots[robot_number]

    if robot["failed"]:

        return

    robot["failed"] = True

    robot["status"] = "FAILED"

    robot["path"] = []

    add_decision(

        "FAILURE: "

        +

        robot["id"]

        +

        " manually failed"

    )

    reassign_failed_order(
        robot
    )

    if robot["order"] is None:

        set_ai_explanation(

            "AI: "

            +

            robot["id"]

            +

            " failed and was removed from fleet."

        )

    assign_orders()


# ============================================================
# KPI
# ============================================================

def get_kpi_values():

    completed_orders = 0

    active_robots = 0

    failed_robots = 0

    total_battery = 0

    charging_robots = 0

    busy_robots = 0

    blocked_robots = 0

    for order in orders:

        if order["status"] == "COMPLETED":

            completed_orders += 1

    for robot in robots:

        if robot["failed"]:

            failed_robots += 1

        else:

            active_robots += 1

        if robot["status"] == "CHARGING":

            charging_robots += 1

        if robot["status"] == "PATH BLOCKED":

            blocked_robots += 1

        if robot["order"] is not None:

            busy_robots += 1

        total_battery += robot["battery"]

    average_battery = (

        total_battery
        /
        len(robots)

    )

    return (

        completed_orders,

        active_robots,

        failed_robots,

        average_battery,

        charging_robots,

        busy_robots,

        blocked_robots,

        len(dynamic_obstacles)

    )


# ============================================================
# INITIAL SYSTEM START
# ============================================================

send_low_battery_robots_to_charge()

assign_orders()


# ============================================================
# FONTS
# ============================================================

title_font = pygame.font.Font(
    None,
    30
)

font = pygame.font.Font(
    None,
    22
)

small_font = pygame.font.Font(
    None,
    18
)

tiny_font = pygame.font.Font(
    None,
    15
)


# ============================================================
# DRAW TEXT
# ============================================================

def draw_text(
    text,
    x,
    y,
    font_object,
    color=WHITE
):

    label = font_object.render(

        text,

        True,

        color

    )

    screen.blit(

        label,

        (x, y)

    )


# ============================================================
# DRAW PICKUP OBJECTS
# ============================================================

def draw_pickup_object(order, position):

    # Show a package at the pickup point only while the order
    # has not yet been picked. Once the robot reaches the point
    # and changes the order to DELIVERY, this object disappears.
    if order["status"] not in ["WAITING", "PICKUP"]:
        return

    x, y = position

    # Shadow
    pygame.draw.rect(
        screen,
        (25, 25, 25),
        (x - 13, y - 9, 28, 18),
        border_radius=2
    )

    # Package body
    pygame.draw.rect(
        screen,
        (190, 150, 90),
        (x - 14, y - 12, 28, 18),
        border_radius=2
    )

    # Top face
    pygame.draw.rect(
        screen,
        (220, 180, 115),
        (x - 13, y - 12, 26, 5),
        border_radius=1
    )

    # Packing tape
    pygame.draw.rect(
        screen,
        (210, 190, 135),
        (x - 2, y - 12, 4, 18)
    )

    # Package outline
    pygame.draw.rect(
        screen,
        (80, 60, 35),
        (x - 14, y - 12, 28, 18),
        1,
        border_radius=2
    )

    # Order ID
    draw_text(
        order["id"],
        x - 10,
        y - 6,
        tiny_font,
        WHITE
    )


def draw_robot(
    robot,
    robot_color
):

    x = int(robot["x"])

    y = int(robot["y"])

    body_width = 28

    body_height = 22

    body_x = x - 4

    body_y = y - 2

    # Wheels

    pygame.draw.rect(

        screen,

        (20, 20, 20),

        (
            body_x - 4,
            body_y + 4,
            5,
            15
        )

    )

    pygame.draw.rect(

        screen,

        (20, 20, 20),

        (
            body_x
            + body_width
            - 1,
            body_y + 4,
            5,
            15
        )

    )

    # Body

    pygame.draw.rect(

        screen,

        robot_color,

        (
            body_x,
            body_y,
            body_width,
            body_height
        ),

        border_radius=5

    )

    # Front panel

    pygame.draw.rect(

        screen,

        (35, 35, 35),

        (
            body_x + 4,
            body_y + 4,
            body_width - 8,
            7
        ),

        border_radius=2

    )

    # Cargo platform

    pygame.draw.rect(

        screen,

        (150, 150, 150),

        (
            body_x + 3,
            body_y - 5,
            body_width - 6,
            6
        ),

        border_radius=2

    )

    # Cargo box
    # The box is visible ONLY after the robot reaches pickup.
    # While the robot is going to pickup, the cargo platform stays empty.

    cargo_order = None

    if robot["order"] is not None:

        for active_order in orders:

            if active_order["id"] == robot["order"]:

                if active_order["status"] == "DELIVERY":

                    cargo_order = active_order

                break

    if cargo_order is not None:

        # Box shadow
        pygame.draw.rect(
            screen,
            (25, 25, 25),
            (
                body_x + 5,
                body_y - 16,
                body_width - 10,
                11
            ),
            border_radius=2
        )

        # Main package box
        pygame.draw.rect(
            screen,
            (190, 150, 90),
            (
                body_x + 6,
                body_y - 18,
                body_width - 12,
                13
            ),
            border_radius=2
        )

        # Box top
        pygame.draw.rect(
            screen,
            (220, 180, 115),
            (
                body_x + 7,
                body_y - 18,
                body_width - 14,
                4
            ),
            border_radius=1
        )

        # Packing tape
        pygame.draw.rect(
            screen,
            (210, 190, 135),
            (
                body_x + body_width // 2 - 2,
                body_y - 18,
                4,
                13
            )
        )

        # Box outline
        pygame.draw.rect(
            screen,
            (80, 60, 35),
            (
                body_x + 6,
                body_y - 18,
                body_width - 12,
                13
            ),
            1,
            border_radius=2
        )

        # Order label
        draw_text(
            cargo_order["id"],
            body_x + 9,
            body_y - 15,
            tiny_font,
            WHITE
        )

    # Sensor

    pygame.draw.circle(

        screen,

        (30, 30, 30),

        (
            body_x
            + body_width // 2,
            body_y + 2
        ),

        5

    )

    pygame.draw.circle(

        screen,

        AI_COLOR,

        (
            body_x
            + body_width // 2,
            body_y + 2
        ),

        2

    )

    # Status light

    battery_risk = predict_battery_risk(
        robot
    )

    if robot["failed"]:

        light_color = FAIL_COLOR

    elif robot["status"] == "CHARGING":

        light_color = GREEN

    elif robot["status"] == "PATH BLOCKED":

        light_color = FAIL_COLOR

    elif battery_risk == "CRITICAL":

        light_color = FAIL_COLOR

    elif battery_risk == "HIGH":

        light_color = YELLOW

    else:

        light_color = AI_COLOR

    pygame.draw.circle(

        screen,

        light_color,

        (
            body_x
            + body_width
            - 4,
            body_y
            + body_height
            - 4
        ),

        3

    )

    # ID

    draw_text(

        robot["id"],

        body_x - 1,

        body_y - 29,

        small_font,

        WHITE

    )

    # Battery percentage - displayed on the RIGHT side of the robot

    battery_value = int(robot["battery"])

    if battery_value <= 15:
        battery_text_color = FAIL_COLOR
    elif battery_value <= 30:
        battery_text_color = YELLOW
    else:
        battery_text_color = GREEN

    battery_label = str(battery_value) + "%"

    battery_surface = tiny_font.render(
        battery_label,
        True,
        battery_text_color
    )

    battery_x = body_x + body_width + 10
    battery_y = body_y + 3

    # Small dark background keeps the percentage readable
    battery_box = pygame.Rect(
        battery_x - 4,
        battery_y - 3,
        battery_surface.get_width() + 8,
        battery_surface.get_height() + 6
    )

    pygame.draw.rect(
        screen,
        (25, 25, 25),
        battery_box,
        border_radius=4
    )

    pygame.draw.rect(
        screen,
        (90, 90, 90),
        battery_box,
        1,
        border_radius=4
    )

    screen.blit(
        battery_surface,
        (battery_x, battery_y)
    )

    # Status

    status = robot["status"]

    if len(status) > 18:

        status = status[:18]

    if robot["failed"]:

        status_color = FAIL_COLOR

    elif robot["status"] == "PATH BLOCKED":

        status_color = FAIL_COLOR

    elif robot["status"] == "CHARGING":

        status_color = GREEN

    else:

        status_color = YELLOW

    draw_text(

        status,

        body_x - 18,

        body_y
        + body_height
        + 23,

        tiny_font,

        status_color

    )


# ============================================================
# MAIN LOOP
# ============================================================

running = True

while running:

    # ========================================================
    # EVENTS
    # ========================================================

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False

        # ====================================================
        # KEYBOARD
        # ====================================================

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_1:

                fail_robot(0)

            elif event.key == pygame.K_2:

                fail_robot(1)

            elif event.key == pygame.K_3:

                fail_robot(2)

            elif event.key == pygame.K_4:

                fail_robot(3)

            elif event.key == pygame.K_5:

                fail_robot(4)

        # ====================================================
        # MOUSE
        # ====================================================

        elif event.type == pygame.MOUSEBUTTONDOWN:

            mouse_x, mouse_y = event.pos

            # =================================================
            # ORDER PRIORITY
            # =================================================

            if (

                event.button == 1

                and

                670 <= mouse_x <= 970

                and

                155 <= mouse_y <= 478

            ):

                order_index = int(

                    (
                        mouse_y - 155
                    )
                    /
                    45

                )

                if (

                    0
                    <= order_index
                    <
                    len(orders)

                ):

                    cycle_priority(

                        orders[
                            order_index
                        ]

                    )

            # =================================================
            # ADD OBSTACLE
            # =================================================

            elif event.button == 1:

                if (

                    WAREHOUSE_X
                    <
                    mouse_x
                    <
                    WAREHOUSE_X
                    + WAREHOUSE_WIDTH

                    and

                    WAREHOUSE_Y
                    <
                    mouse_y
                    <
                    WAREHOUSE_Y
                    + WAREHOUSE_HEIGHT

                ):

                    grid_x, grid_y = (

                        position_to_grid(
                            mouse_x,
                            mouse_y
                        )

                    )

                    obstacle_x, obstacle_y = (

                        grid_to_position(
                            grid_x,
                            grid_y
                        )

                    )

                    obstacle = (

                        obstacle_x - 10,

                        obstacle_y - 10,

                        20,

                        20

                    )

                    if not is_blocked(
                        grid_x,
                        grid_y
                    ):

                        dynamic_obstacles.append(
                            obstacle
                        )

                        for robot in robots:

                            if not robot["failed"]:

                                robot["path"] = []

                                robot["blocked_time"] = 0

                        set_ai_explanation(

                            "AI: Dynamic obstacle detected. "

                            "Replanning fleet routes."

                        )

                        add_decision(

                            "OBSTACLE: "

                            "A* routes recalculated"

                        )

            # =================================================
            # REMOVE OBSTACLE
            # =================================================

            elif event.button == 3:

                for obstacle in dynamic_obstacles:

                    obstacle_rect = pygame.Rect(
                        obstacle
                    )

                    if obstacle_rect.collidepoint(

                        mouse_x,

                        mouse_y

                    ):

                        dynamic_obstacles.remove(
                            obstacle
                        )

                        for robot in robots:

                            if not robot["failed"]:

                                robot["path"] = []

                                robot["blocked_time"] = 0

                        set_ai_explanation(

                            "AI: Obstacle removed. "

                            "Fleet routes recalculated."

                        )

                        add_decision(

                            "OBSTACLE: Route restored"

                        )

                        break

    # ========================================================
    # BATTERY INTELLIGENCE
    # ========================================================

    send_low_battery_robots_to_charge()

    # ========================================================
    # ROBOT EXECUTION
    # ========================================================

    for robot in robots:

        # ====================================================
        # FAILED
        # ====================================================

        if robot["failed"]:

            robot["status"] = "FAILED"

            continue

        # ====================================================
        # GOING TO CHARGE
        # ====================================================

        if robot["status"] == "GOING TO CHARGE":

            reached = move_robot(

                robot,

                (520, 550)

            )

            if robot["status"] == "PATH BLOCKED":

                set_ai_explanation(

                    "AI: "

                    +

                    robot["id"]

                    +

                    " charging route blocked. "

                    +

                    "A* searching for alternate path."

                )

            else:

                robot["status"] = (
                    "GOING TO CHARGE"
                )

            if reached:

                robot["status"] = (
                    "CHARGING"
                )

                robot["path"] = []

                robot["blocked_time"] = 0

                set_ai_explanation(

                    "AI: "

                    +

                    robot["id"]

                    +

                    " reached charging station."

                )

                add_decision(

                    "CHARGE: "

                    +

                    robot["id"]

                )

        # ====================================================
        # CHARGING
        # ====================================================

        elif robot["status"] == "CHARGING":

            if robot["battery"] < 100:

                robot["battery"] += 0.20

                if robot["battery"] > 100:

                    robot["battery"] = 100

            else:

                robot["battery"] = 100

                if robot["resume_after_charge"]:

                    resume_task_after_charging(
                        robot
                    )

                else:

                    # Always decide immediately after charging:
                    # resume the old task, take one waiting task,
                    # or physically go to parking. Never stay IDLE.
                    resume_task_after_charging(
                        robot
                    )

        # ====================================================
        # PARKING
        # ====================================================

        elif robot["status"] == "PARKING":

            if robot["parking_target"] is not None:

                reached = move_robot(

                    robot,

                    robot["parking_target"]

                )

                if robot["status"] == "PATH BLOCKED":

                    set_ai_explanation(

                        "AI: "

                        +

                        robot["id"]

                        +

                        " parking route blocked. Replanning."

                    )

                else:

                    robot["status"] = "PARKING"

                if reached:

                    robot["status"] = "IDLE"

                    robot["path"] = []

                    robot["parking_target"] = None

                    robot["blocked_time"] = 0

                    assign_orders()

        # ====================================================
        # ACTIVE ORDER
        # ====================================================

        elif robot["order"] is not None:

            current_order = None

            for order in orders:

                if (

                    order["id"]
                    ==
                    robot["order"]

                ):

                    current_order = order

                    break

            if current_order is None:

                robot["order"] = None

                robot["status"] = "IDLE"

                continue

            # =================================================
            # PICKUP
            # =================================================

            if current_order["status"] == "PICKUP":

                reached = move_robot(

                    robot,

                    current_order["pickup"]

                )

                if robot["status"] == "PATH BLOCKED":

                    handed_off = reassign_interrupted_order(
                        robot,
                        "PATH BLOCKED"
                    )

                    if not handed_off:

                        set_ai_explanation(

                            "AI: "

                            +

                            robot["id"]

                            +

                            " route blocked. "

                            +

                            "A* searching alternate route."

                        )

                else:

                    robot["status"] = (
                        "GOING TO PICKUP"
                    )

                if reached:

                    current_order["status"] = (
                        "DELIVERY"
                    )

                    if current_order.get("destination_type") == "SHELF":
                        robot["status"] = (
                            "GOING TO SHELF"
                        )
                    else:
                        robot["status"] = (
                            "GOING TO DELIVERY"
                        )

                    robot["path"] = []

                    robot["blocked_time"] = 0

                    set_ai_explanation(

                        "AI: "

                        +

                        robot["id"]

                        +

                        " picked "

                        +

                        current_order["id"]

                        +

                        " from "

                        +

                        (
                            "Pickup Zone"
                            if current_order["pickup"] in pickup_zone_positions
                            else "shelf"
                        )

                        +

                        "."

                    )

                    add_decision(

                        "PICKUP: "

                        +

                        current_order["id"]

                    )

            # =================================================
            # DELIVERY
            # =================================================

            elif current_order["status"] == "DELIVERY":

                reached = move_robot(

                    robot,

                    current_order["delivery"]

                )

                if robot["status"] == "PATH BLOCKED":

                    handed_off = reassign_interrupted_order(
                        robot,
                        "DELIVERY BLOCKED"
                    )

                    if not handed_off:

                        set_ai_explanation(

                            "AI: "

                            +

                            robot["id"]

                            +

                            " delivery route blocked. "

                            +

                            "A* searching alternate route."

                        )

                else:

                    if current_order.get("destination_type") == "SHELF":
                        robot["status"] = (
                            "GOING TO SHELF"
                        )
                    else:
                        robot["status"] = (
                            "GOING TO DELIVERY"
                        )

                if reached:

                    completed_order_id = current_order["id"]

                    is_shelf_delivery = (
                        current_order.get("destination_type") == "SHELF"
                    )

                    current_order["status"] = "COMPLETED"

                    robot["order"] = None
                    robot["path"] = []
                    robot["blocked_time"] = 0
                    robot["parking_target"] = None

                    set_ai_explanation(

                        "AI: "
                        + completed_order_id
                        + (
                            " stored at shelf by "
                            if is_shelf_delivery
                            else " delivered by "
                        )
                        + robot["id"]
                        + ". Checking for next order."
                    )

                    add_decision(
                        "DELIVERY: "
                        + completed_order_id
                        + " completed"
                    )

                    # =================================================
                    # CONTINUOUS TASKING
                    # =================================================
                    # The robot does NOT go to parking first.
                    # Make it available and immediately allocate the
                    # highest-priority waiting order, if one exists.
                    # Only park when there is no waiting order.
                    # =================================================

                    robot["status"] = "IDLE"

                    assign_orders()

                    if robot["order"] is None:

                        robot["parking_target"] = (
                            get_parking_position(robot)
                        )

                        robot["status"] = "PARKING"

                        set_ai_explanation(
                            "AI: "
                            + robot["id"]
                            + " completed "
                            + completed_order_id
                            + ". No waiting order, moving to parking."
                        )

                        add_decision(
                            "PARKING: "
                            + robot["id"]
                            + " -> no waiting order"
                        )

                    else:

                        set_ai_explanation(
                            "AI: "
                            + robot["id"]
                            + " completed "
                            + completed_order_id
                            + " and immediately accepted "
                            + robot["order"]
                            + ". Continuous tasking active."
                        )

    # ========================================================
    # BATTERY CONSUMPTION
    # ========================================================

    for robot in robots:

        if (

            not robot["failed"]

            and

            robot["status"]
            not in
            [
                "IDLE",
                "CHARGING"
            ]

        ):

            if robot["battery"] > 0:

                robot["battery"] -= 0.01

                if robot["battery"] < 0:

                    robot["battery"] = 0

    # ========================================================
    # AUTOMATIC TASK ALLOCATION
    # ========================================================

    assign_orders()

    # ========================================================
    # KPI
    # ========================================================

    (

        completed_orders,

        active_robots,

        failed_robots,

        average_battery,

        charging_robots,

        busy_robots,

        blocked_robots,

        obstacle_count

    ) = get_kpi_values()

    # ========================================================
    # DRAW BACKGROUND
    # ========================================================

    screen.fill(
        BACKGROUND
    )

    pygame.draw.rect(

        screen,

        FLOOR,

        (
            WAREHOUSE_X,
            WAREHOUSE_Y,
            WAREHOUSE_WIDTH,
            WAREHOUSE_HEIGHT
        )

    )

    pygame.draw.rect(

        screen,

        BORDER,

        (
            WAREHOUSE_X,
            WAREHOUSE_Y,
            WAREHOUSE_WIDTH,
            WAREHOUSE_HEIGHT
        ),

        3

    )

    # ========================================================
    # TITLE
    # ========================================================

    draw_text(

        "WAREX WAREHOUSE",

        45,

        55,

        font,

        WHITE

    )

    # ========================================================
    # PICKUP ZONE
    # ========================================================

    pygame.draw.rect(

        screen,

        PICKUP,

        (
            60,
            90,
            170,
            100
        )

    )

    draw_text(

        "PICKUP ZONE",

        78,

        125,

        font,

        WHITE

    )

    draw_text(

        "O6 / O7 PICKUP",

        78,

        150,

        tiny_font,

        WHITE

    )

    # Visible pickup objects.
    # They disappear automatically after the robot picks them up.
    for order in orders:

        if order.get("destination_type") == "SHELF":

            draw_pickup_object(
                order,
                order["pickup"]
            )

    for pickup_index, pickup_position in enumerate(pickup_zone_positions):

        pygame.draw.circle(
            screen,
            WHITE,
            pickup_position,
            7,
            2
        )

        draw_text(
            "O" + str(pickup_index + 6),
            pickup_position[0] - 8,
            pickup_position[1] - 7,
            tiny_font,
            WHITE
        )

    # ========================================================
    # DELIVERY ZONE
    # ========================================================

    delivery_zone = pygame.Rect(
        440,
        90,
        170,
        180
    )

    # Clean delivery area with inner bays.
    pygame.draw.rect(
        screen,
        (34, 76, 135),
        delivery_zone,
        border_radius=10
    )

    pygame.draw.rect(
        screen,
        DELIVERY,
        delivery_zone,
        2,
        border_radius=10
    )

    draw_text(
        "DELIVERY ZONE",
        470,
        105,
        small_font,
        WHITE
    )

    draw_text(
        "OUTBOUND ORDERS",
        470,
        126,
        tiny_font,
        (180, 205, 235)
    )

    # Five dedicated delivery bays.
    for delivery_index, delivery_position in enumerate(
        delivery_positions
    ):

        bay_rect = pygame.Rect(
            500,
            143 + delivery_index * 24,
            88,
            18
        )

        pygame.draw.rect(
            screen,
            (25, 55, 95),
            bay_rect,
            border_radius=4
        )

        pygame.draw.rect(
            screen,
            (100, 155, 215),
            bay_rect,
            1,
            border_radius=4
        )

        draw_text(
            "D" + str(delivery_index + 1),
            507,
            145 + delivery_index * 24,
            tiny_font,
            WHITE
        )

    # ========================================================
    # SHELVES
    # ========================================================

    for index, shelf in enumerate(
        shelves
    ):

        pygame.draw.rect(

            screen,

            SHELF,

            shelf

        )

        draw_text(

            "S" + str(index + 1),

            shelf[0] + 42,

            shelf[1] + 15,

            tiny_font,

            WHITE

        )

    # ========================================================
    # CHARGING ZONE
    # ========================================================

    pygame.draw.rect(

        screen,

        CHARGING,

        (
            440,
            500,
            170,
            100
        )

    )

    draw_text(

        "CHARGING",

        485,

        535,

        font,

        WHITE

    )

    # ========================================================
    # PARKING ZONE
    # ========================================================

    parking_zone = pygame.Rect(
        280,
        485,
        140,
        115
    )

    # Clearly separated from delivery and charging.
    pygame.draw.rect(
        screen,
        (34, 38, 45),
        parking_zone,
        border_radius=10
    )

    pygame.draw.rect(
        screen,
        (115, 125, 140),
        parking_zone,
        2,
        border_radius=10
    )

    draw_text(
        "PARKING",
        317,
        494,
        small_font,
        WHITE
    )

    draw_text(
        "ROBOT STANDBY GRID",
        299,
        514,
        tiny_font,
        (155, 165, 178)
    )

    # Five real parking grid slots.
    for index, position in enumerate(
        parking_positions
    ):

        slot_rect = pygame.Rect(
            position[0] - 17,
            position[1] - 13,
            34,
            26
        )

        pygame.draw.rect(
            screen,
            (48, 54, 63),
            slot_rect,
            border_radius=4
        )

        pygame.draw.rect(
            screen,
            (105, 115, 128),
            slot_rect,
            1,
            border_radius=4
        )

        # Center cross makes each slot visibly grid-based.
        pygame.draw.line(
            screen,
            (72, 80, 91),
            (position[0], position[1] - 9),
            (position[0], position[1] + 9),
            1
        )

        pygame.draw.line(
            screen,
            (72, 80, 91),
            (position[0] - 12, position[1]),
            (position[0] + 12, position[1]),
            1
        )

        draw_text(
            "P" + str(index + 1),
            position[0] - 7,
            position[1] - 6,
            tiny_font,
            (205, 210, 218)
        )

    # ========================================================
    # OBSTACLES
    # ========================================================

    for obstacle in dynamic_obstacles:

        pygame.draw.rect(

            screen,

            OBSTACLE,

            obstacle

        )

    # ========================================================
    # ROBOT PATHS
    # ========================================================

    for i, robot in enumerate(
        robots
    ):

        if (

            not robot["failed"]

            and

            len(robot["path"]) > 1

        ):

            points = []

            for point in robot["path"]:

                points.append(

                    (
                        int(point[0]),
                        int(point[1])
                    )

                )

            pygame.draw.lines(

                screen,

                ROBOT_COLORS[i],

                False,

                points,

                2

            )

    # ========================================================
    # ROBOTS
    # ========================================================

    for i, robot in enumerate(
        robots
    ):

        draw_robot(

            robot,

            ROBOT_COLORS[i]

        )

    # ========================================================
    # RIGHT PANEL
    # ========================================================

    pygame.draw.rect(

        screen,

        PANEL_COLOR,

        (
            670,
            40,
            300,
            600
        )

    )

    pygame.draw.rect(

        screen,

        BORDER,

        (
            670,
            40,
            300,
            600
        ),

        2

    )

    draw_text(

        "WAREX AI CONTROL",

        700,

        60,

        title_font,

        WHITE

    )

    # ========================================================
    # PREMIUM RIGHT-SIDE CONTROL DASHBOARD
    # ========================================================

    # Panel shadow / frame
    pygame.draw.rect(
        screen,
        (12, 15, 20),
        (664, 34, 312, 612),
        border_radius=12
    )

    pygame.draw.rect(
        screen,
        PANEL_COLOR,
        (670, 40, 300, 600),
        border_radius=10
    )

    pygame.draw.rect(
        screen,
        (58, 64, 74),
        (670, 40, 300, 600),
        2,
        border_radius=10
    )

    # Header
    pygame.draw.rect(
        screen,
        (30, 36, 45),
        (682, 51, 276, 69),
        border_radius=9
    )

    pygame.draw.circle(screen, GREEN, (699, 69), 5)

    draw_text(
        "WAREX CONTROL",
        712,
        54,
        title_font,
        WHITE
    )

    draw_text(
        "AUTONOMOUS OPERATIONS",
        712,
        79,
        tiny_font,
        (150, 158, 170)
    )

    # Live indicator
    pygame.draw.rect(
        screen,
        (38, 65, 49),
        (866, 59, 76, 22),
        border_radius=11
    )
    draw_text("● LIVE", 878, 64, tiny_font, GREEN)

    # --------------------------------------------------------
    # ACTIVE ORDERS
    # --------------------------------------------------------

    draw_text("ACTIVE ORDERS", 692, 128, small_font, WHITE)
    draw_text("CLICK TO PRIORITIZE", 837, 130, tiny_font, (125, 132, 143))

    pygame.draw.line(
        screen,
        (55, 61, 70),
        (692, 150),
        (948, 150),
        1
    )

    order_y = 157
    order_card_h = 41
    order_step = 44

    for order_index, order in enumerate(orders):

        priority = order["priority"]

        if priority == "HIGH":
            priority_color = FAIL_COLOR
        elif priority == "MEDIUM":
            priority_color = YELLOW
        else:
            priority_color = GREEN

        if order["status"] == "COMPLETED":
            eta_text = "DONE"
            risk = "DONE"
        elif order["assigned_robot"] is None:
            eta_text = "WAIT"
            risk = "WAIT"
        else:
            eta = calculate_eta(order)
            eta_text = str(round(eta, 1)) + "s"
            risk = predict_delay_risk(order)

        if risk == "HIGH":
            risk_color = FAIL_COLOR
        elif risk == "MEDIUM":
            risk_color = YELLOW
        elif risk == "LOW":
            risk_color = GREEN
        else:
            risk_color = (135, 142, 153)

        oy = order_y + order_index * order_step

        # Card shadow
        pygame.draw.rect(
            screen,
            (16, 19, 24),
            (692, oy + 2, 256, order_card_h),
            border_radius=7
        )

        # Card
        pygame.draw.rect(
            screen,
            (30, 35, 43),
            (690, oy, 258, order_card_h),
            border_radius=7
        )

        pygame.draw.rect(
            screen,
            (62, 68, 78),
            (690, oy, 258, order_card_h),
            1,
            border_radius=7
        )

        # Priority rail
        pygame.draw.rect(
            screen,
            priority_color,
            (690, oy, 4, order_card_h),
            border_radius=2
        )

        # Order identity
        draw_text(
            order["id"],
            702,
            oy + 4,
            small_font,
            WHITE
        )

        # Priority chip
        pygame.draw.rect(
            screen,
            (48, 53, 62),
            (740, oy + 5, 55, 16),
            border_radius=8
        )
        draw_text(
            priority,
            748,
            oy + 7,
            tiny_font,
            priority_color
        )

        # Robot / ETA
        assigned_robot = order["assigned_robot"]
        robot_text = str(assigned_robot) if assigned_robot else "WAIT"
        draw_text(
            robot_text,
            805,
            oy + 6,
            tiny_font,
            WHITE
        )
        draw_text(
            "ETA " + eta_text,
            843,
            oy + 6,
            tiny_font,
            (178, 185, 195)
        )

        # Status + risk
        status_text = order["status"]
        if len(status_text) > 19:
            status_text = status_text[:19]

        draw_text(
            status_text,
            702,
            oy + 24,
            tiny_font,
            (183, 190, 201)
        )

        pygame.draw.circle(
            screen,
            risk_color,
            (928, oy + 29),
            3
        )
        draw_text(
            risk,
            936,
            oy + 24,
            tiny_font,
            risk_color
        )

    # --------------------------------------------------------
    # ROBOT HEALTH
    # --------------------------------------------------------

    health_panel_y = 474

    pygame.draw.rect(
        screen,
        (18, 22, 28),
        (682, health_panel_y, 276, 83),
        border_radius=9
    )

    pygame.draw.rect(
        screen,
        (57, 64, 74),
        (682, health_panel_y, 276, 83),
        1,
        border_radius=9
    )

    draw_text(
        "ROBOT HEALTH",
        694,
        health_panel_y + 7,
        small_font,
        WHITE
    )

    draw_text(
        "BATTERY / STATE",
        858,
        health_panel_y + 9,
        tiny_font,
        (125, 132, 143)
    )

    # Five compact health cards
    health_x = [693, 746, 799, 852, 905]

    for health_index, health_robot in enumerate(robots):

        health_battery = max(
            0,
            min(100, int(health_robot["battery"]))
        )

        if health_robot["failed"]:
            health_color = FAIL_COLOR
        elif health_battery <= 15:
            health_color = FAIL_COLOR
        elif health_battery <= 30:
            health_color = YELLOW
        else:
            health_color = GREEN

        if health_robot["failed"]:
            health_state = "FAIL"
        elif health_robot["status"] in ["CHARGING", "GOING TO CHARGE"]:
            health_state = "CHG"
        elif health_robot["status"] == "PATH BLOCKED":
            health_state = "BLOCK"
        elif health_robot["order"] is not None:
            health_state = "BUSY"
        else:
            health_state = "READY"

        hx = health_x[health_index]
        hy = health_panel_y + 30

        pygame.draw.rect(
            screen,
            (34, 40, 48),
            (hx, hy, 48, 44),
            border_radius=6
        )

        pygame.draw.rect(
            screen,
            health_color,
            (hx, hy, 48, 44),
            1,
            border_radius=6
        )

        draw_text(
            health_robot["id"],
            hx + 4,
            hy + 3,
            tiny_font,
            WHITE
        )

        draw_text(
            str(health_battery) + "%",
            hx + 20,
            hy + 3,
            tiny_font,
            health_color
        )

        # Battery meter
        pygame.draw.rect(
            screen,
            (62, 68, 77),
            (hx + 4, hy + 18, 40, 5),
            border_radius=3
        )

        meter_width = int(40 * health_battery / 100)

        if meter_width > 0:
            pygame.draw.rect(
                screen,
                health_color,
                (hx + 4, hy + 18, meter_width, 5),
                border_radius=3
            )

        draw_text(
            health_state,
            hx + 4,
            hy + 27,
            tiny_font,
            health_color
        )

    # --------------------------------------------------------
    # AI BRAIN
    # --------------------------------------------------------

    ai_panel_y = 567

    pygame.draw.rect(
        screen,
        (18, 22, 28),
        (682, ai_panel_y, 276, 63),
        border_radius=9
    )

    pygame.draw.rect(
        screen,
        (57, 64, 74),
        (682, ai_panel_y, 276, 63),
        1,
        border_radius=9
    )

    pygame.draw.circle(
        screen,
        AI_COLOR,
        (697, ai_panel_y + 15),
        4
    )

    draw_text(
        "AI BRAIN",
        708,
        ai_panel_y + 7,
        small_font,
        AI_COLOR
    )

    draw_text(
        "DECISION ENGINE",
        835,
        ai_panel_y + 9,
        tiny_font,
        (125, 132, 143)
    )

    explanation = ai_explanation

    if len(explanation) > 58:
        line1 = explanation[:58]
        split = line1.rfind(" ")

        if split > 0:
            line1 = explanation[:split]
            line2 = explanation[split + 1:]
        else:
            line2 = explanation[58:]
    else:
        line1 = explanation
        line2 = ""

    draw_text(
        line1,
        694,
        ai_panel_y + 29,
        tiny_font,
        WHITE
    )

    if line2:
        draw_text(
            line2,
            694,
            ai_panel_y + 45,
            tiny_font,
            (185, 190, 200)
        )

    # ========================================================
    # BOTTOM KPI BAR
    # ========================================================

    pygame.draw.rect(

        screen,

        PANEL_COLOR,

        (
            30,
            655,
            940,
            35
        )

    )

    draw_text(

        "ACTIVE: "
        +
        str(active_robots),

        45,

        663,

        tiny_font,

        GREEN

    )

    draw_text(

        "BUSY: "
        +
        str(busy_robots),

        120,

        663,

        tiny_font,

        WHITE

    )

    draw_text(

        "CHARGE: "
        +
        str(charging_robots),

        190,

        663,

        tiny_font,

        YELLOW

    )

    draw_text(

        "BLOCKED: "
        +
        str(blocked_robots),

        285,

        663,

        tiny_font,

        FAIL_COLOR

    )

    draw_text(

        "FAILED: "
        +
        str(failed_robots),

        385,

        663,

        tiny_font,

        FAIL_COLOR

    )

    draw_text(

        "DONE: "
        +
        str(completed_orders)
        +
        "/"
        +
        str(len(orders)),

        485,

        663,

        tiny_font,

        AI_COLOR

    )

    draw_text(

        "BAT "
        +
        str(
            round(
                average_battery
            )
        )
        +
        "%",

        575,

        663,

        tiny_font,

        YELLOW

    )

    draw_text(

        "1-5 FAILURE",

        665,

        663,

        tiny_font,

        FAIL_COLOR

    )

    draw_text(

        "L/R OBSTACLE",

        795,

        663,

        tiny_font,

        WHITE

    )

    # ========================================================
    # DISPLAY
    # ========================================================

    pygame.display.flip()

    clock.tick(60)


# ============================================================
# QUIT
# ============================================================

pygame.quit()