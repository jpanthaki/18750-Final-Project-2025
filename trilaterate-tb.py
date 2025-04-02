import numpy as np
from scipy.optimize import least_squares
import math

from trilaterate import TrilaterationCalculator


def distance_to_rssi(distance, power, n):

    if distance < 1e-9:
        distance = 1e-9
    return power - 10.0 * n * math.log10(distance)


def run_testbench(anchors, true_position, path_loss_exp):
    true_x, true_y = true_position
    print("-------------------------------------------------------")
    print("Anchors:")
    for i, (pos, power) in enumerate(anchors):
        print(f"  Anchor {i+1}: Pos = {pos}, Ref Power = {power} dBm")
    print("True device location: (x, y) = ({:.3f}, {:.3f})".format(true_x, true_y))

    true_distances = [math.dist(true_position, pos) for pos, _ in anchors]

    rssi_values = [distance_to_rssi(d, power, path_loss_exp) for d, (_, power) in zip(true_distances, anchors)]
    print("Synthetic RSSI values (dBm):", ", ".join("{:.2f}".format(rssi) for rssi in rssi_values))

    trilaterator = TrilaterationCalculator(anchors, path_loss_exp)
    est_x, est_y = trilaterator.get_position(rssi_values)
    print("Estimated device location: (x, y) = ({:.3f}, {:.3f})".format(est_x, est_y))

    error_x = est_x - true_x
    error_y = est_y - true_y
    distance_error = math.dist((true_x, true_y), (est_x, est_y))
    print("Error in x: {:.3f}, Error in y: {:.3f}".format(error_x, error_y))
    print("Overall 2D error: {:.3f} meters".format(distance_error))
    print("-------------------------------------------------------\n")


if __name__ == "__main__":
    path_loss_exp = 2.0

    true_position = (3.0, 4.0)

    anchors_3 = [
        ((0.0, 0.0), -45.0),
        ((10.0, 0.0), -43.0),
        ((10.0, 10.0), -42.0)
    ]
    print("Testbench: 3 Anchors")
    run_testbench(anchors_3, true_position, path_loss_exp)

    anchors_4 = [
        ((0.0, 0.0), -45.0),
        ((10.0, 0.0), -43.0),
        ((10.0, 10.0), -42.0),
        ((20.0, 10.0), -44.0)
    ]
    print("Testbench: 4 Anchors")
    run_testbench(anchors_4, true_position, path_loss_exp)

    anchors_5 = [
        ((0.0, 0.0), -45.0),
        ((10.0, 0.0), -43.0),
        ((10.0, 10.0), -42.0),
        ((20.0, 10.0), -44.0),
        ((20.0, 20.0), -43.5)
    ]
    print("Testbench: 5 Anchors")
    run_testbench(anchors_5, true_position, path_loss_exp)
