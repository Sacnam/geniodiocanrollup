# patcher.py
# A simple script to parse Cortex's responses and patch the project files.
import os
import re
import sys

# --- CONFIGURATION ---
# The file where you will paste Cortex's full response.
RESPONSE_FILE = "cortex_response.txt"

# A key file to check for to ensure the script is run from the correct project root.
# This is a safety measure to prevent accidental file overwrites in other directories.
SAFETY_CHECK_FILE = "src/manifest.json" 

# The marker used to split the response into individual file sections.
FILE_DELIMITER = "================================================\nFILE: "

# --- SCRIPT LOGIC ---

def main():
    """
    Main function to run the patcher.
    """
    print("Cortex Patcher Initializing...")

    # 1. Safety Check: Ensure we are in the correct directory.
    if not os.path.exists(SAFETY_CHECK_FILE):
        print(f"\n[ERROR] Safety check failed!")
        print(f"Could not find '{SAFETY_CHECK_FILE}'.")
        print("Please make sure you are running this script from the root of your 'sacnam-genio-rollup' project directory.")
        sys.exit(1)
    
    print(f"Project root verified ('{SAFETY_CHECK_FILE}' found).")

    # 2. Read the response file.
    try:
        with open(RESPONSE_FILE, 'r', encoding='utf-8') as f:
            full_response = f.read()
    except FileNotFoundError:
        print(f"\n[ERROR] Response file not found!")
        print(f"Please create a file named '{RESPONSE_FILE}' in this directory and paste Cortex's full response into it.")
        sys.exit(1)

    print(f"Read content from '{RESPONSE_FILE}'.")

    # 3. Split the response into file blocks.
    # The first split will be empty, so we skip it with [1:].
    file_blocks = full_response.split(FILE_DELIMITER)[1:]

    if not file_blocks:
        print("\n[ERROR] No file blocks found in the response.")
        print(f"Make sure the response contains sections starting with '{FILE_DELIMITER.strip()}'.")
        sys.exit(1)

    print(f"Found {len(file_blocks)} potential file blocks to process.")
    patched_files_count = 0

    # 4. Process each block.
    for block in file_blocks:
        try:
            # The first line of the block is the file path.
            path_line, content_with_code = block.split('\n', 1)
            
            # --- FIX ---
            # Clean the file path from backticks and extra whitespace.
            # Also, replace any forward slashes with the OS-specific separator.
            file_path_raw = path_line.strip()
            file_path_cleaned = file_path_raw.strip('`') # Remove backticks
            file_path = os.path.normpath(file_path_cleaned) # Normalize path for the current OS

            # Regular expression to find the code inside ```...```
            # re.DOTALL makes '.' match newlines, which is crucial here.
            code_match = re.search(r"```[a-zA-Z]*\n(.*?)\n```", content_with_code, re.DOTALL)

            if not code_match:
                print(f"  - Skipping '{file_path}': No code block found.")
                continue

            code_content = code_match.group(1)
            
            # Ensure the directory exists.
            dir_name = os.path.dirname(file_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)

            # Write the new content to the file, overwriting it.
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code_content)
            
            print(f"  - Successfully updated '{file_path}'.")
            patched_files_count += 1

        except Exception as e:
            print(f"\n[ERROR] Failed to process a block: {e}")
            print("Please check the format of the response file.")
            continue

    print(f"\nPatching complete. Updated {patched_files_count} file(s).")

if __name__ == "__main__":
    main()