import tkinter as tk
from tkinter import ttk
import threading
from voice_listener_vad import listen_once
from voice_listener_google import start_google_listening, stop_google_listening
from memory_manager import get_full_memory_log
from ask_gpt import ask_gpt
from local_llm_interface import ask_local_llm

# === Core Callback Router ===
def ask_with_model(prompt):
    mode = model_var.get()
    print(f"\n🧠 Mode selected: {mode}")
    print(f"📤 Prompt sent: {prompt}")

    try:
        if mode == "GPT-4":
            return ask_gpt(prompt)
        elif mode == "Local (Mistral)":
            return ask_local_llm(prompt)
        elif mode == "Auto":
            return ask_local_llm(prompt)
    except:
        return ask_gpt(prompt)

process_command_callback = ask_with_model

# === Main Window ===
root = tk.Tk()
root.title("Friday Assistant")
root.geometry("400x350+50+200")
root.configure(bg='#1f1f1f')
root.attributes("-topmost", True)
root.attributes("-alpha", 0.9)
root.overrideredirect(True)

# === Response Popup ===
popup_container = tk.Toplevel(root)
popup_container.overrideredirect(True)
popup_container.attributes("-topmost", True)
popup_container.attributes("-alpha", 0.92)
popup_container.withdraw()

bubble_frame = tk.Frame(popup_container, bg="#121212")
bubble_frame.pack(padx=10, pady=10)
response_bubbles = []

# === Display New Response Bubble ===
def show_response_popup(text):
    global response_bubbles

    if len(response_bubbles) >= 3:
        response_bubbles[0].destroy()
        response_bubbles = response_bubbles[1:]

    bubble = tk.Frame(bubble_frame, bg="#1e1e1e", padx=10, pady=6)
    lbl = tk.Label(bubble, text=text, font=("Segoe UI", 10), fg="#00FFAA",
                   bg="#1e1e1e", wraplength=280, justify="left")
    lbl.pack(anchor="w")

    btn = tk.Button(bubble, text="✖", command=lambda: remove_bubble(bubble),
                    font=("Segoe UI", 8), bg="#1e1e1e", fg="#ff6666",
                    relief="flat", bd=0)
    btn.place(relx=1.0, rely=0.0, anchor="ne")

    bubble.pack(side="left", padx=10)
    response_bubbles.append(bubble)

    x = root.winfo_x() + root.winfo_width() + 10
    y = root.winfo_y()
    popup_container.geometry(f"+{x}+{y}")
    popup_container.deiconify()

def remove_bubble(bubble):
    if bubble in response_bubbles:
        bubble.destroy()
        response_bubbles.remove(bubble)

# === Input & Output Fields ===
font_main = ("Segoe UI", 11)

model_var = tk.StringVar(value="Auto")
model_selector = ttk.Combobox(root, textvariable=model_var, state="readonly",
                              values=["Auto", "GPT-4", "Local (Mistral)"])
model_selector.place(x=10, y=10)
model_selector.configure(width=20)

header = tk.Label(root, text="🧠 Friday is Ready", font=("Segoe UI", 14, "bold"),
                  bg="#1f1f1f", fg="#00FFAA")
header.pack(pady=(40, 5))

input_text = tk.Entry(root, font=("Segoe UI", 11), bg="#2d2d2d", fg="#FFFFFF",
                      insertbackground='white')
input_text.pack(padx=20, pady=(5, 10), fill="x")
input_text.bind("<Return>", lambda e: send_text_command())

output_text = tk.Text(root, height=6, font=("Segoe UI", 11), bg="#1f1f1f",
                      fg="#FFFFFF", wrap="word", state="disabled")
output_text.pack(padx=20, pady=(5, 10), fill="both")

# === Dragging ===
drag = {"x": 0, "y": 0}

def start_drag(e):
    drag["x"], drag["y"] = e.x, e.y

def do_drag(e):
    dx, dy = e.x - drag["x"], e.y - drag["y"]
    x, y = root.winfo_x() + dx, root.winfo_y() + dy
    root.geometry(f"+{x}+{y}")
    popup_container.geometry(f"+{x + root.winfo_width() + 10}+{y}")

header.bind("<Button-1>", start_drag)
header.bind("<B1-Motion>", do_drag)

# === Actions ===
def send_text_command():
    user_input = input_text.get().strip()
    if not user_input:
        return
    output_text.config(state="normal")
    output_text.insert(tk.END, f"You: {user_input}\n")
    output_text.config(state="disabled")
    input_text.delete(0, tk.END)

    def run():
        response = process_command_callback(user_input)
        show_response_popup(response)

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
            show_response_popup(response)

    threading.Thread(target=run).start()

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
            show_response_popup(response)
            return "🧠 Processed"

        start_google_listening(update_ui, handle)

    else:
        stop_google_listening()
        live_btn.config(text="🟢 Google STT")
        google_active[0] = False

# === Buttons ===
btn_frame = tk.Frame(root, bg="#1f1f1f")
btn_frame.pack(pady=(0, 10))

tk.Button(btn_frame, text="Send", command=send_text_command, font=font_main,
          bg="#444", fg="#FFF", width=10).grid(row=0, column=0, padx=10)

tk.Button(btn_frame, text="🎤 Listen", command=send_voice_command, font=font_main,
          bg="#444", fg="#FFF", width=10).grid(row=0, column=1, padx=10)

live_btn = tk.Button(btn_frame, text="🟢 Google STT", command=toggle_google_mode, font=font_main,
                     bg="#444", fg="#FFF", width=14)
live_btn.grid(row=0, column=2, padx=10)

tk.Button(root, text="✖", command=root.destroy, font=("Segoe UI", 10),
          bg="#aa3333", fg="white").pack(side="bottom", pady=5)

# === Hook Launch ===
def update_overlay(_, __, status):
    output_text.config(state="normal")
    output_text.insert(tk.END, f"{status}\n")
    output_text.config(state="disabled")

def launch_overlay():
    past = get_full_memory_log()
    if past:
        past = [past[-1]]
        output_text.config(state="normal")
        output_text.insert(tk.END, "🔁 Previous Session:\n\n")
        for entry in past:
            role = entry.get("role", "user").capitalize()
            content = entry.get("content", "")
            output_text.insert(tk.END, f"{role}: {content}\n")
        output_text.insert(tk.END, "\n")
        output_text.config(state="disabled")
    root.mainloop()

on_listen_trigger = []
on_send_trigger = []
