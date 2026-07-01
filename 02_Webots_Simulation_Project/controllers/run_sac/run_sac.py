import sys
import os
import cv2
import math
import torch
import numpy as np
import torch.nn as nn
import gymnasium as gym
from gymnasium.spaces import Box
from controller import Supervisor

from stable_baselines3 import SAC
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
from stable_baselines3.common.vec_env import VecFrameStack

# =====================
# CONFIG
# =====================
IMAGE_HEIGHT = 80
IMAGE_WIDTH = 160
MAX_STEERING_ANGLE = 0.8
CRUISING_SPEED = 12.0

# =====================
# ENV (Needed for model architecture)
# =====================
class TrackNavigationEnv(gym.Env):
    def __init__(self):
        super().__init__()

        self.observation_space = Box(
            low=0.0, high=1.0,
            shape=(3, IMAGE_HEIGHT, IMAGE_WIDTH),
            dtype=np.float32
        )

        self.action_space = Box(
            low=np.array([-1.0, 0.0]),
            high=np.array([1.0, 1.0]),
            dtype=np.float32
        )

        self.supervisor = Supervisor()
        self.time_step = int(self.supervisor.getBasicTimeStep())
        self.supervisor.simulationSetMode(self.supervisor.SIMULATION_MODE_REAL_TIME) # 🔥 Set to real-time so you can watch it!

        self.car_node = self.supervisor.getFromDef("wltoys_12428")

        self.camera = self.supervisor.getDevice("oak_d_rgb")
        self.camera.enable(self.time_step)

        self.steer_fl = self.supervisor.getDevice('steer_fl')
        self.steer_fr = self.supervisor.getDevice('steer_fr')

        self.motors = [self.supervisor.getDevice(f'drive_{m}') for m in ['fl','fr','rl','rr']]

        for m in self.motors:
            m.setPosition(float('inf'))
            m.setVelocity(0.0)

        self.prev_pos = None
        self.stuck_counter = 0
        self.current_step = 0

        self.WHEELBASE = 0.253
        self.TRACK_WIDTH = 0.195

    def step(self, action):
        steering = float(action[0]) * MAX_STEERING_ANGLE
        throttle = float(action[1])

        # prevent zero-throttle collapse
        throttle = max(throttle, 0.25)
        base_speed = throttle * CRUISING_SPEED

        # Ackermann steering
        if abs(steering) > 0.001:
            turn_radius = self.WHEELBASE / math.tan(steering)
            angle_fl = math.atan(self.WHEELBASE / (turn_radius - self.TRACK_WIDTH/2))
            angle_fr = math.atan(self.WHEELBASE / (turn_radius + self.TRACK_WIDTH/2))
            speed_left = base_speed * (turn_radius - self.TRACK_WIDTH/2) / turn_radius
            speed_right = base_speed * (turn_radius + self.TRACK_WIDTH/2) / turn_radius
        else:
            angle_fl = angle_fr = 0.0
            speed_left = speed_right = base_speed

        for m in self.motors:
            try:
                m.setAvailableTorque(2.5)
            except:
                try:
                    m.setForce(2.5)
                except:
                    pass

        self.motors[0].setVelocity(speed_left)
        self.motors[1].setVelocity(speed_right)
        self.motors[2].setVelocity(speed_left)
        self.motors[3].setVelocity(speed_right)

        self.steer_fl.setPosition(angle_fl)
        self.steer_fr.setPosition(angle_fr)

        self.supervisor.step(self.time_step)

        obs = self._get_obs()

        pos = self.car_node.getField("translation").getSFVec3f()
        x, y = pos[0], pos[1] 

        if self.prev_pos is None:
            self.prev_pos = pos

        dist = math.sqrt(
            (pos[0] - self.prev_pos[0])**2 +
            (pos[1] - self.prev_pos[1])**2
        )
        self.prev_pos = pos

        if dist < 0.002:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0

        MIN_X, MAX_X = -5.0, 5.0
        MIN_Y, MAX_Y = -5.0, 5.0
        out_of_bounds = (x < MIN_X or x > MAX_X or y < MIN_Y or y > MAX_Y)

        done = False
        reward = dist * 150.0 + 0.5

        if throttle < 0.3:
            reward -= 1.0
            
        if abs(steering) > (MAX_STEERING_ANGLE * 0.8):
            reward -= 0.5 

        if out_of_bounds:
            reward = -10.0
            done = True
        elif self.stuck_counter > 50:
            reward = -5.0
            done = True

        self.current_step += 1
        MAX_STEPS = 1000 
        if self.current_step >= MAX_STEPS:
            done = True

        return obs, reward, done, False, {}

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.supervisor.simulationReset()
        self.supervisor.simulationResetPhysics()
        self.supervisor.step(self.time_step)

        for m in self.motors:
            m.setPosition(float('inf'))
            m.setVelocity(0.0)

        self.prev_pos = None
        self.stuck_counter = 0
        self.current_step = 0

        return self._get_obs(), {}

    def _get_obs(self):
        img = self.camera.getImage()
        if img:
            raw = np.frombuffer(img, np.uint8).reshape(
                (self.camera.getHeight(), self.camera.getWidth(), 4)
            )[:, :, :3]
            resized = cv2.resize(raw, (IMAGE_WIDTH, IMAGE_HEIGHT))
            return np.transpose(resized, (2, 0, 1)).astype(np.float32) / 255.0
        return np.zeros((3, IMAGE_HEIGHT, IMAGE_WIDTH), dtype=np.float32)


# =====================
# CNN (Needed to map the saved weights)
# =====================
class MobileNetLite(BaseFeaturesExtractor):
    def __init__(self, observation_space, features_dim=128):
        super().__init__(observation_space, features_dim)
        c = observation_space.shape[0]
        self.net = nn.Sequential(
            nn.Conv2d(c, 16, 3, 2, 1),
            nn.ReLU(),
            nn.Conv2d(16, 32, 3, 2, 1),
            nn.ReLU(),
            nn.Conv2d(32, 64, 3, 2, 1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten()
        )
        self.linear = nn.Linear(64, features_dim)

    def forward(self, x):
        return self.linear(self.net(x))


# =====================
# RUN INFERENCE
# =====================
def main():
    print("Initializing Webots Environment...")
    env = make_vec_env(TrackNavigationEnv, n_envs=1)
    env = VecFrameStack(env, n_stack=2, channels_order='first')

    # Ensure this path matches exactly where your EvalCallback saved the zip file
    MODEL_PATH = "../../RL Models/best_model_sac.zip"
    
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Error: Could not find model at {MODEL_PATH}")
        print("Did you mean 'car_model_final.zip'?")
        sys.exit(1)

    print(f"Loading Model from {MODEL_PATH}...")
    
    # 1. Define the custom architecture used during training
    custom_objects = {
        "policy_kwargs": dict(
            features_extractor_class=MobileNetLite,
            features_extractor_kwargs=dict(features_dim=128),
        )
    }

    # 2. Pass custom_objects and switch Apple's 'mps' check to 'cuda' for Windows
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SAC.load(MODEL_PATH, env=env, device=device, custom_objects=custom_objects)

    print("Starting Inference Loop! (Press Ctrl+C to stop in terminal)")
    obs = env.reset()
    
    try:
        while True:
            # deterministic=True ensures the agent takes the optimal action without adding random exploration noise
            action, _states = model.predict(obs, deterministic=True)
            
            # The environment will automatically reset when it hits a "done" condition
            obs, rewards, dones, info = env.step(action)
            
    except KeyboardInterrupt:
        print("\nStopping car...")
        env.close()

if __name__ == "__main__":
    main()