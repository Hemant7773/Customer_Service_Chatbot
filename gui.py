import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from PIL import Image, ImageTk
import os
import time
import threading

import utils
from chatbot_engine import ChatbotEngine

class ScrollableChatFrame(tk.Frame):
    """
    A custom scrollable frame container for displaying chat bubbles.
    """
    def __init__(self, container, bg_color, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.configure(bg=bg_color)
        
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0, bg=bg_color)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg_color)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Mousewheel binding
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", self._on_mousewheel)

    def _on_canvas_configure(self, event):
        # Keeps the inner scrollable frame matching the canvas width
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class ChatbotGUI:
    def __init__(self, root, engine: ChatbotEngine, assets_dir, exports_dir, history_dir):
        self.root = root
        self.engine = engine
        self.assets_dir = assets_dir
        self.exports_dir = exports_dir
        self.history_dir = history_dir
        
        # Programmatically generate assets if they are missing
        utils.generate_default_assets(self.assets_dir)
        
        # State Variables
        self.dark_mode = False
        self.voice_output_enabled = tk.BooleanVar(value=True)
        self.is_listening = False
        self.chat_history = []  # List of dicts: {'sender': ..., 'message': ..., 'timestamp': ...}
        
        # Load theme configurations
        self.themes = {
            "light": {
                "root_bg": "#F5F7FB",
                "header_bg": "#1A73E8",
                "header_text": "#FFFFFF",
                "chat_bg": "#FFFFFF",
                "input_area_bg": "#F1F3F4",
                "input_bg": "#FFFFFF",
                "input_text": "#202124",
                "bot_bubble": "#E8F0FE",
                "bot_text": "#202124",
                "user_bubble": "#1A73E8",
                "user_text": "#FFFFFF",
                "button_bg": "#1A73E8",
                "button_text": "#FFFFFF",
                "timestamp_text": "#5F6368"
            },
            "dark": {
                "root_bg": "#121212",
                "header_bg": "#1F1F1F",
                "header_text": "#E8EAED",
                "chat_bg": "#1E1E1E",
                "input_area_bg": "#202124",
                "input_bg": "#2D2D2D",
                "input_text": "#E8EAED",
                "bot_bubble": "#2D2D2D",
                "bot_text": "#E8EAED",
                "user_bubble": "#8AB4F8",
                "user_text": "#202124",
                "button_bg": "#8AB4F8",
                "button_text": "#202124",
                "timestamp_text": "#9AA0A6"
            }
        }
        self.current_theme = self.themes["light"]
        
        # Setup GUI Window
        self.root.title("AssistBot - Customer Service Portal")
        self.root.geometry("520x700") # Set a comfortable size
        self.root.minsize(450, 600)
        self.root.configure(bg=self.current_theme["root_bg"])
        
        # Load Icons
        self.load_images()
        
        # Create UI Elements
        self.create_header()
        self.create_chat_area()
        self.create_input_area()
        
        # Send initial greeting
        self.show_welcome_message()

    def load_images(self):
        """Loads and resizes avatar icons."""
        try:
            bot_img = Image.open(os.path.join(self.assets_dir, "bot.png"))
            self.bot_icon = ImageTk.PhotoImage(bot_img.resize((36, 36), Image.Resampling.LANCZOS))
            
            user_img = Image.open(os.path.join(self.assets_dir, "user.png"))
            self.user_icon = ImageTk.PhotoImage(user_img.resize((36, 36), Image.Resampling.LANCZOS))
            
            logo_img = Image.open(os.path.join(self.assets_dir, "logo.png"))
            self.logo_icon = ImageTk.PhotoImage(logo_img.resize((24, 24), Image.Resampling.LANCZOS))
        except Exception as e:
            print(f"Error loading images: {e}")
            self.bot_icon = None
            self.user_icon = None
            self.logo_icon = None

    def create_header(self):
        """Creates the top header bar of the chatbot."""
        self.header_frame = tk.Frame(self.root, bg=self.current_theme["header_bg"], height=60)
        self.header_frame.pack(fill="x", side="top")
        
        # Logo and Title
        title_container = tk.Frame(self.header_frame, bg=self.current_theme["header_bg"])
        title_container.pack(side="left", padx=15, pady=10)
        
        if self.logo_icon:
            logo_label = tk.Label(title_container, image=self.logo_icon, bg=self.current_theme["header_bg"])
            logo_label.pack(side="left", padx=(0, 8))
            
        self.title_label = tk.Label(
            title_container, 
            text="AssistBot Support", 
            font=("Segoe UI Semibold", 14), 
            fg=self.current_theme["header_text"],
            bg=self.current_theme["header_bg"]
        )
        self.title_label.pack(side="left")
        
        # Action Buttons Container
        actions_container = tk.Frame(self.header_frame, bg=self.current_theme["header_bg"])
        actions_container.pack(side="right", padx=15)
        
        # Admin Portal Button
        self.admin_btn = tk.Button(
            actions_container,
            text="⚙ Admin",
            font=("Segoe UI", 9),
            bg=self.current_theme["header_bg"],
            fg=self.current_theme["header_text"],
            relief="flat",
            activebackground=self.current_theme["header_bg"],
            activeforeground="#FFC107",
            command=self.open_admin_panel,
            cursor="hand2"
        )
        self.admin_btn.pack(side="left", padx=5)
        
        # Dark Mode Toggle Button
        self.theme_btn = tk.Button(
            actions_container,
            text="🌙",
            font=("Segoe UI", 12),
            bg=self.current_theme["header_bg"],
            fg=self.current_theme["header_text"],
            relief="flat",
            activebackground=self.current_theme["header_bg"],
            command=self.toggle_theme,
            cursor="hand2"
        )
        self.theme_btn.pack(side="left", padx=5)

    def create_chat_area(self):
        """Creates the scrollable chat display space."""
        self.chat_container = tk.Frame(self.root, bg=self.current_theme["root_bg"])
        self.chat_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Options Bar under Header
        options_bar = tk.Frame(self.chat_container, bg=self.current_theme["root_bg"])
        options_bar.pack(fill="x", pady=(0, 5))
        
        # Clear Chat Button
        self.clear_btn = tk.Button(
            options_bar,
            text="🧹 Clear",
            font=("Segoe UI", 9),
            bg=self.current_theme["root_bg"],
            fg=self.current_theme["timestamp_text"],
            relief="flat",
            command=self.clear_chat,
            cursor="hand2"
        )
        self.clear_btn.pack(side="left", padx=5)
        
        # Save Log Button
        self.save_btn = tk.Button(
            options_bar,
            text="💾 Save Log",
            font=("Segoe UI", 9),
            bg=self.current_theme["root_bg"],
            fg=self.current_theme["timestamp_text"],
            relief="flat",
            command=self.save_chat_log,
            cursor="hand2"
        )
        self.save_btn.pack(side="left", padx=5)
        
        # Export PDF Button
        self.pdf_btn = tk.Button(
            options_bar,
            text="📄 PDF Export",
            font=("Segoe UI", 9),
            bg=self.current_theme["root_bg"],
            fg=self.current_theme["timestamp_text"],
            relief="flat",
            command=self.export_pdf,
            cursor="hand2"
        )
        self.pdf_btn.pack(side="left", padx=5)
        
        # TTS Sound Toggle Checkbox
        self.sound_cb = tk.Checkbutton(
            options_bar,
            text="🔊 TTS Audio",
            variable=self.voice_output_enabled,
            onvalue=True,
            offvalue=False,
            font=("Segoe UI", 9),
            bg=self.current_theme["root_bg"],
            fg=self.current_theme["timestamp_text"],
            selectcolor=self.current_theme["root_bg"],
            activebackground=self.current_theme["root_bg"],
            cursor="hand2"
        )
        self.sound_cb.pack(side="right", padx=5)
        
        # The Scrollable Chat Area
        self.chat_frame = ScrollableChatFrame(self.chat_container, self.current_theme["chat_bg"])
        self.chat_frame.pack(fill="both", expand=True)

    def create_input_area(self):
        """Creates the bottom text input and send bar."""
        self.input_area = tk.Frame(self.root, bg=self.current_theme["input_area_bg"], height=80)
        self.input_area.pack(fill="x", side="bottom", ipady=5)
        
        # Layout container inside input area
        input_container = tk.Frame(self.input_area, bg=self.input_area.cget("bg"))
        input_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Voice Input Microphone Button
        self.mic_btn = tk.Button(
            input_container,
            text="🎙",
            font=("Segoe UI", 14),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_text"],
            relief="flat",
            activebackground=self.current_theme["button_bg"],
            activeforeground=self.current_theme["button_text"],
            width=3,
            command=self.trigger_voice_input,
            cursor="hand2"
        )
        self.mic_btn.pack(side="left", padx=(0, 5))
        
        # Text Entry box
        self.entry_box = tk.Entry(
            input_container, 
            font=("Segoe UI", 11), 
            bg=self.current_theme["input_bg"],
            fg=self.current_theme["input_text"],
            insertbackground=self.current_theme["input_text"],
            relief="flat"
        )
        self.entry_box.pack(side="left", fill="both", expand=True, ipady=8, padx=5)
        self.entry_box.bind("<Return>", lambda e: self.send_message())
        self.entry_box.focus()
        
        # Send Button
        self.send_btn = tk.Button(
            input_container,
            text="Send",
            font=("Segoe UI Semibold", 10),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_text"],
            relief="flat",
            activebackground=self.current_theme["button_bg"],
            activeforeground=self.current_theme["button_text"],
            width=8,
            command=self.send_message,
            cursor="hand2"
        )
        self.send_btn.pack(side="right", padx=(5, 0))

    def show_welcome_message(self):
        """Displays initial welcome text."""
        welcome = self.engine.config.get("bot_config", {}).get("welcome_message", "Hello! How can I help you today?")
        self.add_message_bubble("Bot", welcome)

    def add_message_bubble(self, sender, text):
        """
        Appends a styled message bubble to the chat view.
        """
        timestamp = utils.get_timestamp()
        
        # Log to list
        self.chat_history.append({
            'sender': sender,
            'message': text,
            'timestamp': timestamp
        })
        
        # Parent bubble container frame
        bubble_row = tk.Frame(self.chat_frame.scrollable_frame, bg=self.current_theme["chat_bg"], pady=6)
        bubble_row.pack(fill="x", anchor="w")
        
        if sender == "Bot":
            # Grid structure: [bot icon] [message bubble frame]
            if self.bot_icon:
                avatar_label = tk.Label(bubble_row, image=self.bot_icon, bg=self.current_theme["chat_bg"])
                avatar_label.pack(side="left", anchor="nw", padx=(10, 5))
                
            # Bubble frame
            bubble = tk.Frame(
                bubble_row, 
                bg=self.current_theme["bot_bubble"],
                padx=12,
                pady=8
            )
            bubble.pack(side="left", anchor="nw", padx=(5, 50))
            
            # Content
            msg_label = tk.Label(
                bubble,
                text=text,
                font=("Segoe UI", 10),
                bg=self.current_theme["bot_bubble"],
                fg=self.current_theme["bot_text"],
                justify="left",
                wraplength=300
            )
            msg_label.pack(anchor="w")
            
            # Time tag
            time_label = tk.Label(
                bubble,
                text=f"AssistBot • {timestamp}",
                font=("Segoe UI", 7),
                bg=self.current_theme["bot_bubble"],
                fg=self.current_theme["timestamp_text"]
            )
            time_label.pack(anchor="w", pady=(4, 0))
            
        else:
            # Grid structure: [message bubble frame] [user icon]
            if self.user_icon:
                avatar_label = tk.Label(bubble_row, image=self.user_icon, bg=self.current_theme["chat_bg"])
                avatar_label.pack(side="right", anchor="ne", padx=(5, 10))
                
            # Bubble frame
            bubble = tk.Frame(
                bubble_row, 
                bg=self.current_theme["user_bubble"],
                padx=12,
                pady=8
            )
            bubble.pack(side="right", anchor="ne", padx=(50, 5))
            
            # Content
            msg_label = tk.Label(
                bubble,
                text=text,
                font=("Segoe UI", 10),
                bg=self.current_theme["user_bubble"],
                fg=self.current_theme["user_text"],
                justify="left",
                wraplength=300
            )
            msg_label.pack(anchor="e")
            
            # Time tag
            time_label = tk.Label(
                bubble,
                text=f"You • {timestamp}",
                font=("Segoe UI", 7),
                bg=self.current_theme["user_bubble"],
                fg=self.current_theme["user_text"]
            )
            time_label.pack(anchor="e", pady=(4, 0))
            
        # Autoscroll
        self.root.update_idletasks()
        self.chat_frame.canvas.yview_moveto(1.0)

    def show_typing_indicator(self):
        """Displays a temporary typing animation block."""
        self.typing_row = tk.Frame(self.chat_frame.scrollable_frame, bg=self.current_theme["chat_bg"], pady=6)
        self.typing_row.pack(fill="x", anchor="w")
        
        if self.bot_icon:
            avatar_label = tk.Label(self.typing_row, image=self.bot_icon, bg=self.current_theme["chat_bg"])
            avatar_label.pack(side="left", anchor="nw", padx=(10, 5))
            
        self.typing_bubble = tk.Frame(
            self.typing_row, 
            bg=self.current_theme["bot_bubble"],
            padx=12,
            pady=8
        )
        self.typing_bubble.pack(side="left", anchor="nw", padx=(5, 50))
        
        self.typing_label = tk.Label(
            self.typing_bubble,
            text="AssistBot is typing...",
            font=("Segoe UI Italic", 9),
            bg=self.current_theme["bot_bubble"],
            fg=self.current_theme["timestamp_text"]
        )
        self.typing_label.pack()
        
        # Scroll to bottom
        self.root.update_idletasks()
        self.chat_frame.canvas.yview_moveto(1.0)
        
        # Start dot blink animation
        self.animate_dots(0)

    def animate_dots(self, count):
        """Blinks dots to simulate typing activity."""
        if hasattr(self, 'typing_row') and self.typing_row.winfo_exists():
            dots = "." * (count % 4)
            self.typing_label.config(text=f"AssistBot is typing{dots}")
            self.root.after(400, lambda: self.animate_dots(count + 1))

    def remove_typing_indicator(self):
        """Removes the typing animation widget."""
        if hasattr(self, 'typing_row') and self.typing_row.winfo_exists():
            self.typing_row.destroy()

    def send_message(self):
        """Handles sending of the user query and triggering bot reply."""
        user_text = self.entry_box.get().strip()
        if not user_text:
            return # Empty validation
            
        # Clear field
        self.entry_box.delete(0, tk.END)
        
        # Display user message bubble
        self.add_message_bubble("User", user_text)
        
        # Trigger typing indicator
        self.show_typing_indicator()
        
        # Process in secondary task to avoid lag (optional, but 1s Tkinter delay simulates response)
        self.root.after(1000, lambda: self.process_bot_reply(user_text))

    def process_bot_reply(self, user_text):
        """Fetches engine response, destroys typing indicator, and appends bubble."""
        self.remove_typing_indicator()
        
        # Generate response
        response = self.engine.get_response(user_text)
        
        # Display bubble
        self.add_message_bubble("Bot", response)
        
        # Speak response if enabled
        if self.voice_output_enabled.get():
            utils.speak_text(response)

    def trigger_voice_input(self):
        """Listens to speech in background thread to avoid freezing GUI."""
        if self.is_listening:
            return
            
        self.is_listening = True
        self.mic_btn.config(text="🔴", bg="#EA4335", fg="#FFFFFF") # Indicate recording state
        
        # Start listening in thread
        t = threading.Thread(target=self._run_voice_input_thread, daemon=True)
        t.start()

    def _run_voice_input_thread(self):
        success, text_or_error = utils.listen_speech()
        
        # Update UI in main thread
        self.root.after(0, lambda: self._handle_voice_input_result(success, text_or_error))

    def _handle_voice_input_result(self, success, result):
        self.is_listening = False
        # Restore mic button appearance
        self.mic_btn.config(
            text="🎙", 
            bg=self.current_theme["button_bg"], 
            fg=self.current_theme["button_text"]
        )
        
        if success:
            # Insert text into entry and set focus
            self.entry_box.delete(0, tk.END)
            self.entry_box.insert(0, result)
            self.send_message() # Automatically send spoken message
        else:
            messagebox.showwarning("Voice Input Failed", result)

    def toggle_theme(self):
        """Switches GUI colors between light and dark modes."""
        self.dark_mode = not self.dark_mode
        theme_key = "dark" if self.dark_mode else "light"
        self.current_theme = self.themes[theme_key]
        self.theme_btn.config(text="☀️" if self.dark_mode else "🌙")
        
        # Update colors on main containers
        self.root.configure(bg=self.current_theme["root_bg"])
        self.header_frame.configure(bg=self.current_theme["header_bg"])
        self.title_label.configure(bg=self.current_theme["header_bg"], fg=self.current_theme["header_text"])
        self.admin_btn.configure(bg=self.current_theme["header_bg"], fg=self.current_theme["header_text"], activebackground=self.current_theme["header_bg"])
        self.theme_btn.configure(bg=self.current_theme["header_bg"], fg=self.current_theme["header_text"], activebackground=self.current_theme["header_bg"])
        
        self.chat_container.configure(bg=self.current_theme["root_bg"])
        self.clear_btn.configure(bg=self.current_theme["root_bg"], fg=self.current_theme["timestamp_text"])
        self.save_btn.configure(bg=self.current_theme["root_bg"], fg=self.current_theme["timestamp_text"])
        self.pdf_btn.configure(bg=self.current_theme["root_bg"], fg=self.current_theme["timestamp_text"])
        self.sound_cb.configure(bg=self.current_theme["root_bg"], fg=self.current_theme["timestamp_text"], selectcolor=self.current_theme["root_bg"], activebackground=self.current_theme["root_bg"])
        
        self.chat_frame.configure(bg=self.current_theme["chat_bg"])
        self.chat_frame.canvas.configure(bg=self.current_theme["chat_bg"])
        self.chat_frame.scrollable_frame.configure(bg=self.current_theme["chat_bg"])
        
        self.input_area.configure(bg=self.current_theme["input_area_bg"])
        self.mic_btn.configure(bg=self.current_theme["button_bg"], fg=self.current_theme["button_text"], activebackground=self.current_theme["button_bg"])
        self.entry_box.configure(bg=self.current_theme["input_bg"], fg=self.current_theme["input_text"], insertbackground=self.current_theme["input_text"])
        self.send_btn.configure(bg=self.current_theme["button_bg"], fg=self.current_theme["button_text"], activebackground=self.current_theme["button_bg"])
        
        # Redraw all message bubbles to apply new colors
        # Clear scrollable frame children
        for child in self.chat_frame.scrollable_frame.winfo_children():
            child.destroy()
            
        # Rebuild bubbles from saved log
        temp_history = list(self.chat_history)
        self.chat_history.clear() # Clear since add_message_bubble appends to it
        for item in temp_history:
            self.add_message_bubble_with_time(item["sender"], item["message"], item["timestamp"])

    def add_message_bubble_with_time(self, sender, text, timestamp):
        """Rebuild bubble logs with fixed original timestamps during theme toggle."""
        self.chat_history.append({
            'sender': sender,
            'message': text,
            'timestamp': timestamp
        })
        
        bubble_row = tk.Frame(self.chat_frame.scrollable_frame, bg=self.current_theme["chat_bg"], pady=6)
        bubble_row.pack(fill="x", anchor="w")
        
        if sender == "Bot":
            if self.bot_icon:
                avatar_label = tk.Label(bubble_row, image=self.bot_icon, bg=self.current_theme["chat_bg"])
                avatar_label.pack(side="left", anchor="nw", padx=(10, 5))
            bubble = tk.Frame(bubble_row, bg=self.current_theme["bot_bubble"], padx=12, pady=8)
            bubble.pack(side="left", anchor="nw", padx=(5, 50))
            msg_label = tk.Label(bubble, text=text, font=("Segoe UI", 10), bg=self.current_theme["bot_bubble"], fg=self.current_theme["bot_text"], justify="left", wraplength=300)
            msg_label.pack(anchor="w")
            time_label = tk.Label(bubble, text=f"AssistBot • {timestamp}", font=("Segoe UI", 7), bg=self.current_theme["bot_bubble"], fg=self.current_theme["timestamp_text"])
            time_label.pack(anchor="w", pady=(4, 0))
        else:
            if self.user_icon:
                avatar_label = tk.Label(bubble_row, image=self.user_icon, bg=self.current_theme["chat_bg"])
                avatar_label.pack(side="right", anchor="ne", padx=(5, 10))
            bubble = tk.Frame(bubble_row, bg=self.current_theme["user_bubble"], padx=12, pady=8)
            bubble.pack(side="right", anchor="ne", padx=(50, 5))
            msg_label = tk.Label(bubble, text=text, font=("Segoe UI", 10), bg=self.current_theme["user_bubble"], fg=self.current_theme["user_text"], justify="left", wraplength=300)
            msg_label.pack(anchor="e")
            time_label = tk.Label(bubble, text=f"You • {timestamp}", font=("Segoe UI", 7), bg=self.current_theme["user_bubble"], fg=self.current_theme["user_text"])
            time_label.pack(anchor="e", pady=(4, 0))
            
        self.chat_frame.canvas.yview_moveto(1.0)

    def clear_chat(self):
        """Resets the conversation dialogue panel."""
        if messagebox.askyesno("Clear Chat", "Are you sure you want to clear this conversation history?"):
            self.chat_history.clear()
            for child in self.chat_frame.scrollable_frame.winfo_children():
                child.destroy()
            self.show_welcome_message()

    def save_chat_log(self):
        """Saves chat logs to text file."""
        if not self.chat_history:
            messagebox.showinfo("Empty Chat", "There is no history to save.")
            return
            
        filename = f"chat_log_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        default_path = os.path.join(self.history_dir, filename)
        
        filepath = filedialog.asksaveasfilename(
            initialfile=filename,
            initialdir=self.history_dir,
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if filepath:
            success, msg = utils.save_chat_to_txt(self.chat_history, filepath)
            if success:
                messagebox.showinfo("Success", msg)
            else:
                messagebox.showerror("Error", f"Could not save file: {msg}")

    def export_pdf(self):
        """Exports chat logs to PDF document."""
        if not self.chat_history:
            messagebox.showinfo("Empty Chat", "There is no history to export.")
            return
            
        filename = f"chat_export_{time.strftime('%Y%m%d_%H%M%S')}.pdf"
        default_path = os.path.join(self.exports_dir, filename)
        
        filepath = filedialog.asksaveasfilename(
            initialfile=filename,
            initialdir=self.exports_dir,
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        
        if filepath:
            success, msg = utils.export_chat_to_pdf(self.chat_history, filepath)
            if success:
                messagebox.showinfo("Success", msg)
            else:
                messagebox.showerror("Error", f"Could not export PDF: {msg}")

    def open_admin_panel(self):
        """Opens separate Admin configuration window for intents file editing."""
        AdminPanel(self.root, self.engine)


class AdminPanel:
    """
    Separate window for administrators to configure intents.json knowledge base.
    """
    def __init__(self, parent, engine: ChatbotEngine):
        self.engine = engine
        self.win = tk.Toplevel(parent)
        self.win.title("Admin Portal - Intent Manager")
        self.win.geometry("600x500")
        self.win.transient(parent)
        self.win.grab_set()
        
        # Top Panel
        top_frame = tk.Frame(self.win, bg="#1A73E8", height=50)
        top_frame.pack(fill="x", side="top")
        
        tk.Label(
            top_frame,
            text="Knowledge Base Editor",
            font=("Segoe UI Semibold", 12),
            fg="#FFFFFF",
            bg="#1A73E8"
        ).pack(side="left", padx=15, pady=10)
        
        # Main Layout
        self.main_pane = tk.PanedWindow(self.win, orient="horizontal", borderwidth=0)
        self.main_pane.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left Panel (Listbox for Intents tags)
        left_frame = tk.Frame(self.main_pane)
        self.main_pane.add(left_frame, width=180)
        
        tk.Label(left_frame, text="Select FAQ Intent Tag:", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 5))
        
        list_container = tk.Frame(left_frame)
        list_container.pack(fill="both", expand=True)
        
        self.intent_listbox = tk.Listbox(list_container, font=("Segoe UI", 9))
        self.intent_listbox.pack(side="left", fill="both", expand=True)
        self.intent_listbox.bind("<<ListboxSelect>>", self.on_intent_select)
        
        scrollbar = tk.Scrollbar(list_container, orient="vertical", command=self.intent_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.intent_listbox.config(yscrollcommand=scrollbar.set)
        
        # Actions for tags
        tag_actions = tk.Frame(left_frame)
        tag_actions.pack(fill="x", pady=5)
        
        tk.Button(tag_actions, text="➕ Add Tag", font=("Segoe UI", 8), command=self.add_new_tag).pack(side="left", fill="x", expand=True, padx=2)
        tk.Button(tag_actions, text="❌ Delete", font=("Segoe UI", 8), bg="#FADBD8", fg="#C0392B", command=self.delete_tag).pack(side="right", fill="x", expand=True, padx=2)
        
        # Right Panel (Details editor)
        self.right_frame = tk.Frame(self.main_pane, bg="#F5F7FB", padx=10, pady=5)
        self.main_pane.add(self.right_frame)
        
        # Editor fields
        tk.Label(self.right_frame, text="Intent Tag Name:", font=("Segoe UI", 9, "bold"), bg="#F5F7FB").pack(anchor="w")
        self.tag_entry = tk.Entry(self.right_frame, font=("Segoe UI", 9), state="readonly")
        self.tag_entry.pack(fill="x", pady=(2, 8))
        
        # Patterns
        tk.Label(self.right_frame, text="User Search Patterns (one per line):", font=("Segoe UI", 9, "bold"), bg="#F5F7FB").pack(anchor="w")
        self.patterns_text = tk.Text(self.right_frame, font=("Segoe UI", 9), height=6)
        self.patterns_text.pack(fill="x", pady=(2, 8))
        
        # Responses
        tk.Label(self.right_frame, text="Bot Answers (one per line):", font=("Segoe UI", 9, "bold"), bg="#F5F7FB").pack(anchor="w")
        self.responses_text = tk.Text(self.right_frame, font=("Segoe UI", 9), height=6)
        self.responses_text.pack(fill="x", pady=(2, 8))
        
        # Save controls
        ctrl_frame = tk.Frame(self.right_frame, bg="#F5F7FB")
        ctrl_frame.pack(fill="x", pady=5)
        
        self.save_btn = tk.Button(
            ctrl_frame,
            text="Save Intent Changes",
            font=("Segoe UI Semibold", 9),
            bg="#1A73E8",
            fg="#FFFFFF",
            command=self.save_intent_details
        )
        self.save_btn.pack(side="right", padx=5)
        
        # Populate Intents
        self.refresh_intent_list()

    def refresh_intent_list(self):
        """Loads tags from engine into Listbox."""
        self.intent_listbox.delete(0, tk.END)
        for intent in self.engine.intents:
            self.intent_listbox.insert(tk.END, intent["tag"])
            
        # Select first item
        if self.engine.intents:
            self.intent_listbox.selection_set(0)
            self.on_intent_select(None)

    def on_intent_select(self, event):
        """Populates editor fields with selected intent data."""
        selection = self.intent_listbox.curselection()
        if not selection:
            return
            
        idx = selection[0]
        selected_tag = self.intent_listbox.get(idx)
        
        # Find matching intent
        intent = next((x for x in self.engine.intents if x["tag"] == selected_tag), None)
        if intent:
            # Set tag text
            self.tag_entry.config(state="normal")
            self.tag_entry.delete(0, tk.END)
            self.tag_entry.insert(0, intent["tag"])
            # If standard tags like 'unknown' or 'greetings', prevent tag renaming
            if intent["tag"] in ["unknown", "greetings", "goodbye"]:
                self.tag_entry.config(state="readonly")
            else:
                self.tag_entry.config(state="normal")
                
            # Set patterns
            self.patterns_text.delete("1.0", tk.END)
            self.patterns_text.insert(tk.END, "\n".join(intent.get("patterns", [])))
            
            # Set responses
            self.responses_text.delete("1.0", tk.END)
            self.responses_text.insert(tk.END, "\n".join(intent.get("responses", [])))

    def save_intent_details(self):
        """Saves text changes of selected intent back to intents list."""
        selection = self.intent_listbox.curselection()
        if not selection:
            return
            
        idx = selection[0]
        old_tag = self.intent_listbox.get(idx)
        new_tag = self.tag_entry.get().strip().lower()
        
        if not new_tag:
            messagebox.showerror("Error", "Tag name cannot be empty.")
            return
            
        # Extract patterns and responses
        pats = [p.strip() for p in self.patterns_text.get("1.0", tk.END).split("\n") if p.strip()]
        resps = [r.strip() for r in self.responses_text.get("1.0", tk.END).split("\n") if r.strip()]
        
        if not resps:
            messagebox.showerror("Error", "There must be at least one bot response.")
            return
            
        # Update engine list
        for intent in self.engine.intents:
            if intent["tag"] == old_tag:
                intent["tag"] = new_tag
                intent["patterns"] = pats
                intent["responses"] = resps
                break
                
        # Write to JSON
        success = self.engine.save_intents()
        if success:
            messagebox.showinfo("Success", "FAQ Intent database updated successfully.")
            self.refresh_intent_list()
        else:
            messagebox.showerror("Error", "Could not save database changes.")

    def add_new_tag(self):
        """Prompts for a new tag name and appends it to intents list."""
        new_tag = messagebox.askquestion("Add New Intent", "Would you like to add a new FAQ tag?").lower()
        if new_tag == "no":
            return
            
        # Open small dialog for text input
        d = tk.Toplevel(self.win)
        d.title("New Tag")
        d.geometry("300x120")
        d.transient(self.win)
        d.grab_set()
        
        tk.Label(d, text="Enter unique tag name (lowercase, no spaces):").pack(pady=10)
        e = tk.Entry(d)
        e.pack(fill="x", padx=20, pady=5)
        e.focus()
        
        def save():
            tag = e.get().strip().lower()
            if not tag:
                messagebox.showerror("Error", "Tag cannot be empty.", parent=d)
                return
            if any(x["tag"] == tag for x in self.engine.intents):
                messagebox.showerror("Error", "Tag already exists.", parent=d)
                return
            
            # Append new empty intent
            self.engine.intents.append({
                "tag": tag,
                "patterns": ["sample question for " + tag],
                "responses": ["sample response for " + tag]
            })
            self.engine.save_intents()
            d.destroy()
            self.refresh_intent_list()
            
        tk.Button(d, text="Create", command=save).pack(pady=10)

    def delete_tag(self):
        """Deletes selected tag from engine lists."""
        selection = self.intent_listbox.curselection()
        if not selection:
            return
            
        idx = selection[0]
        tag = self.intent_listbox.get(idx)
        
        if tag in ["unknown", "greetings", "goodbye"]:
            messagebox.showerror("Action Denied", f"Cannot delete core system tag: '{tag}'")
            return
            
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete intent tag '{tag}'?"):
            self.engine.intents = [x for x in self.engine.intents if x["tag"] != tag]
            self.engine.save_intents()
            self.refresh_intent_list()
