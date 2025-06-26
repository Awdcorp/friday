"""
🧐 Intent Classifier
------------------------
Analyzes clipboard content and classifies what kind of task it represents.
Detects code patches, commands, file instructions, function edits, etc.
"""

import re
from ..agent_core.task_router import route_task

# === Patterns to detect basic task types ===
CODE_DEF_PATTERN = re.compile(r'^\s*(def|class)\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(?.*\)?\s*:', re.MULTILINE)
FILENAME_HINT_PATTERN = re.compile(r'(in\s+)?[`"]?([\w_\-/]+\.py)[`"]?', re.IGNORECASE)
FUNC_HINT_PATTERN = re.compile(r'\b(?:in|update|replace|modify)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\)', re.IGNORECASE)

# === Main Entry ===
def classify_clipboard_content(text: str):
    task_type = "unknown"
    file_guess = None
    function_guess = None

    # === Detect code ===
    is_code = bool(CODE_DEF_PATTERN.search(text)) or ('return' in text and 'def' in text)
    if is_code:
        task_type = "code_patch"

    # === Try to detect file name ===
    file_match = FILENAME_HINT_PATTERN.search(text)
    if file_match:
        file_guess = file_match.group(2)

    # === Try to detect function target ===
    func_match = FUNC_HINT_PATTERN.search(text)
    if func_match:
        function_guess = func_match.group(1)

    # === Build classification result ===
    result = {
        "task_type": task_type,
        "raw_text": text,
        "file_guess": file_guess,
        "function_guess": function_guess
    }

    print(f"[intent_classifier] 🧐 Classification result: {result}")
    route_task(result)
