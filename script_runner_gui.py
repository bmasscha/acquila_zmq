import sys
import json
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QFileDialog, QGroupBox, QStatusBar, QComboBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from acquila_zmq import AcquilaClient, DEFAULT_OUTBOUND_PORT, DEFAULT_INBOUND_PORT

class ScriptWorker(QThread):
    finished = pyqtSignal()
    status_update = pyqtSignal(str)
    
    def __init__(self, connection_info, script_data):
        super().__init__()
        self.conn_info = connection_info # (ip, in_port, out_port)
        self.script_data = script_data
        self._is_running = True

    def run(self):
        # Create a thread-local client
        ip, i_port, o_port = self.conn_info
        try:
            client = AcquilaClient(server_ip=ip, inbound_port=i_port, outbound_port=o_port)
        except Exception as e:
            self.status_update.emit(f"Connection Error: {e}")
            self.finished.emit()
            return

        for i, cmd_data in enumerate(self.script_data):
            if not self._is_running: break
            
            comp = cmd_data.get("component")
            cmd = cmd_data.get("command")
            a1 = cmd_data.get("arg1", "")
            a2 = cmd_data.get("arg2", "")
            wf = cmd_data.get("wait_for", "ACK")
            
            if not wf or wf.strip() == "": wf = "ACK"

            self.status_update.emit(f"Step {i+1}: {cmd} -> {comp} (Wait: {wf})")
            
            if comp and cmd:
                try:
                    # send_command will block until the wait_for condition is met
                    res = client.send_command(comp, cmd, a1, a2, wait_for=wf)
                    if res is None and wf != "no wait":
                        self.status_update.emit(f"Timeout/Failure in step {i+1}")
                except Exception as e:
                    self.status_update.emit(f"Error in step {i+1}: {e}")
            
        self.status_update.emit("Script Finished.")
        self.finished.emit()

    def stop(self):
        self._is_running = False

class ScriptRunnerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Acquila Script Runner")
        self.resize(900, 600)
        
        # Default Client
        self.client = None
        self.worker = None
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Connection Info ---
        conn_layout = QHBoxLayout()
        conn_layout.addWidget(QLabel("Server IP:"))
        self.ip_edit = QLineEdit("127.0.0.1")
        conn_layout.addWidget(self.ip_edit)
        
        conn_layout.addWidget(QLabel("Ports (In/Out):"))
        self.in_port_edit = QLineEdit(str(DEFAULT_INBOUND_PORT))
        self.out_port_edit = QLineEdit(str(DEFAULT_OUTBOUND_PORT))
        conn_layout.addWidget(self.in_port_edit)
        conn_layout.addWidget(self.out_port_edit)
        
        self.connect_btn = QPushButton("Reconnect")
        self.connect_btn.clicked.connect(self.connect_client)
        conn_layout.addWidget(self.connect_btn)
        main_layout.addLayout(conn_layout)

        # --- Single Command Section ---
        single_cmd_group = QGroupBox("Single Command")
        single_layout = QHBoxLayout()
        
        self.comp_edit = QLineEdit()
        self.comp_edit.setPlaceholderText("Component")
        single_layout.addWidget(self.comp_edit)
        
        self.cmd_edit = QLineEdit()
        self.cmd_edit.setPlaceholderText("Command")
        single_layout.addWidget(self.cmd_edit)
        
        self.arg1_edit = QLineEdit()
        self.arg1_edit.setPlaceholderText("Arg 1")
        single_layout.addWidget(self.arg1_edit)
        
        self.arg2_edit = QLineEdit()
        self.arg2_edit.setPlaceholderText("Arg 2")
        single_layout.addWidget(self.arg2_edit)
        
        single_layout.addWidget(QLabel("Wait:"))
        self.wf_combo = QComboBox()
        self.wf_combo.addItems(["ACK", "RCV", "no wait"])
        single_layout.addWidget(self.wf_combo)
        
        send_btn = QPushButton("Send Single")
        send_btn.clicked.connect(self.send_single_command)
        single_layout.addWidget(send_btn)
        
        single_cmd_group.setLayout(single_layout)
        main_layout.addWidget(single_cmd_group)

        # --- Script Table Section ---
        main_layout.addWidget(QLabel("<b>Command Script</b>"))
        self.script_table = QTableWidget(0, 5)
        self.script_table.setHorizontalHeaderLabels(["Component", "Command", "Arg 1", "Arg 2", "Wait For"])
        self.script_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.script_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        main_layout.addWidget(self.script_table)

        # --- Script Controls ---
        script_controls = QHBoxLayout()
        
        add_btn = QPushButton("Add Row")
        add_btn.clicked.connect(self.add_row)
        script_controls.addWidget(add_btn)
        
        rem_btn = QPushButton("Remove Row")
        rem_btn.clicked.connect(self.remove_row)
        script_controls.addWidget(rem_btn)

        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_table)
        script_controls.addWidget(clear_btn)
        
        script_controls.addStretch()
        
        load_btn = QPushButton("Load Script")
        load_btn.clicked.connect(self.load_script)
        script_controls.addWidget(load_btn)
        
        save_btn = QPushButton("Save Script")
        save_btn.clicked.connect(self.save_script)
        script_controls.addWidget(save_btn)
        
        self.run_btn = QPushButton("RUN SCRIPT")
        self.run_btn.setMinimumWidth(120)
        self.run_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.run_btn.clicked.connect(self.toggle_script)
        script_controls.addWidget(self.run_btn)
        
        main_layout.addLayout(script_controls)
        
        # Status Bar
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")
        
        # Initial Connect
        self.connect_client()

    def connect_client(self):
        try:
            ip = self.ip_edit.text()
            i_port = int(self.in_port_edit.text())
            o_port = int(self.out_port_edit.text())
            self.client = AcquilaClient(server_ip=ip, inbound_port=i_port, outbound_port=o_port)
            self.statusBar().showMessage(f"Connected to {ip}:{i_port}/{o_port}")
        except Exception as e:
            self.statusBar().showMessage(f"Connection Error: {e}")

    def send_single_command(self):
        if not self.ensure_client(): return
        
        comp = self.comp_edit.text()
        cmd = self.cmd_edit.text()
        a1 = self.arg1_edit.text()
        a2 = self.arg2_edit.text()
        wf = self.wf_combo.currentText()
        
        if not comp or not cmd:
            self.statusBar().showMessage("Error: Component and Command are required.")
            return

        # Use a background thread for a single command if it's blocking
        if wf == "no wait":
            self.client.send_command(comp, cmd, a1, a2, wait_for=wf)
            self.statusBar().showMessage(f"Sent (no wait): {cmd}")
        else:
            # We'll just run it in a tiny script worker for simplicity so UI doesn't hang
            single_script = [{"component": comp, "command": cmd, "arg1": a1, "arg2": a2, "wait_for": wf}]
            self.start_worker(single_script)

    def add_row(self):
        row = self.script_table.rowCount()
        self.script_table.insertRow(row)
        
        # Initialize columns with empty editable items
        for col in range(5):
            val = "ACK" if col == 4 else ""
            item = QTableWidgetItem(val)
            self.script_table.setItem(row, col, item)
            
        # Focus on the first cell of the new row for immediate typing
        self.script_table.setCurrentCell(row, 0)
        self.script_table.editItem(self.script_table.item(row, 0))
        self.script_table.scrollToBottom()

    def remove_row(self):
        current_row = self.script_table.currentRow()
        if current_row >= 0:
            self.script_table.removeRow(current_row)

    def clear_table(self):
        self.script_table.setRowCount(0)
        self.statusBar().showMessage("Table cleared.")

    def load_script(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Script", "", "Text Files (*.txt);;JSON Files (*.json)")
        if file_name:
            try:
                if file_name.endswith(".json"):
                    with open(file_name, 'r') as f:
                        data = json.load(f)
                        self.script_table.setRowCount(0)
                        for cmd in data:
                            row = self.script_table.rowCount()
                            self.script_table.insertRow(row)
                            self.script_table.setItem(row, 0, QTableWidgetItem(cmd.get("component", "")))
                            self.script_table.setItem(row, 1, QTableWidgetItem(cmd.get("command", "")))
                            self.script_table.setItem(row, 2, QTableWidgetItem(cmd.get("arg1", "")))
                            self.script_table.setItem(row, 3, QTableWidgetItem(cmd.get("arg2", "")))
                            self.script_table.setItem(row, 4, QTableWidgetItem(cmd.get("wait_for", "ACK")))
                else:
                    # TXT format: tab separated
                    with open(file_name, 'r') as f:
                        self.script_table.setRowCount(0)
                        for line in f:
                            line = line.strip()
                            if not line: continue
                            parts = line.split('\t')
                            # Ensure at least 2 parts (comp, cmd)
                            if len(parts) >= 2:
                                row = self.script_table.rowCount()
                                self.script_table.insertRow(row)
                                self.script_table.setItem(row, 0, QTableWidgetItem(parts[0].strip()))
                                self.script_table.setItem(row, 1, QTableWidgetItem(parts[1].strip()))
                                self.script_table.setItem(row, 2, QTableWidgetItem(parts[2].strip() if len(parts) > 2 else ""))
                                self.script_table.setItem(row, 3, QTableWidgetItem(parts[3].strip() if len(parts) > 3 else ""))
                                
                                wf = parts[4].strip() if len(parts) > 4 else "ACK"
                                if not wf: wf = "ACK"
                                self.script_table.setItem(row, 4, QTableWidgetItem(wf))
                self.statusBar().showMessage(f"Loaded: {file_name}")
            except Exception as e:
                self.statusBar().showMessage(f"Load Error: {e}")

    def save_script(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Script", "", "Text Files (*.txt)")
        if file_name:
            try:
                # Always save as TXT tab separated
                if not file_name.lower().endswith(".txt"): 
                    file_name += ".txt"
                
                with open(file_name, 'w') as f:
                    for row in range(self.script_table.rowCount()):
                        parts = [
                            self.get_table_text(row, 0),
                            self.get_table_text(row, 1),
                            self.get_table_text(row, 2),
                            self.get_table_text(row, 3),
                            self.get_table_text(row, 4)
                        ]
                        # Ensure no None or empty strings that break tabs
                        parts = [p if p else "" for p in parts]
                        f.write("\t".join(parts) + "\n")
                
                self.statusBar().showMessage(f"Saved: {file_name}")
            except Exception as e:
                self.statusBar().showMessage(f"Save Error: {e}")

    def toggle_script(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.statusBar().showMessage("Stopping Script...")
        else:
            self.run_script()

    def run_script(self):
        if not self.ensure_client(): return
        
        script_data = []
        for row in range(self.script_table.rowCount()):
            script_data.append({
                "component": self.get_table_text(row, 0),
                "command": self.get_table_text(row, 1),
                "arg1": self.get_table_text(row, 2),
                "arg2": self.get_table_text(row, 3),
                "wait_for": self.get_table_text(row, 4)
            })
        
        if not script_data:
            self.statusBar().showMessage("No commands in script.")
            return

        self.start_worker(script_data)

    def start_worker(self, script_data):
        # Pass connection info so worker can create its own thread-safe client
        ip = self.ip_edit.text()
        i_port = int(self.in_port_edit.text())
        o_port = int(self.out_port_edit.text())
        conn_info = (ip, i_port, o_port)

        self.worker = ScriptWorker(conn_info, script_data)
        self.worker.status_update.connect(lambda s: self.statusBar().showMessage(s))
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()
        
        self.run_btn.setText("STOP SCRIPT")
        self.run_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")

    def on_worker_finished(self):
        self.run_btn.setText("RUN SCRIPT")
        self.run_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.statusBar().showMessage("Script Execution Finished.")

    def ensure_client(self):
        if not self.client:
            self.connect_client()
        return self.client is not None

    def get_table_text(self, row, col):
        item = self.script_table.item(row, col)
        return item.text() if item else ""

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScriptRunnerGUI()
    window.show()
    sys.exit(app.exec())
