import zmq
import json
import uuid
import time

# Default ports
DEFAULT_OUTBOUND_PORT = 5555
DEFAULT_INBOUND_PORT = 5556

class AcquilaServer:
    """
    Emulates the Acquila Main Program (Server).
    No changes needed here from the previous version.
    """
    def __init__(self, outbound_port=DEFAULT_OUTBOUND_PORT, inbound_port=DEFAULT_INBOUND_PORT):
        self.context = zmq.Context()
        self.socket_out = self.context.socket(zmq.PUB)
        self.socket_out.bind(f"tcp://*:{outbound_port}")
        self.socket_in = self.context.socket(zmq.SUB)
        self.socket_in.bind(f"tcp://*:{inbound_port}")
        self.socket_in.setsockopt_string(zmq.SUBSCRIBE, "") 
        self.running = False
        print(f"Acquila Server started on {inbound_port} (in) / {outbound_port} (out)")

    def start(self):
        self.running = True
        try:
            while self.running:
                try:
                    msg = self.socket_in.recv_string()
                    # Simply relay the message to all subscribers
                    self.socket_out.send_string(msg)
                except zmq.ZMQError:
                    break
        except KeyboardInterrupt:
            print("Server stopping...")
        finally:
            self.socket_out.close()
            self.socket_in.close()
            self.context.term()

class AcquilaClient:
    def __init__(self, server_ip="127.0.0.1", outbound_port=DEFAULT_OUTBOUND_PORT, inbound_port=DEFAULT_INBOUND_PORT):
        self.context = zmq.Context()
        self.uuid = str(uuid.uuid4())
        
        # Socket to SEND commands (connects to Server Inbound)
        self.socket_send = self.context.socket(zmq.PUB)
        self.socket_send.connect(f"tcp://{server_ip}:{inbound_port}")
        
        # Socket to RECEIVE commands (connects to Server Outbound)
        self.socket_recv = self.context.socket(zmq.SUB)
        self.socket_recv.connect(f"tcp://{server_ip}:{outbound_port}")
        self.socket_recv.setsockopt_string(zmq.SUBSCRIBE, "") 
        
        time.sleep(0.5) # Allow connection time

    def _create_payload(self, component, comp_phys, command, arg1, arg2, reply, reply_type, uuid_val=None):
        return {
            "component": component,
            "comp_phys": comp_phys,
            "command": command,
            "arg1": arg1,
            "arg2": arg2,
            "reply": reply,
            "reply type": reply_type, 
            "comp_type": "python_client",
            "tick count": int(time.time() * 1000),
            "UUID": uuid_val if uuid_val else str(uuid.uuid4())
        }

    def send_feedback(self, original_command_data, feedback_msg):
        """
        Sends an FDB (Feedback) event. 
        Used by a component to report progress during execution[cite: 36].
        """
        payload = self._create_payload(
            component=original_command_data.get("component"),
            comp_phys=original_command_data.get("comp_phys"),
            command=original_command_data.get("command"),
            arg1=original_command_data.get("arg1"),
            arg2=original_command_data.get("arg2"),
            reply=feedback_msg,
            reply_type="FDB", # [cite: 42]
            uuid_val=original_command_data.get("UUID") # Must match original UUID
        )
        self.socket_send.send_string(json.dumps(payload))
        print(f"[COMPONENT] Sent Feedback: {feedback_msg}")

    def send_command(self, component, command, arg1="", arg2="", wait_for="ACK", timeout_ms=5000):
        """
        Standard command sending.
        """
        my_uuid = str(uuid.uuid4())
        payload = self._create_payload(component, "", command, arg1, arg2, "", "SENT", my_uuid)
        
        self.socket_send.send_string(json.dumps(payload))
        print(f"[SCRIPT] Sent: {command} (UUID: {my_uuid})")

        if wait_for == "no wait": return None

        start_time = time.time() * 1000
        while (time.time() * 1000 - start_time) < timeout_ms:
            try:
                rec_string = self.socket_recv.recv_string(flags=zmq.NOBLOCK)
                rec_json = json.loads(rec_string)

                if rec_json.get("UUID") == my_uuid:
                    r_type = rec_json.get("reply type")
                    
                    # If we receive feedback while waiting for ACK, print it but don't exit
                    if r_type == "FDB":
                        print(f"   <-- Feedback received: {rec_json.get('reply')}")
                        if wait_for == "FDB": return rec_json
                    
                    elif r_type == wait_for:
                        return rec_json
                    
                    # Handle finishing
                    elif wait_for == "ACK" and r_type == "ACK":
                        return rec_json
                        
            except zmq.Again:
                time.sleep(0.01)
        
        print("Timeout.")
        return None

    def send_command_until(self, component, command, expected_feedback, interval_ms=500, timeout_ms=10000):
        """
        Implements the REPEAT UNTIL structure[cite: 79].
        Repeats a command until the reply matches 'expected_feedback'.
        """
        print(f"[SCRIPT] REPEAT UNTIL '{expected_feedback}' cmd: {command}...")
        start_time = time.time() * 1000
        
        while (time.time() * 1000 - start_time) < timeout_ms:
            # Send the command and wait for immediate ACK/Result
            response = self.send_command(component, command, wait_for="ACK", timeout_ms=1000)
            
            if response:
                reply_content = response.get("reply")
                # Strict case-sensitive match as per [cite: 92]
                if reply_content == expected_feedback:
                    print(f"[SCRIPT] Target feedback '{expected_feedback}' reached!")
                    return True
                else:
                    print(f"   ... got '{reply_content}', retrying...")
            
            time.sleep(interval_ms / 1000.0)
            
        print("[SCRIPT] REPEAT UNTIL Timeout.")
        return False

    def listen_and_process(self, physical_name, callback_function):
        """
        Listening loop for components.
        Callback signature: callback(client_instance, command_data)
        """
        print(f"Listening for commands for: {physical_name}...")
        while True:
            msg = self.socket_recv.recv_string()
            data = json.loads(msg)
            
            if data.get("reply type") == "SENT":
                tgt_phys = data.get("comp_phys")
                tgt_abs = data.get("component")
                
                if tgt_phys == physical_name or tgt_abs == physical_name:
                    # 1. Send RCV [cite: 35]
                    ack_payload = data.copy()
                    ack_payload["reply type"] = "RCV"
                    self.socket_send.send_string(json.dumps(ack_payload))
                    
                    # 2. Execute Logic (Pass self so callback can send FDB)
                    try:
                        result = callback_function(self, data)
                        ack_payload["reply type"] = "ACK" # [cite: 36]
                        ack_payload["reply"] = str(result)
                    except Exception as e:
                        ack_payload["reply type"] = "ERR" # [cite: 37]
                        ack_payload["reply"] = str(e)
                    
                    # 3. Send Final ACK/ERR
                    self.socket_send.send_string(json.dumps(ack_payload))