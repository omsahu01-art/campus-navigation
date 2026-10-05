"""Start the CampusNav server:   python run.py"""

import socket

from backend.app import app
from config.config import APP_NAME, DEBUG, HOST, PORT


def _lan_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return None


if __name__ == "__main__":
    print("=" * 56)
    print(f"  {APP_NAME} is running")
    print(f"  Open in your browser:  http://127.0.0.1:{PORT}")
    if HOST == "0.0.0.0" and _lan_ip():
        print(f"  On your phone (same Wi-Fi):  http://{_lan_ip()}:{PORT}")
    print("  Press CTRL+C to stop")
    print("=" * 56)
    app.run(host=HOST, port=PORT, debug=DEBUG, use_reloader=DEBUG)
