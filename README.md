# Messaging App Demo

A minimal real-time, two-user messaging prototype using Python's standard library (Tkinter, sockets, and threading).

## Run

Use Python 3 with Tkinter installed. Open a terminal in this folder.

1. Start server: `python3 server.py`
2. Open another terminal and start client: `python3 main.py`
3. Open a third terminal and start a second client: `python3 main.py`
4. In the two windows, connect with unique usernames `Alice` and `Bob`. Keep Server IP `127.0.0.1`.
5. In Alice's window, enter `Bob` in **Send to username**, type a message and click **Send**. Bob should receive it. Reply by entering `Alice` in Bob's window.

## Different computers

Connect both computers to the same trusted LAN. Run the server on one machine, find that machine's LAN IP, and enter that IP in **Server IP** in both clients. Port TCP 5050 must be allowed by the network and firewall. Campus networks may block peer-to-peer connections.

## Limitations

No authentication, encryption, message persistence, or offline delivery. This is a local-network classroom demo only; do not expose the server to the public internet or send sensitive information.
