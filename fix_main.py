def fix_file():
    path = "app/main.py"
    try:
        with open(path, "rb") as f:
            content = f.read()
        
        # Replace null bytes with nothing
        clean_content = content.replace(b'\x00', b'')
        
        # Attempt to decode as utf-8, ignoring errors to be safe
        text = clean_content.decode('utf-8', errors='ignore')
        
        # Remove potential BOM chars if any remaining
        text = text.replace('\ufeff', '')
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
            
        print(f"Fixed {path}. New size: {len(text)} chars.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_file()
