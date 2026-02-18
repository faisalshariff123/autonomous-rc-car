"""
Keyboard Input Thread
Collects user character input from the keyboard
Sends commands to kbd_queue and status messages to msg_queue
Runs as a separate thread
"""

import config

def keyboard_input_thread(kbd_queue, msg_queue):
    """
    Continuously listens for keyboard input and processes control commands
    
    Args:
        kbd_queue: Queue for sending control characters to motor thread
        msg_queue: Queue for sending status messages to display thread
    
    Exits when user presses the quit key (defined in config)
    """
    
    # Send startup message
    msg_queue.place_on_queue_non_blocking(config.STARTUP_MESSAGE)
    msg_queue.place_on_queue_non_blocking(config.QUIT_COMMAND_MESSAGE)
    
    loop forever:
        # Wait for keyboard character input (blocking call)
        input_character = block_waiting_to_receive_keyboard_character_input()
        
        # Check if this is a meaningful control character
        if input_character == config.KEY_FORWARD:
            kbd_queue.place_on_queue_non_blocking(input_character)
            msg_queue.place_on_queue_non_blocking("Command: FORWARD")
            
        elif input_character == config.KEY_BACKWARD:
            kbd_queue.place_on_queue_non_blocking(input_character)
            msg_queue.place_on_queue_non_blocking("Command: BACKWARD")
            
        elif input_character == config.KEY_LEFT:
            kbd_queue.place_on_queue_non_blocking(input_character)
            msg_queue.place_on_queue_non_blocking("Command: LEFT")
            
        elif input_character == config.KEY_RIGHT:
            kbd_queue.place_on_queue_non_blocking(input_character)
            msg_queue.place_on_queue_non_blocking("Command: RIGHT")
            
        elif input_character == config.KEY_STOP:
            kbd_queue.place_on_queue_non_blocking(input_character)
            msg_queue.place_on_queue_non_blocking("Command: STOP")
            
        elif input_character == config.KEY_QUIT:
            msg_queue.place_on_queue_non_blocking("Quit command received")
            break
            
        else:
            # Unrecognized key - send informational message
            msg_queue.place_on_queue_non_blocking(f"Unknown key: {input_character}")