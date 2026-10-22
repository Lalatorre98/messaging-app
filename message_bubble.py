
import tkinter as tk


class MessageBubble(tk.Canvas):
    """A rounded message bubble for SYVO."""

    def __init__(
        self,
        parent,
        text,
        background,
        foreground,
        font=("Helvetica", 12),
        max_width=390
    ):
        super().__init__(
            parent,
            bg=parent.cget("bg"),
            highlightthickness=0,
            bd=0
        )

        padding_x = 15
        padding_y = 11
        radius = 14

        text_id = self.create_text(
            padding_x,
            padding_y,
            text=text,
            fill=foreground,
            font=font,
            anchor="nw",
            width=max_width - 2 * padding_x
        )

        bounds = self.bbox(text_id)
        width = bounds[2] + padding_x
        height = bounds[3] + padding_y

        self.configure(width=width, height=height)

        
# Draw a rounded rectangle with four curved corners.
        r = min(radius, width / 2, height / 2)

        self.create_polygon(
            r, 0,
            width - r, 0,
            width, 0,
            width, r,
            width, height - r,
            width, height,
            width - r, height,
            r, height,
            0, height,
            0, height - r,
            0, r,
            0, 0,
            r, 0,
            smooth=True,
            splinesteps=24,
            fill=background,
            outline=background,
            tags="bubble_background"
        )

        self.tag_lower("bubble_background")


       
        self.tag_raise(text_id)
