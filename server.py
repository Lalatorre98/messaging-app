import socket
import threading
import json

HOST = '0.0.0.0'
PORT = 5050
clients = {}
lock = threading.Lock()

def send(sock, payload):
    sock.sendall((json.dumps(payload) + '\n').encode('utf-8'))

def handle(conn):
    username = None
    try:
        reader = conn.makefile('r', encoding='utf-8')
        hello = json.loads(reader.readline())
        username = str(hello.get('username', '')).strip()
        if not username:
            send(conn, {'type': 'error', 'text': 'Username required'})
            return
        with lock:
            if username in clients:
                send(conn, {'type': 'error', 'text': 'Username already connected'})
                return
            clients[username] = conn
        send(conn, {'type': 'info', 'text': f'Connected as {username}'})
        for line in reader:
            msg = json.loads(line)
            if msg.get('type') != 'message':
                continue
            recipient = str(msg.get('to', '')).strip()
            body = str(msg.get('text', '')).strip()
            if not recipient or not body:
                continue
            with lock:
                target = clients.get(recipient)
            if target:
                try:
                    send(target, {'type': 'message', 'from': username, 'text': body})
                    send(conn, {'type': 'info', 'text': f'Delivered to {recipient}'})
                except OSError:
                    send(conn, {'type': 'error', 'text': 'Delivery failed'})
            else:
                send(conn, {'type': 'error', 'text': f'{recipient} is not connected'})
    except (OSError, ValueError, json.JSONDecodeError):
        pass
    finally:
        with lock:
            if username and clients.get(username) is conn:
                del clients[username]
        conn.close()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f'Server listening on port {PORT}', flush=True)
    while True:
        conn, _ = server.accept()
        threading.Thread(target=handle, args=(conn,), daemon=True).start()
