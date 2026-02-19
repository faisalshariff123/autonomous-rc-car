from pynput import keyboard
from queue import Full, Empty
import config

def keyboard_input_thread(kbd_queue, msg_queue):
    """
    Continuously listens for keyboard input
    """
    
    msg_queue.put("RC Car Control System Starting...")
    msg_queue.put("Press 'q' to quit")
    
    def on_press(key):

        try:
            input_character = key.char
            
        except AttributeError:

            if key == keyboard.Key.space:
                input_character = ' '
            else:
                # Ignore special keys silently
                return

        try:
            if input_character == 'w':
                kbd_queue.put_nowait(input_character)
                msg_queue.put_nowait("Command: FORWARD")
                
            elif input_character == 's':
                kbd_queue.put_nowait(input_character)
                msg_queue.put_nowait("Command: BACKWARD")
                
            elif input_character == 'a':
                kbd_queue.put_nowait(input_character)
                msg_queue.put_nowait("Command: LEFT")
                
            elif input_character == 'd':
                kbd_queue.put_nowait(input_character)
                msg_queue.put_nowait("Command: RIGHT")
                
            elif input_character == ' ':
                kbd_queue.put_nowait(input_character)
                msg_queue.put_nowait("Command: STOP")
                
            elif input_character == 'q':
                msg_queue.put_nowait("Quit command received")
                return False  # Stop listener
                
            else:
                msg_queue.put_nowait(f"Unknown key: {input_character}")
                
        except Full:
            # Queue is full - its showing a key press dropped ALERT
            msg_queue.put_nowait("Warning: Command queue full, input ignored")
    
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join() #waits here until the listener is stopped (when 'q' is pressed) but dosent block the main thread, allowing it to continue processing other tasks while listening for keyboard input