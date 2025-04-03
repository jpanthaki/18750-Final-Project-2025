import numpy as np
from scipy.optimize import least_squares
import math

class TrilaterationCalculator:

    def __init__(self, anchors, path_loss_exp):

        self.anchors = anchors
        self.path_loss_exp = path_loss_exp

    def get_distance(self, rssi, power):
        return 10 ** ((power - rssi) / (10 * self.path_loss_exp))

    def get_residuals(self, x0, distances):

        x, y, offset = x0

        res = []

        for i, (ax, ay) in enumerate(self.anchors):
            d = distances[i]

            residual = (x - ax) ** 2 + (y - ay) ** 2 - (offset - d) ** 2
            res.append(residual)

        return np.array(res)

    def get_position(self, rssi_values):

        distances = []

        for rssi, anchor in zip(rssi_values, self.anchors):
            distances.append(self.get_distance(rssi, anchor[1]))

        
        results = least_squares(self.get_residuals, x0=[0,0,0], args=(distances, ))
        
        

        return results.x[0], results.x[1]