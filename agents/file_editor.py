"""
file_editor.py
--------------
Basic file editing utilities for applying structured code patches to source files.
Supports line replacement, function replacement, and insertion above/below keywords.
"""

import re

def replace_line_containing(file_path: str, keyword: str, new_line: str) -> bool:
    """
    Replace the first line in a file that contains the given keyword with the new_line.
    Indentation will be preserved automatically.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        replaced = False
        for i, line in enumerate(lines):
            if keyword in line:
                indent = line[:len(line) - len(line.lstrip())]
                lines[i] = f"{indent}{new_line}\n"
                replaced = True
                break

        if replaced:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"[file_editor] ✅ Replaced line containing '{keyword}' in {file_path}")
            return True
        else:
            print(f"[file_editor] ⚠️ Keyword '{keyword}' not found in {file_path}")
            return False

    except Exception as e:
        print(f"[file_editor] ❌ Error replacing line: {e}")
        return False


def insert_above(file_path: str, keyword: str, new_line: str) -> bool:
    """
    Insert a line above the line that contains the given keyword.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            if keyword in line:
                indent = line[:len(line) - len(line.lstrip())]
                lines.insert(i, f"{indent}{new_line}\n")
                break
        else:
            print(f"[file_editor] ⚠️ Keyword '{keyword}' not found in {file_path}")
            return False

        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"[file_editor] ✅ Inserted above line with keyword '{keyword}' in {file_path}")
        return True

    except Exception as e:
        print(f"[file_editor] ❌ Error in insert_above: {e}")
        return False


def insert_below(file_path: str, keyword: str, new_line: str) -> bool:
    """
    Insert a line below the line that contains the given keyword.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            if keyword in line:
                indent = line[:len(line) - len(line.lstrip())]
                lines.insert(i + 1, f"{indent}{new_line}\n")
                break
        else:
            print(f"[file_editor] ⚠️ Keyword '{keyword}' not found in {file_path}")
            return False

        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"[file_editor] ✅ Inserted below line with keyword '{keyword}' in {file_path}")
        return True

    except Exception as e:
        print(f"[file_editor] ❌ Error in insert_below: {e}")
        return False


def replace_or_insert_function(file_path: str, func_name: str, new_code: str) -> bool:
    """
    Replace an existing function by name, or insert it at the end if not found.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        pattern = re.compile(rf'^\s*def\s+{re.escape(func_name)}\s*\(.*\)\s*:')
        start = end = None

        # Find the function block
        for i, line in enumerate(lines):
            if pattern.match(line):
                start = i
                indent_level = len(line) - len(line.lstrip())
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() == "":
                        continue
                    current_indent = len(lines[j]) - len(lines[j].lstrip())
                    if current_indent <= indent_level:
                        end = j
                        break
                if end is None:
                    end = len(lines)
                break

        new_block = new_code.strip().splitlines(keepends=True)
        new_block = [line if line.endswith('\n') else line + '\n' for line in new_block]

        if start is not None:
            # Replace function
            lines = lines[:start] + new_block + lines[end:]
            print(f"[file_editor] 🔁 Replaced existing function '{func_name}' in {file_path}")
        else:
            # Append to file
            lines.append("\n" + "".join(new_block))
            print(f"[file_editor] ➕ Appended new function '{func_name}' to {file_path}")

        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        return True

    except Exception as e:
        print(f"[file_editor] ❌ Error in replace_or_insert_function: {e}")
        return False

def append_to_file(file_path: str, new_code: str) -> bool:
    """
    Appends the given code block to the end of the file.
    """
    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write("\n" + new_code.strip() + "\n")
        print(f"[file_editor] ✅ Appended new code to {file_path}")
        return True
    except Exception as e:
        print(f"[file_editor] ❌ Error appending to file: {e}")
        return False


def prepend_to_file(file_path: str, new_code: str) -> bool:
    """
    Prepends the given code block to the top of the file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        lines = [new_code.strip() + "\n\n"] + lines

        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"[file_editor] ✅ Prepended code to top of {file_path}")
        return True
    except Exception as e:
        print(f"[file_editor] ❌ Error prepending to file: {e}")
        return False


def comment_out_line(file_path: str, keyword: str) -> bool:
    """
    Finds the first line containing the keyword and comments it out.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            if keyword in line and not line.strip().startswith("#"):
                lines[i] = f"# {line}"
                break
        else:
            print(f"[file_editor] ⚠️ Keyword not found or already commented: {keyword}")
            return False

        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"[file_editor] ✅ Commented out line with '{keyword}' in {file_path}")
        return True

    except Exception as e:
        print(f"[file_editor] ❌ Error commenting out line: {e}")
        return False

def apply_patch(patch: dict) -> bool:
    """
    Dispatch a patch instruction to the correct editor function.
    Expected keys in patch:
        - action: str ("replace_line", "insert_above", "insert_below", etc.)
        - file: str (target file path)
        - target: str (line keyword or function name)
        - content: str (new line or function block)

    Returns:
        - True if applied successfully, False otherwise
    """
    action = patch.get("action")
    file_path = patch.get("file")
    target = patch.get("target", "")
    content = patch.get("content", "")

    if action == "replace_line":
        return replace_line_containing(file_path, target, content)
    elif action == "insert_above":
        return insert_above(file_path, target, content)
    elif action == "insert_below":
        return insert_below(file_path, target, content)
    elif action == "replace_function":
        return replace_or_insert_function(file_path, target, content)
    elif action == "prepend":
        return prepend_to_file(file_path, content)
    elif action == "append":
        return append_to_file(file_path, content)
    elif action == "comment_out":
        return comment_out_line(file_path, target)
    else:
        print(f"[file_editor] ❌ Unknown patch action: {action}")
        return False
