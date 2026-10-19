import tkinter as tk
from tkinter import ttk, messagebox
from queue import Queue, Empty
from core import MessagingClient

class MessagingUI:
    def __init__(self, root):
        self.root = root
        root.title('Messaging Demo')
        root.geometry('620x510')
        self.events = Queue()
        self.client = None
        top = ttk.Frame(root, padding=12)
        top.pack(fill='x')
        ttk.Label(top, text='Username').grid(row=0, column=0)
        self.username = ttk.Entry(top, width=13)
        self.username.grid(row=0, column=1, padx=5)
        ttk.Label(top, text='Server IP').grid(row=0, column=2)
        self.host = ttk.Entry(top, width=14)
        self.host.insert(0, '127.0.0.1')
        self.host.grid(row=0, column=3, padx=5)
        self.connect_btn = ttk.Button(top, text='Connect', command=self.connect)
        self.connect_btn.grid(row=0, column=4)
        peer = ttk.Frame(root, padding=(12, 0, 12, 8))
        peer.pack(fill='x')
        ttk.Label(peer, text='Send to username:').pack(side='left')
        self.recipient = ttk.Entry(peer)
        self.recipient.pack(side='left', fill='x', expand=True, padx=8)
        self.chat = tk.Text(root, state='disabled', wrap='word', font=('Arial', 12), padx=12, pady=12)
        self.chat.pack(fill='both', expand=True, padx=12, pady=4)
        bottom = ttk.Frame(root, padding=12)
        bottom.pack(fill='x')
        self.message = ttk.Entry(bottom)
        self.message.pack(side='left', fill='x', expand=True)
        self.message.bind('<Return>', lambda event: self.send())
        ttk.Button(bottom, text='Send', command=self.send).pack(side='left', padx=(8, 0))
        self.root.after(100, self.process_events)
        self.root.protocol('WM_DELETE_WINDOW', self.close)

    def append(self, text):
        self.chat.configure(state='normal')
        self.chat.insert('end', text + '\n')
        self.chat.see('end')
        self.chat.configure(state='disabled')

    def connect(self):
        username = self.username.get().strip()
        if not username:
            messagebox.showwarning('Missing username', 'Enter a username')
            return
        try:
            self.client = MessagingClient(self.host.get().strip(), 5050, username, self.events.put)
            self.connect_btn.configure(state='disabled')
            self.username.configure(state='disabled')
        except OSError as exc:
            messagebox.showerror('Connection failed', str(exc))

    def send(self):
        if not self.client:
            messagebox.showwarning('Not connected', 'Connect first')
            return
        recipient = self.recipient.get().strip()
        text = self.message.get().strip()
        if not recipient or not text:
            return
        try:
            self.client.send_message(recipient, text)
            self.append(f'Me → {recipient}: {text}')
            self.message.delete(0, 'end')
        except OSError as exc:
            messagebox.showerror('Send failed', str(exc))

    def process_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                if event.get('type') == 'message':
                    self.append(f"{event['from']}: {event['text']}")
                else:
                    self.append(f"[{event.get('text', 'Unknown event')}]")
        except Empty:
            pass
        self.root.after(100, self.process_events)

    def close(self):
        if self.client:
            self.client.close()
        self.root.destroy()
