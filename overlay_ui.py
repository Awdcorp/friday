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

main_minimized = [False]  # Track minimize state
drag = {"x": 0, "y": 0}
fixed_popups = [None, None, None]
popup_index = 0
minimized_popups = []

# === Popup Layout Constants ===
POPUP_WIDTH = 420
POPUP_HEIGHT = 260
START_X = 100
START_Y = 100
COL_SPACING = 20
ROW_SPACING = 20
MAX_COLS = 3

# === Title Bar Frame (Draggable with Buttons) ===
titlebar_frame = tk.Frame(root, bg="#1f1f1f", height=30)
titlebar_frame.pack(fill="x", side="top")

def start_drag(e): drag["x"], drag["y"] = e.x, e.y

def do_drag(e):
    dx, dy = e.x - drag["x"], e.y - drag["y"]
    x, y = root.winfo_x() + dx, root.winfo_y() + dy
    root.geometry(f"+{x}+{y}")

titlebar_frame.bind("<Button-1>", start_drag)
titlebar_frame.bind("<B1-Motion>", do_drag)

btn_main_close = tk.Button(titlebar_frame, text="✖", font=("Segoe UI", 9),
                           command=root.destroy, bg="#1f1f1f", fg="red",
                           relief="flat", bd=0)
btn_main_close.pack(side="right", padx=4, pady=2)

btn_main_min = tk.Button(titlebar_frame, text="—", font=("Segoe UI", 9),
                         command=lambda: restore_main() if main_minimized[0] else minimize_main(),
                         bg="#1f1f1f", fg="white", relief="flat", bd=0)
btn_main_min.pack(side="right", padx=2, pady=2)

# === Taskbar ===
taskbar_frame = tk.Frame(root, bg="#2a2a2a", height=28)
taskbar_frame.pack(fill="x", side="top")

def restore_all_minimized():
    for popup, _ in minimized_popups:
        if popup.winfo_exists():
            popup.deiconify()
    minimized_popups.clear()
    render_minimized_bar()

def render_minimized_bar():
    for widget in taskbar_frame.winfo_children():
        widget.destroy()

    if minimized_popups:
        tk.Label(taskbar_frame, text="🗂", bg="#2a2a2a", fg="white").pack(side="left", padx=6)

    still_valid = []
    for idx, (popup, title) in enumerate(minimized_popups):
        if not popup.winfo_exists(): continue
        def restore(p=popup, i=idx):
            try: p.deiconify()
            except: pass
            if i < len(minimized_popups):
                del minimized_popups[i]
            render_minimized_bar()

        btn = tk.Button(taskbar_frame, text=f"{title}", command=restore,
                        font=("Segoe UI", 9), bg="#333", fg="#fff",
                        relief="flat", padx=6, pady=2)
        btn.pack(side="left", padx=4)
        still_valid.append((popup, title))

    if minimized_popups:
        btn_all = tk.Button(taskbar_frame, text="⤴️ Restore All", command=restore_all_minimized,
                            font=("Segoe UI", 9), bg="#555", fg="#fff", relief="flat", padx=4, pady=2)
        btn_all.pack(side="right", padx=6)

    minimized_popups[:] = still_valid

# === Minimize/Restore Logic ===
def minimize_main():
    main_minimized[0] = True
    for widget in root.winfo_children():
        if widget not in [titlebar_frame, taskbar_frame] and widget.winfo_manager() == "pack":
            widget.pack_forget()
    root.geometry("400x64+50+200")
    for entry in fixed_popups:
        if entry and entry['win'].winfo_exists():
            entry['win'].withdraw()
            if all(entry['win'] != p for p, _ in minimized_popups):
                minimized_popups.append((entry['win'], "Friday Message"))
    render_minimized_bar()

def restore_main():
    if main_minimized[0]:
        header.pack(pady=(10, 5))
        input_text.pack(padx=20, pady=(0, 10), fill="x")
        output_text.pack(padx=20, pady=(0, 10), fill="both")
        btn_frame.pack(pady=(0, 10))
        model_selector.pack(pady=(0, 10))
        close_btn.pack(side="bottom", pady=5)
        root.geometry("400x350+50+200")
        main_minimized[0] = False
        for popup, _ in minimized_popups:
            if popup.winfo_exists():
                popup.deiconify()
        minimized_popups.clear()
        render_minimized_bar()

# === Popup Close Cleanup ===
def on_popup_close(win):
    for i, entry in enumerate(fixed_popups):
        if entry and entry['win'] == win:
            fixed_popups[i] = None
            break
    minimized_popups[:] = [(p, t) for (p, t) in minimized_popups if p != win]
    render_minimized_bar()
    win.destroy()

# === UI Content ===
header = tk.Label(root, text="🧠 Friday is Ready", font=("Segoe UI", 14, "bold"), bg="#1f1f1f", fg="#00FFAA")
header.pack(pady=(10, 5))
header.bind("<Button-1>", start_drag)
header.bind("<B1-Motion>", do_drag)

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

model_var = tk.StringVar(value="Auto")
model_selector = ttk.Combobox(root, textvariable=model_var, state="readonly",
                              values=["Auto", "GPT-4", "Local (Mistral)"])
model_selector.pack(pady=(0, 10))
model_selector.configure(width=20)

close_btn = tk.Button(root, text="✖", command=root.destroy, font=("Segoe UI", 10), bg="#aa3333", fg="white")
close_btn.pack(side="bottom", pady=5)

# === Floating Response Popup ===
def show_floating_response(text):
    global popup_index, fixed_popups

    # Estimate popup height based on lines
    line_count = text.count('\n') + 1
    line_height = 55
    base_height = 100 + (line_count * line_height)
    max_height = 900
    height = min(base_height, max_height)

    col = popup_index % 3
    row = popup_index // 3

    # Default position (if no existing popup)
    px = 100 + col * (420 + 20)
    py = 100 + row * (260 + 20)

    # If reusing an existing popup, get its current position
    if fixed_popups[col]:
        old_win = fixed_popups[col]['win']
        try:
            px = old_win.winfo_x()
            py = old_win.winfo_y()
        except:
            pass
        minimized_popups[:] = [(p, t) for (p, t) in minimized_popups if p != old_win]
        old_win.destroy()
        render_minimized_bar()

    # Create new popup
    popup = tk.Toplevel(root)
    popup.overrideredirect(True)
    popup.attributes("-topmost", True)
    popup.geometry(f"420x{height}+{px}+{py}")
    popup.configure(bg="#2b2b2b")

    outer = tk.Frame(popup, bg="#2b2b2b", bd=0, highlightthickness=0)
    outer.pack(expand=True, fill="both", padx=0, pady=0)

    title_text = text.strip().splitlines()[0][:7] if text.strip() else "Friday Message"

    titlebar = tk.Frame(outer, bg="#202020", height=28)
    titlebar.pack(fill="x", side="top")

    title = tk.Label(titlebar, text=f"🪡 {title_text}", bg="#202020", fg="#FFFFFF", font=("Segoe UI", 9, "bold"))
    title.pack(side="left", padx=8)

    def minimize_popup():
        if all(popup != p for p, _ in minimized_popups):
            minimized_popups.append((popup, title_text))
        popup.withdraw()
        render_minimized_bar()

    btn_minimize = tk.Button(titlebar, text="—", font=("Segoe UI", 9), command=minimize_popup,
                             bg="#202020", fg="white", relief="flat", bd=0)
    btn_minimize.pack(side="right", padx=(4, 2))

    btn_close = tk.Button(titlebar, text="✖", font=("Segoe UI", 9), command=lambda: on_popup_close(popup),
                          bg="#202020", fg="red", relief="flat", bd=0)
    btn_close.pack(side="right", padx=(2, 8))

    # === Make popup draggable on its own ===
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
                   wraplength=400, justify="left", anchor="nw")
    lbl.pack(padx=(8, 0), pady=6, anchor="nw", fill="x")

    fixed_popups[col] = {
        "win": popup,
        "col": col,
        "row": row,
        "height": height
    }

    popup_index = (popup_index + 1) % 3

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