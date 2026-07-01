import math
from controller import Robot, Keyboard

# 1. Initialize the Robot and Timestep
robot = Robot()
timestep = int(robot.getBasicTimeStep())

# 2. Initialize Keyboard
keyboard = Keyboard()
keyboard.enable(timestep)

# --- VEHICLE SPECIFICATIONS ---
# Measurements derived from the WLToys 12428 specs
TRACK_WIDTH = 0.195  # meters (Distance between left/right wheels)
WHEELBASE = 0.253    # meters (Distance between front/rear axles)
MAX_STEER = 0.55     # Approx 32 degrees in radians

# 3. Get all 6 Motors
steer_fl = robot.getDevice('steer_fl')
steer_fr = robot.getDevice('steer_fr')

drive_fl = robot.getDevice('drive_fl')
drive_fr = robot.getDevice('drive_fr')
drive_rl = robot.getDevice('drive_rl')
drive_rr = robot.getDevice('drive_rr')

# 4. Configure Drive Motors for continuous rotation
drive_motors = [drive_fl, drive_fr, drive_rl, drive_rr]
for motor in drive_motors:
    motor.setPosition(float('inf'))
    motor.setVelocity(0.0)

# 5. Configure Steer Motors
steer_fl.setPosition(0.0)
steer_fr.setPosition(0.0)

current_steering = 0.0
print("4WD Ackermann Controller Started! Use ARROW KEYS to drive.")

# 6. Main Simulation Loop
while robot.step(timestep) != -1:
    # Read the first key from the buffer
    key = keyboard.getKey()
    
    # We reset base_speed every frame to 0, 
    # but we only update it if a key is found in the buffer.
    base_speed = 0.0
    steering_pressed = False
    
    # Drain the keyboard buffer to find ALL currently pressed keys
    while key != -1:
        # --- THROTTLE (Up/Down) ---
        if key == Keyboard.UP:
            base_speed = 25.0  # rad/s
        elif key == Keyboard.DOWN:
            base_speed = -25.0
            
        # --- STEERING (Left/Right) ---
        if key == Keyboard.LEFT:
            current_steering += 0.02
            steering_pressed = True
        elif key == Keyboard.RIGHT:
            current_steering -= 0.02
            steering_pressed = True
            
        # Move to the next key in the buffer
        key = keyboard.getKey()
        
    # If no steering keys are held, apply auto-centering
    if not steering_pressed:
        current_steering *= 0.8 
        
    # Clamp steering to physical limit (32 degrees)
    current_steering = max(min(current_steering, MAX_STEER), -MAX_STEER)

    # --- ACKERMANN & DIFFERENTIAL KINEMATICS ---
    if abs(current_steering) > 0.001:
        # R = L / tan(theta)
        turn_radius = WHEELBASE / math.tan(current_steering)
        
        # Inner wheel turns sharper
        angle_fl = math.atan(WHEELBASE / (turn_radius - (TRACK_WIDTH / 2)))
        angle_fr = math.atan(WHEELBASE / (turn_radius + (TRACK_WIDTH / 2)))
        
        # Electronic Differential (Outer wheels spin faster)
        # speed = v * (R_wheel / R_center)
        speed_left = base_speed * ((turn_radius - (TRACK_WIDTH / 2)) / turn_radius)
        speed_right = base_speed * ((turn_radius + (TRACK_WIDTH / 2)) / turn_radius)
        
    else:
        # Driving straight
        angle_fl = 0.0
        angle_fr = 0.0
        speed_left = base_speed
        speed_right = base_speed

    # --- APPLY COMMANDS ---
    steer_fl.setPosition(angle_fl)
    steer_fr.setPosition(angle_fr)
    
    drive_fl.setVelocity(speed_left)
    drive_rl.setVelocity(speed_left)
    drive_fr.setVelocity(speed_right)
    drive_rr.setVelocity(speed_right)