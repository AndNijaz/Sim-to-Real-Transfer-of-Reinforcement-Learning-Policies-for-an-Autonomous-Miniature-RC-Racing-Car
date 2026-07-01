# Webots 10-minute deterministic evaluation summary

## Summary metrics

| model         |   wall_time_s |   total_steps |   steps_per_second |   episodes_logged |   completed_or_terminated_episodes |   interrupted_rows |   mean_episode_steps |   median_episode_steps |   max_episode_steps |   mean_episode_duration_s |   max_episode_duration_s |   mean_total_reward |   max_total_reward |   mean_avg_reward_per_step_episode_table |   mean_step_reward |   mean_abs_steering_step |   steering_saturation_abs_gt_0_8_step |   mean_throttle_raw_step |   mean_throttle_clamped_step |   mean_forward_speed_step |   max_forward_speed_step |
|:--------------|--------------:|--------------:|-------------------:|------------------:|-----------------------------------:|-------------------:|---------------------:|-----------------------:|--------------------:|--------------------------:|-------------------------:|--------------------:|-------------------:|-----------------------------------------:|-------------------:|-------------------------:|--------------------------------------:|-------------------------:|-----------------------------:|--------------------------:|-------------------------:|
| PPO prototype |       600.032 |         17559 |            29.2634 |                17 |                                 16 |                  1 |              1032.88 |                   1084 |                1084 |                   35.295  |                  41.4974 |             509.382 |             534.5  |                                   0.4935 |             0.4932 |                   0.6512 |                                0.4846 |                 nan      |                      nan     |                   nan     |                 nan      |
| SAC           |       600.018 |         16297 |            27.1609 |                13 |                                 12 |                  1 |              1253.62 |                   1500 |                1500 |                   46.1542 |                  66.368  |            3495.97  |            4302.78 |                                   2.7569 |             2.7887 |                   0.4058 |                                0.1151 |                   0.8001 |                        0.801 |                     0.493 |                   0.7902 |


## Termination counts

| model         | termination_reason        |   count |
|:--------------|:--------------------------|--------:|
| PPO prototype | boundary_or_stuck         |      16 |
| PPO prototype | interrupted_or_time_limit |       1 |
| SAC           | interrupted_or_time_limit |       1 |
| SAC           | max_steps_timeout         |      10 |
| SAC           | red_blue_boundary         |       2 |


## Notes

- PPO log is from the earlier `best_model_ppo.zip` prototype script, not the final `ppo_buggy_final.zip` BuggyEnv model.
- SAC log is from `best_model_sac.zip` and matches the SAC Webots evaluation setup.
- PPO termination reason is inferred from reward because the older PPO environment does not return a detailed `info` dictionary.
- SAC termination reason is directly logged by the patched evaluation environment.