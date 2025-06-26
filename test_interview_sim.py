from agents.file_editor import apply_patch

patches = [
    {
        "action": "insert_below",
        "file": "agents/file_editor.py",
        "target": "print(f\"[file_editor] ❌ Unknown patch action: {action}\")\n    return False",
        "content": "print('Inserted after replaced line')"
    }
]

for i, patch in enumerate(patches):
    print(f"\n🧩 Running patch {i+1}: {patch['action']}")
    success = apply_patch(patch)
    print(f"✅ Patch {i+1} result: {success}")
