import numpy as np


class KalmanFilter:
    #implemented thanks to https://thekalmanfilter.com/kalman-filter-explained-simply/
    def __init__(
        self, 
        x0=np.array([[-70.]]), 
        P0=np.array([[5.]]), 
        A=np.array([[1.]]), 
        H=np.array([[1.]]), 
        Q=np.array([[0.1]]), 
        R=np.array([[2.]])
    ):
        #unsure about default values right now
        
        self.x = x0
        self.P = P0
        self.A = A
        self.H = H
        self.Q = Q
        self.R = R

    def predict(self):
        #update system state
        self.x = self.A @ self.x

        #update system state error covariance
        self.P = self.A @ self.P @ self.A.T + self.Q

    def update(self, z):
        #kalman gain
        K = (self.P @ self.H.T) @ np.linalg.inv(self.H @ self.P @ self.H.T + self.R)

        #system state estimation
        self.x = self.x + K @ (z - self.H @ self.x)

        #system state error covariance estimation
        self.P = self.P - K @ self.H @ self.P

    def step(self, z):
        #run prediction step
        self.predict()
        #run update step
        self.update(z)

        #return prdicted values
        return self.x, self.P