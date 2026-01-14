import zmq
import json
import time

def monitor():
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://127.0.0.1:5555")
    socket.setsockopt_string(zmq.SUBSCRIBE, "")
    print("Monitoring ZMQ on port 5555...")
    
    with open("zmq_monitor.log", "w") as f:
        while True:
            try:
                msg = socket.recv_string(flags=zmq.NOBLOCK)
                timestamp = time.strftime('%H:%M:%S')
                f.write(f"[{timestamp}] {msg}\n")
                f.flush()
                print(f"[{timestamp}] Received message")
            except zmq.Again:
                time.sleep(0.1)

if __name__ == "__main__":
    monitor()
