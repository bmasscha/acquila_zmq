# Using acquila_zmq in Your Projects

## Integration with 3dviewer and 3drecon

### Step 1: Install the Library

From your **3dviewer** or **3drecon** project directory:

```bash
pip install -e c:\code\antigravity\zmq_communication
```

This installs the library in "editable" mode, meaning changes you make to the `zmq_communication` code will immediately be available in your other projects without reinstalling.

### Step 2: Import in Your Code

```python
from acquila_zmq import AcquilaServer, AcquilaClient
```

## Common Use Cases

### Use Case 1: Running a Server in 3drecon

If your **3drecon** application acts as the central hub:

```python
from acquila_zmq import AcquilaServer

def start_communication_server():
    server = AcquilaServer(outbound_port=5555, inbound_port=5556)
    # Run in a separate thread to avoid blocking
    import threading
    thread = threading.Thread(target=server.start, daemon=True)
    thread.start()
    return server
```

### Use Case 2: Connecting 3dviewer as a Client

If your **3dviewer** needs to send commands or receive updates:

```python
from acquila_zmq import AcquilaClient

class Viewer3D:
    def __init__(self):
        # Connect to the server (could be running in 3drecon)
        self.client = AcquilaClient(server_ip="127.0.0.1")
    
    def send_reconstruction_command(self, params):
        """Send a command to start reconstruction"""
        response = self.client.send_command(
            component="reconstruction_engine",
            command="start_recon",
            arg1=json.dumps(params),
            wait_for="ACK",
            timeout_ms=10000
        )
        return response
    
    def listen_for_updates(self):
        """Listen for reconstruction progress updates"""
        def handle_update(client, command_data):
            cmd = command_data.get("command")
            if cmd == "progress_update":
                progress = command_data.get("arg1")
                self.update_progress_bar(progress)
                return "OK"
            return "Unknown command"
        
        # Run in background thread
        import threading
        thread = threading.Thread(
            target=self.client.listen_and_process,
            args=("viewer_component", handle_update),
            daemon=True
        )
        thread.start()
```

### Use Case 3: Bidirectional Communication

Both applications can act as both server and client:

**In 3drecon:**
```python
from acquila_zmq import AcquilaServer, AcquilaClient
import threading

# Start server for receiving commands
server = AcquilaServer()
server_thread = threading.Thread(target=server.start, daemon=True)
server_thread.start()

# Create client for sending updates
client = AcquilaClient()

def reconstruction_callback(client_instance, command_data):
    """Handle incoming reconstruction requests"""
    cmd = command_data.get("command")
    
    if cmd == "start_recon":
        # Send progress updates during reconstruction
        for i in range(0, 101, 10):
            client_instance.send_feedback(command_data, f"Progress: {i}%")
            # ... do reconstruction work ...
        
        return "Reconstruction complete"
    
    return "Unknown command"

# Listen for commands
listen_thread = threading.Thread(
    target=client.listen_and_process,
    args=("reconstruction_engine", reconstruction_callback),
    daemon=True
)
listen_thread.start()
```

**In 3dviewer:**
```python
from acquila_zmq import AcquilaClient

client = AcquilaClient()

# Send command and wait for completion
response = client.send_command(
    component="reconstruction_engine",
    command="start_recon",
    arg1='{"slices": 512, "algorithm": "FBP"}',
    wait_for="ACK",
    timeout_ms=60000  # 60 seconds
)

print(f"Result: {response.get('reply')}")
```

## Advanced Features

### Polling Until Condition Met

```python
# Keep checking motor status until it reports "idle"
success = client.send_command_until(
    component="motor_controller",
    command="get_status",
    expected_feedback="idle",
    interval_ms=500,
    timeout_ms=30000
)
```

### Custom Ports for Multiple Instances

```python
# Server 1 (for reconstruction)
recon_server = AcquilaServer(outbound_port=5555, inbound_port=5556)

# Server 2 (for motor control)
motor_server = AcquilaServer(outbound_port=6555, inbound_port=6556)

# Clients connect to specific servers
recon_client = AcquilaClient(outbound_port=5555, inbound_port=5556)
motor_client = AcquilaClient(outbound_port=6555, inbound_port=6556)
```

### Remote Communication

```python
# Connect to a server running on another machine
client = AcquilaClient(
    server_ip="192.168.1.100",
    outbound_port=5555,
    inbound_port=5556
)
```

## Best Practices

1. **Always use threading**: Run servers and listeners in separate threads to avoid blocking your main application
2. **Set appropriate timeouts**: Long-running operations should have longer timeouts
3. **Use feedback for progress**: For operations that take time, send feedback messages to keep the client informed
4. **Handle errors gracefully**: Wrap command execution in try-except blocks
5. **Clean shutdown**: Store thread references and properly close connections when your application exits

## Troubleshooting

### Import Error
```
ModuleNotFoundError: No module named 'acquila_zmq'
```
**Solution**: Make sure you've installed the library with `pip install -e c:\code\antigravity\zmq_communication`

### Connection Timeout
```
Timeout.
```
**Solution**: 
- Check that the server is running
- Verify the ports match between server and client
- Increase the timeout value
- Check firewall settings if connecting remotely

### Port Already in Use
```
zmq.error.ZMQError: Address already in use
```
**Solution**: 
- Another instance is already running on that port
- Use different ports for multiple instances
- Kill the existing process or wait for it to release the port
