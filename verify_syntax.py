
try:
    import app.main
    print("Optimization: Syntax OK")
except Exception as e:
    # Streamlit scripts often fail to run as modules because of st commands, but syntax errors will catch
    print(f"Error: {e}")
