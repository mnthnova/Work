import subprocess
import os

def get_diff_output():
    """Runs git diff with 3 lines of context (-U3)."""
    try:
        return subprocess.check_output(['git', 'diff', '-U3', 'HEAD~1', 'HEAD'], text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running git diff: {e}")
        return ""

def call_translation_api(text, target_lang):
    """Replace with your actual translation API call."""
    return f".. TRANSLATED TO {target_lang.upper()} ..\n{text}"

def process_hunk(file_path, target_path, target_lang, context_lines, added_lines):
    """Translates the block and injects it into the target file."""
    if not context_lines or not added_lines:
        return

    # Translate the new addition
    new_translated_text = call_translation_api('\n'.join(added_lines), target_lang)
    
    # Translate the context to find the anchor in the target file
    translated_context = [call_translation_api(line, target_lang) for line in context_lines]

    with open(target_path, 'r', encoding='utf-8') as f:
        target_file_lines = f.read().splitlines()

    # Search for the 3-line context block
    insertion_index = -1
    for i in range(len(target_file_lines) - len(translated_context)):
        if target_file_lines[i:i+len(translated_context)] == translated_context:
            insertion_index = i + len(translated_context)
            break

    if insertion_index != -1:
        # Inject the new text right after the context block
        target_file_lines.insert(insertion_index, new_translated_text)
        
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(target_file_lines) + '\n')
        print(f"Successfully synced hunk to {target_path}")
    else:
        print(f"WARNING: Could not find matching context block in {target_path}. Skipping hunk.")

def main():
    diff_text = get_diff_output()
    if not diff_text:
        return

    current_file = ""
    context_lines = []
    added_lines = []

    # A simplified parser to extract context and additions from the diff
    for line in diff_text.splitlines():
        if line.startswith('+++ b/'):
            # Trigger sync for the previous file before moving to the next
            current_file = line.replace('+++ b/', '')
            context_lines = []
            added_lines = []
        elif line.startswith(' ') and current_file:
            context_lines.append(line[1:]) # Keep context without the space
        elif line.startswith('+') and not line.startswith('+++'):
            added_lines.append(line[1:])
            
        # When we hit the end of a block, process it
        if added_lines and line.startswith((' ', '-', '@@')) and current_file:
            if current_file.startswith('content/') and current_file.endswith('.rst'):
                target = current_file.replace('content/', 'content_ja/', 1)
                os.makedirs(os.path.dirname(target), exist_ok=True)
                process_hunk(current_file, target, 'ja', context_lines[-3:], added_lines)
            
            added_lines = [] # Reset for the next addition in the same file

if __name__ == "__main__":
    main()
