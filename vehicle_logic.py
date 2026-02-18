"""
Vehicle Logic - The Brain
Manages vehicle state and calculates speed/steering commands
Converts keyboard input into normalized speed and steering values
"""

import config

class VehicleLogic:
    """
    Manages the internal state of the vehicle and calculates control commands
    
    Attributes:
        msg_queue: Queue for sending status messages
        current_speed: Current speed state (-1.0 to +1.0)
        current_steering: Current steering state (-1.0 to +1.0)
    """
    
    def __init__(self, msg_queue):
        """
        Initialize the vehicle logic with default state
        
        Args:
            msg_queue: Queue for sending status messages
        """
        self.msg_queue = msg_queue
        self.current_speed = 0.0
        self.current_steering = 0.0
        
        # Send initialization message
        self.msg_queue.place_on_queue_non_blocking("VehicleLogic initialized")
    
    
    def update_vehicle_logic_kbd(self, input_character):
        """
        Update the vehicle internal state based on keyboard input
        
        Args:
            input_character: The key pressed by the user
        
        Updates:
            self.current_speed: Based on forward/backward commands
            self.current_steering: Based on left/right commands
        """
        
        # Handle forward command
        if input_character == config.KEY_FORWARD:
            # Increase speed incrementally
            self.current_speed = self.current_speed + 0.2
            
            # Ensure we don't exceed maximum
            if self.current_speed > config.MAX_SPEED:
                self.current_speed = config.MAX_SPEED
                
            self.msg_queue.place_on_queue_non_blocking(
                f"Speed increased to {self.current_speed:.2f}"
            )
        
        # Handle backward command
        elif input_character == config.KEY_BACKWARD:
            # Decrease speed incrementally
            self.current_speed = self.current_speed - 0.2
            
            # Ensure we don't exceed minimum (reverse limit)
            if self.current_speed < config.MIN_SPEED:
                self.current_speed = config.MIN_SPEED
                
            self.msg_queue.place_on_queue_non_blocking(
                f"Speed decreased to {self.current_speed:.2f}"
            )
        
        # Handle left turn command
        elif input_character == config.KEY_LEFT:
            # Turn more to the left
            self.current_steering = self.current_steering - 0.3
            
            # Ensure we don't exceed maximum left
            if self.current_steering < config.MIN_STEERING:
                self.current_steering = config.MIN_STEERING
                
            self.msg_queue.place_on_queue_non_blocking(
                f"Steering LEFT: {self.current_steering:.2f}"
            )
        
        # Handle right turn command
        elif input_character == config.KEY_RIGHT:
            # Turn more to the right
            self.current_steering = self.current_steering + 0.3
            
            # Ensure we don't exceed maximum right
            if self.current_steering > config.MAX_STEERING:
                self.current_steering = config.MAX_STEERING
                
            self.msg_queue.place_on_queue_non_blocking(
                f"Steering RIGHT: {self.current_steering:.2f}"
            )
        
        # Handle stop command
        elif input_character == config.KEY_STOP:
            # Emergency stop - set everything to zero
            self.current_speed = 0.0
            self.current_steering = 0.0
            
            self.msg_queue.place_on_queue_non_blocking(
                "EMERGENCY STOP - All systems halted"
            )
    
    
    def get_next_speed_steering_data(self):
        """
        Calculate and return the next speed and steering commands
        
        Returns:
            tuple: (speed, steering) both in range [-1.0 to +1.0]
        
        This is where more complex logic could be added:
        - Gradual acceleration/deceleration
        - Speed-dependent steering limits
        - Traction control
        - Drift mode, etc.
        """
        
        # For now, simply return the current state
        # In a more advanced version, this could implement:
        # - Smooth ramping (gradual speed changes)
        # - Physics simulation
        # - Autonomous driving logic
        
        speed = self.current_speed
        steering = self.current_steering
        
        return speed, steering