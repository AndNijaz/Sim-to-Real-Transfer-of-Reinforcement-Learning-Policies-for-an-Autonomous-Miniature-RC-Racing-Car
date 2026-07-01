# Webots Simulation Project

This folder contains the Webots simulation project used to support the thesis evidence. It includes controllers, worlds, protos, meshes, image assets, Webots project files, and RL model files used inside the Webots project.

Important areas:

- `worlds`: Webots world files and related project metadata.
- `controllers`: Webots controller scripts, including PPO and SAC run/training controller folders.
- `protos`: custom Webots proto and mesh assets, including OAK-D Lite and vehicle-related files.
- `STL and Meshes`: additional mesh and image assets.
- `RL Models`: PPO and SAC model files used from inside the Webots project.

Do not rename Webots assets or folders without checking relative paths in the Webots project, because simulation files may depend on exact filenames and locations.
