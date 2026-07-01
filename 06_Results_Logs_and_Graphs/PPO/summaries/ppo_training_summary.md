# PPO Training Graph Summary

Source event file: `events.out.tfevents.1776003163.MARFs-MacBook-Air.local.39557.0`

This is the longest PPO TensorBoard scalar log with rollout metrics. It reaches 1,001,472 timesteps and contains reward, episode length, FPS, explained variance, policy standard deviation, and value loss scalars.

| Metric | First | Final | Peak/Range |
|---|---:|---:|---:|
| Mean episode reward | -0.1316 | 379.3723 | min -0.1316, max 546.6064 |
| Mean episode length | 123.5714 | 170.3100 | min 123.5714, max 266.2700 |
| FPS | 134.0000 | 102.0000 | min 100.0000, max 134.0000 |
| Explained variance | -0.0005 | 0.9066 | min -1.3380, max 0.9685 |
| Policy std | 1.0026 | 0.3934 | min 0.3818, max 1.2031 |
| Value loss | 420.7999 | 0.3023 | min 0.0803, max 3676.4832 |

Suggested thesis interpretation: PPO training shows clear improvement in the logged simulation run, with mean episode reward increasing from approximately -0.13 to 379.37 and peaking at 546.61. Mean episode length also increases from approximately 123.57 steps to 170.31 steps, peaking at 266.27 steps.
