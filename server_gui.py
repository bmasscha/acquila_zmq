import sys
import json
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTextEdit, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QSplitter)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from acquila_zmq import AcquilaServer, DEFAULT_OUTBOUND_PORT, DEFAULT_INBOUND_PORT

class ServerWorker(QThread):
    message_received = pyqtSignal(dict)
    server_stopped = pyqtSignal()

    def __init__(self, outbound_port, inbound_port):
        super().__init__()
        self.outbound_port = outbound_port
        self.inbound_port = inbound_port
        self.server = None

    def run(self):
        self.server = AcquilaServer(outbound_port=self.outbound_port, inbound_port=self.inbound_port)
        self.server.start(on_message=self.handle_message)
        self.server_stopped.emit()

    def handle_message(self, data):
        self.message_received.emit(data)

    def stop(self):
        if self.server:
            self.server.stop()

class AcquilaServerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Acquila ZMQ Server Control")
        self.resize(1000, 700)
        
        self.worker = None
        self.init_ui()
        
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_queue_table)
        self.refresh_timer.start(500)

        # Auto-start server on launch
        QTimer.singleShot(100, self.start_server)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Controls Area ---
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Inbound Port:"))
        self.in_port_edit = QLineEdit(str(DEFAULT_INBOUND_PORT))
        controls_layout.addWidget(self.in_port_edit)

        controls_layout.addWidget(QLabel("Outbound Port:"))
        self.out_port_edit = QLineEdit(str(DEFAULT_OUTBOUND_PORT))
        controls_layout.addWidget(self.out_port_edit)

        self.toggle_btn = QPushButton("Start Server")
        self.toggle_btn.clicked.connect(self.toggle_server)
        self.toggle_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 5px;")
        controls_layout.addWidget(self.toggle_btn)
        
        main_layout.addLayout(controls_layout)

        # --- Visualization Area (Splitter) ---
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top: Active Queue Table
        queue_container = QWidget()
        queue_layout = QVBoxLayout(queue_container)
        queue_layout.addWidget(QLabel("<b>Active Command Queue</b>"))
        self.queue_table = QTableWidget(0, 6)
        self.queue_table.setHorizontalHeaderLabels(["UUID", "Status", "Component", "Command", "Reply", "Added At"])
        self.queue_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.queue_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn) 
        queue_layout.addWidget(self.queue_table)
        splitter.addWidget(queue_container)

        # Bottom: Communication Log
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.addWidget(QLabel("<b>Communication Log (Tunnel)</b>"))
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.document().setMaximumBlockCount(1000) # Limit history to 1000 messages
        self.log_area.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; font-family: 'Consolas', 'Courier New';")
        log_layout.addWidget(self.log_area)
        splitter.addWidget(log_container)

        main_layout.addWidget(splitter)
        
        # Status Bar
        self.statusBar().showMessage("Ready")

    def toggle_server(self):
        if self.worker and self.worker.isRunning():
            self.stop_server()
        else:
            self.start_server()

    def start_server(self):
        try:
            in_port = int(self.in_port_edit.text())
            out_port = int(self.out_port_edit.text())
        except ValueError:
            self.log_append("Invalid port numbers.")
            return

        self.worker = ServerWorker(out_port, in_port)
        self.worker.message_received.connect(self.handle_server_message)
        self.worker.server_stopped.connect(self.on_server_stop)
        self.worker.start()

        self.toggle_btn.setText("Stop Server")
        self.toggle_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 5px;")
        self.statusBar().showMessage(f"Server Running on {in_port} (in) / {out_port} (out)")
        self.log_append(f"--- Server Started at {time.strftime('%H:%M:%S')} ---")
        
        self.in_port_edit.setEnabled(False)
        self.out_port_edit.setEnabled(False)

    def stop_server(self):
        if self.worker:
            self.worker.stop()
            self.statusBar().showMessage("Stopping Server...")

    def on_server_stop(self):
        self.toggle_btn.setText("Start Server")
        self.toggle_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 5px;")
        self.statusBar().showMessage("Server Stopped")
        self.log_append(f"--- Server Stopped at {time.strftime('%H:%M:%S')} ---")
        
        self.in_port_edit.setEnabled(True)
        self.out_port_edit.setEnabled(True)

    def handle_server_message(self, data):
        # Format JSON for log
        log_entry = json.dumps(data, indent=2)
        self.log_append(log_entry)

    def log_append(self, text):
        self.log_area.append(text)
        # Auto-scroll
        self.log_area.moveCursor(self.log_area.textCursor().MoveOperation.End)

    def update_queue_table(self):
        if not self.worker or not self.worker.server:
            self.queue_table.setRowCount(0)
            return

        now = time.time()
        grace_period = 10.0 # Keep finished commands for 10 seconds
        
        # Lock while reading and pruning
        with self.worker.server.lock:
            # Prune stale finished commands
            stale_keys = [k for k, v in self.worker.server.command_queue.items() 
                         if v.get("status") == "FINISHED" and (now - v.get("finish_time", 0)) > grace_period]
            for k in stale_keys:
                del self.worker.server.command_queue[k]
                
            queue_items = list(self.worker.server.command_queue.items())
            
        self.queue_table.setRowCount(len(queue_items))
        
        # Sort so newer/active ones stay together or just display as is
        for i, (uuid_val, data) in enumerate(queue_items):
            status = data.get("status", "PENDING")
            
            self.queue_table.setItem(i, 0, QTableWidgetItem(str(uuid_val)))
            
            # Status Item with color coding
            status_item = QTableWidgetItem(status)
            if status == "RUNNING":
                status_item.setForeground(Qt.GlobalColor.green)
            elif status == "FINISHED":
                status_item.setForeground(Qt.GlobalColor.gray)
                if data.get("reply type") == "ERR":
                    status_item.setForeground(Qt.GlobalColor.red)
            self.queue_table.setItem(i, 1, status_item)
            
            self.queue_table.setItem(i, 2, QTableWidgetItem(str(data.get("component", ""))))
            self.queue_table.setItem(i, 3, QTableWidgetItem(str(data.get("command", ""))))
            self.queue_table.setItem(i, 4, QTableWidgetItem(str(data.get("reply", ""))))
            
            # Format tick count to readable time if available
            tick = data.get("tick count")
            if tick:
                readable_time = time.strftime('%H:%M:%S', time.localtime(tick/1000.0))
            else:
                readable_time = "N/A"
            self.queue_table.setItem(i, 5, QTableWidgetItem(readable_time))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AcquilaServerGUI()
    window.show()
    sys.exit(app.exec())
