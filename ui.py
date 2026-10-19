"""Navy + teal desktop messaging interface. Compatible with existing core.py."""
import tkinter as tk
from tkinter import messagebox
from queue import Queue, Empty
from datetime import datetime
from core import MessagingClient

NAVY = '#12243A'
NAVY_2 = '#1B344D'
TEAL = '#087F82'
TEAL_LIGHT = '#D9F1EF'
BG = '#F4F7FA'
INK = '#17283C'
MUTED = '#687A8E'
WHITE = '#FFFFFF'


class MessagingUI:
    def __init__(self, root):
        self.root = root
        self.root.title('Syvo • Messaging Demo')
        self.root.geometry('1000x680')
        self.root.minsize(700, 480)
        self.root.configure(bg=BG)
        self.events = Queue()
        self.client = None
        self.me = ''
        self.active = None
        self.history = {}
        self.contacts = []
        self.connected = False

        header = tk.Frame(root, bg=WHITE, height=70)
        header.pack(side='top', fill='x')
        header.pack_propagate(False)
        tk.Label(header, text='◈  SYVO', bg=WHITE, fg=NAVY, font=('Helvetica', 18, 'bold')).pack(side='left', padx=(22, 18))
        tk.Label(header, text='Username', bg=WHITE, fg=MUTED, font=('Helvetica', 10)).pack(side='left')
        self.username = tk.Entry(header, width=12, relief='flat', bg=BG, fg=INK, font=('Helvetica', 12), insertbackground=INK)
        self.username.pack(side='left', ipady=8, padx=(7, 14))
        tk.Label(header, text='Server', bg=WHITE, fg=MUTED, font=('Helvetica', 10)).pack(side='left')
        self.host = tk.Entry(header, width=13, relief='flat', bg=BG, fg=INK, font=('Helvetica', 12), insertbackground=INK)
        self.host.insert(0, '127.0.0.1')
        self.host.pack(side='left', ipady=8, padx=(7, 12))
        self.connect_btn = tk.Button(header, text='Connect', command=self.connect, bg=TEAL, fg=WHITE,
                                     activebackground=NAVY_2, activeforeground=WHITE, relief='flat',
                                     font=('Helvetica', 11, 'bold'), padx=15, pady=7)
        self.connect_btn.pack(side='left')
        self.status = tk.Label(header, text='● Offline', bg=WHITE, fg=MUTED, font=('Helvetica', 10))
        self.status.pack(side='right', padx=20)

        main = tk.Frame(root, bg=BG)
        main.pack(fill='both', expand=True)
        sidebar = tk.Frame(main, bg=NAVY, width=265)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        tk.Label(sidebar, text='CONVERSATIONS', bg=NAVY, fg='#AFC5D4', font=('Helvetica', 10, 'bold')).pack(anchor='w', padx=19, pady=(24, 12))
        new_row = tk.Frame(sidebar, bg=NAVY)
        new_row.pack(fill='x', padx=15)
        self.recipient = tk.Entry(new_row, relief='flat', bg=NAVY_2, fg=WHITE, insertbackground=WHITE,
                                  font=('Helvetica', 12), width=13)
        self.recipient.pack(side='left', fill='x', expand=True, ipady=9)
        self.recipient.bind('<Return>', lambda e: self.new_conversation())
        tk.Button(new_row, text='+', command=self.new_conversation, bg=TEAL, fg=WHITE, relief='flat',
                  font=('Helvetica', 17, 'bold'), width=3).pack(side='left', padx=(7, 0))
        tk.Label(sidebar, text='Type a username and press +', bg=NAVY, fg='#8DA8B9', font=('Helvetica', 9)).pack(anchor='w', padx=18, pady=(8, 18))
        self.contact_area = tk.Frame(sidebar, bg=NAVY)
        self.contact_area.pack(fill='both', expand=True)

        right = tk.Frame(main, bg=BG)
        right.pack(side='left', fill='both', expand=True)
        chat_header = tk.Frame(right, bg=WHITE, height=67)
        chat_header.pack(side='top', fill='x')
        chat_header.pack_propagate(False)
        self.chat_title = tk.Label(chat_header, text='Select a conversation', bg=WHITE, fg=INK,
                                   font=('Helvetica', 17, 'bold'))
        self.chat_title.pack(side='left', padx=24)
        self.chat_hint = tk.Label(chat_header, text='Private messages', bg=WHITE, fg=MUTED, font=('Helvetica', 10))
        self.chat_hint.pack(side='right', padx=24)

        # Reserve composer space before the expanding message area.
        composer = tk.Frame(right, bg=WHITE, height=82)
        composer.pack(side='bottom', fill='x')
        composer.pack_propagate(False)
        composer_inner = tk.Frame(composer, bg=WHITE)
        composer_inner.pack(fill='both', expand=True, padx=18, pady=17)
        self.message = tk.Entry(composer_inner, bg=BG, fg=INK, relief='flat', font=('Helvetica', 12), insertbackground=INK)
        self.message.pack(side='left', fill='both', expand=True, ipady=10)
        self.message.bind('<Return>', lambda e: self.send())
        self.send_btn = tk.Button(composer_inner, text='Send  ➜', command=self.send, bg=TEAL, fg=WHITE,
                                  activebackground=NAVY_2, activeforeground=WHITE, relief='flat',
                                  font=('Helvetica', 11, 'bold'), padx=19)
        self.send_btn.pack(side='right', fill='y', padx=(10, 0))

        chat_holder = tk.Frame(right, bg=BG)
        chat_holder.pack(fill='both', expand=True)
        self.canvas = tk.Canvas(chat_holder, bg=BG, highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(chat_holder, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.message_area = tk.Frame(self.canvas, bg=BG)
        self.window_id = self.canvas.create_window((0, 0), window=self.message_area, anchor='nw')
        self.message_area.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfigure(self.window_id, width=e.width))
        self.render_chat()
        self.root.after(100, self.process_events)
        self.root.protocol('WM_DELETE_WINDOW', self.close)

    def new_conversation(self):
        peer = self.recipient.get().strip()
        if not peer:
            return
        if peer == self.me and self.me:
            messagebox.showwarning('Invalid recipient', 'Choose a different username')
            return
        if peer not in self.history:
            self.history[peer] = []
            self.contacts.insert(0, peer)
        self.active = peer
        self.recipient.delete(0, 'end')
        self.render_contacts()
        self.render_chat()
        self.message.focus_set()

    def render_contacts(self):
        for child in self.contact_area.winfo_children():
            child.destroy()
        for peer in self.contacts:
            selected = peer == self.active
            bg = NAVY_2 if selected else NAVY
            row = tk.Frame(self.contact_area, bg=bg, height=66, cursor='hand2')
            row.pack(fill='x', pady=2, padx=8)
            row.pack_propagate(False)
            avatar = tk.Label(row, text=peer[:1].upper(), bg=TEAL, fg=WHITE,
                              font=('Helvetica', 13, 'bold'), width=3, height=2)
            avatar.pack(side='left', padx=(9, 10), pady=8)
            details = tk.Frame(row, bg=bg)
            details.pack(side='left', fill='both', expand=True, pady=9)
            name = tk.Label(details, text=peer, bg=bg, fg=WHITE, font=('Helvetica', 12, 'bold'), anchor='w')
            name.pack(fill='x')
            preview = self.history[peer][-1]['text'] if self.history[peer] else 'Start a conversation'
            label = tk.Label(details, text=preview[:26], bg=bg, fg='#AFC5D4', font=('Helvetica', 10), anchor='w')
            label.pack(fill='x')
            for widget in (row, avatar, details, name, label):
                widget.bind('<Button-1>', lambda e, p=peer: self.select_contact(p))

    def select_contact(self, peer):
        self.active = peer
        self.render_contacts()
        self.render_chat()

    def add_message(self, peer, sender, text):
        if peer not in self.history:
            self.history[peer] = []
            self.contacts.insert(0, peer)
        self.history[peer].append({'sender': sender, 'text': text, 'time': datetime.now().strftime('%I:%M %p').lstrip('0')})
        self.render_contacts()
        if self.active == peer:
            self.render_chat()

    def render_chat(self):
        for child in self.message_area.winfo_children():
            child.destroy()
        if not self.active:
            self.chat_title.configure(text='Select a conversation')
            tk.Label(self.message_area, text='Your conversations start here', bg=BG, fg=INK,
                     font=('Helvetica', 17, 'bold')).pack(pady=(85, 8))
            tk.Label(self.message_area, text='Enter a username on the left to begin.', bg=BG, fg=MUTED,
                     font=('Helvetica', 11)).pack()
            return
        self.chat_title.configure(text=self.active)
        items = self.history[self.active]
        if not items:
            tk.Label(self.message_area, text=f'Say hello to {self.active} 👋', bg=BG, fg=MUTED,
                     font=('Helvetica', 12)).pack(pady=75)
        for i, msg in enumerate(items):
            mine = msg['sender'] == 'me'
            changed = i == 0 or items[i - 1]['sender'] != msg['sender']
            row = tk.Frame(self.message_area, bg=BG)
            row.pack(fill='x', padx=22, pady=(19 if changed else 5, 2))
            bubble = tk.Label(row, text=msg['text'], bg=TEAL if mine else WHITE,
                              fg=WHITE if mine else INK, font=('Helvetica', 12),
                              padx=15, pady=11, wraplength=390, justify='left')
            bubble.pack(side='right' if mine else 'left')
            last_in_group = i == len(items) - 1 or items[i + 1]['sender'] != msg['sender']
            if last_in_group:
                meta = tk.Frame(self.message_area, bg=BG)
                meta.pack(fill='x', padx=25)
                tk.Label(meta, text=('You' if mine else self.active) + '  ·  ' + msg['time'],
                         bg=BG, fg=MUTED, font=('Helvetica', 9)).pack(side='right' if mine else 'left')
        self.root.after_idle(lambda: self.canvas.yview_moveto(1.0))

    def connect(self):
        name = self.username.get().strip()
        if not name:
            messagebox.showwarning('Missing username', 'Enter a username first')
            return
        try:
            self.client = MessagingClient(self.host.get().strip(), 5050, name, self.events.put)
            self.me = name
            self.connected = True
            self.username.configure(state='disabled')
            self.host.configure(state='disabled')
            self.connect_btn.configure(state='disabled')
            self.status.configure(text=f'● Connected as {name}', fg=TEAL)
        except OSError as exc:
            messagebox.showerror('Connection failed', str(exc))

    def send(self):
        if not self.client or not self.connected:
            messagebox.showwarning('Not connected', 'Connect to the server first')
            return
        if not self.active:
            messagebox.showwarning('No conversation', 'Choose a conversation first')
            return
        text = self.message.get().strip()
        if not text:
            return
        try:
            self.client.send_message(self.active, text)
            self.add_message(self.active, 'me', text)
            self.message.delete(0, 'end')
        except OSError as exc:
            messagebox.showerror('Send failed', str(exc))

    def process_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                kind = event.get('type')
                if kind == 'message':
                    peer = str(event.get('from', 'Unknown'))
                    self.add_message(peer, peer, str(event.get('text', '')))
                    if self.active is None:
                        self.select_contact(peer)
                elif kind == 'info':
                    info = str(event.get('text', ''))
                    if 'Disconnected from server' in info:
                        self.connected = False
                        self.status.configure(text='● Disconnected', fg='#BD5555')
                    elif info.startswith('Connected as '):
                        self.status.configure(text='● ' + info, fg=TEAL)
                    else:
                        self.chat_hint.configure(text=info[:45])
        except Empty:
            pass
        self.root.after(100, self.process_events)

    def close(self):
        if self.client:
            self.client.close()
        self.root.destroy()
