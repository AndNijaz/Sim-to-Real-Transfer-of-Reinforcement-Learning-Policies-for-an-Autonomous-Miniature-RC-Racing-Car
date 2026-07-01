# Submission Checklist

This checklist is based on the current folder structure and filenames. It does not confirm runtime behavior, model performance, or the internal contents of documents, code, media, or model files.

## Final Thesis Documents

| Item | Status | Notes |
|---|---|---|
| Final thesis PDF | Present | Located in `01_Final_Thesis`. |
| Final thesis DOCX | Present | Located in `01_Final_Thesis`. |

## Simulation Project

| Item | Status | Notes |
|---|---|---|
| Webots simulation folder | Present | `02_Webots_Simulation_Project` exists. |
| Webots world files | Present | `Arena.wbt` and `Vechicle.wbt` are present. |
| Webots project files | Present | Several `.wbproj` files are present in `worlds`. |
| Webots controllers | Present | PPO, SAC, buggy test, and camera/vehicle controller folders are present. |
| Protos and mesh assets | Present | `.proto`, `.stl`, `.dae`, and image assets are present. |
| Webots run instructions | Present but optional | Existing `README_Webots_Run_Instructions.txt` is present. |

## Reinforcement Learning Code

| Item | Status | Notes |
|---|---|---|
| PPO training code | Present | `03_Reinforcement_Learning_Code/PPO/train_ppo.py`. |
| PPO run/evaluation code | Present | `03_Reinforcement_Learning_Code/PPO/run_ppo.py`. |
| PPO environment code | Present | `03_Reinforcement_Learning_Code/PPO/env/buggy_env.py`. |
| SAC training code | Present | `03_Reinforcement_Learning_Code/SAC/train_sac.py`. |
| SAC run/evaluation code | Present | `03_Reinforcement_Learning_Code/SAC/run_sac.py`. |
| Additional SAC training script | Present but optional | `train_sac2.py` appears to be an alternate or supporting script. |
| Utilities folder | Present but optional | Folder exists, but no files appeared in the inspected listing. |

## Real-World Deployment Code

| Item | Status | Notes |
|---|---|---|
| Arduino actuator controller | Present | `arduino_servo_esc_controller.ino`. |
| Raspberry Pi autonomous inference scripts | Present | PPO and SAC real-world scripts are present. |
| Camera/perception scripts | Present | OAK-D Lite testing, preview, recording, and validation scripts are present. |
| Core vehicle control scripts | Present | Car controller and real camera adapter scripts are present. |
| Manual driving and calibration scripts | Present but optional | Useful for setup and testing, but not all are necessary for commission review. |
| Configuration and environment notes | Present | Configuration and requirements text files are present. |

## Trained Models

| Item | Status | Notes |
|---|---|---|
| PPO trained model `.zip` files | Present | `best_model_ppo.zip` and `ppo_buggy_final.zip` are present. |
| SAC trained model `.zip` files | Present | `best_model_sac.zip` and `best_model_for_sac.zip` are present. |
| Duplicate or nested SAC model copy | Present but optional | `05_Trained_Models/SAC/best_sac_model/best_model_for_sac.zip`. |
| Model copies inside Webots project | Present but optional | Model zips also appear under `02_Webots_Simulation_Project/RL Models`. |

## Results, Logs, and Graphs

| Item | Status | Notes |
|---|---|---|
| PPO training logs and summaries | Present | PPO summaries and TensorBoard exports are present. |
| PPO 10-minute deterministic evaluation logs | Present | PPO episode, live summary, and step logs are present. |
| SAC 10-minute deterministic evaluation logs | Present | SAC episode, live summary, and step logs are present. |
| Combined Webots evaluation summary | Present | Contains combined PPO/SAC comparison summary files. |
| Final thesis figures | Present | Figures 1 through 19 appear in `Thesis_Figures_Final`. |

## Photos and Videos

| Item | Status | Notes |
|---|---|---|
| Thesis demonstration video | Present | `Thesis Demonstration Video.mp4` is present. |
| Real-world testing videos | Present | Additional `.MOV` and `.mov` test videos are present. |
| Webots videos | Present | Several Webots run videos are present. |
| Physical car photo | Present | `Physical Car on Track Fully Built.jpg` is present. |
| Physical track photos | Present | Multiple real track photos are present. |
| Build/setup media | Present but optional | Additional photos and videos support hardware setup evidence. |

## References

| Item | Status | Notes |
|---|---|---|
| Reference PDF folder | Present | `08_References` exists. |
| PPO reference PDF | Present | `Proximal Policy Optimization Algorithms.pdf`. |
| SAC reference PDF | Present | `Soft Actor-Critic.pdf`. |
| Reinforcement learning and autonomous racing references | Present | Multiple local PDF references are present. |

## Documentation

| Item | Status | Notes |
|---|---|---|
| Main README | Present | `README_MAIN.md` created for commission review. |
| Manifest | Present | `MANIFEST.md` created for structured file overview. |
| Submission checklist | Present | This file. |
| Cleanup report | Present | `CLEANUP_REPORT.md` created. |
| Folder-level README files | Present | Added to each numbered submission folder. |
| Existing empty `README_MAIN.txt` | Present but optional | This file exists at root and is empty; it was not modified. |

## Overall Checklist Verdict

Based on filenames and folder structure, the package appears broadly complete for commission submission. The main items expected for a thesis package are present. A few optional or duplicate-looking files remain, but they do not prevent review if the commission is given the Markdown documentation files as the main navigation guide.
