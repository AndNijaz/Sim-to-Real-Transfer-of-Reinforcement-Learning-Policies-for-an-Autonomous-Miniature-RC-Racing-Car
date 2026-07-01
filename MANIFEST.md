# Submission Manifest

This manifest lists the important files and folders in the thesis submission package. Importance labels are:

- **MAIN:** primary evidence or core submission material.
- **SUPPORTING:** useful implementation, setup, calibration, or explanatory material.
- **OPTIONAL:** extra media, backups, caches, duplicate copies, or files that may not be required for commission review.

## Final Thesis Documents

| Folder | File | Type | Importance | Description |
|---|---|---|---|---|
| `01_Final_Thesis` | `Nijaz Andelic - Sim-to-Real Transfer of Reinforcement Learning Policies for an Autonomous Miniature RC Racing Car.pdf` | PDF | MAIN | Final thesis PDF for commission review. |
| `01_Final_Thesis` | `Nijaz Andelic - Sim-to-Real Transfer of Reinforcement Learning Policies for an Autonomous Miniature RC Racing Car.docx` | DOCX | MAIN | Editable final thesis document. |

## Webots Simulation Project

| Folder | File | Type | Importance | Description |
|---|---|---|---|---|
| `02_Webots_Simulation_Project/worlds` | `Arena.wbt` | Webots world | MAIN | Main Webots racing environment world file. |
| `02_Webots_Simulation_Project/worlds` | `Vechicle.wbt` | Webots world | MAIN | Webots vehicle-related world file. The filename appears to use the spelling `Vechicle`. |
| `02_Webots_Simulation_Project/worlds` | `.Arena.wbproj`, `.Arena2.wbproj`, `.Further.wbproj`, `.Vechicle.wbproj` | Webots project files | MAIN | Webots project metadata files associated with the worlds. |
| `02_Webots_Simulation_Project/controllers/run_ppo` | `run_ppo.py` | Python script | MAIN | PPO controller/run script for Webots. |
| `02_Webots_Simulation_Project/controllers/run_ppo` | `train_lane_follower.py` | Python script | MAIN | PPO-related lane-following training/controller code inside the Webots project. |
| `02_Webots_Simulation_Project/controllers/run_sac` | `run_sac.py` | Python script | MAIN | SAC controller/run script for Webots. |
| `02_Webots_Simulation_Project/controllers/run_sac` | `train_lane_follower.py` | Python script | MAIN | SAC-related lane-following training/controller code inside the Webots project. |
| `02_Webots_Simulation_Project/protos` | `OakDLite.proto`, `wltoys_12428.proto` | Webots proto | MAIN | Custom Webots proto definitions for the camera and RC vehicle model. |
| `02_Webots_Simulation_Project/protos`, `02_Webots_Simulation_Project/worlds`, `02_Webots_Simulation_Project/STL and Meshes` | `.stl`, `.dae`, `.png`, `.jpg` assets | Mesh/image assets | SUPPORTING | Simulation assets referenced by Webots worlds and protos. Do not rename without checking relative paths. |
| `02_Webots_Simulation_Project/RL Models` | `best_model_ppo.zip`, `best_model_sac.zip`, `ppo_buggy_final.zip` | Model zip | MAIN | RL model files available inside the Webots project. |
| `02_Webots_Simulation_Project/controllers/buggy_test` | `buggy_test.py` | Python script | SUPPORTING | Test controller script. |
| `02_Webots_Simulation_Project/controllers/Camwithcar` | `Camwithcar.py` | Python script | SUPPORTING | Camera/vehicle controller script. |
| `02_Webots_Simulation_Project/controllers/run_ppo/__pycache__` | `train_lane_follower.cpython-312.pyc` | Python cache | OPTIONAL | Generated Python cache file, not needed for thesis review. |
| `02_Webots_Simulation_Project` | `README_Webots_Run_Instructions.txt` | Text note | SUPPORTING | Existing run instructions for Webots. |

## Reinforcement Learning Code

| Folder | File | Type | Importance | Description |
|---|---|---|---|---|
| `03_Reinforcement_Learning_Code/PPO` | `train_ppo.py` | Python script | MAIN | PPO training code. |
| `03_Reinforcement_Learning_Code/PPO` | `run_ppo.py` | Python script | MAIN | PPO run/evaluation code. |
| `03_Reinforcement_Learning_Code/PPO/env` | `buggy_env.py` | Python script | MAIN | PPO environment wrapper/code used by the training setup. |
| `03_Reinforcement_Learning_Code/SAC` | `train_sac.py` | Python script | MAIN | SAC training code. |
| `03_Reinforcement_Learning_Code/SAC` | `run_sac.py` | Python script | MAIN | SAC run/evaluation code. |
| `03_Reinforcement_Learning_Code/SAC` | `train_sac2.py` | Python script | SUPPORTING | Additional or alternate SAC training script. |
| `03_Reinforcement_Learning_Code/PPO` | `README_PPO.txt` | Text note | SUPPORTING | Existing PPO notes. |
| `03_Reinforcement_Learning_Code/SAC` | `README_SAC.txt` | Text note | SUPPORTING | Existing SAC notes. |
| `03_Reinforcement_Learning_Code/Utilities` | Folder | Utilities | SUPPORTING | Utility folder exists; no files were present in the inspected folder listing. |

## Real-World Deployment Code

| Folder | File | Type | Importance | Description |
|---|---|---|---|---|
| `04_Real_World_Deployment_Code/Arduino/arduino_servo_esc_controller` | `arduino_servo_esc_controller.ino` | Arduino sketch | MAIN | Arduino actuator controller for steering servo and ESC control. |
| `04_Real_World_Deployment_Code/Raspberry_Pi/autonomous_inference` | `run_real_ppo_track_test_v1.py` | Python script | MAIN | Raspberry Pi PPO real-world track test script. |
| `04_Real_World_Deployment_Code/Raspberry_Pi/autonomous_inference` | `run_real_sac_track_record_v1.py` | Python script | MAIN | Raspberry Pi SAC real-world track recording script. |
| `04_Real_World_Deployment_Code/Raspberry_Pi/autonomous_inference` | `run_real_sac_track_test_WORKING.py` | Python script | MAIN | Working SAC real-world track test script. |
| `04_Real_World_Deployment_Code/Raspberry_Pi/autonomous_inference` | `run_real_sac_WORKING_RESET.py` | Python script | SUPPORTING | Working/reset variant of SAC deployment script. |
| `04_Real_World_Deployment_Code/Raspberry_Pi/core_control` | `car_controller.py`, `car_controller_v2.py`, `real_camera_adapter.py` | Python scripts | MAIN | Core vehicle control and camera adapter code. |
| `04_Real_World_Deployment_Code/Raspberry_Pi/core_control` | `*_WORKING*` files | Python scripts | SUPPORTING | Working baseline variants retained as supporting evidence. |
| `04_Real_World_Deployment_Code/Raspberry_Pi/camera_and_perception` | `camera_preview_low_latency_v3.py`, `camera_record_v3.py`, `test_oak_detect.py`, `test_oak_rgb.py`, `validate_real_camera_adapter.py` | Python scripts | SUPPORTING | OAK-D Lite camera and perception utilities, tests, and validation scripts. |
| `04_Real_World_Deployment_Code/Raspberry_Pi/manual_and_calibration` | Calibration and manual driving scripts | Python scripts | SUPPORTING | Manual drive, ESC calibration, servo tests, and actuator validation helpers. |
| `04_Real_World_Deployment_Code/Configs` | `requirements_raspberry_pi.txt`, `environment_info.txt`, `WORKING_CONFIG.txt`, `AUTONOMOUS_WORKING_CONFIG.txt`, `Arduino_PWM_Protocol.txt` | Text/config | SUPPORTING | Configuration and environment notes for deployment. |
| `04_Real_World_Deployment_Code/Arduino` | `README_Arduino_PWM_Protocol.txt` | Text note | SUPPORTING | Arduino PWM protocol notes. |

## Trained Models

| Folder | File | Type | Importance | Description |
|---|---|---|---|---|
| `05_Trained_Models/PPO` | `best_model_ppo.zip` | Model zip | MAIN | PPO trained model file. |
| `05_Trained_Models/PPO` | `ppo_buggy_final.zip` | Model zip | MAIN | Final PPO model file. |
| `05_Trained_Models/SAC` | `best_model_sac.zip` | Model zip | MAIN | SAC trained model file. |
| `05_Trained_Models/SAC` | `best_model_for_sac.zip` | Model zip | MAIN | SAC trained model file. |
| `05_Trained_Models/SAC/best_sac_model` | `best_model_for_sac.zip` | Model zip | SUPPORTING | Duplicate or nested SAC model copy. |

## Results, Logs, and Graphs

| Folder | File | Type | Importance | Description |
|---|---|---|---|---|
| `06_Results_Logs_and_Graphs/PPO/summaries` | `ppo_training_summary.csv`, `ppo_training_summary.md` | CSV/Markdown | MAIN | PPO training summary supporting PPO training curves. |
| `06_Results_Logs_and_Graphs/PPO/tensorboard_exports` | `ppo_training_scalars_from_tensorboard.csv`, `ppo_training_summary.md` | CSV/Markdown | MAIN | PPO TensorBoard export and summary supporting PPO training curves. |
| `06_Results_Logs_and_Graphs/PPO/deterministic_10min_evaluation` | `ppo_episode_log_20260524_141709.csv`, `ppo_live_summary_20260524_141709.csv`, `ppo_step_log_20260524_141709.csv` | CSV logs | MAIN | PPO 10-minute deterministic Webots evaluation logs. |
| `06_Results_Logs_and_Graphs/SAC` | `sac_episode_log_20260524_140037.csv`, `sac_live_summary_20260524_140037.csv`, `sac_step_log_20260524_140037.csv` | CSV logs | MAIN | SAC 10-minute deterministic Webots evaluation logs. |
| `06_Results_Logs_and_Graphs/Webots_10min_Evaluation/combined_summary` | `webots_10min_eval_summary.csv`, `webots_10min_eval_summary.md`, `webots_10min_termination_counts.csv` | CSV/Markdown | MAIN | Combined Webots evaluation summary containing both PPO and SAC comparison data. |
| `06_Results_Logs_and_Graphs/Thesis_Figures_Final` | `Figure 1...` through `Figure 19...` | Images | MAIN | Final thesis figures used to support the written thesis evidence. |

## Photos and Videos

| Folder | File | Type | Importance | Description |
|---|---|---|---|---|
| `07_Photos_and_Videos/Real_World_Testing_Videos` | `Thesis Demonstration Video.mp4` | Video | MAIN | Main thesis demonstration video. |
| `07_Photos_and_Videos/Real_World_Testing_Videos` | `Best Demo Video.MOV`, `Try 1.MOV`, `Try 2.mov`, `Try 3.MOV`, `Try 4.mov` | Videos | SUPPORTING | Additional real-world test videos. |
| `07_Photos_and_Videos/Webots_Videos` | `Arena_2-longest PPO ever.mp4`, `Arena_2-longest sac ever.mp4`, `Arena_2-run-1.mp4`, `Arena_PPO-run-1.mp4`, `LongPPO.mp4`, `LongSAC.mp4` | Videos | SUPPORTING | Webots simulation run videos. |
| `07_Photos_and_Videos/Physical_Car_Photos` | `Physical Car on Track Fully Built.jpg` | Image | MAIN | Main physical vehicle photo. |
| `07_Photos_and_Videos/Physical_Track_Photos` | `Real Track 1.jpg`, `Real Track 2.jpg`, `Real Track 3.HEIC`, `Real Track 4.HEIC`, `Real Track 5.HEIC` | Images | SUPPORTING | Physical track photos. |
| `07_Photos_and_Videos/Building_Car_Photos_And_Videos` | Build/setup photos and videos | Images/videos | SUPPORTING | Build and hardware setup media. |

## References

| Folder | File | Type | Importance | Description |
|---|---|---|---|---|
| `08_References` | `Proximal Policy Optimization Algorithms.pdf` | PDF | MAIN | Reference PDF related to PPO. |
| `08_References` | `Soft Actor-Critic.pdf` | PDF | MAIN | Reference PDF related to SAC. |
| `08_References` | `Stable-Baselines3 Reliable Reinforcement Learning.pdf` | PDF | MAIN | Reference PDF related to the RL software framework. |
| `08_References` | `Reinforcement Learning.pdf` | PDF | MAIN | General reinforcement learning reference. |
| `08_References` | `Domain Randomization for Transferring Deep Neural Networks from.pdf` | PDF | MAIN | Sim-to-real/domain randomization reference. |
| `08_References` | `AMZ Driverless The Full Autonomous Racing System.pdf` | PDF | MAIN | Autonomous racing system reference. |
| `08_References` | `Autonomous Overtaking in Gran Turismo Sport.pdf` | PDF | MAIN | Autonomous racing and driving reference. |
| `08_References` | `Autonomous_Vehicles_on_the_Edge_A_Survey_on_Autonomous_Vehicle_Racing.pdf` | PDF | MAIN | Autonomous vehicle racing survey reference. |
| `08_References` | `Comparing deep reinforcement learning architectures for autonomous racing.pdf` | PDF | MAIN | Deep RL architecture comparison reference. |
| `08_References` | `CONTINUOUS CONTROL WITH DEEP REINFORCEMENT.pdf` | PDF | MAIN | Continuous-control reinforcement learning reference. |
| `08_References` | `Cyberbotics Ltd..pdf` | PDF | MAIN | Webots/Cyberbotics reference. |
| `08_References` | `Deterministic Policy Gradient Algorithms.pdf` | PDF | MAIN | Deterministic policy gradient reference. |
| `08_References` | `End-to-End Race Driving with Deep Reinforcement Learning.pdf` | PDF | MAIN | End-to-end RL race-driving reference. |
| `08_References` | `F1TENTH An Open-source Evaluation Environment for.pdf` | PDF | MAIN | F1TENTH/autonomous racing environment reference. |
| `08_References` | `Learning on the Fly Rapid Policy Adap.pdf` | PDF | MAIN | Policy adaptation reference. |
| `08_References` | `On learning racing policies with reinforcement learning.pdf` | PDF | MAIN | Racing policy learning reference. |
| `08_References` | `OpenAI Gym.pdf` | PDF | MAIN | RL environment API reference. |
| `08_References` | `Reference-Free Formula Drift with Reinforcement Learning From.pdf` | PDF | MAIN | Reinforcement learning driving reference. |
| `08_References` | `Towards Time-Optimal Race Car Driving using Nonlinear MPC in.pdf` | PDF | MAIN | Race-car control reference. |

## Documentation Files Added for Submission

| Folder | File | Type | Importance | Description |
|---|---|---|---|---|
| Root | `README_MAIN.md` | Markdown | MAIN | Main overview of the thesis submission package. |
| Root | `MANIFEST.md` | Markdown | MAIN | Structured manifest of important files. |
| Root | `SUBMISSION_CHECKLIST.md` | Markdown | MAIN | Presence checklist for the submission package. |
| Root | `CLEANUP_REPORT.md` | Markdown | MAIN | Practical cleanup and readiness report. |
| Numbered folders | `README.md` | Markdown | MAIN | Folder-level explanations for commission review. |
