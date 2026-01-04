# Quick Start Guide for 3dviewer and 3drecon Integration

## Installation (Do this ONCE in each project)

### In your 3dviewer project:
```bash
cd c:\code\antigravity\3dviewer
pip install -e c:\code\antigravity\zmq_communication
```

### In your 3drecon project:
```bash
cd c:\code\antigravity\3drecon
pip install -e c:\code\antigravity\zmq_communication
```

## Basic Import

```python
from acquila_zmq import AcquilaServer, AcquilaClient
```

## Minimal Working Example

### Server (in 3drecon or standalone):
```python
from acquila_zmq import AcquilaServer
import threading

server = AcquilaServer()
thread = threading.Thread(target=server.start, daemon=True)
thread.start()
print("Server running...")
```

### Client (in 3dviewer or any other app):
```python
from acquila_zmq import AcquilaClient

client = AcquilaClient()

# Send a command
response = client.send_command(
    component="my_component",
    command="do_something",
    wait_for="ACK"
)

print(f"Response: {response.get('reply')}")
```

### Component (listens for commands):
```python
from acquila_zmq import AcquilaClient

def handle_command(client, command_data):
    cmd = command_data.get("command")
    
    if cmd == "do_something":
        # Send progress updates
        client.send_feedback(command_data, "Starting...")
        # ... do work ...
        client.send_feedback(command_data, "50% done...")
        # ... more work ...
        return "Completed successfully!"
    
    return "Unknown command"

client = AcquilaClient()
client.listen_and_process("my_component", handle_command)
```

## Testing the Installation

Run this to verify it works:

```bash
python -c "from acquila_zmq import AcquilaServer, AcquilaClient; print('✓ Installation successful!')"
```

## Next Steps

1. Read `USAGE.md` for detailed examples
2. Check `examples/` folder for working code
3. Integrate into your 3dviewer and 3drecon projects

## Common Patterns

### Pattern 1: 3drecon as Server, 3dviewer as Client
- 3drecon runs `AcquilaServer()` and listens for reconstruction commands
- 3dviewer uses `AcquilaClient()` to send commands and receive updates

### Pattern 2: Bidirectional Communication
- Both applications run a server AND client
- They can send commands to each other
- Useful for synchronized updates

### Pattern 3: Multiple Components
- One server, multiple clients
- Each client has a unique component name
- Server relays messages between all clients
