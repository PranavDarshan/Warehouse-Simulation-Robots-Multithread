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
app = Flask(__name__)
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
# larger grid to demonstrate more complex layouts
GRID_SIZE = 15

# create a more complex shelf layout: 12 shelves with 6 slots each
NUM_SHELVES = 12
SLOTS_PER_SHELF = 6
shelves = [[None] * SLOTS_PER_SHELF for _ in range(NUM_SHELVES)]

# explicit shelf positions (row, col) scattered across the grid
shelf_positions = {
    0: (3, 2),   1: (3, 5),   2: (3, 8),   3: (3, 11),
    4: (7, 2),   5: (7, 5),   6: (7, 8),   7: (7, 11),
    8: (11, 2),  9: (11, 5), 10: (11, 8), 11: (11, 11)
}

SUPPLY_STATION = (0, 7)
DELIVERY_STATION = (14, 7)

supply_robot = {"pos": [0, 7], "carrying": None}
delivery_robot = {"pos": [14, 7], "carrying": None}


incoming_supply_queue = []
delivery_order_queue = []
delivered_items = []
all_orders = []

ITEMS = ["A", "B", "C"]
arrival_rates = {"A": 0.5, "B": 0.3, "C": 0.2}

lock = threading.Lock()

# seed some initial stock to show up in visualization
for _ in range(20):
    s = random.randrange(NUM_SHELVES)
    slot = random.randrange(SLOTS_PER_SHELF)
    if shelves[s][slot] is None:
        shelves[s][slot] = random.choice(ITEMS)


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
        "shelves": shelves,
        "shelf_positions": shelf_positions,   # send server's shelf positions
        "supply_station": SUPPLY_STATION,
        "delivery_station": DELIVERY_STATION,
        "grid_size": GRID_SIZE
    })


def move_robot(robot, target):
    # target expected as (row, col) or [row, col]
    tx, ty = target
    while tuple(robot["pos"]) != (tx, ty):
        x, y = robot["pos"]

        if x < tx:
            x += 1
        elif x > tx:
            x -= 1
        elif y < ty:
            y += 1
        elif y > ty:
            y -= 1

        robot["pos"] = [x, y]
        emit_state()
        time.sleep(0.25)


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
        # iterate dynamically over shelves and slots
        for s in range(len(shelves)):
            for slot in range(len(shelves[s])):
                if shelves[s][slot] is None:
                    # go to supply station, pick up, then move to shelf position
                    move_robot(supply_robot, SUPPLY_STATION)
                    supply_robot["carrying"] = item
                    emit_state()

                    target = shelf_positions.get(s, (0, 0))
                    move_robot(supply_robot, target)
                    with lock:
                        shelves[s][slot] = item
                        supply_robot["carrying"] = None
                        print("[SUPPLY ROBOT] Stored", item, "at shelf", s, "slot", slot)
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
        # search dynamically across shelves and slots
        for s in range(len(shelves)):
            for slot in range(len(shelves[s])):
                if shelves[s][slot] == item:
                    target = shelf_positions.get(s, (0, 0))
                    move_robot(delivery_robot, target)
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
if __name__ == "__main__":
    print("Starting complex warehouse simulation...")
    start_threads()
    socketio.run(app, host="0.0.0.0", port=5000)

