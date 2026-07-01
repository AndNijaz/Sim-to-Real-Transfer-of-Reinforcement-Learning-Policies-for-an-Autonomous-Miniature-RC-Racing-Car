import sys
import os

# --- WEBOTS PATH ---
os.environ['WEBOTS_HOME'] = '/Applications/Webots.app'
for p in [
    '/Applications/Webots.app/Contents/lib/controller/python',
    '/Applications/Webots.app/lib/controller/python'
]:
    if os.path.exists(p):
        sys.path.insert(0, p)
        break

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
from stable_baselines3.common.callbacks import EvalCallback

# =====================
# CONFIG
# =====================
IMAGE_HEIGHT = 80
IMAGE_WIDTH = 160
MAX_STEERING_ANGLE = 0.8
CRUISING_SPEED = 12.0

DEBUG_FORCE_FORWARD = False   # 🔥 set True to bypass RL and test physics
PRINT_ACTIONS = False        # 🔍 set True to see what SAC outputs

# =====================
# ENV
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
        self.supervisor.simulationSetMode(self.supervisor.SIMULATION_MODE_FAST)

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
        self.current_step = 0
        self.stuck_counter = 0

        self.WHEELBASE = 0.253
        self.TRACK_WIDTH = 0.195

    # =====================
    # STEP
    # =====================
    def step(self, action):

        # 🔥 DEBUG BYPASS
        if DEBUG_FORCE_FORWARD:
            steering = 0.0
            throttle = 0.6
        else:
            steering = float(action[0]) * MAX_STEERING_ANGLE
            throttle = float(action[1])

            # prevent zero-throttle collapse
            throttle = max(throttle, 0.25)

        if PRINT_ACTIONS:
            print("Action:", action, "-> throttle:", throttle)

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

        # 🔥 CRITICAL: re-apply torque EVERY step
        for m in self.motors:
            try:
                m.setAvailableTorque(5.0)
            except:
                try:
                    m.setForce(5.0)
                except:
                    pass

        # Apply motion
        self.motors[0].setVelocity(speed_left)
        self.motors[1].setVelocity(speed_right)
        self.motors[2].setVelocity(speed_left)
        self.motors[3].setVelocity(speed_right)

        self.steer_fl.setPosition(angle_fl)
        self.steer_fr.setPosition(angle_fr)

        self.supervisor.step(self.time_step)

        # =====================
        # STATE OBSERVATION
        # =====================
        obs = self._get_obs()

        pos = self.car_node.getField("translation").getSFVec3f()
        x, y = pos[0], pos[1] # Assuming X and Y are your floor axes

        if self.prev_pos is None:
            self.prev_pos = pos

        dist = math.sqrt(
            (pos[0] - self.prev_pos[0])**2 +
            (pos[1] - self.prev_pos[1])**2
        )
        self.prev_pos = pos

        # Update stuck counter (using a slightly tighter threshold as discussed)
        if dist < 0.002:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0

        # Define your world limits (Adjust these to fit your track)
        MIN_X, MAX_X = -5.0, 5.0
        MIN_Y, MAX_Y = -5.0, 5.0
        out_of_bounds = (x < MIN_X or x > MAX_X or y < MIN_Y or y > MAX_Y)

        # =====================
        # REWARD & TERMINATION
        # =====================
        done = False
        
        # 1. Calculate base reward for moving forward safely
        reward = dist * 150.0 + 0.5

        # 2. Apply minor penalties
        if throttle < 0.3:
            reward -= 1.0
        
        if abs(steering) > (MAX_STEERING_ANGLE * 0.8):
            reward -= 0.5

        # 3. Check terminal states (These OVERRIDE the base reward)
        if out_of_bounds:
            reward = -10.0
            done = True
        elif self.stuck_counter > 50:
            reward = -5.0
            done = True

        # 🔥 Increment the step counter
        self.current_step += 1
        MAX_STEPS = 1000 # Adjust this based on how long a normal lap should take

        # Force termination if it takes too long
        if self.current_step >= MAX_STEPS:
            done = True
            # Optional: Add a timeout penalty so it prefers finishing fast
            # reward -= 5.0 

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
        
        # 🔥 Add a step counter
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
# CNN
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
# TRAIN
# =====================
def main():
    # 1. Create ONLY ONE Environment
    env = make_vec_env(TrackNavigationEnv, n_envs=1)
    env = VecFrameStack(env, n_stack=2, channels_order='first')

    # 2. Setup the EvalCallback to use the same training environment
    eval_callback = EvalCallback(
        env,  # <--- Notice we just pass 'env' here now
        best_model_save_path='./best_sac_model/',
        log_path='./logs/sac_results/',
        eval_freq=25000,
        deterministic=True,
        render=False
    )

    model = SAC(
        "CnnPolicy",
        env,
        policy_kwargs=dict(features_extractor_class=MobileNetLite),
        buffer_size=20000,
        learning_starts=1000,
        train_freq=8,
        gradient_steps=4,
        ent_coef='auto_0.5',
        verbose=1,
        device="mps" if torch.backends.mps.is_available() else "cpu"
    )

    # 3. Pass the callback into the learn function
    model.learn(total_timesteps=200000, callback=eval_callback)
    
    # Save the final model at the very end of training
    model.save("car_model_final")


if __name__ == "__main__":
    main()