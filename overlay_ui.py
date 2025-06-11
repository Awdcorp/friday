import tkinter as tk
import threading
from voice_listener_vad import listen_once
from memory_manager import get_full_memory_log

# === External Callback Handler ===
process_command_callback = None

# === Main Window ===
root = tk.Tk()
root.title("Friday Assistant")
root.geometry("400x350+50+200")
root.configure(bg='#1f1f1f')
root.attributes("-topmost", True)
root.attributes("-alpha", 0.9)
root.overrideredirect(True)

# === Popup Window for GPT Response ===
response_popup = tk.Toplevel(root)
response_popup.overrideredirect(True)
response_popup.attributes("-topmost", True)
response_popup.attributes("-alpha", 0.92)
response_popup.configure(bg="#202020")
response_popup.withdraw()

# === GPT Text Area + Close Button ===
response_frame = tk.Frame(response_popup, bg="#202020")
response_frame.pack(padx=8, pady=8)

response_label = tk.Label(response_frame, text="", font=("Segoe UI", 10), bg="#202020",
                          fg="#00FFAA", wraplength=300, justify="left")
response_label.pack(side="left")

close_btn = tk.Button(response_frame, text="✖", command=lambda: close_popup(show_fallback=True),
                      font=("Segoe UI", 10), bg="#aa3333", fg="white", padx=6)
close_btn.pack(side="right", padx=(10, 0))

popup_visible = False  # Tracks popup visibility state

# === Styling ===
text_fg = "#FFFFFF"
btn_bg = "#444"
btn_fg = "#FFF"
font_main = ("Segoe UI", 11)

# === Header ===
header = tk.Label(root, text="🧠 Friday is Ready", font=("Segoe UI", 14, "bold"),
                  bg="#1f1f1f", fg="#00FFAA")
header.pack(pady=(10, 5))

# === Input Field ===
input_text = tk.Entry(root, font=font_main, bg="#2d2d2d", fg=text_fg, insertbackground='white')
input_text.pack(padx=20, pady=(5, 10), fill="x")
input_text.bind("<Return>", lambda event: send_text_command())

# === Output Display (Only shows fallback GPT response) ===
output_text = tk.Text(root, height=6, font=font_main, bg="#1f1f1f", fg=text_fg,
                      wrap="word", state="disabled")
output_text.pack(padx=20, pady=(5, 10), fill="both")

# === Dragging Logic ===
drag_data = {"x": 0, "y": 0}

def start_drag(event):
    drag_data["x"] = event.x
    drag_data["y"] = event.y

def do_drag(event):
    dx = event.x - drag_data["x"]
    dy = event.y - drag_data["y"]
    x = root.winfo_x() + dx
    y = root.winfo_y() + dy
    root.geometry(f"+{x}+{y}")
    if popup_visible:
        response_popup.geometry(f"+{x + 410}+{y}")

header.bind("<Button-1>", start_drag)
header.bind("<B1-Motion>", do_drag)

# === Floating GPT Response Handling ===
def show_response_popup(text):
    global popup_visible
    popup_visible = True
    response_label.config(text=f"🤖 {text}")
    x = root.winfo_x() + 410
    y = root.winfo_y()
    response_popup.geometry(f"+{x}+{y}")
    response_popup.deiconify()

def close_popup(show_fallback=False):
    global popup_visible
    popup_visible = False
    response_popup.withdraw()
    if show_fallback:
        output_text.config(state="normal")
        output_text.insert(tk.END, f"Friday: 🤖 {response_label.cget('text')}\n")
        output_text.config(state="disabled")

# === Input: Text Command ===
def send_text_command():
    user_input = input_text.get().strip()
    if not user_input:
        return

    output_text.config(state="normal")
    output_text.insert(tk.END, f"You: {user_input}\n")
    output_text.config(state="disabled")
    input_text.delete(0, tk.END)

    def process():
        if process_command_callback:
            response = process_command_callback(user_input)
            if response.startswith("🤖 "):
                show_response_popup(response[2:])
            else:
                output_text.config(state="normal")
                output_text.insert(tk.END, f"Friday: {response}\n")
                output_text.config(state="disabled")

    threading.Thread(target=process).start()

# === Input: Voice Command ===
def send_voice_command():
    output_text.config(state="normal")
    output_text.insert(tk.END, "🎤 Listening...\n")
    output_text.config(state="disabled")

    def listen_and_process():
        transcript = listen_once()
        output_text.config(state="normal")
        output_text.insert(tk.END, f"You (Voice): {transcript}\n")
        output_text.config(state="disabled")
        if process_command_callback:
            response = process_command_callback(transcript)
            if response.startswith("🤖 "):
                show_response_popup(response[2:])
            else:
                output_text.config(state="normal")
                output_text.insert(tk.END, f"Friday: {response}\n")
                output_text.config(state="disabled")

    threading.Thread(target=listen_and_process).start()

# === Button Layout ===
btn_frame = tk.Frame(root, bg="#1f1f1f")
btn_frame.pack(pady=(0, 10))

send_btn = tk.Button(btn_frame, text="Send", command=send_text_command, font=font_main,
                     bg=btn_bg, fg=btn_fg, width=10)
send_btn.grid(row=0, column=0, padx=10)

voice_btn = tk.Button(btn_frame, text="🎤 Listen", command=send_voice_command, font=font_main,
                      bg=btn_bg, fg=btn_fg, width=10)
voice_btn.grid(row=0, column=1, padx=10)

exit_btn = tk.Button(root, text="✖", command=root.destroy, font=("Segoe UI", 10),
                     bg="#aa3333", fg="white")
exit_btn.pack(side="bottom", pady=5)

# === Dummy triggers (not used internally anymore) ===
on_listen_trigger = []
on_send_trigger = []

# === External API Functions ===
def update_overlay(obj_list, screen_text, status):
    output_text.config(state="normal")
    output_text.insert(tk.END, f"{status}\n")
    output_text.config(state="disabled")

def launch_overlay():
    past = get_full_memory_log()
    if past:
        output_text.config(state="normal")
        output_text.insert(tk.END, "🔁 Previous Session:\n\n")
        for entry in past:
            role = entry.get("role", "user").capitalize()
            content = entry.get("content", "")
            output_text.insert(tk.END, f"{role}: {content}\n")
        output_text.insert(tk.END, "\n")
        output_text.config(state="disabled")

    root.mainloop()
