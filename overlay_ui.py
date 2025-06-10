# overlay_ui.py
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
import sys
import threading

class Overlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(50, 50, 500, 200)

        layout = QVBoxLayout()

        self.objects_label = QLabel("🧠 Objects: ")
        self.text_label = QLabel("📄 Text: ")
        self.intent_label = QLabel("💬 Intent: ")

        for label in [self.objects_label, self.text_label, self.intent_label]:
            label.setStyleSheet("color: white; background-color: rgba(0, 0, 0, 150); padding: 5px;")
            label.setFont(QFont("Consolas", 10))
            layout.addWidget(label)

        self.setLayout(layout)

    def update_overlay(self, objects, screen_text, intent):
        self.objects_label.setText(f"🧠 Objects: {', '.join(objects) if objects else 'None'}")
        self.text_label.setText(f"📄 Text: {screen_text or 'None'}")
        self.intent_label.setText(f"💬 Intent: {intent or 'Thinking...'}")

def start_overlay_thread(overlay_ref):
    app = QApplication(sys.argv)
    overlay = Overlay()
    overlay_ref.append(overlay)  # Save reference so we can update it later
    overlay.show()
    sys.exit(app.exec_())

# Global accessor to start and update overlay from main.py
overlay_instance = []

def launch_overlay():
    t = threading.Thread(target=start_overlay_thread, args=(overlay_instance,), daemon=True)
    t.start()

def update_overlay(objects, screen_text, intent):
    if overlay_instance:
        overlay_instance[0].update_overlay(objects, screen_text, intent)
