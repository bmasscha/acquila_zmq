from acquila_zmq import AcquilaClient

client = AcquilaClient()

print("--- TEST 1: Long Running Command with Feedback ---")
# This will print "Moving... 1/3", "Moving... 2/3" etc. as they arrive
# Increase timeout to 10 seconds since it's a 'long_running' command
reply = client.send_command("motor_X", "move_long", wait_for="ACK", timeout_ms=10000)

if reply:
    print(f"Final Result: {reply.get('reply')}\n")
else:
    print("Command timed out or failed.\n")

print("--- TEST 2: REPEAT UNTIL Structure ---")
# This will keep sending 'status_get' until the motor returns "TRUE"
# This mimics the PDF structure: tube REPEAT UNTIL TRUE status_XReady_get [cite: 88]
success = client.send_command_until(
    component="motor_X", 
    command="status_get", 
    expected_feedback="TRUE"
)

if success:
    print("Script continued after receiving TRUE.")
else:
    print("Script aborted (timeout).")