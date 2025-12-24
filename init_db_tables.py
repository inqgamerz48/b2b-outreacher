from src.data_manager import initialize_db

if __name__ == "__main__":
    print("[*] Creating Tables...")
    try:
        initialize_db()
        print("[SUCCESS] Tables created.")
    except Exception as e:
        print(f"[ERROR] {e}")
