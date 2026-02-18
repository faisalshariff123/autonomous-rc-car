"""
Motor Steering Driver - The Muscles
Converts normalized speed/steering values to PWM signals
Sends signals to ESC (Electronic Speed Controller) and steering servo
"""

import config

class MotorSteeringDriver:
    """
    Handles low-level PWM control for motor and steering servo
    
    Attributes:
        msg_queue: Queue for sending status messages
    """
    
    def __init__(self, msg_queue):
        """
        Initialize the motor and steering driver
        
        Args:
            msg_queue: Queue for sending status messages
        """
        self.msg_queue = msg_queue
        
        # Initialize GPIO pins and PWM here
        # Example (pseudocode):
        # GPIO.setup(MOTOR_PIN, GPIO.OUT)
        # GPIO.setup(STEERING_PIN, GPIO.OUT)
        # self.motor_pwm = GPIO.PWM(MOTOR_PIN, 50)  # 50Hz
        # self.steering_pwm = GPIO.PWM(STEERING_PIN, 50)
        
        self.msg_queue.place_on_queue_non_blocking(
            "MotorSteeringDriver initialized"
        )
    
    
    def set_speed_steering(self, speed, steering):
        """
        Set the speed and steering by converting to PWM and sending signals
        
        Args:
            speed: Normalized speed value (-1.0 to +1.0)
            steering: Normalized steering value (-1.0 to +1.0)
        
        Process:
            1. Clip values to safe ranges
            2. Map to PWM pulse widths
            3. Send PWM signals to hardware
        """
        
        # ========================================
        # STEP 1: CLIP VALUES TO SAFE RANGES
        # ========================================
        # Ensure speed is within valid range
        if speed > config.MAX_SPEED:
            speed = config.MAX_SPEED
        elif speed < config.MIN_SPEED:
            speed = config.MIN_SPEED
        
        # Ensure steering is within valid range
        if steering > config.MAX_STEERING:
            steering = config.MAX_STEERING
        elif steering < config.MIN_STEERING:
            steering = config.MIN_STEERING
        
        
        # ========================================
        # STEP 2: MAP TO PWM VALUES
        # ========================================
        
        # MAP SPEED: [-1.0, +1.0] → [1000, 2000] microseconds
        # Formula: output = ((input - input_min) / (input_max - input_min)) * (output_max - output_min) + output_min
        
        pwm_speed_pulse = map_value(
            value=speed,
            from_min=config.MIN_SPEED,      # -1.0
            from_max=config.MAX_SPEED,      # +1.0
            to_min=config.MAX_REV_POINT,    # 1000 (reverse)
            to_max=config.MAX_FWD_POINT     # 2000 (forward)
        )
        
        # MAP STEERING: [-1.0, +1.0] → [CENTER-190, CENTER+190]
        pwm_steering_pulse = map_value(
            value=steering,
            from_min=config.MIN_STEERING,   # -1.0
            from_max=config.MAX_STEERING,   # +1.0
            to_min=config.STEERING_CENTER - config.STEERING_PLUS_MINUS,  # ~1310
            to_max=config.STEERING_CENTER + config.STEERING_PLUS_MINUS   # ~1690
        )
        
        
        # ========================================
        # STEP 3: SEND PWM SIGNALS TO HARDWARE
        # ========================================
        
        # Send status message
        self.msg_queue.place_on_queue_non_blocking(
            f"PWM → Speed: {pwm_speed_pulse:.0f}μs, Steering: {pwm_steering_pulse:.0f}μs"
        )
        
        # Apply PWM signals to the ESC and steering servo
        # Example (pseudocode):
        # duty_cycle_motor = pulse_width_to_duty_cycle(pwm_speed_pulse)
        # duty_cycle_steering = pulse_width_to_duty_cycle(pwm_steering_pulse)
        # self.motor_pwm.ChangeDutyCycle(duty_cycle_motor)
        # self.steering_pwm.ChangeDutyCycle(duty_cycle_steering)
        
        apply_pwm_pulse_to_esc(pwm_speed_pulse)
        apply_pwm_pulse_to_steering_servo(pwm_steering_pulse)
    
    
    def stop(self):
        """
        Emergency stop - set all controls to neutral/stopped
        """
        self.msg_queue.place_on_queue_non_blocking("Motor driver STOP called")
        
        # Set speed and steering to zero (stopped, centered)
        self.set_speed_steering(0.0, 0.0)
        
        # Optionally disable PWM outputs
        # self.motor_pwm.stop()
        # self.steering_pwm.stop()


def map_value(value, from_min, from_max, to_min, to_max):
    """
    Map a value from one range to another range (linear interpolation)
    
    Args:
        value: The input value to map
        from_min: Minimum of input range
        from_max: Maximum of input range
        to_min: Minimum of output range
        to_max: Maximum of output range
    
    Returns:
        Mapped value in the output range
    
    Example:
        map_value(0.5, -1.0, 1.0, 1000, 2000) → 1750
    """
    
    # Calculate the percentage of the input range
    input_range = from_max - from_min
    input_percentage = (value - from_min) / input_range
    
    # Apply that percentage to the output range
    output_range = to_max - to_min
    output_value = (input_percentage * output_range) + to_min
    
    return output_value