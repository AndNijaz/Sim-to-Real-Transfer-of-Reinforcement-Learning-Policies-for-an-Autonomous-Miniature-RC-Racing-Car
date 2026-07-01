import os
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.vec_env import DummyVecEnv, VecFrameStack
from env.buggy_env import BuggyEnv

def main():
    # Setup directories
    log_dir = "./logs/"
    model_dir = "./models/"
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)

    print("Initializing Webots Environment...")
    
    # 1. Initialize the raw base environment
    base_env = BuggyEnv()
    
    # 2. Check the environment BEFORE we apply complex wrappers
    print("Running Gym compliance check...")
    check_env(base_env)

    # 3. Apply SB3-native Vectorization and Frame Stacking
    print("Applying 4-Frame Stacking...")
    vec_env = DummyVecEnv([lambda: base_env])
    
    # This magically stacks four 3-channel RGB images into one 12-channel image
    env = VecFrameStack(vec_env, n_stack=4, channels_order='last')

    # 4. Setup PPO Model
    print("Setting up PPO Model...")
    model = PPO(
        "CnnPolicy", 
        env, 
        verbose=1, 
        tensorboard_log=log_dir,
        learning_rate=0.0003,
        n_steps=2048,
        batch_size=64
    )

    # 5. Train the Model
    print("Starting Training! (This will take a while)...")
    # Set to 500k to ensure the CNN has enough time to learn the track visuals
    model.learn(total_timesteps=1000000, tb_log_name="PPO_vision_run_1")

    # 6. Save the Model
    print("Saving Model...")
    model.save(f"{model_dir}/ppo_buggy_final")

if __name__ == "__main__":
    main()