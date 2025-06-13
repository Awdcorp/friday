import tkinter as tk
from tkinter import ttk
import threading
from voice_listener_vad import listen_once
from voice_listener_google import start_google_listening, stop_google_listening
from memory_manager import get_full_memory_log
from ask_gpt import ask_gpt
from local_llm_interface import ask_local_llm

# === Unified Prompt Router ===
def ask_with_model(prompt):
    mode = model_var.get()
    print(f"\n🧠 Mode selected: {mode}")
    print(f"📤 Prompt sent: {prompt}")

    if mode == "GPT-4":
        print("🌐 Sending to GPT-4 (Cloud)")
        return ask_gpt(prompt)
    elif mode == "Local (Mistral)":
        print("💻 Sending to Local LLM (Mistral via Ollama)")
        return ask_local_llm(prompt)
    elif mode == "Auto":
        try:
            print("🔄 Trying Local LLM first...")
            return ask_local_llm(prompt)
        except Exception as e:
            print("⚠️ Local LLM failed, switching to GPT.")
            return ask_gpt(prompt)

# === External Callback Handler ===
process_command_callback = ask_with_model

# === Main Window ===
root = tk.Tk()
root.title("Friday Assistant")
root.geometry("400x350+50+200")
root.configure(bg='#1f1f1f')
root.attributes("-topmost", True)
root.attributes("-alpha", 0.9)
root.overrideredirect(True)

# === Floating Container for Response Bubbles ===
popup_container = tk.Toplevel(root)
popup_container.overrideredirect(True)
popup_container.attributes("-topmost", True)
popup_container.attributes("-alpha", 0.0)
popup_container.configure(bg="")
popup_container.withdraw()

popup_grid_frame = tk.Frame(popup_container, bg="", bd=0, highlightthickness=0)
popup_grid_frame.pack(padx=6, pady=6)

response_bubbles = []

# === Model Selector Dropdown ===
model_var = tk.StringVar(value="Auto")
model_selector = ttk.Combobox(root, textvariable=model_var, state="readonly",
                              values=["Auto", "GPT-4", "Local (Mistral)"])
model_selector.place(x=10, y=10)
model_selector.configure(width=20)

# === GPT Text Area (fallback) + Close Popup Logic ===
def refresh_bubble_layout():
    for idx, bubble in enumerate(response_bubbles):
        bubble.grid(row=0, column=idx, padx=10, pady=10, sticky="n")

def remove_bubble(frame):
    frame.grid_forget()
    if frame in response_bubbles:
        response_bubbles.remove(frame)
    refresh_bubble_layout()

def show_response_popup(text):
    global response_bubbles

    if len(response_bubbles) >= 3:
        response_bubbles[0].destroy()
        response_bubbles = response_bubbles[1:]

    frame = tk.Frame(popup_grid_frame, bg="#1e1e1e", bd=0, highlightthickness=0)

    label = tk.Label(
        frame, text=f"{text}", font=("Segoe UI", 10),
        bg="#1e1e1e", fg="#00FFAA",
        wraplength=200, justify="left", anchor="nw"
    )
    label.pack(side="top", anchor="w", padx=10, pady=6)

    close_btn = tk.Button(
        frame, text="✖", command=lambda: remove_bubble(frame),
        font=("Segoe UI", 8), bg="#1e1e1e", fg="#ff6666",
        relief="flat", bd=0, highlightthickness=0
    )
    close_btn.place(relx=1.0, rely=0.0, anchor="ne", x=-4, y=4)

    response_bubbles.append(frame)
    refresh_bubble_layout()

    x = root.winfo_x() + root.winfo_width() + 10
    y = root.winfo_y()
    popup_container.geometry(f"+{x}+{y}")
    popup_container.attributes("-alpha", 0.92)
    popup_container.deiconify()

# === Styling ===
text_fg = "#FFFFFF"
btn_bg = "#444"
btn_fg = "#FFF"
font_main = ("Segoe UI", 11)

# === Header ===
header = tk.Label(root, text="🧠 Friday is Ready", font=("Segoe UI", 14, "bold"),
                  bg="#1f1f1f", fg="#00FFAA")
header.pack(pady=(40, 5))

# === Input Field ===
input_text = tk.Entry(root, font=font_main, bg="#2d2d2d", fg=text_fg, insertbackground='white')
input_text.pack(padx=20, pady=(5, 10), fill="x")
input_text.bind("<Return>", lambda event: send_text_command())

# === Output Display (Fallback)
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
    popup_container.geometry(f"+{x + root.winfo_width() + 10}+{y}")

header.bind("<Button-1>", start_drag)
header.bind("<B1-Motion>", do_drag)

# === Text Command Input ===
def send_text_command():
    user_input = input_text.get().strip()
    if not user_input:
        return

    output_text.config(state="normal")
    output_text.insert(tk.END, f"You: {user_input}\n")
    output_text.config(state="disabled")
    input_text.delete(0, tk.END)

    def process():
        response = process_command_callback(user_input)
        show_response_popup(response)

    threading.Thread(target=process).start()

# === Voice Command Input ===
def send_voice_command():
    output_text.config(state="normal")
    output_text.insert(tk.END, "🎤 Listening...\n")
    output_text.config(state="disabled")

    def listen_and_process():
        transcript = listen_once()
        if transcript.strip():  # Only process if not empty
            output_text.config(state="normal")
            output_text.insert(tk.END, f"You (Voice): {transcript}\n")
            output_text.config(state="disabled")
            response = process_command_callback(transcript)
            show_response_popup(response)
        else:
            print("⚠️ Empty voice input skipped.")


    threading.Thread(target=listen_and_process).start()

# === Google Live Mode Trigger ===
def start_google_mode():
    def update_ui(_1, _2, status):
        if status.startswith("🧠 Final:"):
            final_transcript = status.replace("🧠 Final:", "").strip()
            output_text.config(state="normal")
            output_text.insert(tk.END, f"You (Voice): {final_transcript}\n")
            output_text.config(state="disabled")

    def handle_final_transcript(transcript):
        response = process_command_callback(transcript)
        show_response_popup(response)
        return "🧠 Processed"

    threading.Thread(target=start_google_listening, args=(update_ui, handle_final_transcript)).start()

# === Buttons ===
btn_frame = tk.Frame(root, bg="#1f1f1f")
btn_frame.pack(pady=(0, 10))

send_btn = tk.Button(btn_frame, text="Send", command=send_text_command, font=font_main,
                     bg=btn_bg, fg=btn_fg, width=10)
send_btn.grid(row=0, column=0, padx=10)

voice_btn = tk.Button(btn_frame, text="🎤 Listen", command=send_voice_command, font=font_main,
                      bg=btn_bg, fg=btn_fg, width=10)
voice_btn.grid(row=0, column=1, padx=10)

live_btn = tk.Button(btn_frame, text="🟢 Google STT", command=start_google_mode, font=font_main,
                     bg=btn_bg, fg=btn_fg, width=14)
live_btn.grid(row=0, column=2, padx=10)

exit_btn = tk.Button(root, text="✖", command=root.destroy, font=("Segoe UI", 10),
                     bg="#aa3333", fg="white")
exit_btn.pack(side="bottom", pady=5)

# === External Functions ===
def update_overlay(obj_list, screen_text, status):
    output_text.config(state="normal")
    output_text.insert(tk.END, f"{status}\n")
    output_text.config(state="disabled")

def launch_overlay():
    past = get_full_memory_log()
    if past:
        past = [past[-1]]
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

# Dummy triggers
on_listen_trigger = []
on_send_trigger = []
