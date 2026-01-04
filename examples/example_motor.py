import time
from acquila_zmq import AcquilaClient

def motor_logic(client, command_data):
    """
    Logic for the motor. 
    Accepts 'client' to send feedback updates.
    """
    cmd = command_data.get("command")
    
    if cmd == "move_long":
        # Simulate a long action (e.g. 3 seconds)
        # Send FDB events every second
        for i in range(1, 4):
            time.sleep(1)
            client.send_feedback(command_data, f"Moving... {i}/3 sec")
        return "Position Reached"
    
    elif cmd == "status_get":
        # Returns TRUE or FALSE for the Repeat Until test
        # Let's toggle it based on seconds being even/odd for testing
        is_ready = "TRUE" if int(time.time()) % 2 == 0 else "FALSE"
        return is_ready

    else:
        return "Unknown Command"

# Start the component
client = AcquilaClient()
client.listen_and_process(physical_name="motor_X", callback_function=motor_logic)
