# 🤖 WAREX — Autonomous Warehouse

## AI-Powered Autonomous Warehouse Simulation

WAREX is an AI-powered warehouse simulation designed to coordinate multiple autonomous robots in a dynamic warehouse environment.

Instead of using fixed robot assignments, WAREX continuously monitors the condition of each robot and the warehouse environment, then dynamically decides which robot should perform a task.

The system demonstrates intelligent task allocation, safe path planning, obstacle avoidance, battery monitoring, explainable decision-making, and intelligent task handover.

---

## 🎯 Key Features

- 🤖 Multi-robot warehouse simulation
- 📦 Automatic order generation
- 🧠 Intelligent AI-based task allocation
- 🔋 Real-time battery monitoring
- 📍 Robot location and workload tracking
- 🚧 Dynamic obstacle detection
- 🗺️ Safe A* path planning
- 🔄 Intelligent task handover
- ⚡ Charging and battery management
- 💬 Explainable AI decisions
- 🔁 Continuous monitoring and replanning
- 🚨 Robot failure and recovery handling

---

# 🧠 How WAREX Works

WAREX follows a continuous decision-making loop:

### 1️⃣ Order Received

A new warehouse order is generated and sent to the WAREX AI Manager.

### 2️⃣ Observe

WAREX monitors:

- Robot battery
- Robot location
- Distance to task
- Workload
- Speed
- Congestion
- Robot availability
- Environment conditions

### 3️⃣ Calculate

The AI Manager calculates the suitability of available robots using multiple task-related factors.

### 4️⃣ Decide

WAREX selects the most suitable available robot for the task.

### 5️⃣ Command

The selected robot receives a command and begins executing the task.

### 6️⃣ Execute

The robot travels to the pickup location, reaches the required shelf, collects the product and moves toward delivery.

### 7️⃣ Monitor

WAREX continuously monitors robot status and warehouse conditions.

### 8️⃣ Replan

If an obstacle appears or the environment changes, WAREX calculates a new safe route using A* path planning.

### 9️⃣ Recover

If a robot fails or its battery becomes critically low, WAREX can select another available robot and transfer the task.

---

# 🚧 Dynamic Environment

The warehouse contains shelves and dynamic obstacles that robots must avoid.

Shelves are treated as **NO-DRIVE zones**.

When an obstacle blocks the current route, WAREX detects the environmental change and triggers path replanning.

```text
Current Route
      ↓
🚧 Obstacle Detected
      ↓
🧠 WAREX Detects Change
      ↓
🗺️ A* Replanning
      ↓
New Safe Route
      ↓
🤖 Robot Continues Task
