import threading
import time
import random
from flask import Flask, render_template
from flask_socketio import SocketIO

import eventlet
eventlet.monkey_patch()


# ----------------------------
# Flask + SocketIO Setup
# ----------------------------
app = Flask(_name_)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")


# ----------------------------
# ROUTES (MUST BE BEFORE run)
# ----------------------------
@app.route("/")
def index():
    return render_template("index.html")

# ----------------------------
# Warehouse State
# ----------------------------
GRID_SIZE = 10

shelves = [[None]*5 for _ in range(4)]
shelf_positions = {
    0: (2, 2),
    1: (2, 7),
    2: (7, 2),
    3: (7, 7)
}

SUPPLY_STATION = (0, 5)
DELIVERY_STATION = (9, 5)

supply_robot = {"pos": [0, 5], "carrying": None}
delivery_robot = {"pos": [9, 5], "carrying": None}


incoming_supply_queue = []
delivery_order_queue = []
delivered_items = []
all_orders = [] 

ITEMS = ["A", "B", "C"]
arrival_rates = {"A": 0.5, "B": 0.3, "C": 0.2}

lock = threading.Lock()

# ----------------------------
# Utility
# ----------------------------
def emit_state():
    socketio.emit("state", {
        "inventory": inventory_summary(),
        "shelf_inventory": shelf_inventory(),
        "incoming_queue": incoming_supply_queue.copy(),
        "delivered_items": delivered_items.copy(),
        "supply_robot": supply_robot,
        "delivery_robot": delivery_robot,
        "shelves": shelves
    })



def move_robot(robot, target):
    while tuple(robot["pos"]) != target:
        x, y = robot["pos"]
        tx, ty = target

        if x < tx: x += 1
        elif x > tx: x -= 1
        elif y < ty: y += 1
        elif y > ty: y -= 1

        robot["pos"] = [x, y]
        emit_state()
        time.sleep(0.5)

# ----------------------------
# Threads
# ----------------------------
def stock_arrival_thread():
    while True:
        time.sleep(1)
        with lock:
            for item, p in arrival_rates.items():
                if random.random() < p:
                    incoming_supply_queue.append(item)
                    print("[STOCK]", item)
                    emit_state()

def order_thread():
    while True:
        time.sleep(random.uniform(2, 4))
        with lock:
            item = random.choice(ITEMS)
            delivery_order_queue.append(item)
            print("[ORDER]", item)
            emit_state()

def supply_robot_thread():
    while True:
        time.sleep(1)
        with lock:
            if not incoming_supply_queue:
                continue
            item = incoming_supply_queue.pop(0)

        placed = False
        for s in range(4):
            for slot in range(5):
                if shelves[s][slot] is None:
                    move_robot(supply_robot, SUPPLY_STATION)
                    supply_robot["carrying"] = item
                    emit_state()

                    move_robot(supply_robot, shelf_positions[s])
                    with lock:
                        shelves[s][slot] = item
                        supply_robot["carrying"] = None
                        print("[SUPPLY ROBOT] Stored", item)
                        emit_state()
                    placed = True
                    break
            if placed:
                break


def delivery_robot_thread():
    while True:
        time.sleep(1)
        with lock:
            if not delivery_order_queue:
                continue
            item = delivery_order_queue.pop(0)

        found = False
        for s in range(4):
            for slot in range(5):
                if shelves[s][slot] == item:
                    move_robot(delivery_robot, shelf_positions[s])
                    delivery_robot["carrying"] = item

                    with lock:
                        shelves[s][slot] = None
                        emit_state()

                    move_robot(delivery_robot, DELIVERY_STATION)
                    delivery_robot["carrying"] = None
                    with lock:
                        delivered_items.append(item)
                        print("[DELIVERY ROBOT] Delivered", item)
                        emit_state()

                    found = True
                    break
            if found:
                break

def inventory_summary():
    inv = {"A": 0, "B": 0, "C": 0}
    for shelf in shelves:
        for item in shelf:
            if item:
                inv[item] += 1
    return inv


def inventory_summary():
    inv = {"A": 0, "B": 0, "C": 0}
    for shelf in shelves:
        for item in shelf:
            if item:
                inv[item] += 1
    return inv

def shelf_inventory():
    result = {}
    for i, shelf in enumerate(shelves):
        counts = {"A": 0, "B": 0, "C": 0}
        for item in shelf:
            if item:
                counts[item] += 1
        result[f"Shelf {i}"] = counts
    return result




# ----------------------------
# Launch Threads
# ----------------------------
def start_threads():
    threading.Thread(target=stock_arrival_thread, daemon=True).start()
    threading.Thread(target=order_thread, daemon=True).start()
    threading.Thread(target=supply_robot_thread, daemon=True).start()
    threading.Thread(target=delivery_robot_thread, daemon=True).start()

# ----------------------------
# Main
# ----------------------------
if _name_ == "_main_":
    print("Starting warehouse simulation...")
    start_threads()
    socketio.run(app, host="0.0.0.0", port=5000)
