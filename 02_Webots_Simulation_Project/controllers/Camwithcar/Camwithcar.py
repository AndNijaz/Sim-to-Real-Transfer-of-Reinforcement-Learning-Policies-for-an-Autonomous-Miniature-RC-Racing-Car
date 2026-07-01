import math
from controller import Robot, Keyboard

robot = Robot()
timestep = int(robot.getBasicTimeStep())

keyboard = Keyboard()
keyboard.enable(timestep)

# --- VEHICLE SPECS ---
TRACK_WIDTH = 0.195
WHEELBASE = 0.253
MAX_STEER = 0.55

# --- MOTORS ---
steer_fl = robot.getDevice('steer_fl')
steer_fr = robot.getDevice('steer_fr')
drive_fl = robot.getDevice('drive_fl')
drive_fr = robot.getDevice('drive_fr')
drive_rl = robot.getDevice('drive_rl')
drive_rr = robot.getDevice('drive_rr')

drive_motors = [drive_fl, drive_fr, drive_rl, drive_rr]
for motor in drive_motors:
    motor.setPosition(float('inf'))
    motor.setVelocity(0.0)

steer_fl.setPosition(0.0)
steer_fr.setPosition(0.0)

# --- SENSORS ---
camera = robot.getDevice('oak_d_rgb')
camera.enable(timestep)

imu = robot.getDevice('imu')
imu.enable(timestep)

accelerometer = robot.getDevice('accelerometer')
accelerometer.enable(timestep)

gyro = robot.getDevice('gyro')
gyro.enable(timestep)

current_steering = 0.0

# Enable Stereo Cameras
left_camera = robot.getDevice('oak_d_left')
left_camera.enable(timestep)

right_camera = robot.getDevice('oak_d_right')
right_camera.enable(timestep)

while robot.step(timestep) != -1:
    # 1. READ TELEMETRY
    rpy = imu.getRollPitchYaw()  # Returns [roll, pitch, yaw]
    accel = accelerometer.getValues()  # Returns [x, y, z] in m/s^2
    omega = gyro.getValues()  # Returns [x, y, z] in rad/s

    # Print to console (formatted for readability)
    print(f"--- IMU DATA ---")
    print(f"Roll: {rpy[0]:.2f} | Pitch: {rpy[1]:.2f} | Yaw: {rpy[2]:.2f}")
    print(f"Accel (z): {accel[2]:.2f} m/s^2") # Check gravity/vertical bumps
    
# 2. KEYBOARD LOGIC
    key = keyboard.getKey()
    base_speed = 0.0
    steering_target = 0.0  # New target-based logic
    
    if key != -1:
        while key != -1:
            if key == Keyboard.UP:
                base_speed = 25.0
            elif key == Keyboard.DOWN:
                base_speed = -25.0
            
            # Increase the increment to 0.15 for fast response
            # Or set it directly to MAX_STEER for instant response
            if key == Keyboard.LEFT:
                steering_target = MAX_STEER 
            elif key == Keyboard.RIGHT:
                steering_target = -MAX_STEER
            key = keyboard.getKey()

    # Smooth but FAST transition (Linear Interpolation)
    # This makes the servo move at a realistic 25g speed
    alpha = 0.3  # Increase this to 1.0 for instant snapping
    current_steering = (alpha * steering_target) + ((1.0 - alpha) * current_steering)

    # 3. KINEMATICS
    if abs(current_steering) > 0.001:
        turn_radius = WHEELBASE / math.tan(current_steering)
        angle_fl = math.atan(WHEELBASE / (turn_radius - (TRACK_WIDTH / 2)))
        angle_fr = math.atan(WHEELBASE / (turn_radius + (TRACK_WIDTH / 2)))
        speed_left = base_speed * ((turn_radius - (TRACK_WIDTH / 2)) / turn_radius)
        speed_right = base_speed * ((turn_radius + (TRACK_WIDTH / 2)) / turn_radius)
    else:
        angle_fl = angle_fr = 0.0
        speed_left = speed_right = base_speed

    # 4. APPLY COMMANDS
    steer_fl.setPosition(angle_fl)
    steer_fr.setPosition(angle_fr)
    drive_fl.setVelocity(speed_left)
    drive_rl.setVelocity(speed_left)
    drive_fr.setVelocity(speed_right)
    drive_rr.setVelocity(speed_right)