"""
Display Output Thread
Centralized handler for displaying status messages to the terminal
Reads messages from a msg_queue and displays them
Runs as a separate thread
"""

def output_display_thread(msg_queue):
    """
    Continuously retrieves and displays messages from the msg_queue
    
    Args:
        msg_queue: Queue object containing messages to display
    
    This function runs in an infinite loop until the program terminates
    """
    
    loop forever:
        # Block and wait until a message arrives
        input_message = msg_queue.retrieve_from_queue_blocking()
        
        # Display the message on the screen
        display(input_message)