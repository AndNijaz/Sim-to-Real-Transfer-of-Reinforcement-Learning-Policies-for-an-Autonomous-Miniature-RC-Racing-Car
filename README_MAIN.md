# Thesis Submission Package

**Thesis title:** Sim-to-Real Transfer of Reinforcement Learning Policies for an Autonomous Miniature RC Racing Car

**Author:** Nijaz Andelić

This folder contains the main materials for the undergraduate thesis submission package. It is organized to help the thesis commission locate the final thesis documents, simulation project, reinforcement learning code, real-world deployment code, trained models, logs, figures, videos, and references that support the thesis evidence.

## Main Folder Overview

| Folder | Contents |
|---|---|
| `01_Final_Thesis` | Final thesis document files in PDF and DOCX format. |
| `02_Webots_Simulation_Project` | Webots simulation project with worlds, controllers, protos, meshes, project files, and RL models used inside Webots. |
| `03_Reinforcement_Learning_Code` | Separate PPO and SAC reinforcement learning implementation folders, plus utilities. |
| `04_Real_World_Deployment_Code` | Raspberry Pi deployment scripts, Arduino actuator controller, configuration files, camera/perception scripts, manual/calibration scripts, and autonomous inference scripts. |
| `05_Trained_Models` | Trained PPO and SAC model `.zip` files. |
| `06_Results_Logs_and_Graphs` | PPO training logs, PPO and SAC deterministic evaluation logs, combined Webots evaluation summaries, and final thesis figures. |
| `07_Photos_and_Videos` | Photos and videos of the physical car, physical track, Webots runs, real-world testing, and build/setup media. |
| `08_References` | Local PDF copies of papers and sources used in the bibliography/reference list. |

## System Architecture Summary

The thesis package documents a sim-to-real autonomous miniature RC racing system. The development workflow uses a Webots simulation environment for reinforcement learning, with PPO and SAC policies trained and evaluated in simulation. The real-world deployment is represented by Raspberry Pi scripts for autonomous control and perception, an OAK-D Lite camera for visual input, and an Arduino-based actuator controller for steering servo and ESC commands.

In practical terms, the package connects:

- Webots simulation environment and world files.
- PPO and SAC reinforcement learning training and evaluation code.
- Trained policy model files.
- Raspberry Pi autonomous deployment scripts.
- OAK-D Lite camera and perception utilities.
- Arduino actuator control for the steering servo and ESC.
- Logs, figures, photos, and videos that support the thesis evidence.

## Notes for Reviewers

The package is arranged for review rather than execution. Some files are supporting or optional, such as calibration scripts, manual test scripts, older test files, duplicate model copies, and extra media. The documentation files in this package identify the main evidence while preserving the original project structure and filenames.
