# Warehouse Simulation with Multi-Robot System

This project is a simulation of a warehouse environment where multiple robots work together to fulfill orders. The simulation is built using Python and multithreading to handle the concurrent operations of the robots. It also features a web-based interface to visualize the warehouse, the robots' movements, and performance metrics.

## Features

-   **Multithreaded Simulation:** The simulation uses multiple threads to control each robot independently, allowing for concurrent and realistic warehouse operations.
-   **Web-Based Visualization:** A 3D visualization of the warehouse and robots is provided through a web interface, built with Flask and Three.js.
-   **Performance Dashboard:** The web interface includes a dashboard to monitor key performance metrics of the warehouse, such as the number of orders fulfilled, the average time per order, and robot utilization.
-   **Customizable Scenarios:** The simulation allows for easy customization of various parameters, including:
    -   **Warehouse Layout:** The layout of the warehouse can be modified in the code to simulate different environments.
    -   **Arrival and Delivery Rates:** The rates at which orders arrive and are delivered can be adjusted to test the system under different loads.

## How it Works

The simulation is orchestrated by the `threadTest.py` script, which initializes the warehouse, the robots, and the order queues. Each robot is managed by a separate thread, which controls its movement, charging, and order fulfillment tasks. The simulation uses a grid-based system to represent the warehouse layout, with specific locations for charging stations, pickup points, and delivery points.

The backend is powered by a Flask web server that serves the frontend application and provides data to the visualization through a WebSocket connection.

## Visualization

The project includes a web-based visualization to monitor the simulation in real-time.

-   **3D Warehouse View:** A 3D representation of the warehouse shows the robots moving between locations.
-   **Dashboard:** A dashboard displays key performance metrics, providing insights into the efficiency of the warehouse operations.

## Customization

The simulation can be customized by modifying the parameters in the `threadTest.py` script.

### Warehouse Layout

The warehouse layout is defined by a 2D array in the code. You can change the dimensions of the warehouse and the locations of the charging stations, pickup points, and delivery points to simulate different warehouse configurations.

### Arrival and Delivery Rates

The arrival rate of new orders and the delivery rate of the robots can be adjusted in the code to simulate different operational scenarios. This allows for testing the system's performance under various levels of demand.

## How to Run

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: A `requirements.txt` file is not provided. You will need to create one based on the imports in `threadTest.py`, which include Flask, Flask-SocketIO, and other standard Python libraries.)*

2.  **Run the Simulation:**
    ```bash
    python threadTest.py
    ```

3.  **View the Visualization:**
    Open a web browser and navigate to `http://127.0.0.1:5000` to view the simulation.

## Dependencies

-   Python 3
-   Flask
-   Flask-SocketIO
-   Numpy
-   Three.js (for the 3D visualization)
