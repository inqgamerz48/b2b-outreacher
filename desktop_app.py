# desktop_app.py
import webview
import time
import sys
import os
import socket
import subprocess

def get_free_port():
    """Finds a free port on localhost."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

def start_streamlit_background(port):
    """Starts Streamlit in a background process."""
    dashboard_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.py")
    
    cmd = [
        sys.executable, "-m", "streamlit", "run", dashboard_path,
        "--server.port", str(port),
        "--server.headless", "true",
        "--global.developmentMode", "false"
    ]
    
    # Hide console window on Windows if possible (optional refinement)
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    print(f"[*] Starting Streamlit on port {port}...")
    process = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        startupinfo=startupinfo
    )
    return process

if __name__ == '__main__':
    port = get_free_port()
    
    # Start Streamlit
    process = start_streamlit_background(port)
    
    # Wait for Streamlit to initialize (simple modification can be dynamic if needed, but sleep is robust enough)
    time.sleep(2)
    
    window_title = "B2B Cold Outreach System"
    url = f"http://localhost:{port}"
    
    # Create Native Window
    webview.create_window(window_title, url, width=1200, height=900)
    
    try:
        print("[*] Dashboard Window Opened.")
        webview.start()
    except Exception as e:
        print(f"[ERROR] GUI Failed: {e}")
    finally:
        print("[*] Closing App...")
        process.terminate()
        sys.exit()
