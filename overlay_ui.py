from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
import sys

# Shared state
transcribed_text = ""
on_listen_trigger = []
on_send_trigger = []

class OverlayWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 200); color: white;")

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.listen_button = QPushButton("🎙️ Start Listening")
        self.listen_button.clicked.connect(self.start_listening)

        self.output_label = QLabel("🧠 Waiting for input...")
        self.output_label.setAlignment(Qt.AlignCenter)

        self.send_button = QPushButton("✅ Send to GPT")
        self.send_button.clicked.connect(self.send_to_gpt)
        self.send_button.setEnabled(False)

        layout.addWidget(self.listen_button)
        layout.addWidget(self.output_label)
        layout.addWidget(self.send_button)

        self.setLayout(layout)
        self.resize(400, 200)
        self.move(100, 100)  # Top-left position

    def start_listening(self):
        self.output_label.setText("🎤 Listening...")
        self.send_button.setEnabled(False)
        for callback in on_listen_trigger:
            callback()

    def send_to_gpt(self):
        for callback in on_send_trigger:
            callback(transcribed_text)


    def update_output(self, text):
        global transcribed_text
        transcribed_text = text
        self.output_label.setText(f"🧠 You said:\n{text}")
        self.send_button.setEnabled(True)

# === Entry point ===
overlay = None

def launch_overlay():
    global overlay
    app = QApplication(sys.argv)
    overlay = OverlayWindow()
    overlay.show()
    sys.exit(app.exec_())

def update_overlay(_, __, message):
    if overlay:
        overlay.update_output(message)
