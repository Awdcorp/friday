"""
🚧 Task Router
------------------------
Receives classified tasks from intent classifier.
Routes to the appropriate handler: file editing, running, UI action, etc.
"""

from .file_editor import apply_code_patch
# Future modules:
# from agent_modules.terminal_executor import run_project
# from agents.gui_mouse import click_button_by_text


def route_task(task):
    task_type = task.get("task_type")

    if task_type == "code_patch":
        print("[task_router] 🚧 Routing to file_editor...")
        apply_code_patch(task)

    else:
        print(f"[task_router] ❓ No handler for task type: {task_type}")
