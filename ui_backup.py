import tkinter as tk
from tkinter import messagebox
from queue import Queue, Empty
from datetime import datetime
from core import MessagingClient

BG = '#f3f5f9'
SIDEBAR = '#e8edf5'
WHITE = '#ffffff'
BLUE = '#2878f0'
INK = '#1d2939'
MUTED = '#667085'

class MessagingUI:
    def __init__(self, root):
        self.root = root
        root.title('Messages • Demo')
        root.geometry('900x600')
        root.minsize(680, 440)
        root.configure(bg=BG)
        self.events = Queue()
        self.client = None
        self.username_value = ''
        self.active_peer = None
        self.conversations = {}
        self.status = tk.StringVar(value='Not connected')

        top = tk.Frame(root, bg=WHITE, padx=15, pady=12)
        top.pack(fill='x')
        tk.Label(top, text='Messages', bg=WHITE, fg=INK, font=('Helvetica', 18, 'bold')).pack(side='left', padx=(0, 18))
        tk.Label(top, text='Username', bg=WHITE, fg=MUTED).pack(side='left')
        self.username = tk.Entry(top, width=12, relief='solid', bd=1)
        self.username.pack(side='left', padx=(5, 12), ipady=5)
        tk.Label(top, text='Server IP', bg=WHITE, fg=MUTED).pack(side='left')
        self.host = tk.Entry(top, width=14, relief='solid', bd=1)
        self.host.insert(0, '127.0.0.1')
        self.host.pack(side='left', padx=(5, 10), ipady=5)
        self.connect_btn = tk.Button(top, text='Connect', command=self.connect, bg=BLUE, fg=WHITE, relief='flat', padx=14, pady=5)
        self.connect_btn.pack(side='left')
        tk.Label(top, textvariable=self.status, bg=WHITE, fg=MUTED).pack(side='right', padx=8)

        body = tk.Frame(root, bg=BG)
        body.pack(fill='both', expand=True)
        sidebar = tk.Frame(body, bg=SIDEBAR, width=230)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        tk.Label(sidebar, text='Conversations', bg=SIDEBAR, fg=INK, font=('Helvetica', 15, 'bold')).pack(anchor='w', padx=16, pady=(20, 8))
        self.peer_entry = tk.Entry(sidebar, relief='flat', font=('Helvetica', 12))
        self.peer_entry.pack(fill='x', padx=12, ipady=7)
        self.peer_entry.insert(0, '')
        self.peer_entry.bind('<Return>', lambda _e: self.add_conversation())
        tk.Button(sidebar, text='+ New conversation', command=self.add_conversation, bg=WHITE, fg=BLUE, relief='flat', pady=7).pack(fill='x', padx=12, pady=8)
        self.peer_list = tk.Listbox(sidebar, bg=SIDEBAR, fg=INK, selectbackground=BLUE, selectforeground=WHITE, borderwidth=0, highlightthickness=0, font=('Helvetica', 13), activestyle='none')
        self.peer_list.pack(fill='both', expand=True, padx=8, pady=(8, 14))
        self.peer_list.bind('<<ListboxSelect>>', self.select_peer)
        self.peer_names = []

        main = tk.Frame(body, bg=BG)
        main.pack(side='left', fill='both', expand=True)
        self.header = tk.Label(main, text='Choose or start a conversation', bg=WHITE, fg=INK, font=('Helvetica', 15, 'bold'), anchor='w', padx=18, pady=15)
        self.header.pack(fill='x')
        self.chat = tk.Text(main, bg=BG, fg=INK, state='disabled', wrap='word', borderwidth=0, highlightthickness=0, font=('Helvetica', 12), padx=20, pady=16, spacing3=9)
        self.chat.pack(fill='both', expand=True)
        self.chat.tag_configure('out', foreground=BLUE, justify='right', lmargin1=80, lmargin2=80, rmargin=10)
        self.chat.tag_configure('incoming', foreground=INK, justify='left', lmargin1=10, lmargin2=10, rmargin=80)
        self.chat.tag_configure('system', foreground=MUTED, justify='center')
        bottom = tk.Frame(main, bg=WHITE, padx=14, pady=12)
        bottom.pack(fill='x')
        self.message = tk.Entry(bottom, relief='solid', bd=1, font=('Helvetica', 12))
        self.message.pack(side='left', fill='x', expand=True, ipady=8)
        self.message.bind('<Return>', lambda _e: self.send())
        tk.Button(bottom, text='Send ➤', command=self.send, bg=BLUE, fg=WHITE, relief='flat', padx=18, pady=8).pack(side='left', padx=(10, 0))
        self.root.after(100, self.process_events)
        self.root.protocol('WM_DELETE_WINDOW', self.close)

    def add_conversation(self, peer=None):
        if peer is None:
            peer = self.peer_entry.get().strip()
        if not peer:
            messagebox.showinfo('Recipient', 'Enter a username in the sidebar.')
            return
        if peer == self.username_value and self.username_value:
            messagebox.showinfo('Recipient', 'Choose another user.')
            return
        if peer not in self.conversations:
            self.conversations[peer] = []
            self.peer_names.append(peer)
            self.peer_list.insert('end', '  ' + peer)
        self.active_peer = peer
        idx = self.peer_names.index(peer)
        self.peer_list.selection_clear(0, 'end')
        self.peer_list.selection_set(idx)
        self.peer_list.activate(idx)
        self.peer_entry.delete(0, 'end')
        self.render_chat()
        self.message.focus_set()

    def select_peer(self, _event=None):
        selection = self.peer_list.curselection()
        if selection:
            self.active_peer = self.peer_names[selection[0]]
            self.render_chat()

    def render_chat(self):
        self.header.config(text=self.active_peer or 'Choose or start a conversation')
        self.chat.config(state='normal')
        self.chat.delete('1.0', 'end')
        if self.active_peer:
            for direction, content, timestamp in self.conversations.get(self.active_peer, []):
                tag = 'out' if direction == 'out' else 'incoming' if direction == 'in' else 'system'
                if direction == 'out':
                    label = 'You'
                elif direction == 'in':
                    label = self.active_peer
                else:
                    label = 'System'
                self.chat.insert('end', f'{label} · {timestamp}\n{content}\n\n', tag)
        self.chat.see('end')
        self.chat.config(state='disabled')

    def record(self, peer, direction, content):
        if not peer:
            return
        if peer not in self.conversations:
            self.add_conversation(peer)
        self.conversations[peer].append((direction, content, datetime.now().strftime('%I:%M %p').lstrip('0')))
        if peer == self.active_peer:
            self.render_chat()

    def connect(self):
        username = self.username.get().strip()
        if not username:
            messagebox.showwarning('Missing username', 'Enter a username first.')
            return
        try:
            self.client = MessagingClient(self.host.get().strip(), 5050, username, self.events.put)
        except OSError as exc:
            messagebox.showerror('Connection failed', str(exc))
            return
        self.username_value = username
        self.username.config(state='disabled')
        self.host.config(state='disabled')
        self.connect_btn.config(state='disabled')
        self.status.set('Connected as ' + username)

    def send(self):
        if not self.client:
            messagebox.showwarning('Not connected', 'Connect first.')
            return
        if not self.active_peer:
            messagebox.showwarning('No conversation', 'Start a conversation in the sidebar.')
            return
        content = self.message.get().strip()
        if not content:
            return
        try:
            self.client.send_message(self.active_peer, content)
        except OSError as exc:
            messagebox.showerror('Send failed', str(exc))
            return
        self.record(self.active_peer, 'out', content)
        self.message.delete(0, 'end')

    def process_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                if event.get('type') == 'message':
                    sender = str(event.get('from', '')).strip()
                    if sender:
                        self.record(sender, 'in', str(event.get('text', '')))
                else:
                    detail = str(event.get('text', ''))
                    if 'Disconnected' in detail:
                        self.status.set('Disconnected')
                        self.client = None
                    elif detail:
                        self.status.set(detail)
        except Empty:
            pass
        self.root.after(100, self.process_events)

    def close(self):
        if self.client:
            self.client.close()
        self.root.destroy()
