"""
Friday File Editor
-------------------
Applies structured edit instructions to text/code files.
Supports editing by line number, pattern match, block match, and function scope.
"""

import re
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# === Core Editor ===
def apply_patch(file_path, patch):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    original_lines = lines[:]
    updated_lines = lines[:]

    action = patch['action']

    if action == 'replace_line_number':
        updated_lines[patch['line'] - 1] = patch['new_line'] + '\n'

    elif action == 'insert_above_line_number':
        idx = patch['line'] - 1
        for new in reversed(patch['lines']):
            updated_lines.insert(idx, new + '\n')

    elif action == 'insert_below_line_number':
        idx = patch['line'] 
        for new in reversed(patch['lines']):
            updated_lines.insert(idx, new + '\n')

    elif action == 'delete_line_number':
        del updated_lines[patch['line'] - 1]

    elif action == 'replace_line_matching':
        updated_lines = [
            (patch['new_line'] + '\n') if line.strip() == patch['match'].strip() else line
            for line in updated_lines
        ]

    elif action == 'insert_above_match':
        for i, line in enumerate(updated_lines):
            if line.strip() == patch['match'].strip():
                for new in reversed(patch['lines']):
                    updated_lines.insert(i, new + '\n')
                break

    elif action == 'insert_below_match':
        for i, line in enumerate(updated_lines):
            if line.strip() == patch['match'].strip():
                for new in reversed(patch['lines']):
                    updated_lines.insert(i + 1, new + '\n')
                break

    elif action == 'delete_lines_matching':
        updated_lines = [line for line in updated_lines if line.strip() != patch['match'].strip()]

    elif action == 'replace_block_match':
        block = patch['match_block']
        for i in range(len(updated_lines) - len(block) + 1):
            window = [updated_lines[i + j].rstrip('\n') for j in range(len(block))]
            if window == block:
                updated_lines[i:i + len(block)] = [line + '\n' for line in patch['new_block']]
                break

    elif action == 'insert_below_match_block':
        block = patch['match_block']
        for i in range(len(updated_lines) - len(block) + 1):
            window = [updated_lines[i + j].rstrip('\n') for j in range(len(block))]
            if window == block:
                insertion_point = i + len(block)
                for new in reversed(patch['lines']):
                    updated_lines.insert(insertion_point, new + '\n')
                break

    elif action == 'delete_block_match':
        block = patch['match_block']
        for i in range(len(updated_lines) - len(block) + 1):
            window = [updated_lines[i + j].rstrip('\n') for j in range(len(block))]
            if window == block:
                del updated_lines[i:i + len(block)]
                break

    # Add more actions here if needed

    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(updated_lines)

    return original_lines, updated_lines


# === Patch Executor ===
def apply_patch_file(patch_file):
    import json
    print(f"📥 Loading patch file: {patch_file}")
    print("🔍 Looking for:", os.path.abspath(patch_file))

    with open(patch_file, 'r', encoding='utf-8') as f:
        patch_data = json.load(f)

    file_path = patch_data['file']
    print(f"📂 Editing file: {file_path}")

    for i, patch in enumerate(patch_data['patches']):
        print(f"🔧 Applying patch #{i+1}: {patch['action']}")
        apply_patch(file_path, patch)

    print("✅ Done applying patches.")


# === Sample usage ===
if __name__ == '__main__':
    apply_patch_file('sample_patch.json')