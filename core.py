import socket
import threading
import json

class MessagingClient:
    def __init__(self, host, port, username, on_event):
        self.on_event = on_event
        self.sock = socket.create_connection((host, port), timeout=5)
        self.sock.settimeout(None)
        self.lock = threading.Lock()
        self._send({'username': username})
        threading.Thread(target=self._listen, daemon=True).start()

    def _send(self, data):
        with self.lock:
            self.sock.sendall((json.dumps(data) + '\n').encode('utf-8'))

    def send_message(self, recipient, text):
        self._send({'type': 'message', 'to': recipient, 'text': text})

    def _listen(self):
        try:
            for line in self.sock.makefile('r', encoding='utf-8'):
                self.on_event(json.loads(line))
        except (OSError, ValueError, json.JSONDecodeError):
            pass
        self.on_event({'type': 'info', 'text': 'Disconnected from server'})

    def close(self):
        self.sock.close()
