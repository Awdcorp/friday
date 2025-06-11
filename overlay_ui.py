import tkinter as tk
import threading
from voice_listener_vad import listen_once
from memory_manager import get_full_memory_log  # ✅ Updated import

# === External Callback Handlers (to be set by main_brain) ===
process_command_callback = None

# === Setup Main Window ===
root = tk.Tk()
root.title("Friday Assistant")
root.geometry("400x350+50+200")
root.configure(bg='#1f1f1f')
root.attributes("-topmost", True)
root.attributes("-alpha", 0.85)
root.overrideredirect(True)

# === Style ===
text_fg = "#FFFFFF"
btn_bg = "#444"
btn_fg = "#FFF"
font_main = ("Segoe UI", 11)

# === Header ===
header = tk.Label(root, text="🧠 Friday is Ready", font=("Segoe UI", 14, "bold"),
                  bg="#1f1f1f", fg="#00FFAA")
header.pack(pady=(10, 5))

# === Text Input Field ===
input_text = tk.Entry(root, font=font_main, bg="#2d2d2d", fg=text_fg, insertbackground='white')
input_text.pack(padx=20, pady=(5, 10), fill="x")
input_text.bind("<Return>", lambda event: send_text_command())

# === Output Display ===
output_text = tk.Text(root, height=6, font=font_main, bg="#1f1f1f", fg=text_fg, wrap="word")
output_text.pack(padx=20, pady=(5, 10), fill="both")

# === Text Input Handler ===
def send_text_command():
    user_input = input_text.get().strip()
    if not user_input:
        return
    output_text.insert(tk.END, f"You: {user_input}\n")
    input_text.delete(0, tk.END)

    def process():
        if process_command_callback:
            response = process_command_callback(user_input)
            output_text.insert(tk.END, f"Friday: {response}\n")
        else:
            output_text.insert(tk.END, "⚠️ No handler defined for text command.\n")

    threading.Thread(target=process).start()

# === Voice Input Handler ===
def send_voice_command():
    output_text.insert(tk.END, "🎤 Listening...\n")

    def listen_and_process():
        transcript = listen_once()
        output_text.insert(tk.END, f"You (Voice): {transcript}\n")
        if process_command_callback:
            response = process_command_callback(transcript)
            output_text.insert(tk.END, f"Friday: {response}\n")

    threading.Thread(target=listen_and_process).start()

# === Buttons ===
btn_frame = tk.Frame(root, bg="#1f1f1f")
btn_frame.pack(pady=(0, 10))

send_btn = tk.Button(btn_frame, text="Send", command=send_text_command, font=font_main,
                     bg=btn_bg, fg=btn_fg, width=10)
send_btn.grid(row=0, column=0, padx=10)

voice_btn = tk.Button(btn_frame, text="🎤 Listen", command=send_voice_command, font=font_main,
                      bg=btn_bg, fg=btn_fg, width=10)
voice_btn.grid(row=0, column=1, padx=10)

# === Exit Button ===
exit_btn = tk.Button(root, text="✖", command=root.destroy, font=("Segoe UI", 10),
                     bg="#aa3333", fg="white")
exit_btn.pack(side="bottom", pady=5)

# === Event Triggers (still exposed, but not used internally anymore) ===
on_listen_trigger = []
on_send_trigger = []

# === External API Functions ===
def update_overlay(obj_list, screen_text, status):
    output_text.insert(tk.END, f"{status}\n")

def launch_overlay():
    # ✅ Load and display saved memory
    past = get_full_memory_log()
    if past:
        output_text.insert(tk.END, "🔁 Previous Session:\n\n")
        for entry in past:
            role = entry.get("role", "user").capitalize()
            content = entry.get("content", "")
            output_text.insert(tk.END, f"{role}: {content}\n")
        output_text.insert(tk.END, "\n")

    root.mainloop()
