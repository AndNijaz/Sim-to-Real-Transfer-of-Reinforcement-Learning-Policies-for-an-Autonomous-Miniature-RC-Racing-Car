import os
import sys
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import VecFrameStack

import cv2
import numpy as np

from train_lane_follower import TrackNavigationEnv, CustomCNN


def main():
    print("Initializing Webots Environment...")

    env = make_vec_env(TrackNavigationEnv, n_envs=1)

    print("Applying 4-Frame Stacking for Inference...")
    env = VecFrameStack(env, n_stack=4, channels_order='first')

    print("Loading trained PPO model...")

    model_path = "../../RL Models/best_model_ppo.zip"

    if not os.path.exists(model_path):
        print(f"Error: Model file '{model_path}' not found!")
        return

    # 1. Define the exact network architecture used during training
    # Based on your error log, features_dim was 128, and the MLP was likely [64, 64]
    custom_objects = {
        "policy_kwargs": dict(
            features_extractor_class=CustomCNN,
            features_extractor_kwargs=dict(features_dim=128),
            net_arch=dict(pi=[64, 64], vf=[64, 64])
        )
    }

    # 2. Pass the custom_objects to bypass the Python 3.12 deserialization bug
    model = PPO.load(model_path, env=env, custom_objects=custom_objects)

    print("Starting Autonomous Driving! Press Ctrl+C to stop.")

    obs = env.reset()

    try:
        while True:
            # deterministic=True = no randomness
            action, _states = model.predict(obs, deterministic=True)

            obs, rewards, dones, infos = env.step(action)

            if dones[0]:
                print("Episode Reset")

    except KeyboardInterrupt:
        print("\nStopping autonomous inference...")


if __name__ == "__main__":
    main()