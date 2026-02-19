"""
Configuration file for RC Car Control System
Contains all calibration values and constants
"""

# ============================================
# PWM CALIBRATION VALUES FOR ESC (Motor)
# ============================================
# These values were determined through testing with your specific ESC, these are the pulse widths in microseconds corresponding to different speed commands
NEUTRAL_ZERO_POINT = 1500  # Stopped position (microseconds)
MAX_FWD_POINT = 2000       # Full forward throttle
MAX_REV_POINT = 1000       # Full reverse throttle

# ============================================
# PWM CALIBRATION VALUES FOR STEERING SERVO
# ============================================
STEERING_NOMINAL_CENTER = 1500  # Default center position
STEERING_OFFSET = 0             # Adjustment if servo is not perfectly centered, amount to add to nominal center to get actual center
STEERING_PLUS_MINUS = 190       # Range of movement (+/- from center)

# Calculate actual steering center with offset
STEERING_CENTER = STEERING_NOMINAL_CENTER + STEERING_OFFSET

# ============================================
# SPEED AND STEERING LIMITS
# ============================================
# Valid ranges for normalized values, these will be mapped to PWM values in the motor driver, are the software limits for the control system
MIN_SPEED = -1.0
MAX_SPEED = 1.0
MIN_STEERING = -1.0
MAX_STEERING = 1.0

# ============================================
# CONTROL LOOP TIMING
# ============================================
CONTROL_LOOP_SLEEP_TIME = 0.02  # 20ms = 50Hz update rate, to

# ============================================
# THREAD SHUTDOWN TIMING
# ============================================
GRACEFUL_SHUTDOWN_DELAY = 0.5  # Time to wait for threads to close (seconds)

# ============================================
# KEYBOARD CONTROL KEYS
# ============================================
# Define which keys control what
KEY_FORWARD = 'w'
KEY_BACKWARD = 's'
KEY_LEFT = 'a'
KEY_RIGHT = 'd'
KEY_STOP = ' '  # Spacebar
KEY_QUIT = 'q'

# ============================================
# DISPLAY MESSAGES
# ============================================
STARTUP_MESSAGE = "RC Car Control System Starting..."
SHUTDOWN_MESSAGE = "Shutting down gracefully..."
QUIT_COMMAND_MESSAGE = "Press 'q' to quit"