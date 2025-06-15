import tkinter as tk
from tkinter import ttk
import threading
import time
from voice_listener_vad import listen_once
from voice_listener_google import start_google_listening, stop_google_listening
from memory_manager import get_full_memory_log
from ask_gpt import ask_gpt
from local_llm_interface import ask_local_llm

# === Core Callback ===
def ask_with_model(prompt):
    mode = model_var.get()
    try:
        if mode == "GPT-4": return ask_gpt(prompt)
        elif mode == "Local (Mistral)": return ask_local_llm(prompt)
        elif mode == "Auto": return ask_local_llm(prompt)
    except: return ask_gpt(prompt)

process_command_callback = ask_with_model

# === Main Assistant Panel ===
root = tk.Tk()
root.title("Friday Assistant")
root.geometry("360x320+100+100")
root.configure(bg='#1f1f1f')
root.attributes("-topmost", True)
root.attributes("-alpha", 0.96)
root.overrideredirect(True)

# === Dragging ===
drag = {"x": 0, "y": 0}
fixed_popups = [None, None, None]
popup_index = 0


def start_drag(e):
    drag["x"], drag["y"] = e.x, e.y

def do_drag(e):
    dx, dy = e.x - drag["x"], e.y - drag["y"]
    x, y = root.winfo_x() + dx, root.winfo_y() + dy
    root.geometry(f"+{x}+{y}")
    for idx, entry in enumerate(fixed_popups):
        if entry:
            col = idx % 3
            row = idx // 3
            px = x + 420 + (col * 460)
            py = y + 60 + (row * 260)
            entry['win'].geometry(f"420x{entry['height']}+{px}+{py}")

# === Header ===
header = tk.Label(root, text="🧠 AI is Ready", font=("Segoe UI", 13, "bold"), bg="#1f1f1f", fg="#00FFAA")
header.pack(pady=(6, 4))
header.bind("<Button-1>", start_drag)
header.bind("<B1-Motion>", do_drag)

# === Model Selector ===
model_var = tk.StringVar(value="Auto")
model_selector = ttk.Combobox(root, textvariable=model_var, state="readonly", values=["Auto", "GPT-4", "Local (Mistral)"])
model_selector.pack(pady=(0, 6))
model_selector.configure(width=18)

# === Input ===
input_text = tk.Entry(root, font=("Segoe UI", 11), bg="#2d2d2d", fg="#FFFFFF", insertbackground='white')
input_text.pack(padx=10, pady=(0, 6), fill="x")
input_text.bind("<Return>", lambda e: send_text_command())

# === Buttons ===
btn_frame = tk.Frame(root, bg="#1f1f1f")
btn_frame.pack(pady=4)

btn_send = tk.Button(btn_frame, text="Send", command=lambda: send_text_command(), font=("Segoe UI", 10), bg="#444", fg="#FFF", width=8)
btn_send.grid(row=0, column=0, padx=5)

btn_listen = tk.Button(btn_frame, text="🎤", command=lambda: send_voice_command(), font=("Segoe UI", 11), bg="#444", fg="#FFF", width=4)
btn_listen.grid(row=0, column=1, padx=5)

live_btn = tk.Button(btn_frame, text="🟢", command=lambda: toggle_google_mode(), font=("Segoe UI", 11), bg="#444", fg="#FFF", width=4)
live_btn.grid(row=0, column=2, padx=5)

btn_close = tk.Button(root, text="✖", command=root.destroy, font=("Segoe UI", 10), bg="#aa3333", fg="white")
btn_close.pack(pady=4)

# === Floating Popup Slots ===
def show_floating_response(text):
    global popup_index, fixed_popups

    col = popup_index % 3
    row = popup_index // 3

    content_length = len(text)
    base_height = 120 + (content_length // 5)
    max_height = 400
    height = min(base_height, max_height)

    px = root.winfo_x() + 420 + (col * 460)
    py = root.winfo_y() + 60 + (row * 260)

    if fixed_popups[col]:
        fixed_popups[col]['win'].destroy()

    popup = tk.Toplevel(root)
    popup.overrideredirect(True)
    popup.attributes("-topmost", True)
    popup.geometry(f"420x{height}+{px}+{py}")

    outer = tk.Frame(popup, bg="#2b2b2b", bd=2)
    outer.pack(expand=True, fill="both", padx=10, pady=10)

    canvas = tk.Canvas(outer, bg="#2b2b2b", highlightthickness=0)
    frame = tk.Frame(canvas, bg="#2b2b2b")
    canvas.pack(side="left", fill="both", expand=True)
    canvas.create_window((0, 0), window=frame, anchor='nw')

    def on_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    frame.bind("<Configure>", on_configure)

    def bind_scroll():
        def _on_mousewheel(e): canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Enter>", lambda e: bind_scroll())
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
    bind_scroll()

    lbl = tk.Label(frame, text=text, font=("Segoe UI", 10), fg="#DDDDDD", bg="#2b2b2b", wraplength=380, justify="left", anchor="nw")
    lbl.pack(anchor="w", padx=8, pady=6, expand=True, fill="both")

    delete_btn = tk.Button(frame, text="🗑 Remove", command=popup.destroy, font=("Segoe UI", 9), bg="#444", fg="red", relief="flat")
    delete_btn.pack(anchor="se", padx=6, pady=(0, 6))

    popup.configure(bg="#1a1a1a")
    outer.configure(bg="#333333", relief="raised", bd=3)

    fixed_popups[col] = {"win": popup, "col": col, "row": row, "height": height}
    popup_index = (popup_index + 1) % 3


# === Text Command ===
def send_text_command():
    user_input = input_text.get().strip()
    if not user_input: return
    input_text.delete(0, tk.END)
    def run():
        response = process_command_callback(user_input)
        show_floating_response(response)
    threading.Thread(target=run).start()


# === Voice Command ===
def send_voice_command():
    def run():
        transcript = listen_once()
        if transcript.strip():
            response = process_command_callback(transcript)
            show_floating_response(response)
    threading.Thread(target=run).start()


# === Google Toggle ===
google_active = [False]

def toggle_google_mode():
    if not google_active[0]:
        google_active[0] = True
        live_btn.config(text="🔴")
        def update_ui(_1, _2, status):
            if status.startswith("🧠 Final:"):
                final = status.replace("🧠 Final:", "").strip()
                show_floating_response(final)
        def handle(transcript):
            response = process_command_callback(transcript)
            show_floating_response(response)
            return "🧠 Processed"
        start_google_listening(update_ui, handle)
    else:
        stop_google_listening()
        live_btn.config(text="🟢")
        google_active[0] = False


# === Hook ===
def update_overlay(_, __, status):
    show_floating_response(status)

def launch_overlay():
    past = get_full_memory_log()
    if past:
        show_floating_response(past[-1]['content'])
    root.mainloop()

on_listen_trigger = []
on_send_trigger = []