# WAREX — Autonomous Warehouse

## 🤖 AI-Powered Autonomous Warehouse Simulation

WAREX is an AI-powered warehouse simulation designed to manage multiple autonomous robots in a dynamic warehouse environment.

The system demonstrates intelligent robot task allocation, path planning, obstacle avoidance, battery monitoring, and task handover between robots.

Instead of using fixed robot assignments, WAREX continuously monitors the warehouse and makes decisions based on the current condition of each robot.

---

## 🎯 Key Features

- 🤖 Multi-robot warehouse simulation
- 📦 Automatic order generation
- 🧠 Intelligent task allocation
- 🔋 Real-time battery monitoring
- 📍 Robot location and workload tracking
- 🚧 Dynamic obstacle avoidance
- 🗺️ Safe path planning
- 🔄 Intelligent task handover
- ⚡ Charging and battery management
- 💬 Explainable AI decisions
- 🔁 Continuous monitoring and replanning

---

## 🧠 How WAREX Works

1. A new order arrives at the pickup station.
2. WAREX checks the available robots.
3. The system considers battery, workload, distance and robot availability.
4. The most suitable robot is selected for the task.
5. The robot travels to the required shelf using a safe route.
6. The product is picked up and transported to the delivery station.
7. WAREX continuously monitors the robot and environment.
8. If a robot is blocked, fails or has low battery, the system can replan the task.
9. Another available robot can take over the task when required.
10. The original robot can move toward charging or recovery.

---

## 🚧 Dynamic Environment

The warehouse contains shelves and obstacles that robots must avoid.

When the environment changes, WAREX can calculate an alternative route instead of allowing the robot to move through blocked areas.

This demonstrates how the system can adapt to changing warehouse conditions.

---

## 🔄 Intelligent Task Handover

One of the main features of WAREX is task handover.

For example:

**Robot 1 → Low Battery**

↓  

**WAREX detects the condition**

↓  

**Robot 2 → Selected for takeover**

↓  

**Robot 2 completes the task**

↓  

**Robot 1 → Charging**

This allows the task to continue instead of stopping the entire operation.

---

## 💡 Why WAREX?

Traditional fixed robot assignment can cause unnecessary travel, delays and inefficient battery usage.

WAREX uses continuous monitoring and decision-making to dynamically select robots and adapt to changing conditions.

The goal is to demonstrate an AI-based decision layer that can coordinate multiple autonomous robots in a warehouse.

---

## ⚙️ Technologies Used

- Python
- Artificial Intelligence / Machine Learning
- Path Planning
- A* Algorithm
- Pygame / Simulation Interface
- Robot State Monitoring
- Dynamic Task Allocation

---

## 🏗️ System Architecture

```text
        📦 ORDERS
            ↓
     🧠 WAREX AI BRAIN
            ↓
   ┌────────┼────────┐
   ↓        ↓        ↓
🤖 ROBOTS  🔋 BATTERY  🚧 ENVIRONMENT
   ↓        ↓        ↓
   └────────┼────────┘
            ↓
      🎯 TASK DECISION
            ↓
      🗺️ PATH PLANNING
            ↓
       🤖 ROBOT ACTION
            ↓
     📊 MONITORING
            ↓
       🔄 REPLANNING
