import tkinter as tk
from tkinter import ttk
import threading
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

# === Main Window ===
root = tk.Tk()
root.title("Friday Assistant")
root.geometry("400x350+50+200")
root.configure(bg='#1f1f1f')
root.attributes("-topmost", True)
root.attributes("-alpha", 0.96)
root.overrideredirect(True)

# === Popup State ===
drag = {"x": 0, "y": 0}
fixed_popups = [None, None, None]
popup_index = 0
minimized_popups = []

# === Restore Bar UI ===
taskbar_frame = tk.Frame(root, bg="#1f1f1f")
taskbar_frame.pack(fill="x", pady=(0, 6))

def render_minimized_bar():
    for widget in taskbar_frame.winfo_children():
        widget.destroy()

    still_valid = []
    for idx, (popup, title) in enumerate(minimized_popups):
        if not popup.winfo_exists():
            continue
        def restore(p=popup, i=idx):
            try:
                p.deiconify()
            except:
                pass
            if i < len(minimized_popups):
                minimized_popups.pop(i)
            render_minimized_bar()

        btn = tk.Button(taskbar_frame, text=f"🪡 {title}", command=restore,
                        font=("Segoe UI", 9), bg="#333", fg="#fff",
                        relief="flat", padx=6, pady=2)
        btn.pack(side="left", padx=4)
        still_valid.append((popup, title))

    minimized_popups[:] = still_valid

# === Floating Response Popup ===
def show_floating_response(text):
    global popup_index, fixed_popups

    line_count = text.count('\n') + 1
    line_height = 55
    base_height = 100 + (line_count * line_height)
    max_height = 900
    height = min(base_height, max_height)

    col = popup_index % 3
    row = popup_index // 3
    px = root.winfo_x() + 420 + (col * 460)
    py = root.winfo_y() + (row * 260)

    if fixed_popups[col]:
        old_win = fixed_popups[col]['win']
        minimized_popups[:] = [(p, t) for (p, t) in minimized_popups if p != old_win]
        old_win.destroy()
        render_minimized_bar()

    popup = tk.Toplevel(root)
    popup.overrideredirect(True)
    popup.attributes("-topmost", True)
    popup.geometry(f"420x{height}+{px}+{py}")
    popup.configure(bg="#2b2b2b")

    outer = tk.Frame(popup, bg="#2b2b2b", bd=0, highlightthickness=0)
    outer.pack(expand=True, fill="both", padx=0, pady=0)

    titlebar = tk.Frame(outer, bg="#202020", height=28)
    titlebar.pack(fill="x", side="top")

    title = tk.Label(titlebar, text="🪡 Friday Message", bg="#202020", fg="#FFFFFF",
                     font=("Segoe UI", 9, "bold"))
    title.pack(side="left", padx=8)

    def minimize_popup():
        minimized_popups.append((popup, "Friday Message"))
        popup.withdraw()
        render_minimized_bar()

    btn_minimize = tk.Button(titlebar, text="—", font=("Segoe UI", 9),
                             command=minimize_popup, bg="#202020", fg="white",
                             relief="flat", bd=0)
    btn_minimize.pack(side="right", padx=(4, 2))

    btn_close = tk.Button(titlebar, text="✖", font=("Segoe UI", 9),
                          command=popup.destroy, bg="#202020", fg="red",
                          relief="flat", bd=0)
    btn_close.pack(side="right", padx=(2, 8))

    def popup_drag_start(e): popup._drag_offset = (e.x, e.y)
    def popup_drag_move(e):
        dx, dy = popup._drag_offset
        popup.geometry(f"+{e.x_root - dx}+{e.y_root - dy}")
    titlebar.bind("<Button-1>", popup_drag_start)
    titlebar.bind("<B1-Motion>", popup_drag_move)

    canvas = tk.Canvas(outer, bg="#2b2b2b", highlightthickness=0)
    canvas.pack(side="left", fill="both", expand=True)

    frame = tk.Frame(canvas, bg="#2b2b2b")
    canvas.create_window((0, 0), window=frame, anchor='nw')

    def on_configure(event): canvas.configure(scrollregion=canvas.bbox("all"))
    frame.bind("<Configure>", on_configure)

    def bind_scroll():
        def _on_mousewheel(e): canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Enter>", lambda e: bind_scroll())
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
    bind_scroll()

    lbl = tk.Label(frame, text=text, font=("Segoe UI", 10), fg="#DDDDDD", bg="#2b2b2b",
                   wraplength=380, justify="left", anchor="nw")
    lbl.pack(anchor="w", padx=8, pady=6, expand=True, fill="both")

    fixed_popups[col] = {"win": popup, "col": col, "row": row, "height": height}
    popup_index = (popup_index + 1) % 3

# === Dragging Sync ===
def start_drag(e): drag["x"], drag["y"] = e.x, e.y

def do_drag(e):
    dx, dy = e.x - drag["x"], e.y - drag["y"]
    x, y = root.winfo_x() + dx, root.winfo_y() + dy
    root.geometry(f"+{x}+{y}")
    for idx, entry in enumerate(fixed_popups):
        if entry:
            col = idx % 3
            row = idx // 3
            px = x + 420 + (col * 460)
            py = y + (row * 260)
            entry['win'].geometry(f"420x{entry['height']}+{px}+{py}")

# === UI Controls ===
header = tk.Label(root, text="🧠 Friday is Ready", font=("Segoe UI", 14, "bold"), bg="#1f1f1f", fg="#00FFAA")
header.pack(pady=(10, 5))
header.bind("<Button-1>", start_drag)
header.bind("<B1-Motion>", do_drag)

model_var = tk.StringVar(value="Auto")
model_selector = ttk.Combobox(root, textvariable=model_var, state="readonly",
                              values=["Auto", "GPT-4", "Local (Mistral)"])
model_selector.pack(pady=(0, 10))
model_selector.configure(width=20)

input_text = tk.Entry(root, font=("Segoe UI", 11), bg="#2d2d2d", fg="#FFFFFF", insertbackground='white')
input_text.pack(padx=20, pady=(0, 10), fill="x")
input_text.bind("<Return>", lambda e: send_text_command())

output_text = tk.Text(root, height=6, font=("Segoe UI", 11), bg="#1f1f1f", fg="#FFFFFF", wrap="word", state="disabled")
output_text.pack(padx=20, pady=(0, 10), fill="both")

btn_frame = tk.Frame(root, bg="#1f1f1f")
btn_frame.pack(pady=(0, 10))

tk.Button(btn_frame, text="Send", command=lambda: send_text_command(), font=("Segoe UI", 10),
          bg="#444", fg="#FFF", width=10).grid(row=0, column=0, padx=10)

tk.Button(btn_frame, text="🎤 Listen", command=lambda: send_voice_command(), font=("Segoe UI", 10),
          bg="#444", fg="#FFF", width=10).grid(row=0, column=1, padx=10)

live_btn = tk.Button(btn_frame, text="🟢 Google STT", command=lambda: toggle_google_mode(),
                     font=("Segoe UI", 10), bg="#444", fg="#FFF", width=14)
live_btn.grid(row=0, column=2, padx=10)

tk.Button(root, text="✖", command=root.destroy, font=("Segoe UI", 10), bg="#aa3333", fg="white").pack(side="bottom", pady=5)

# === Command Handlers ===
def send_text_command():
    user_input = input_text.get().strip()
    if not user_input: return
    output_text.config(state="normal")
    output_text.insert(tk.END, f"You: {user_input}\n")
    output_text.config(state="disabled")
    input_text.delete(0, tk.END)
    def run():
        response = process_command_callback(user_input)
        show_floating_response(response)
    threading.Thread(target=run).start()

def send_voice_command():
    output_text.config(state="normal")
    output_text.insert(tk.END, "🎤 Listening...\n")
    output_text.config(state="disabled")
    def run():
        transcript = listen_once()
        if transcript.strip():
            output_text.config(state="normal")
            output_text.insert(tk.END, f"You (Voice): {transcript}\n")
            output_text.config(state="disabled")
            response = process_command_callback(transcript)
            show_floating_response(response)
    threading.Thread(target=run).start()

# === Google STT Toggle ===
google_active = [False]
def toggle_google_mode():
    if not google_active[0]:
        google_active[0] = True
        live_btn.config(text="🔴 Stop STT")
        def update_ui(_1, _2, status):
            if status.startswith("🧠 Final:"):
                final = status.replace("🧠 Final:", "").strip()
                output_text.config(state="normal")
                output_text.insert(tk.END, f"You (Voice): {final}\n")
                output_text.config(state="disabled")
        def handle(transcript):
            response = process_command_callback(transcript)
            show_floating_response(response)
            return "🧠 Processed"
        start_google_listening(update_ui, handle)
    else:
        stop_google_listening()
        live_btn.config(text="🟢 Google STT")
        google_active[0] = False

# === Hooks ===
def update_overlay(_, __, status): show_floating_response(status)
def launch_overlay():
    past = get_full_memory_log()
    if past:
        root.after(300, lambda: show_floating_response(past[-1]['content']))
    root.mainloop()

on_listen_trigger = []
on_send_trigger = []