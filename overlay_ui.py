import tkinter as tk
from tkinter import ttk
import threading
from voice_listener_vad import listen_once
from voice_listener_google import start_mic_listener, stop_mic_listener
from voice_listener_system import start_system_listener, stop_system_listener
from memory_manager import get_full_memory_log
from ask_gpt import ask_gpt
from local_llm_interface import ask_local_llm
from conversation_mode.conversation_mode_handler import start_conversation_mode, stop_conversation_mode, run_single_utterance  
from interview_mode.interview_mode_handler import start_interview_mode, stop_interview_mode

# === Core Callback ===
def ask_with_model(prompt):
    mode = model_var.get()
    try:
        if mode == "GPT-4": return ask_gpt(prompt)
        elif mode == "Local (Mistral)": return ask_local_llm(prompt)
        elif mode == "Auto": return ask_local_llm(prompt)
    except: return ask_gpt(prompt)

process_command_callback = ask_with_model

# === Global State ===
conversation_active = [False]
interview_active = [False]

# === Main Window ===
root = tk.Tk()
root.title("Friday Assistant")  # 🖼️ Change app window title here
root.geometry("400x500+1200+200")  # 📏 Change window size & initial position here
root.configure(bg='#1f1f1f')  # 🎨 Main background color of the app
root.attributes("-topmost", True)
root.attributes("-alpha", 0.9)  # 🪟 Window transparency (0.0 to 1.0)
root.overrideredirect(True)  # 🖼️ Remove window decorations (title bar, borders)

main_minimized = [False]  # Track minimize state
drag = {"x": 0, "y": 0} 
fixed_popups = [None, None, None]
popup_index = 0
minimized_popups = []
last_main_position = [None]

# === Popup Layout Constants ===
POPUP_WIDTH = 420
POPUP_HEIGHT = 600
START_X = 50
START_Y = 50
COL_SPACING = 100    
ROW_SPACING = 20
MAX_COLS = 2 # Controls how many floating popups are allowed side by side

# === Interview Audio Source Selector ===
interview_source_var = tk.StringVar(value="system")

# === Interview Mode Toggle Button ===
def toggle_interview_mode():
    if not interview_active[0]:
        interview_active[0] = True
        interview_btn.config(text="🎙️ Interview Mode: On")
        selected_source = interview_source_var.get()
        print(f"🔊 Starting Interview Mode with source='{selected_source}'")
        start_interview_mode(update_text_box_only, handle_interview_response,
                             profile="software_engineer",
                             source=selected_source)
    else:
        interview_active[0] = False
        interview_btn.config(text="🎙️ Interview Mode: Off")
        stop_interview_mode()

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
    last_main_position[0] = (root.winfo_x(), root.winfo_y())
    root.geometry(f"400x64+{last_main_position[0][0]}+{last_main_position[0][1]}")
    for entry in fixed_popups:
        if entry and entry['win'].winfo_exists():
            entry['win'].withdraw()
            if all(entry['win'] != p for p, _ in minimized_popups):
                title = entry.get("title", "Friday Message")  # 🆕 Get stored dynamic title
                minimized_popups.append((entry['win'], title))
    render_minimized_bar()

def restore_main():
    if main_minimized[0]:
        header.pack(pady=(10, 5))
        input_text.pack(padx=20, pady=(0, 10), fill="x")
        output_text.pack(padx=20, pady=(0, 10), fill="both")
        btn_frame.pack(pady=(0, 10))
        model_selector.pack(pady=(0, 10))
        mode_btn.pack(pady=(0, 10))
        interview_btn.pack(pady=(0, 10))
        interview_audio_frame.pack(pady=(0, 10))
        conversation_btn.pack(pady=(0, 0))
        audio_mode_frame.pack(pady=(0, 10))
        alpha_frame.pack(pady=(0, 10))

        if last_main_position[0]:
            root.geometry(f"400x500+{last_main_position[0][0]}+{last_main_position[0][1]}")
        else:
            root.geometry("400x500+1200+200")  # fallback
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
header = tk.Label(root, text="🧠 Friday is Ready", font=("Segoe UI", 14, "bold"), bg="#1f1f1f", fg="#CED6D3")
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

model_var = tk.StringVar(value="GPT-4")
model_selector = ttk.Combobox(root, textvariable=model_var, state="readonly",
                              values=["GPT-4", "Auto", "Local (Mistral)"])
model_selector.pack(pady=(0, 10))
model_selector.configure(width=20)

interview_btn = tk.Button(root, text="🎙️ Interview Mode: Off", command=toggle_interview_mode,
                          font=("Segoe UI", 10), bg="#555", fg="#fff", relief="flat")
interview_btn.pack(pady=(0, 10))

# Interview Audio Source Radio Buttons
interview_audio_frame = tk.Frame(root, bg="#1f1f1f")
interview_audio_frame.pack(pady=(0, 10))

tk.Label(interview_audio_frame, text="🎧 Interview Input:", bg="#1f1f1f", fg="#fff").pack(side="left", padx=(0, 6))

for mode, label in [("mic", "Mic"), ("system", "System")]:
    btn = tk.Radiobutton(interview_audio_frame, text=label, value=mode,
                         variable=interview_source_var,
                         font=("Segoe UI", 9), bg="#1f1f1f", fg="#fff",
                         activebackground="#2a2a2a", selectcolor="#444")
    btn.pack(side="left", padx=6)
    
# === Mode Toggle ===
mode_var = tk.StringVar(value="Chat")  # Default is Chat mode

def toggle_mode():
    current = mode_var.get()
    mode_var.set("Command" if current == "Chat" else "Chat")
    mode_btn.config(text=f"🧠 Mode: {mode_var.get()}")

mode_btn = tk.Button(root, text=f"🧠 Mode: {mode_var.get()}", command=toggle_mode,
                     font=("Segoe UI", 10), bg="#555", fg="#fff", relief="flat")
mode_btn.pack(pady=(0, 10))

def toggle_conversation_mode():
    if not conversation_active[0]:
        conversation_active[0] = True
        conversation_btn.config(text="🎙️ Passive Mode: On")
        print("🟢 Conversation Mode: ON")
        def handle_transcript(text):
            print(f"📡 Passive handle_transcript text='{text}'")
            output_text.config(state="normal")
            if text.startswith("[Interim]"):
                output_text.insert(tk.END, f"{text}\n")
            else:
                output_text.insert(tk.END, f"🎙️ Final: {text}\n")
            output_text.config(state="disabled")

            if not text.startswith("[Interim]"):
                def run():
                    print(f"🛠 run_single_utterance for passive='{text}'")
                    response = run_single_utterance(text)
                    print(f"📝 Passive got response='{response}'")
                    if response:
                        show_floating_response(response)
                threading.Thread(target=run).start()

        start_conversation_mode(update_overlay, handle_transcript)
    else:
        conversation_active[0] = False
        conversation_btn.config(text="🎙️ Passive Mode: Off")
        stop_conversation_mode()
        print("🔴 Conversation Mode: OFF")

# Add toggle button to UI
conversation_btn = tk.Button(root, text="🎙️ Passive Mode: Off", command=toggle_conversation_mode,
                             font=("Segoe UI", 10), bg="#555", fg="#fff", relief="flat")
conversation_btn.pack(pady=(0, 10))

# === Audio Input Mode Selector ===
from conversation_mode.conversation_config import AUDIO_INPUT_MODE, set_audio_input_mode

audio_mode_var = tk.StringVar(value=AUDIO_INPUT_MODE)  # default from config

def update_audio_mode():
    selected = audio_mode_var.get()
    set_audio_input_mode(selected)

audio_mode_frame = tk.Frame(root, bg="#1f1f1f")
audio_mode_frame.pack(pady=(0, 10))

tk.Label(audio_mode_frame, text="🎛 Audio Source:", bg="#1f1f1f", fg="#fff").pack(side="left", padx=(0, 6))

for mode, label in [("mic", "Mic Only"), ("system", "System Only"), ("both", "Both")]:
    btn = tk.Radiobutton(audio_mode_frame, text=label, value=mode,
                         variable=audio_mode_var, command=update_audio_mode,
                         font=("Segoe UI", 9), bg="#1f1f1f", fg="#fff",
                         activebackground="#2a2a2a", selectcolor="#444")
    btn.pack(side="left", padx=6)

# === Transparency Slider ===
def on_alpha_change(value):
    alpha = float(value)
    root.attributes("-alpha", alpha)
    for entry in fixed_popups:
        if entry and entry["win"].winfo_exists():
            entry["win"].attributes("-alpha", alpha)

# === Transparency Controls in One Line ===
alpha_frame = tk.Frame(root, bg="#1f1f1f")
alpha_frame.pack(pady=(0, 10))

tk.Label(alpha_frame, text="Set Transparency", bg="#1f1f1f", fg="#FFFFFF", font=("Segoe UI", 9)).pack(side="left", padx=(0, 10))

alpha_slider = tk.Scale(alpha_frame, from_=0.2, to=1.0, resolution=0.01, orient="horizontal",
                        length=180, command=on_alpha_change, bg="#1f1f1f", fg="#FFFFFF",
                        troughcolor="#444", highlightthickness=0)
alpha_slider.set(root.attributes("-alpha"))
alpha_slider.pack(side="left")

# === Floating Response Popup ===
def show_floating_response(text, popup_id=1):
    global popup_index, fixed_popups

    col = popup_id - 1  # convert popup_id to column index
    if col < 0 or col >= MAX_COLS:
        col = 0  # fallback if invalid

    line_count = text.count('\n') + 1
    line_height = 55
    base_height = 100 + (line_count * line_height)
    max_height = 800
    default_height = min(base_height, max_height)

    px = START_X + col * (POPUP_WIDTH + COL_SPACING)
    py = START_Y

    if fixed_popups[col]:
        old_win = fixed_popups[col]['win']
        try:
            px = old_win.winfo_x()
            py = old_win.winfo_y()
            popup_width = old_win.winfo_width()
            popup_height = old_win.winfo_height()
        except:
            popup_width, popup_height = POPUP_WIDTH, default_height
        old_win.destroy()
        minimized_popups[:] = [(p, t) for (p, t) in minimized_popups if p != old_win]
        render_minimized_bar()
    else:
        popup_width, popup_height = POPUP_WIDTH, default_height

    popup = tk.Toplevel(root)
    popup.overrideredirect(True)
    popup.attributes("-topmost", True)
    popup.attributes("-alpha", root.attributes("-alpha"))
    popup.geometry(f"{popup_width}x{popup_height}+{px}+{py}")
    popup.configure(bg="#1f1f1f", highlightthickness=1, highlightbackground="#444", bd=2)

    outer = tk.Frame(popup, bg="#2b2b2b", bd=0, highlightthickness=0)
    outer.pack(expand=True, fill="both", padx=0, pady=0)

    title_text = f"{popup_id} " + text.strip().splitlines()[0][:7] if text.strip() else "Friday Message"

    titlebar = tk.Frame(outer, bg="#202020", height=28)
    titlebar.pack(fill="x", side="top")

    title = tk.Label(titlebar, text=f"🪡 {title_text}", bg="#202020", fg="#FFFFFF", font=("Segoe UI", 9, "bold"))
    title.pack(side="left", padx=8)

    def minimize_popup():
        if all(popup != p for p, _ in minimized_popups):
            minimized_popups.append((popup, title_text))
        popup.withdraw()
        render_minimized_bar()

    btn_close = tk.Button(titlebar, text="✖", font=("Segoe UI", 9), command=lambda: on_popup_close(popup),
                          bg="#202020", fg="red", relief="flat", bd=0)
    btn_close.pack(side="right", padx=(2, 8))

    btn_minimize = tk.Button(titlebar, text="—", font=("Segoe UI", 9), command=minimize_popup,
                             bg="#202020", fg="white", relief="flat", bd=0)
    btn_minimize.pack(side="right", padx=(4, 2))

    def copy_to_clipboard():
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        print("📋 Copied popup text to clipboard")

    btn_copy = tk.Button(titlebar, text="📋", font=("Segoe UI", 9), command=copy_to_clipboard,
                        bg="#202020", fg="white", relief="flat", bd=0)
    btn_copy.pack(side="right", padx=(2, 2))
    
    def popup_drag_start(e): popup._drag_offset = (e.x, e.y)
    def popup_drag_move(e):
        dx, dy = popup._drag_offset
        popup.geometry(f"+{e.x_root - dx}+{e.y_root - dy}")

    titlebar.bind("<Button-1>", popup_drag_start)
    titlebar.bind("<B1-Motion>", popup_drag_move)

    # === Scrollable Canvas
    canvas = tk.Canvas(outer, bg="#2b2b2b", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    frame = tk.Frame(canvas, bg="#2b2b2b")
    canvas_window = canvas.create_window((0, 0), window=frame, anchor='nw')

    def on_configure(event): canvas.configure(scrollregion=canvas.bbox("all"))
    frame.bind("<Configure>", on_configure)

    def bind_scroll():
        def _on_mousewheel(e): canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Enter>", lambda e: bind_scroll())
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
    bind_scroll()

    lbl = tk.Label(frame, text=text, font=("Segoe UI", 12), fg="#DDDDDD", bg="#2b2b2b",
                   wraplength=popup_width - 20, justify="left", anchor="nw")
    lbl.pack(padx=(8, 0), pady=6, anchor="nw", fill="x")

    resize_grip = tk.Frame(popup, cursor="bottom_right_corner", bg="#444", width=10, height=10)
    resize_grip.place(relx=1.0, rely=1.0, anchor="se")

    def start_resize(e):
        popup._resize_start = (e.x_root, e.y_root, popup.winfo_width(), popup.winfo_height())

    def do_resize(e):
        x0, y0, w0, h0 = popup._resize_start
        dx, dy = e.x_root - x0, e.y_root - y0
        new_width = max(300, w0 + dx)
        new_height = max(150, h0 + dy)
        popup.geometry(f"{new_width}x{new_height}")
        lbl.config(wraplength=new_width - 20)

    resize_grip.bind("<Button-1>", start_resize)
    resize_grip.bind("<B1-Motion>", do_resize)

    fixed_popups[col] = {
        "win": popup,
        "col": col,
        "row": 0,
        "height": popup_height,
        "title": title_text
    }

    popup_index = (popup_index + 1) % MAX_COLS

# === Command Handlers ===
def send_text_command():
    user_input = input_text.get().strip()
    print(f"🎯 send_text_command: user_input='{user_input}'")
    if not user_input:
        print("⚠️ send_text_command: empty input, ignoring")
        return
    output_text.config(state="normal")
    output_text.insert(tk.END, f"You: {user_input}\n")
    output_text.config(state="disabled")
    input_text.delete(0, tk.END)
    def run():
        print(f"🛠 Running process_command_callback for text command")
        response = process_command_callback(user_input)
        print(f"📝 Text command got response='{response}'")
        show_floating_response(response)
    threading.Thread(target=run).start()

# === Voice Command Handler ===
def send_voice_command():
    print("🎤 send_voice_command: listening once")
    output_text.config(state="normal")
    output_text.insert(tk.END, "🎤 Listening...\n")
    output_text.config(state="disabled")
    def run():
        transcript = listen_once()
        print(f"🔊 send_voice_command: transcript='{transcript}'")
        if transcript.strip():
            output_text.config(state="normal")
            output_text.insert(tk.END, f"You (Voice): {transcript}\n")
            output_text.config(state="disabled")
            response = process_command_callback(transcript)
            print(f"📝 Voice command got response='{response}'")
            show_floating_response(response)
        else:
            print("⚠️ send_voice_command: empty transcript, nothing to process")
    threading.Thread(target=run).start()

# === Google STT Toggle ===
google_active = [False]
def toggle_google_mode():
    if not google_active[0]:
        google_active[0] = True
        live_btn.config(text="🔴 Stop STT")
        print("🟢 Google STT started")
        def update_ui(_1, _2, status):
            if status.startswith("🧠 Final:"):
                final = status.replace("🧠 Final:", "").strip()
                print(f"📩 Google STT final status='{final}'")
                output_text.config(state="normal")
                output_text.insert(tk.END, f"You (Voice): {final}\n")
                output_text.config(state="disabled")
        def handle(transcript):
            print(f"▶️ Google STT handle transcript='{transcript}'")
            response = process_command_callback(transcript)
            print(f"📝 STT handle got response='{response}'")
            show_floating_response(response)
            return "🧠 Processed"
        start_mic_listener(update_ui, handle)
    else:
        stop_mic_listener()
        live_btn.config(text="🟢 Google STT")
        google_active[0] = False
        print("🔴 Google STT stopped")

# Interview Mode STT → output_text only
def update_text_box_only(_, __, status):
    if status.startswith("🧠 Final:"):
        final = status.replace("🧠 Final:", "").strip()
        output_text.config(state="normal")
        output_text.insert("end", f"You (System): {final}\n")
        output_text.config(state="disabled")

# === Floating Response Renderer ===
followup_popup_refs = []

def show_followup_response(text):
    """Creates a follow-up popup using the same styling as the main floating popup."""
    popup = tk.Toplevel(root)
    popup.overrideredirect(True)
    popup.configure(bg="#111111")
    popup.wm_attributes("-topmost", 1)
    popup.wm_attributes("-alpha", 0.92)

    label = tk.Label(popup, text=text, fg="white", bg="#111111", justify="left",
                     font=("Segoe UI", 10), wraplength=400, padx=12, pady=10)
    label.pack()

    # Position offset near main popup or center
    popup.update_idletasks()
    w, h = popup.winfo_width(), popup.winfo_height()
    x = root.winfo_x() + 80
    y = root.winfo_y() + 120 + (len(followup_popup_refs) * (h + 10))
    popup.geometry(f"{w}x{h}+{x}+{y}")

    # Schedule auto-destroy
    popup.after(15000, popup.destroy)
    followup_popup_refs.append(popup)

# === Interview Response Handler with Optional Popup Control ===
def handle_interview_response(response, replace_popup=True, popup_id=1):
    print(f"[overlay_ui] 🎯 handle_interview_response: popup_id={popup_id}, replace={replace_popup}")
    if replace_popup:
        show_floating_response(response, popup_id=popup_id)
    else:
        show_followup_response(response)

# === System STT Toggle ===
system_active = [False]
def toggle_system_mode():
    if not system_active[0]:
        system_active[0] = True
        system_btn.config(text="🔴 Stop System")
        print("🟢 System STT started")
        def update_ui(_1, _2, status):
            if status.startswith("🧠 Final:"):
                final = status.replace("🧠 Final:", "").strip()
                print(f"📩 System STT final status='{final}'")
                output_text.config(state="normal")
                output_text.insert(tk.END, f"You (System): {final}\n")
                output_text.config(state="disabled")
        def handle(transcript):
            print(f"▶️ System STT handle transcript='{transcript}'")
            response = process_command_callback(transcript)
            print(f"📝 System STT handle got response='{response}'")
            show_floating_response(response)
            return "🧠 Processed"
        start_system_listener(update_ui, handle)
    else:
        stop_system_listener()
        system_btn.config(text="🟢 System Listen")
        system_active[0] = False
        print("🔴 System STT stopped")

# === Add to Button Frame ===
system_btn = tk.Button(btn_frame, text="🟢 System Listen", command=toggle_system_mode,
                       font=("Segoe UI", 10), bg="#444", fg="#FFF", width=14)
system_btn.grid(row=1, column=0, columnspan=3, pady=(10, 0), padx=10, sticky="ew")

# === Hooks ===
def update_overlay(_, __, status): show_floating_response(status)
def launch_overlay():
    past = get_full_memory_log()
    if past:
        root.after(300, lambda: show_floating_response(past[-1]['content']))
    root.mainloop()

on_listen_trigger = []
on_send_trigger = []