import cv2
import numpy as np
import math
import torch
import torch.nn as nn
import gymnasium as gym
from gymnasium.spaces import Box

from controller import Supervisor

from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
from stable_baselines3.common.vec_env import VecFrameStack
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.callbacks import EvalCallback

# --- Configuration ---
# For PPO:
IMAGE_HEIGHT = 160
IMAGE_WIDTH = 250

MAX_STEERING_ANGLE = 0.8
CRUISING_SPEED = 10.0 # Bumping speed slightly so it clears the starting line nicely!
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


# --- Vision Processing Pipeline ---
def check_boundaries(image):
    """
    Simply scans for Red and Blue pixels. 
    If it sees them in the lower half of the screen, it hit a wall!
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

    if cv2.countNonZero(bottom_mask) > 200:
        return True

    red_pixels = cv2.countNonZero(mask_red)
    blue_pixels = cv2.countNonZero(mask_blue)

    # FIX: Increased from 150 to 2000 pixels! 
    # In a 500x200 image, 150 is just a speck of dust.
    if red_pixels > 300 or blue_pixels > 300:
        return True
        
    return False


# --- Gymnasium Environment ---
class TrackNavigationEnv(gym.Env):
    def __init__(self, car_def_name="wltoys_12428"):
        super().__init__()
        
        self.observation_space = Box(low=0, high=255, shape=(IMAGE_HEIGHT, IMAGE_WIDTH, 3), dtype=np.uint8)
        self.action_space = Box(low=-1.0, high=1.0, shape=(1,), dtype=np.float32)

        self.supervisor = Supervisor()
        self.time_step = int(self.supervisor.getBasicTimeStep())
        
        self.car_node = self.supervisor.getFromDef(car_def_name)
        if self.car_node is None:
            raise ValueError(f"Error: Could not find Automobile with DEF '{car_def_name}'")

        # Vehicle Specs for Kinematics
        self.TRACK_WIDTH = 0.195
        self.WHEELBASE = 0.253

        # Initialize Devices
        self.camera = self.supervisor.getDevice("oak_d_rgb")
        self.camera.enable(self.time_step)

        self.stuck_counter = 0
        self.previous_pos = [0.0, 0.0, 0.0]
        
        self.steer_fl = self.supervisor.getDevice('steer_fl')
        self.steer_fr = self.supervisor.getDevice('steer_fr')
        self.drive_motors = [
            self.supervisor.getDevice('drive_fl'), self.supervisor.getDevice('drive_fr'),
            self.supervisor.getDevice('drive_rl'), self.supervisor.getDevice('drive_rr')
        ]
        
        for motor in self.drive_motors:
            motor.setPosition(float('inf'))
            motor.setVelocity(0.0)

    def step(self, action):
        steering_target = float(action[0]) * MAX_STEERING_ANGLE
        base_speed = CRUISING_SPEED
        
        # Ackermann Kinematics
        if abs(steering_target) > 0.001:
            turn_radius = self.WHEELBASE / math.tan(steering_target)
            angle_fl = math.atan(self.WHEELBASE / (turn_radius - (self.TRACK_WIDTH / 2)))
            angle_fr = math.atan(self.WHEELBASE / (turn_radius + (self.TRACK_WIDTH / 2)))
            speed_left = base_speed * ((turn_radius - (self.TRACK_WIDTH / 2)) / turn_radius)
            speed_right = base_speed * ((turn_radius + (self.TRACK_WIDTH / 2)) / turn_radius)
        else:
            angle_fl = angle_fr = 0.0
            speed_left = speed_right = base_speed

        self.steer_fl.setPosition(angle_fl)
        self.steer_fr.setPosition(angle_fr)
        self.drive_motors[0].setVelocity(speed_left)
        self.drive_motors[2].setVelocity(speed_left)
        self.drive_motors[1].setVelocity(speed_right)
        self.drive_motors[3].setVelocity(speed_right)
        
        self.supervisor.step(self.time_step)

        obs = self._get_observation()
        is_crashed = check_boundaries(obs)

        # Baseline survival reward (points just for moving and not dying!)
        reward = 0.5
        terminated = False
        
        pos = self.car_node.getField("translation").getSFVec3f()

        # --- STUCK DETECTION ---
        movement = math.sqrt((pos[0] - self.previous_pos[0])**2 + (pos[1] - self.previous_pos[1])**2)
        if movement < 0.002: 
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0
            
        self.previous_pos = pos 

        # --- TERMINAL STATE CONDITIONS ---
        if 66.0 < pos[0] < 69.5 and -50.3 < pos[1] < -44.7:
            print("🏁 SUCCESS: Reached the Target Zone!")
            reward = 5.0
            terminated = True
        elif is_crashed: 
            print("💀 DEATH: Hit the Red/Blue Boundary!")
            reward = -7.0
            terminated = True
        elif self.stuck_counter > 50: 
            print("🚗 DEATH: Got stuck physically!")
            reward = -7.0
            terminated = True

        return obs, reward, terminated, False, {}

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        self.supervisor.simulationReset()
        self.supervisor.simulationResetPhysics()
        self.supervisor.step(self.time_step)

        self.steer_fl.setPosition(0.0)
        self.steer_fr.setPosition(0.0)
        
        for motor in self.drive_motors:
            motor.setPosition(float('inf')) 
            motor.setVelocity(0.0)

        self.stuck_counter = 0
        self.previous_pos = self.car_node.getField("translation").getSFVec3f()

        return self._get_observation(), {}

    def _get_observation(self):
        image_data = self.camera.getImage()
        if image_data:
            # Extract raw byte buffer (Windows outputs BGRA)
            raw_image = np.frombuffer(image_data, dtype=np.uint8).reshape((self.camera.getHeight(), self.camera.getWidth(), 4))
            
            # Slice out the Alpha channel, and safely force BGR to RGB conversion
            image_rgb = cv2.cvtColor(raw_image[:, :, :3], cv2.COLOR_BGR2RGB)
            
            # Resize for the Neural Network
            image_resized = cv2.resize(image_rgb, (IMAGE_WIDTH, IMAGE_HEIGHT))
            return image_resized
            
        return np.zeros((IMAGE_HEIGHT, IMAGE_WIDTH, 3), dtype=np.uint8)


# --- Custom Convolutional Architecture ---
class CustomCNN(BaseFeaturesExtractor):
    def __init__(self, observation_space: gym.spaces.Box, features_dim: int = 128):
        super().__init__(observation_space, features_dim)
        
        n_input_channels = observation_space.shape[0]
        
        self.cnn = nn.Sequential(
            nn.Conv2d(n_input_channels, 32, kernel_size=8, stride=4, padding=0),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=4, stride=2, padding=0),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=0),
            nn.ReLU(),
            nn.Flatten(),
        )

        with torch.no_grad():
            sample_input = torch.as_tensor(observation_space.sample()[None]).float()
            n_flatten = self.cnn(sample_input).shape[1]

        self.linear = nn.Sequential(
            nn.Linear(n_flatten, features_dim),
            nn.ReLU()
        )

    def forward(self, observations: torch.Tensor) -> torch.Tensor:
        return self.linear(self.cnn(observations))

if __name__ == "__main__":
    # Initialize Environment
    env = make_vec_env(TrackNavigationEnv, n_envs=1)
    
    # 4-Frame Stacking
    env = VecFrameStack(env, n_stack=4, channels_order='first')

    policy_kwargs = dict(
        features_extractor_class=CustomCNN,
        features_extractor_kwargs=dict(features_dim=128),
    )

    model_path = "../../RL Models/best_model_sac.zip"

    print("Initializing PPO Training...")

    if os.path.exists(model_path):
        print("🔁 Loading existing model and continuing training...")
        model = PPO.load(model_path, env=env)
    else:
        print("🆕 Creating new model...")
        model = PPO(
            "CnnPolicy",
            env,
            n_steps=512,
            verbose=2,
            policy_kwargs=policy_kwargs,
            learning_rate=0.0003
        )
    
    checkpoint_callback = CheckpointCallback(
        save_freq=5000,                 # save every 5000 steps
        save_path="./checkpoints/",     # folder
        name_prefix="cnn_track_model"   # file name prefix
    )

    # Best Model
    eval_callback = EvalCallback(
        env,
        best_model_save_path="./best_model/",
        log_path="./logs/",
        eval_freq=5000,
        deterministic=True,
        render=False
    )

    model.learn(
        total_timesteps=50000,
        callback=[checkpoint_callback, eval_callback]
    )

    print("Saving Model...")
    model.save("cnn_track_agent")