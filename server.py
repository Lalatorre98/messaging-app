import socket
import threading
import json

HOST = '0.0.0.0'
PORT = 5050
clients = {}
lock = threading.Lock()

# User Discovery privacy preferences
# False = hidden, True = discoverable
#only an in-memory setting for the demo. Handling persistence and account based
#settings later
discovery_visibility = {}




def send(sock, payload):
    sock.sendall((json.dumps(payload) + '\n').encode('utf-8'))



def broadcast_online_users():
    """Update discovery lists and existing conversation presence."""
    with lock:
        connected = list(clients.items())
        visible_users = {
            name for name, _ in connected
            if discovery_visibility.get(name, False)
        }

    all_online = {name for name, _ in connected}

    for username, conn in connected:
        discoverable = sorted(
            name for name in visible_users
            if name != username
        )

        try:
            send(conn, {
                "type": "users_list",
                "users": discoverable
            })
            # Only broadcast discoverable users for now.
            # Hidden users must not be exposed through presence updates.
            send(conn, {
                "type": "presence_list",
                "users": sorted(visible_users - {username})
            })
        except OSError:
            pass



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
            discovery_visibility[username] = False  # Default to hidden for privacy
        send(conn, {'type': 'info', 'text': f'Connected as {username}'})
        broadcast_online_users()
        
        for line in reader:
            msg = json.loads(line)


            if msg.get("type") == "set_discovery":
                visible = msg.get("visible")

                if not isinstance(visible, bool):
                    send(conn, {
                        "type": "error",
                        "text": "Invalid discovery setting"
                    })
                    continue

                with lock:
                    discovery_visibility[username] = visible

                send(conn, {
                    "type": "discovery_updated",
                    "visible": visible
                })

                broadcast_online_users()
                continue



            if msg.get('type') == 'list_users':
                
                with lock:
                    online_users = [
                        name for name in clients
                        if name != username
                        and discovery_visibility.get(name, False)]

                   

                send(conn, {
                    'type': 'users_list',
                    'users': online_users
                })
                continue

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
                    send(target, {
                        'type': 'message',
                        'from': username,
                        'text': body
                    })

                    send(conn, {
                        'type': 'info',
                        'text': f'Delivered to {recipient}'
                    })

                except OSError:
                    send(conn, {
                        'type': 'error',
                        'text': 'Delivery failed'
                    })
            else:
                send(conn, {'type': 'error', 'text': f'{recipient} is not connected'})
    except (OSError, ValueError, json.JSONDecodeError):
        pass

    finally:
        user_removed = False

        with lock:
            if username and clients.get(username) is conn:
                del clients[username]
                discovery_visibility.pop(username, None)
                user_removed = True

        conn.close()

        if user_removed:
            broadcast_online_users()
        



with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f'Server listening on port {PORT}', flush=True)
    while True:
        conn, _ = server.accept()
        threading.Thread(target=handle, args=(conn,), daemon=True).start()
