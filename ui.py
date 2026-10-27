"""Navy + teal desktop messaging interface. Compatible with existing core.py."""
import tkinter as tk
from tkinter import messagebox, colorchooser
import json
from pathlib import Path
from queue import Queue, Empty
from datetime import datetime
import colorsys
from core import MessagingClient
from themes import THEMES, DEFAULT_THEME
from message_bubble import MessageBubble
from profile import ProfileWindow

NAVY = '#12243A'
NAVY_2 = '#1B344D'
TEAL = '#087F82'
TEAL_LIGHT = '#D9F1EF'
BG = '#F4F7FA'
INK = '#17283C'
MUTED = '#687A8E'
WHITE = '#FFFFFF'



class MessagingUI:

    def build_palette(self):
        """Adapt the new SYVO theme to the existing UI."""

        theme = self.base_theme.copy()

        theme["chat"] = theme["background"]
        theme["selected"] = theme["sidebar_alt"]
        return theme
    
    def change_appearance(self, theme_name):

        """Switch between SYVO's dark and light themes."""

        if theme_name not in THEMES:
            return

        self.theme_name = theme_name
        self.base_theme = THEMES[theme_name].copy()
        self.palette = self.build_palette()
        self.palette["accent"] = self.accent
        self.palette["outgoing"] = self.accent


        self.apply_theme()
        self.save_theme()

    def __init__(self, root):
        self.root = root
        self.root.title('SYVO • Messaging Demo')
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
        self.theme_name = DEFAULT_THEME
        self.accent = TEAL
        self.settings_file = Path.home() / '.syvo_theme.json'
        self.load_theme()
        self.base_theme= THEMES[self.theme_name].copy()
        self.palette = self.build_palette()
        self.palette["accent"] = self.accent
        self.palette["outgoing"] = self.accent

        header = tk.Frame(root, bg=WHITE, height=70)
        header.pack(side='top', fill='x')
        header.pack_propagate(False)

        self.logo = tk.Label(header, text="◈  SYVO", bg=WHITE, fg=NAVY, font=("Helvetica", 18, "bold")
        )
        self.logo.pack(side="left", padx=(22, 18))

        self.username_label = tk.Label(header, text='Username', bg=WHITE, fg=MUTED, font=('Helvetica', 10))
        self.username_label.pack(side='left')
        self.username = tk.Entry(header, width=12, relief='flat', bg=BG, fg=INK, font=('Helvetica', 12), insertbackground=INK)
        self.username.pack(side='left', ipady=8, padx=(7, 14))
        self.server_label = tk.Label(header, text='Server', bg=WHITE, fg=MUTED, font=('Helvetica', 10))
        self.server_label.pack(side='left')
        self.host = tk.Entry(header, width=13, relief='flat', bg=BG, fg=INK, font=('Helvetica', 12), insertbackground=INK)
        self.host.insert(0, '127.0.0.1')
        self.host.pack(side='left', ipady=8, padx=(7, 12))

        self.connect_btn = tk.Label(header, text="Connect", bg=self.accent, fg=WHITE, font=("Helvetica", 11, "bold"), padx=15, pady=10, cursor="hand2"
        )

        self.connect_btn.pack(side="left")
        self.connect_btn.bind("<Button-1>", lambda event: self.connect())


        self.status = tk.Label(header, text='● Offline', bg=WHITE, fg=MUTED, font=('Helvetica', 10))
        self.status.pack(side='right', padx=20)
        # Connection inputs are hidden after a successful connection.
        # The status label remains visible; the server address is not shown.

        main = tk.Frame(root, bg=BG)
        self.main = main
        main.pack(fill='both', expand=True)
        sidebar = tk.Frame(main, bg=NAVY, width=265)
        self.sidebar = sidebar
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        self.sidebar_title = tk.Label(sidebar, text='CONVERSATIONS', bg=NAVY, fg='#AFC5D4', font=('Helvetica', 10, 'bold'))
        self.sidebar_title.pack(anchor='w', padx=19, pady=(24, 12))
        new_row = tk.Frame(sidebar, bg=NAVY)
        self.new_row = new_row
        new_row.pack(fill='x', padx=15)
        self.recipient = tk.Entry(new_row, relief='flat', bg=NAVY_2, fg=WHITE, insertbackground=WHITE,
                                  font=('Helvetica', 12), width=13)
        self.recipient.pack(side='left', fill='x', expand=True, ipady=9)
        self.recipient.bind('<Return>', lambda e: self.new_conversation())

        self.new_btn = tk.Label(
            new_row,
            text="+",
            bg=self.accent,
            fg=WHITE,
            font=("Helvetica", 17, "bold"),
            width=3,
            pady=5,
            cursor="hand2"
        )

        self.new_btn.pack(side="left", padx=(7, 0))
        self.new_btn.bind(
            "<Button-1>",
            lambda event: self.new_conversation())
        
        self.new_btn.pack(side='left', padx=(7, 0))
        self.sidebar_help = tk.Label(sidebar, text='Type a username and press +', bg=NAVY, fg='#8DA8B9', font=('Helvetica', 9))
        self.sidebar_help.pack(anchor='w', padx=18, pady=(8, 18))
        theme_row = tk.Frame(sidebar, bg=NAVY)
        self.theme_row = theme_row
        theme_row.pack(fill='x', padx=16, pady=(0, 12))
        theme_row.pack_propagate(True)
        self.theme_label = tk.Label(theme_row, text='MY COLOR', bg=NAVY, fg='#AFC5D4', font=('Helvetica', 9, 'bold'))
        self.theme_label.pack(anchor="w",pady=(0, 10))
        self.settings_btn = tk.Label(theme_row, text="⚙  Appearance settings  →", bg=NAVY_2, fg=WHITE,
                                     font=('Helvetica', 11, 'bold'), padx=12, pady=10, cursor='hand2')
        self.settings_btn.pack(fill='x', expand=True)
        self.settings_btn.bind('<Button-1>', lambda e: self.open_settings())
        self.contact_area = tk.Frame(sidebar, bg=NAVY)
        self.contact_area.pack(fill='both', expand=True)

                # My Profile section
        self.profile_row = tk.Frame(sidebar, bg=self.palette["sidebar"])
        self.profile_row.pack(side="bottom", fill="x", padx=16, pady=(8, 16))

        self.profile_btn = tk.Label(
            self.profile_row,
            text="◉  My Profile  →",
            bg=self.palette["sidebar_alt"],
            fg=self.palette["text"],
            font=("Helvetica", 11, "bold"),
            padx=14,
            pady=12,
            anchor="w",
            cursor="hand2"
        )

        self.profile_btn.pack(fill="x")

        self.profile_btn.bind("<Button-1>",lambda event: self.open_profile())

        right = tk.Frame(main, bg=BG)
        self.right = right
        right.pack(side='left', fill='both', expand=True)
        chat_header = tk.Frame(right, bg=WHITE, height=67)
        self.chat_header = chat_header
        self.header = header
        chat_header.pack(side='top', fill='x')
        chat_header.pack_propagate(False)
        self.chat_title = tk.Label(chat_header, text='Welcome to SYVO', bg=WHITE, fg=INK,
                                   font=('Helvetica', 17, 'bold'))
        self.chat_title.pack(side='left', padx=24)
        self.chat_hint = tk.Label(chat_header, text='Your messages, your space', bg=WHITE, fg=MUTED, font=('Helvetica', 10))
        self.chat_hint.pack(side='right', padx=24)

        # Reserve composer space before the expanding message area.
        composer = tk.Frame(right, bg=WHITE, height=82)
        self.composer = composer
        composer.pack(side='bottom', fill='x')
        # Allow the composer frame to follow the Text widget's requested height.
        composer_inner = tk.Frame(composer, bg=WHITE)
        self.composer_inner = composer_inner
        composer_inner.pack(fill='x', padx=18, pady=12)
        self.message = tk.Text(composer_inner, font=("Helvetica", 12), height=1, width=40, wrap="word",
        undo=True,padx=12, pady=10, bd=0,highlightthickness=0)
        self.message.pack(side='left', fill='x', expand=True)
        self.message.bind('<Return>', self.on_message_enter)
        self.message.bind('<<Modified>>', self.on_composer_modified)
        self.message.edit_modified(False)

        self.send_btn = tk.Label(
            composer_inner,
            text="Send  ➜",
            bg=self.accent,
            fg=WHITE,
            font=("Helvetica", 11, "bold"),
            padx=19,
            pady=10,
            cursor="hand2"
        )

        self.send_btn.pack(side="right", fill="y", padx=(10, 0))
        self.send_btn.bind("<Button-1>", lambda event: self.send())

        chat_holder = tk.Frame(right, bg=BG)
        self.chat_holder = chat_holder
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
        self.apply_theme()
        self.root.after(100, self.process_events)
        self.root.protocol('WM_DELETE_WINDOW', self.close)

    def load_theme(self):
        """Load saved appearance preferences."""
        try:
            data = json.loads(
                self.settings_file.read_text(encoding="utf-8")
            )

            saved_theme = data.get("theme", DEFAULT_THEME)
            if saved_theme in THEMES:
                self.theme_name = saved_theme

            saved_accent = data.get("accent", TEAL)
            if (
                isinstance(saved_accent, str)
                and len(saved_accent) == 7
                and saved_accent.startswith("#")
            ):
                int(saved_accent[1:], 16)
                self.accent = saved_accent

        except (OSError, ValueError, TypeError):
            pass

    def save_theme(self):
        """Save appearance preferences."""
        data = {
            "theme": self.theme_name,
            "accent": self.accent
        }

        try:
            self.settings_file.write_text(
                json.dumps(data, indent=4),
                encoding="utf-8"
            )
        except OSError:
            pass

    def save_theme(self):
        """Save the user's appearance mode and accent color."""
        data = {
            "theme": self.theme_name,
            "accent": self.accent
        }

        try:
            self.settings_file.write_text(
                json.dumps(data, indent=4),
                encoding="utf-8"
            )
        except OSError:
            pass

    def pick_color(self):
        chosen = colorchooser.askcolor(color=self.accent, title='Choose your SYVO color')[1]
        if chosen:
            self.set_theme(chosen)

    @staticmethod
    def make_palette(accent):
        r, g, b = (int(accent[i:i+2], 16) / 255 for i in (1, 3, 5))
        h, sat, val = colorsys.rgb_to_hsv(r, g, b)
        def hex_hsv(hue, saturation, value):
            rgb = colorsys.hsv_to_rgb(hue, saturation, value)
            return '#' + ''.join(f'{round(c * 255):02X}' for c in rgb)
        return {
            'accent': accent,
            'sidebar': hex_hsv(h, min(.60, max(.35, sat * .65)), .17),
            'sidebar_alt': hex_hsv(h, min(.55, max(.30, sat * .55)), .26),
            'chat': hex_hsv(h, min(.12, sat * .17), .975),
            'input': hex_hsv(h, min(.11, sat * .15), .95),
            'selected': hex_hsv(h, min(.50, max(.25, sat * .55)), .30),
        }

    def apply_theme(self):
        p = self.palette

        # Apply the selected accent to interactive controls
        self.connect_btn.configure(bg=self.accent, fg="#FFFFFF")
        self.new_btn.configure(bg=self.accent, fg="#FFFFFF")
        self.send_btn.configure(bg=self.accent, fg="#FFFFFF")


        self.logo.configure(bg=p["header"], fg=p["text"])
        self.username_label.configure(bg=p["header"], fg=p["secondary_text"])
        self.server_label.configure(bg=p["header"], fg=p["secondary_text"])
        self.status.configure(bg=p["header"], fg=p["accent"] if self.connected else p["secondary_text"])


        # Midnight Blue headers and message composer
        self.header.configure(bg=p["header"])
        self.chat_header.configure(bg=p["header"])
        self.composer.configure(bg=p["header"])
        self.composer_inner.configure(bg=p["header"])

        # Conversation header text
        self.chat_title.configure(bg=p["header"], fg=p["text"])

        self.chat_hint.configure(bg=p["header"], fg=p["secondary_text"])

        self.root.configure(bg=p['chat'])
        self.main.configure(bg=p['chat'])
        self.sidebar.configure(bg=p['sidebar'])
        self.sidebar_title.configure(bg=p["sidebar"], fg=p["secondary_text"])
        self.new_row.configure(bg=p['sidebar'])
        self.recipient.configure(bg=p["sidebar_alt"], fg=p["text"], insertbackground=p["text"])
        self.sidebar_help.configure(bg=p["sidebar"], fg=p["secondary_text"])
        self.theme_row.configure(bg=p['sidebar'])
        self.theme_label.configure(
        bg=p["sidebar"],fg=p["secondary_text"], text="PERSONALIZATION")
        self.settings_btn.configure(bg=p["sidebar_alt"], fg=p["text"])
        # Update My Profile colors when switching themes
        self.profile_row.configure(bg=p["sidebar"])
        self.profile_btn.configure(
            bg=p["sidebar_alt"],
            fg=p["text"]
        )

        self.contact_area.configure(bg=p['sidebar'])
        self.right.configure(bg=p['chat'])
        self.chat_holder.configure(bg=p['chat'])
        self.canvas.configure(bg=p['chat'])
        self.message_area.configure(bg=p['chat'])

        input_bg = (
    "#E8EEF5" if self.theme_name == "midnight_light" else "#233A55")

        self.message.configure(
            bg=input_bg,fg=p["text"],
            insertbackground=p["text"], highlightthickness=0, bd=0, relief="flat")
       
        self.status.configure(fg=p['accent'] if self.connected else p['secondary_text'])

        for entry in (self.username, self.host):
            entry.configure(
            bg=p["input"],
            fg=p["text"],
            insertbackground=p["text"],
            disabledforeground=p["secondary_text"],
            highlightthickness=0,
            bd=0
        )

        self.connect_btn.configure(highlightthickness=0, bd=0, relief='flat')
        self.send_btn.configure(highlightthickness=0, bd=0, relief='flat')
        self.new_btn.configure(highlightthickness=0, bd=0, relief='flat')
        self.render_contacts()
        self.render_chat()

    def set_theme(self, color):
        try:
            if len(color) != 7 or not color.startswith('#'):
                return
            int(color[1:], 16)
        except (TypeError, ValueError):
            return
        self.accent = color

        # Keep the selected Dark/Light appearance
        self.palette = self.build_palette()

        # Apply the selected accent color
        self.palette["accent"] = color
        self.palette["outgoing"] = color

        # Refresh the interface
        self.apply_theme()
        self.save_theme()
    
    
    def open_profile(self):
        """Open one profile window at a time."""

        if getattr(self, "profile_window", None) is not None:
            try:
                if self.profile_window.window.winfo_exists():
                    self.profile_window.window.lift()
                    self.profile_window.window.focus_force()
                    return
            except tk.TclError:
                pass

        self.profile_window = ProfileWindow(
            parent=self.root,
            username=self.me,
            palette=self.palette,
            accent=self.accent
        )

        
    def open_settings(self):
        """Independent, local appearance settings; networking is unchanged."""
        if getattr(self, '_settings_window', None) is not None:
            try:
                if self._settings_window.winfo_exists():
                    self._settings_window.lift()
                    self._settings_window.focus_force()
                    return
            except tk.TclError:
                pass
        window = tk.Toplevel(self.root)
        self._settings_window = window
        window.title('SYVO • Appearance')
        window.geometry("520x680")
        window.minsize(480, 620)
        window.configure(bg=WHITE)
        window.transient(self.root)
        tk.Label(window, text='Appearance', font=('Helvetica', 21, 'bold'), bg=WHITE, fg=INK).pack(anchor='w', padx=26, pady=(25, 4))
        tk.Label(window, text='Make SYVO feel like yours. Changes apply instantly.', bg=WHITE,
                 fg=MUTED, font=('Helvetica', 11)).pack(anchor='w', padx=26, pady=(0, 20))
        
        # SYVO appearance mode selector
        mode_frame = tk.Frame(window, bg=WHITE)
        mode_frame.pack(fill="x", padx=26, pady=(0, 15))

        tk.Label(
            mode_frame,
            text="APPEARANCE MODE",
            bg=WHITE,
            fg=MUTED,
            font=("Helvetica", 10, "bold")
        ).pack(anchor="w", pady=(0, 8))

        mode_choice = tk.StringVar(value=self.theme_name)

        for label, theme_key in [
            ("🌙 Dark", "midnight_dark"),
            ("☀ Light", "midnight_light")
        ]:
            tk.Radiobutton(
                mode_frame,
                text=label,
                variable=mode_choice,
                value=theme_key,
                command=lambda: self.change_appearance(mode_choice.get()),
                bg=WHITE,
                fg=INK,
                selectcolor=WHITE,
                activebackground=WHITE,
                font=("Helvetica", 11)
            ).pack(side="left", padx=(0, 20))



        tk.Label(window, text='CHOOSE A THEME', bg=WHITE, fg=MUTED,
                 font=('Helvetica', 10, 'bold')).pack(anchor='w', padx=26, pady=(0, 8))
        colors = [('Ocean', '#087F82'), ('Midnight', '#2563EB'),
                  ('Lavender', '#8B5CF6'), ('Rose', '#D94683'), ('Sunset', '#EA580C')]
        preview = tk.Frame(window, bg=self.palette['chat'], height=150)
        preview.pack(side='bottom', fill='x', padx=26, pady=(12, 22))
        preview.pack_propagate(False)
        tk.Label(preview, text='LIVE PREVIEW', bg=self.palette['chat'], fg=MUTED,
                 font=('Helvetica', 9, 'bold')).pack(anchor='w', padx=15, pady=(12, 5))
        sample = tk.Label(preview, text='Your SYVO, your colors ✦', bg=self.accent,
                          fg=WHITE, font=('Helvetica', 11), padx=14, pady=10)
        sample.pack(anchor='e', padx=15, pady=8)
        selected_label = tk.Label(window, text='', bg=WHITE, fg=MUTED, font=('Helvetica', 10))
        selected_label.pack(side='bottom', anchor='w', padx=26)
        def refresh_preview():
            preview.configure(bg=self.palette['chat'])
            for child in preview.winfo_children():
                if child is not sample:
                    child.configure(bg=self.palette['chat'])
            sample.configure(bg=self.accent)
            selected_label.configure(text='Current accent: ' + self.accent.upper())
        grid = tk.Frame(window, bg=WHITE)
        grid.pack(fill='x', padx=22)
        theme_tiles = []

        def update_selection():
            for tile, color in theme_tiles:
                tile.configure(bg=INK if self.accent.lower() == color.lower() else WHITE)

        def choose_theme(color):
            self.set_theme(color)
            refresh_preview()
            update_selection()

        for index, (name, color) in enumerate(colors):
            # Labels inside frames avoid macOS native Button colors overriding fg/bg.
            tile = tk.Frame(grid, bg=WHITE, padx=3, pady=3)
            tile.grid(row=index // 3, column=index % 3, padx=4, pady=7, sticky='ew')
            swatch = tk.Label(tile, text='●  ' + name, bg=color, fg=WHITE,
                              font=('Helvetica', 10, 'bold'), padx=12, pady=12,
                              cursor='hand2', takefocus=1)
            swatch.pack(fill='x')
            swatch.bind('<Button-1>', lambda event, c=color: choose_theme(c))
            swatch.bind('<Return>', lambda event, c=color: choose_theme(c))
            swatch.bind('<space>', lambda event, c=color: choose_theme(c))
            theme_tiles.append((tile, color))
            grid.columnconfigure(index % 3, weight=1)

        def custom():
            self.pick_color()
            refresh_preview()
            update_selection()

        custom_btn = tk.Label(window, text='Choose custom color…', bg='#E9EEF4', fg=INK,
                              font=('Helvetica', 11), padx=14, pady=10,
                              cursor='hand2', takefocus=1)
        custom_btn.pack(anchor='w', padx=26, pady=(14, 0))
        custom_btn.bind('<Button-1>', lambda event: custom())
        custom_btn.bind('<Return>', lambda event: custom())
        custom_btn.bind('<space>', lambda event: custom())
        refresh_preview()
        update_selection()

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
            # Adapt contact text colors to Dark and Light Mode
            name_color = self.palette["text"]
            preview_color = self.palette["secondary_text"]
            bg = self.palette['selected'] if selected else self.palette['sidebar']
            row = tk.Frame(self.contact_area, bg=bg, height=66, cursor='hand2')
            row.pack(fill='x', pady=2, padx=8)
            row.pack_propagate(False)
            avatar = tk.Label(row, text=peer[:1].upper(), bg=self.accent, fg=WHITE,
                              font=('Helvetica', 13, 'bold'), width=3, height=2)
            avatar.pack(side='left', padx=(9, 10), pady=8)
            details = tk.Frame(row, bg=bg)
            details.pack(side='left', fill='both', expand=True, pady=9)
            name = tk.Label(details, text=peer, bg=bg, fg=name_color, font=('Helvetica', 12, 'bold'), anchor='w')
            name.pack(fill='x')
            preview = self.history[peer][-1]['text'] if self.history[peer] else 'Start a conversation'
            label = tk.Label(details, text=preview[:26], bg=bg, fg=preview_color, font=('Helvetica', 10), anchor='w')
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
        chat_bg = self.palette['chat']
        if not self.active:
            self.chat_title.configure(text='Welcome to SYVO')
            self.chat_hint.configure(text='Your messages, your space')
            tk.Label(self.message_area, text='✦', bg=chat_bg, fg=self.accent,
                     font=('Helvetica', 34, 'bold')).pack(pady=(78, 8))
            tk.Label(self.message_area, text='A better place to connect', bg=chat_bg, fg=self.palette["text"],
                     font=('Helvetica', 19, 'bold')).pack(pady=(0, 8))
            tk.Label(self.message_area, text='Start a conversation using the sidebar, or choose an existing chat.',
                     bg=chat_bg, fg=self.palette["secondary_text"], font=('Helvetica', 11), wraplength=440).pack()
            return
        self.chat_title.configure(text='◉  ' + self.active)
        self.chat_hint.configure(text='Direct conversation')
        items = self.history[self.active]
        if not items:
            tk.Label(self.message_area, text=f'Say hello to {self.active} 👋', bg=chat_bg, fg=self.palette["secondary_text"],
                     font=('Helvetica', 12)).pack(pady=75)
        for i, msg in enumerate(items):
            mine = msg['sender'] == 'me'
            changed = i == 0 or items[i - 1]['sender'] != msg['sender']
            row = tk.Frame(self.message_area, bg=chat_bg)
            row.pack(fill='x', padx=22, pady=(19 if changed else 5, 2))
            
            bubble = MessageBubble(row, text=msg["text"],
            background=self.palette["outgoing"] if mine else self.palette["incoming"],
            foreground="#FFFFFF" if mine else self.palette["text"],font=("Helvetica", 12))

            bubble.pack(side='right' if mine else 'left')
            last_in_group = i == len(items) - 1 or items[i + 1]['sender'] != msg['sender']
            if last_in_group:
                meta = tk.Frame(self.message_area, bg=chat_bg)
                meta.pack(fill='x', padx=25)
                tk.Label(meta, text=('You' if mine else self.active) + '  ·  ' + msg['time'],
                         bg=chat_bg, fg=self.palette["secondary_text"], font=('Helvetica', 9)).pack(side='right' if mine else 'left')
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
            # The Connect control is a Label, not a Button; it has no state option.
            for widget in (self.username_label, self.username, self.server_label, self.host, self.connect_btn):
                widget.pack_forget()
            self.status.configure(text=f'● Connected as {name}', fg=self.accent)
        except OSError as exc:
            messagebox.showerror('Connection failed', str(exc))
    
    def on_message_enter(self, event):
        if event.state & 0x0001:
            return None  # Shift+Enter inserts a newline

        self.send()
        return "break"
    

    
    def resize_composer(self, event=None):
        """Resize to 1–4 displayed lines, including automatic word wrapping."""
        if not self.message.winfo_exists():
            return
        self.message.update_idletasks()
        # Text.count returns the number of display-line transitions; add one
        # for the first line.  This also handles Shift+Enter line breaks.
        result = self.message.count('1.0', 'end-1c', 'displaylines')
        lines = 1 + (result[0] if result else 0)
        lines = max(1, min(4, lines))
        if int(self.message.cget('height')) != lines:
            self.message.configure(height=lines)

    def on_composer_modified(self, event=None):
        if self.message.edit_modified():
            self.message.edit_modified(False)
            self.message.after_idle(self.resize_composer)


    def send(self):
        if not self.client or not self.connected:
            messagebox.showwarning('Not connected', 'Connect to the server first')
            return
        if not self.active:
            messagebox.showwarning('No conversation', 'Choose a conversation first')
            return
        text = self.message.get("1.0", "end-1c").strip()
        if not text:
            return
        try:
            self.client.send_message(self.active, text)
            self.add_message(self.active, 'me', text)
            self.message.delete("1.0", "end")
            self.message.configure(height=1)
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
                        self.status.configure(text='● ' + info, fg=self.accent)
                    else:
                        self.chat_hint.configure(text=info[:45])
        except Empty:
            pass
        self.root.after(100, self.process_events)

    def close(self):
        if self.client:
            self.client.close()
        self.root.destroy()
