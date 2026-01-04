"""
Simple test to verify the acquila_zmq library is properly installed and working.
Run this script to test the installation.
"""

import sys
import time
import threading

try:
    from acquila_zmq import AcquilaServer, AcquilaClient, __version__
    print(f"✓ Import successful! Version: {__version__}")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    print("\nPlease install the library first:")
    print("  pip install -e c:\\code\\antigravity\\zmq_communication")
    sys.exit(1)

def test_communication():
    """Test basic server-client communication"""
    print("\n--- Testing Server-Client Communication ---")
    
    # Start server in background
    print("Starting server...")
    server = AcquilaServer()
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    time.sleep(1)  # Give server time to start
    
    # Create component that listens for commands
    print("Starting component listener...")
    def component_logic(client, command_data):
        cmd = command_data.get("command")
        if cmd == "test_command":
            client.send_feedback(command_data, "Processing...")
            time.sleep(0.1)
            return "Test successful!"
        return "Unknown command"
    
    component_client = AcquilaClient()
    component_thread = threading.Thread(
        target=component_client.listen_and_process,
        args=("test_component", component_logic),
        daemon=True
    )
    component_thread.start()
    time.sleep(0.5)  # Give component time to start listening
    
    # Send command from script client
    print("Sending test command...")
    script_client = AcquilaClient()
    response = script_client.send_command(
        component="test_component",
        command="test_command",
        wait_for="ACK",
        timeout_ms=3000
    )
    
    if response and response.get("reply") == "Test successful!":
        print("✓ Communication test PASSED!")
        print(f"  Response: {response.get('reply')}")
        return True
    else:
        print("✗ Communication test FAILED!")
        print(f"  Response: {response}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Acquila ZMQ Library - Installation Test")
    print("=" * 50)
    
    success = test_communication()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ All tests PASSED!")
        print("\nYou can now use this library in your projects:")
        print("  from acquila_zmq import AcquilaServer, AcquilaClient")
    else:
        print("✗ Tests FAILED!")
        print("\nPlease check the error messages above.")
    print("=" * 50)
    
    # Keep alive for a moment to see results
    time.sleep(1)
