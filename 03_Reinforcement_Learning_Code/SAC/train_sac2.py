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
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

DEBUG_FORCE_FORWARD = False   # 🔥 set True to bypass RL and test physics
PRINT_ACTIONS = False        # 🔍 set True to see what SAC outputs


# =====================
# VISION PROCESSING
# =====================
def check_boundaries(image):
    """
    Scans for Red and Blue pixels. 
    Adapted for 80x160 resolution.
    """
    h, w, _ = image.shape
    roi = image[int(h*0.75):h, int(w*0.3):int(w*0.7)]
    
    # Convert to HSV for accurate color detection
    hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)

    # Red ranges
    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([180, 255, 255])

    # Blue range
    lower_blue = np.array([100, 150, 0])
    upper_blue = np.array([140, 255, 255])

    # Create masks
    mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
    mask = cv2.bitwise_or(mask_red, mask_blue)
    
    bottom_mask = mask[int(mask.shape[0]*0.6):, :]

    # Thresholds scaled down for 80x160 SAC image size
    if cv2.countNonZero(bottom_mask) > 70:
        return True

    red_pixels = cv2.countNonZero(mask_red)
    blue_pixels = cv2.countNonZero(mask_blue)

    if red_pixels > 100 or blue_pixels > 100:
        return True
        
    return False


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
        if self.car_node is None:
            raise ValueError("Error: Could not find Automobile with DEF 'wltoys_12428'")

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
        
        # Buffer to hold standard image for OpenCV processing
        self.latest_rgb_image = np.zeros((IMAGE_HEIGHT, IMAGE_WIDTH, 3), dtype=np.uint8)

        self.WHEELBASE = 0.253
        self.TRACK_WIDTH = 0.195

    # =====================
    # STEP
    # =====================
    def step(self, action):
        if DEBUG_FORCE_FORWARD:
            steering = 0.0
            throttle = 0.6
        else:
            steering = float(action[0]) * MAX_STEERING_ANGLE
            throttle = float(action[1])
            throttle = max(throttle, 0.25) # prevent zero-throttle collapse

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

        # Re-apply torque EVERY step
        for m in self.motors:
            try: m.setAvailableTorque(5.0)
            except:
                try: m.setForce(5.0)
                except: pass

        # Apply motion
        self.motors[0].setVelocity(speed_left)
        self.motors[1].setVelocity(speed_right)
        self.motors[2].setVelocity(speed_left)
        self.motors[3].setVelocity(speed_right)

        self.steer_fl.setPosition(angle_fl)
        self.steer_fr.setPosition(angle_fr)

        self.supervisor.step(self.time_step)
        self.current_step += 1

        # =====================
        # STATE OBSERVATION
        # =====================
        obs = self._get_obs()
        is_crashed = check_boundaries(self.latest_rgb_image)

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

        # Boundary logic from your PPO setup
        MIN_X, MAX_X = -100.0, 100.0
        MIN_Y, MAX_Y = -100.0, 100.0
        out_of_world = (x < MIN_X or x > MAX_X or y < MIN_Y or y > MAX_Y)
        
        # Target Zone logic
        in_target_zone = (66.0 < x < 69.5 and -50.3 < y < -44.7)

        # =====================
        # REWARD & TERMINATION
        # =====================
        done = False
        
        # Base reward for dense learning (SAC needs this to learn to drive fast)
        reward = dist * 150.0 + 0.5

        # Minor penalties
        if throttle < 0.3:
            reward -= 1.0
        if abs(steering) > (MAX_STEERING_ANGLE * 0.8):
            reward -= 0.5

        # Terminal conditions (Overrides base rewards)
        if in_target_zone:
            print(f"🏁 SUCCESS: Reached Target Zone at step {self.current_step}!")
            reward = 10.0
            done = True
        elif is_crashed:
            print("💀 DEATH: Hit the Red/Blue Boundary!")
            reward = -7.0
            done = True
        elif out_of_world:
            print("🛸 DEATH: Wandered off the map into the void!")
            reward = -7.0
            done = True
        elif self.stuck_counter > 50:
            print("🚗 DEATH: Got stuck physically!")
            reward = -7.0
            done = True
        elif self.current_step >= 1500:
            print("⏳ TIMEOUT: Took too long to finish track!")
            reward = -5.0
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
            
            # 🔥 Save for OpenCV boundary check before normalizing for PyTorch
            self.latest_rgb_image = resized 

            return np.transpose(resized, (2, 0, 1)).astype(np.float32) / 255.0

        self.latest_rgb_image = np.zeros((IMAGE_HEIGHT, IMAGE_WIDTH, 3), dtype=np.uint8)
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
    env = make_vec_env(TrackNavigationEnv, n_envs=1)
    env = VecFrameStack(env, n_stack=2, channels_order='first')

    eval_callback = EvalCallback(
        env,
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

    model.learn(total_timesteps=200000, callback=eval_callback)
    model.save("car_model_final")


if __name__ == "__main__":
    main()