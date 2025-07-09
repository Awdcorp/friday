from agents.gui_mouse import click_text

def run_text_command_interface():
    print("🖱️ Friday Mouse Control — Text Mode")
    while True:
        cmd = input("Enter text to click (or 'exit'): ").strip()
        if cmd.lower() == 'exit':
            break
        success = click_text(cmd)
        if success:
            print(f"✅ Clicked on '{cmd}'")
        else:
            print(f"❌ Could not find '{cmd}' on screen")

if __name__ == "__main__":
    run_text_command_interface()
