# import threading
# import matplotlib.pyplot as plt
# import time
# import queue

# class RealTimeVisualizer:
#     def __init__(self, static_points, update_queue):
#         self.static_points = static_points
#         self.moving_point = [0, 0]  # initial position
#         self.update_queue = update_queue

#         plt.ion()
#         self.figure, self.ax = plt.subplots()
#         self.scatter_static = self.ax.scatter(*zip(*self.static_points), c='green')
#         self.scatter_moving = self.ax.scatter(*self.moving_point, c='red')

#         self.ax.set_xlim(0, 1)  # Adjust limits as necessary
#         self.ax.set_ylim(0, 1)
#         self.ax.set_aspect('equal')

#     def update_loop(self):
#         while True:
#             try:
#                 # Non-blocking check for new data
#                 new_point = self.update_queue.get_nowait()
#                 if new_point is None:  # Signal to stop visualization
#                     break
#                 self.moving_point = new_point
#             except queue.Empty:
#                 pass  # No new data; continue with existing point
            
#             self.scatter_moving.set_offsets([self.moving_point])
#             self.figure.canvas.draw()
#             self.figure.canvas.flush_events()
#             time.sleep(0.05)  # Adjust refresh rate

# def server_simulation(update_queue):
#     """Simulate server logic that updates the moving point position."""
#     import random
#     try:
#         while True:
#             new_pos = [random.uniform(0.1, 0.9), random.uniform(0.1, 0.9)]
#             update_queue.put(new_pos)
#             time.sleep(0.1)
#     except KeyboardInterrupt:
#         update_queue.put(None)  # Signal visualization to stop

# if __name__ == "__main__":
#     static_points = [(0.1, 0.9), (0.9, 0.9), (0.1, 0.1)]
#     update_queue = queue.Queue()

#     # Start server simulation in a background thread
#     server_thread = threading.Thread(target=server_simulation, args=(update_queue,), daemon=True)
#     server_thread.start()

#     # Start visualization on main thread
#     visualizer = RealTimeVisualizer(static_points, update_queue)
#     visualizer.update_loop()

import threading
import matplotlib.pyplot as plt
import time
import queue

class RealTimeVisualizer:
    def __init__(self, static_points, update_queue):
        self.static_points = static_points
        self.moving_point = [0, 0]  # initial position
        self.update_queue = update_queue

        plt.ion()
        self.figure, self.ax = plt.subplots()
        self.figure.patch.set_facecolor('black')
        self.ax.set_facecolor('black')

        self.scatter_static = self.ax.scatter(*zip(*self.static_points), c='green')
        self.scatter_moving = self.ax.scatter(*self.moving_point, c='red')

        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.set_aspect('equal')

        self.ax.grid(True, color='white')
        self.ax.tick_params(colors='white')
        for spine in self.ax.spines.values():
            spine.set_edgecolor('white')

    def update_loop(self):
        while True:
            try:
                new_point = self.update_queue.get_nowait()
                if new_point is None:
                    break
                self.moving_point = new_point
            except queue.Empty:
                pass

            self.scatter_moving.set_offsets([self.moving_point])
            self.figure.canvas.draw()
            self.figure.canvas.flush_events()
            time.sleep(0.25)

def server_simulation(update_queue):
    import random
    try:
        while True:
            new_pos = [random.uniform(0.1, 0.9), random.uniform(0.1, 0.9)]
            update_queue.put(new_pos)
            time.sleep(0.5)
    except KeyboardInterrupt:
        update_queue.put(None)

if __name__ == "__main__":
    static_points = [(0.1, 0.9), (0.9, 0.9), (0.1, 0.1)]
    update_queue = queue.Queue()

    server_thread = threading.Thread(target=server_simulation, args=(update_queue,), daemon=True)
    server_thread.start()

    visualizer = RealTimeVisualizer(static_points, update_queue)
    visualizer.update_loop()