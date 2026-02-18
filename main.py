"""
Main Entry Point for RC Car Control System
Manages all threads and coordinates the overall system
"""

import config
from vehicle_logic import VehicleLogic
from motor_driver import MotorSteeringDriver
from keyboard_input import keyboard_input_thread
from display_output import output_display_thread


def motor_steering_control_thread(kbd_queue, msg_queue, run_flag):
    """
    Main control thread that coordinates vehicle logic and motor control
    
    Args:
        kbd_queue: Queue containing keyboard commands
        msg_queue: Queue for status messages
        run_flag: Flag to signal thread shutdown
    
    This is the heart of the control system - it:
    1. Reads keyboard commands
    2. Updates vehicle logic
    3. Calculates speed/steering
    4. Sends commands to motors
    """
    
    # ========================================
    # INITIALIZE COMPONENTS
    # ========================================
    
    # Create the brain (vehicle logic)
    vehicle_logic = VehicleLogic(msg_queue)
    
    # Create the muscles (motor driver)
    motor_steering_driver = MotorSteeringDriver(msg_queue)
    
    # Get initial state and set motors
    speed, steering = vehicle_logic.get_next_speed_steering_data()
    motor_steering_driver.set_speed_steering(speed, steering)
    
    msg_queue.place_on_queue_non_blocking("Control thread started")
    
    
    # ========================================
    # MAIN CONTROL LOOP
    # ========================================
    
    loop until run_flag says stop:
        
        # Get the next keyboard command (non-blocking)
        input_character = kbd_queue.retrieve_character_from_queue_non_blocking()
        
        # If we got a character, update the vehicle logic
        if input_character is not None:
            vehicle_logic.update_vehicle_logic_kbd(input_character)
        
        # Calculate the next speed and steering commands
        speed, steering = vehicle_logic.get_next_speed_steering_data()
        
        # Send commands to the motor and steering
        motor_steering_driver.set_speed_steering(speed, steering)
        
        # Sleep to maintain consistent loop timing (e.g., 50Hz = 20ms)
        sleep(config.CONTROL_LOOP_SLEEP_TIME)
    
    
    # ========================================
    # CLEAN SHUTDOWN
    # ========================================
    
    msg_queue.place_on_queue_non_blocking("Control thread shutting down")
    
    # Stop the motor and center steering
    motor_steering_driver.stop()


def master_vehicle_process():
    """
    Master process that manages all threads and coordinates startup/shutdown
    
    This is the top-level function that:
    1. Creates all queues
    2. Starts all threads
    3. Waits for quit command
    4. Shuts everything down gracefully
    """
    
    # ========================================
    # INITIALIZE SYSTEM
    # ========================================
    
    # Create the run flag for controlling threads
    run_flag = initialize_flag_for_controlling_threads()
    
    
    # ========================================
    # START OUTPUT DISPLAY THREAD
    # ========================================
    
    # Create message queue for display output
    msg_queue = create_new_message_queue()
    
    # Create and start the display thread
    display_thread = create_new_thread(
        target=output_display_thread,
        args=(msg_queue,)
    )
    display_thread.start()
    
    
    # ========================================
    # START MOTOR CONTROL THREAD
    # ========================================
    
    # Create keyboard command queue
    kbd_queue = create_new_keyboard_command_queue()
    
    # Create and start the motor control thread
    controller_thread = create_new_thread(
        target=motor_steering_control_thread,
        args=(kbd_queue, msg_queue, run_flag)
    )
    controller_thread.start()
    
    
    # ========================================
    # START KEYBOARD INPUT THREAD
    # ========================================
    
    # Create and start the keyboard input thread
    keyboard_thread = create_new_thread(
        target=keyboard_input_thread,
        args=(kbd_queue, msg_queue)
    )
    keyboard_thread.start()
    
    
    # ========================================
    # WAIT FOR USER TO QUIT
    # ========================================
    
    # Wait for the keyboard thread to signal quit
    # (keyboard_thread will exit when user presses 'q')
    keyboard_thread.join()
    
    
    # ========================================
    # SHUTDOWN ALL THREADS
    # ========================================
    
    msg_queue.place_on_queue_non_blocking(config.SHUTDOWN_MESSAGE)
    
    # Signal all threads to stop
    run_flag.reset()
    
    # Give threads time to shut down gracefully
    sleep(config.GRACEFUL_SHUTDOWN_DELAY)
    
    msg_queue.place_on_queue_non_blocking("System shutdown complete")


# ========================================
# PROGRAM ENTRY POINT
# ========================================

if __name__ == "__main__":
    """
    Entry point when running the script directly
    """
    master_vehicle_process()