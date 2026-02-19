"""
Display Output Thread
Centralized handler for displaying status messages to the terminal
Reads messages from a msg_queue and displays them
Runs as a separate thread
"""

def output_display_thread(msg_queue):
    while True:
        input_message = msg_queue.get()
        print(input_message)