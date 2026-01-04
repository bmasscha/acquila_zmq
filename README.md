# Acquila ZMQ Communication Library

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub](https://img.shields.io/badge/GitHub-bmasscha%2Facquila__zmq-blue)](https://github.com/bmasscha/acquila_zmq)

A Python library for ZMQ-based communication between Acquila components. Provides a simple server-client architecture with support for feedback, command tracking, and bidirectional messaging.

## Installation

### Option 1: Install from GitHub (Recommended)

Install directly from the GitHub repository:

```bash
pip install git+https://github.com/bmasscha/acquila_zmq.git
```

Or in development/editable mode:
```bash
git clone https://github.com/bmasscha/acquila_zmq.git
cd acquila_zmq
pip install -e .
```

After installation, you can import it in your **3dviewer** and **3drecon** projects:
```python
from acquila_zmq import AcquilaServer, AcquilaClient
```

### Option 2: Install from Local Directory (For local development)

This allows you to use the library in your other projects while still being able to edit it:

```bash
# Navigate to the library directory
cd c:\code\antigravity\zmq_communication

# Install in editable/development mode
pip install -e .
```

### Option 3: Install as a Regular Package

```bash
pip install c:\code\antigravity\zmq_communication
```

### Option 4: Add to requirements.txt

In your **3dviewer** or **3drecon** project's `requirements.txt`:
```
# From GitHub
git+https://github.com/bmasscha/acquila_zmq.git

# Or local development
# -e c:\code\antigravity\zmq_communication

# Or as a regular install
# c:\code\antigravity\zmq_communication
```

### Option 5: From PyPI (when published)
```bash
pip install acquila_zmq
```

## Quick Start

### 1. Start the Server
```python
from acquila_zmq import AcquilaServer

server = AcquilaServer()
server.start()
```

### 2. Create a Component
```python
from acquila_zmq import AcquilaClient

def my_component_logic(client, command_data):
    cmd = command_data.get("command")
    if cmd == "do_something":
        # Send feedback during execution
        client.send_feedback(command_data, "Working...")
        return "Done!"
    return "Unknown Command"

client = AcquilaClient()
client.listen_and_process(physical_name="my_component", callback_function=my_component_logic)
```

### 3. Send Commands
```python
from acquila_zmq import AcquilaClient

client = AcquilaClient()
reply = client.send_command("my_component", "do_something", wait_for="ACK")
print(reply.get('reply'))
```

## Features

- **Server-Client Architecture**: Central server relays messages between components
- **Feedback Support**: Components can send progress updates during long operations
- **REPEAT UNTIL**: Built-in support for polling until a condition is met
- **Timeout Handling**: Configurable timeouts for all operations
- **UUID Tracking**: Every command is tracked with a unique identifier

## Examples

See the `examples/` directory for complete working examples:
- `run_server.py` - Start the message relay server
- `example_motor.py` - Example component with feedback
- `run_script_example.py` - Example script sending commands

## Configuration

Default ports:
- **Outbound (Server → Clients)**: 5555
- **Inbound (Clients → Server)**: 5556

To use custom ports:
```python
server = AcquilaServer(outbound_port=6000, inbound_port=6001)
client = AcquilaClient(server_ip="192.168.1.100", outbound_port=6000, inbound_port=6001)
```

## License

MIT
