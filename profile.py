import tkinter as tk
from tkinter import filedialog, messagebox
import io
import os
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageTk, UnidentifiedImageError, ImageOps


class ProfileWindow:
    """SYVO profile interface."""

    def __init__(self, parent, username, palette, accent):
        self.window = tk.Toplevel(parent)
        self.window.title("SYVO • My Profile")
        self.window.geometry("440x690")
        self.window.minsize(400, 650)
        self.window.configure(bg=palette["background"])
        self.window.transient(parent)
        self.profile_file = Path.home() / ".syvo_profile.json"
        self.avatar_file = Path.home() / ".syvo_avatar.png"
        self.avatar_photo = None
        self.initial = username[:1].upper() if username else "?"
        self.accent = accent

        bg = palette["background"]
        text = palette["text"]
        secondary = palette["secondary_text"]

        # Page heading
        tk.Label(
            self.window,
            text="My Profile",
            bg=bg,
            fg=text,
            font=("Helvetica", 22, "bold")
        ).pack(anchor="w", padx=28, pady=(28, 8))

        tk.Label(
            self.window,
            text="Your space. Your voice. Your control.",
            bg=bg,
            fg=secondary,
            font=("Helvetica", 11)
        ).pack(anchor="w", padx=28)

        # Profile avatar
        self.avatar = tk.Label(
            self.window,
            text=self.initial,
            bg=palette["background"],
            fg="#FFFFFF",
            font=("Helvetica", 30, "bold"),
            width=3,
            height=2
        )
        self.avatar.pack(pady=(16, 8))
        self.load_avatar()

        picture_actions = tk.Frame(self.window, bg=bg)
        picture_actions.pack(pady=(0, 8))
        self.change_picture_btn = tk.Label(
            picture_actions, text="Change Picture", bg=palette["sidebar_alt"],
            fg=text, font=("Helvetica", 10, "bold"), padx=12, pady=7,
            cursor="hand2"
        )
        self.change_picture_btn.pack(side="left", padx=4)
        self.change_picture_btn.bind("<Button-1>", lambda event: self.change_picture())
        self.remove_picture_btn = tk.Label(
            picture_actions, text="Remove Picture", bg=palette["sidebar_alt"],
            fg=text, font=("Helvetica", 10), padx=12, pady=7,
            cursor="hand2"
        )
        self.remove_picture_btn.pack(side="left", padx=4)
        self.remove_picture_btn.bind("<Button-1>", lambda event: self.remove_picture())

        # Username
        tk.Label(
            self.window,
            text=f"@{username}" if username else "Not connected",
            bg=bg,
            fg=text,
            font=("Helvetica", 15, "bold")
        ).pack()

            # Editable profile information
        form = tk.Frame(self.window, bg=bg)
        form.pack(fill="x", padx=28, pady=(16, 0))

        tk.Label(
            form,
            text="DISPLAY NAME",
            bg=bg,
            fg=secondary,
            font=("Helvetica", 10, "bold")
        ).pack(anchor="w", pady=(0, 6))

        self.display_name = tk.Entry(
            form,
            font=("Helvetica", 12),
            bg=palette["input"],
            fg=text,
            insertbackground=text,
            relief="flat"
        )
        self.display_name.pack(fill="x", ipady=10)

        tk.Label(
            form,
            text="BIO",
            bg=bg,
            fg=secondary,
            font=("Helvetica", 10, "bold")
        ).pack(anchor="w", pady=(20, 6))

        self.bio = tk.Text(
            form,
            height=3,
            font=("Helvetica", 12),
            bg=palette["input"],
            fg=text,
            insertbackground=text,
            wrap="word",
            relief="flat",
            padx=10,
            pady=8
        )
        self.bio.pack(fill="x")

        # Load previously saved profile information
        self.load_profile()

        # Save Profile button
        self.save_btn = tk.Label(
            self.window,
            text="Save Profile",
    
            bg=accent,
            fg="#FFFFFF",
            font=("Helvetica", 11, "bold"),
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.save_btn.pack(fill="x", padx=28, pady=(16, 18))
        self.save_btn.bind("<Button-1>",lambda event: self.save_profile())
        
    def save_profile(self):
        """Save the user's display name and bio locally."""
        data = {
            "display_name": self.display_name.get().strip(),
            "bio": self.bio.get("1.0", "end-1c").strip()
        }

        try:
            self.profile_file.write_text(
                json.dumps(data, indent=4),
                encoding="utf-8"
            )
            self.save_btn.configure(text="✓ Saved!")
        except OSError:
            self.save_btn.configure(text="Save failed")

    def load_profile(self):
        """Restore previously saved profile information."""
        try:
            data = json.loads(
                self.profile_file.read_text(encoding="utf-8")
            )

            self.display_name.insert(
                0,
                data.get("display_name", "")
            )

            self.bio.insert(
                "1.0",
                data.get("bio", "")
            )

        except (OSError, ValueError, TypeError):
            pass

    def _show_initial_avatar(self):
        """Show the username initial when no picture has been chosen."""
        self.avatar_photo = None
        self.avatar.configure(image="", text=self.initial, bg=self.accent,
                              width=3, height=2)

    def _show_avatar_image(self, image):
        """Crop a Pillow image into a circular 112-pixel avatar."""
        image = image.convert("RGB")
        side = min(image.size)
        left = (image.width - side) // 2
        top = (image.height - side) // 2
        image = image.crop((left, top, left + side, top + side))
        image = image.resize((112, 112), Image.Resampling.LANCZOS)
        mask = Image.new("L", (112, 112), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 111, 111), fill=255)
        image.putalpha(mask)
        self.avatar_photo = ImageTk.PhotoImage(image, master=self.window)
        self.avatar.configure(image=self.avatar_photo, text="", width=112,
                              height=112)

    def load_avatar(self):
        """Load the locally stored avatar, or fall back to initials."""
        try:
            with Image.open(self.avatar_file) as image:
                self._show_avatar_image(image)
        except (OSError, ValueError, UnidentifiedImageError):
            self._show_initial_avatar()

    def change_picture(self):
        """Choose and locally store a PNG or JPEG avatar."""
        selected = filedialog.askopenfilename(
            parent=self.window,
            title="Choose your SYVO profile picture",
            filetypes=[("Image files", "*.png *.jpg *.jpeg"),
                       ("PNG images", "*.png"), ("JPEG images", "*.jpg *.jpeg")]
        )
        if not selected:
            return
        try:
            with Image.open(selected) as original:
                original = ImageOps.exif_transpose(original)

                if original.width * original.height > 40_000_000:
                    raise ValueError("Choose an image smaller than 40 megapixels.")
                # Create the preview and a small, normalized copy for local storage.
                self._show_avatar_image(original)
                normalized = original.convert("RGB")
                normalized.thumbnail((512, 512), Image.Resampling.LANCZOS)
                buffer = io.BytesIO()
                normalized.save(buffer, format="PNG")
            temporary = self.avatar_file.with_suffix(".tmp")
            temporary.write_bytes(buffer.getvalue())
            os.replace(temporary, self.avatar_file)
        except (OSError, ValueError, UnidentifiedImageError) as exc:
            self.load_avatar()
            messagebox.showerror("Profile picture", f"Could not use that image: {exc}",
                                 parent=self.window)

    def remove_picture(self):
        """Remove the locally saved image and restore the initials avatar."""
        try:
            self.avatar_file.unlink(missing_ok=True)
            self._show_initial_avatar()
        except OSError as exc:
            messagebox.showerror("Profile picture", f"Could not remove image: {exc}",
                                 parent=self.window)
