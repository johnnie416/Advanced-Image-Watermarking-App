import tkinter as tk
from tkinter import filedialog, colorchooser, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont

# -----------------------------
# Scrollable Left Panel
# -----------------------------
class ScrollableLeftPanel(tk.Frame):
    def __init__(self, parent, width=260, height=600, *args, **kwargs):
        super().__init__(parent, width=width, height=height, *args, **kwargs)
        self.pack_propagate(False)
        self.canvas = tk.Canvas(self, width=width-30, height=height, bg="#3b3b3b", highlightthickness=0)
        self.scroll_frame = tk.Frame(self.canvas, bg="#3b3b3b")
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.create_window((0,0), window=self.scroll_frame, anchor="nw")
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def add_widget(self, widget):
        widget.pack(fill="x", padx=10, pady=5)

# -----------------------------
# Watermark App
# -----------------------------
class WatermarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Watermark App")
        self.root.geometry("1000x600")
        self.root.configure(bg="#2e2e2e")
        try:
            self.root.iconbitmap("app_icon.ico")
        except: pass

        # Attributes
        self.images = []
        self.current_index = 0
        self.history = []
        self.redo_stack = []
        self.tk_img = None
        self.watermark_color = "#FFFFFF"
        self.logo_image = None
        self.available_fonts = ["arial.ttf", "times.ttf", "cour.ttf", "calibri.ttf"]

        # Left panel (scrollable)
        self.left_frame = ScrollableLeftPanel(root)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)

        # Right frame
        self.right_frame = tk.Frame(root, bg="#1e1e1e")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(self.right_frame, bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", self.refresh_image)

        # Build buttons & controls
        self.create_controls()

        # Keyboard shortcuts
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Control-s>", lambda e: self.save_image())

    # -----------------------------
    # Helper
    # -----------------------------
    def hex_to_rgba(self, hex_color, alpha=255):
        hex_color = hex_color.lstrip("#")
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0,2,4))
        return (r,g,b, alpha)

    # -----------------------------
    # Controls
    # -----------------------------
    def create_controls(self):
        btn_font = ("Arial", 11, "bold")

        # Upload images first
        self.left_frame.add_widget(tk.Button(self.left_frame.scroll_frame, text="Upload Images", command=self.upload_images, bg="#4CAF50", fg="white", font=btn_font))

        # Navigation buttons
        self.left_frame.add_widget(tk.Button(self.left_frame.scroll_frame, text="Previous Image", command=self.prev_image, bg="#795548", fg="white", font=btn_font))
        self.left_frame.add_widget(tk.Button(self.left_frame.scroll_frame, text="Next Image", command=self.next_image, bg="#795548", fg="white", font=btn_font))

        # Watermark Text
        tk.Label(self.left_frame.scroll_frame, text="Watermark Text:", bg="#3b3b3b", fg="white").pack(anchor="w", padx=10)
        self.text_entry = tk.Entry(self.left_frame.scroll_frame, font=("Arial",12))
        self.text_entry.pack(fill="x", padx=10, pady=5)

        # Font Size
        tk.Label(self.left_frame.scroll_frame, text="Font Size:", bg="#3b3b3b", fg="white").pack(anchor="w", padx=10)
        self.font_size = tk.IntVar(value=30)
        tk.Spinbox(self.left_frame.scroll_frame, from_=10, to=100, textvariable=self.font_size, font=("Arial",11)).pack(fill="x", padx=10, pady=5)

        # Font
        tk.Label(self.left_frame.scroll_frame, text="Font:", bg="#3b3b3b", fg="white").pack(anchor="w", padx=10)
        self.font_var = tk.StringVar(value=self.available_fonts[0])
        tk.OptionMenu(self.left_frame.scroll_frame, self.font_var, *self.available_fonts).pack(fill="x", padx=10, pady=5)

        # Position
        tk.Label(self.left_frame.scroll_frame, text="Position:", bg="#3b3b3b", fg="white").pack(anchor="w", padx=10)
        self.position_var = tk.StringVar(value="Bottom-Right")
        tk.OptionMenu(self.left_frame.scroll_frame, self.position_var, "Top-Left","Top-Right","Bottom-Left","Bottom-Right","Center").pack(fill="x", padx=10, pady=5)

        # Other buttons
        self.left_frame.add_widget(tk.Button(self.left_frame.scroll_frame, text="Choose Color", command=self.choose_color, bg="#2196F3", fg="white", font=btn_font))
        self.left_frame.add_widget(tk.Button(self.left_frame.scroll_frame, text="Upload Logo", command=self.upload_logo, bg="#FF9800", fg="white", font=btn_font))
        self.left_frame.add_widget(tk.Button(self.left_frame.scroll_frame, text="Apply Watermark", command=self.apply_watermark, bg="#9C27B0", fg="white", font=btn_font))
        self.left_frame.add_widget(tk.Button(self.left_frame.scroll_frame, text="Apply to All Images", command=self.apply_watermark_all, bg="#FF5722", fg="white", font=btn_font))
        self.left_frame.add_widget(tk.Button(self.left_frame.scroll_frame, text="Undo", command=self.undo, bg="#f44336", fg="white", font=btn_font))
        self.left_frame.add_widget(tk.Button(self.left_frame.scroll_frame, text="Redo", command=self.redo, bg="#607D8B", fg="white", font=btn_font))
        self.left_frame.add_widget(tk.Button(self.left_frame.scroll_frame, text="Save Image", command=self.save_image, bg="#009688", fg="white", font=btn_font))
        self.left_frame.add_widget(tk.Button(self.left_frame.scroll_frame, text="About", command=self.show_about, bg="#607D8B", fg="white", font=btn_font))

    # -----------------------------
    # About popup
    # -----------------------------
    def show_about(self):
        messagebox.showinfo(
            "About Watermark App",
            "Watermark App v1.0\nCreated by [Your Name]\nPython | Tkinter | Pillow"
        )

    # -----------------------------
    # Actions
    # -----------------------------
    def upload_images(self):
        paths = filedialog.askopenfilenames(filetypes=[("Image files","*.png *.jpg *.jpeg")])
        if paths:
            self.images = [Image.open(p).convert("RGBA") for p in paths]
            self.current_index = 0
            self.history = [self.images[0].copy()]
            self.redo_stack = []
            self.show_image(self.images[0])

    def choose_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.watermark_color = color

    def upload_logo(self):
        path = filedialog.askopenfilename(filetypes=[("Image files","*.png *.jpg *.jpeg")])
        if path:
            self.logo_image = Image.open(path).convert("RGBA")
            messagebox.showinfo("Logo Loaded", "Logo watermark loaded successfully!")

    def apply_watermark(self):
        if not self.images:
            messagebox.showwarning("No Image", "Upload images first.")
            return

        img = self.images[self.current_index].copy().convert("RGBA")
        draw = ImageDraw.Draw(img)
        text = self.text_entry.get()
        font_size = self.font_size.get()
        font_name = self.font_var.get()
        try:
            font = ImageFont.truetype(font_name, font_size)
        except:
            font = ImageFont.load_default()

        # Add text
        if text:
            bbox = draw.textbbox((0,0), text, font=font)
            text_width = bbox[2]-bbox[0]
            text_height = bbox[3]-bbox[1]

            pos_choice = self.position_var.get()
            if pos_choice=="Top-Left": pos=(10,10)
            elif pos_choice=="Top-Right": pos=(img.width-text_width-10,10)
            elif pos_choice=="Bottom-Left": pos=(10,img.height-text_height-10)
            elif pos_choice=="Bottom-Right": pos=(img.width-text_width-10,img.height-text_height-10)
            else: pos=((img.width-text_width)//2,(img.height-text_height)//2)

            draw.text(pos, text, font=font, fill=self.hex_to_rgba(self.watermark_color,255))

        # Add logo
        if self.logo_image:
            logo = self.logo_image.copy()
            max_width = int(img.width*0.15)
            ratio = max_width/logo.width
            logo = logo.resize((max_width,int(logo.height*ratio)),Image.LANCZOS)

            if self.position_var.get()=="Top-Left": logo_pos=(10,10)
            elif self.position_var.get()=="Top-Right": logo_pos=(img.width-logo.width-10,10)
            elif self.position_var.get()=="Bottom-Left": logo_pos=(10,img.height-logo.height-10)
            elif self.position_var.get()=="Bottom-Right": logo_pos=(img.width-logo.width-10,img.height-logo.height-10)
            else: logo_pos=((img.width-logo.width)//2,(img.height-logo.height)//2)

            img.paste(logo, logo_pos, logo)

        self.history.append(img.copy())
        self.redo_stack=[]
        self.images[self.current_index]=img
        self.show_image(img)

    def apply_watermark_all(self):
        for idx in range(len(self.images)):
            self.current_index=idx
            self.apply_watermark()

    # -----------------------------
    # Undo / Redo / Navigation
    # -----------------------------
    def undo(self):
        if len(self.history)>1:
            self.redo_stack.append(self.history.pop())
            self.images[self.current_index]=self.history[-1].copy()
            self.show_image(self.images[self.current_index])

    def redo(self):
        if self.redo_stack:
            img = self.redo_stack.pop()
            self.history.append(img.copy())
            self.images[self.current_index]=img
            self.show_image(img)

    def prev_image(self):
        if self.images:
            self.current_index=(self.current_index-1)%len(self.images)
            self.show_image(self.images[self.current_index])

    def next_image(self):
        if self.images:
            self.current_index=(self.current_index+1)%len(self.images)
            self.show_image(self.images[self.current_index])

    # -----------------------------
    # Show / Save Image
    # -----------------------------
    def show_image(self,img):
        self.current_image = img
        self.refresh_image(None)

    def refresh_image(self, event):
        if not hasattr(self, 'current_image') or self.current_image is None: return
        img = self.current_image
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width <1 or canvas_height<1:
            self.root.after(100, lambda:self.refresh_image(event))
            return
        img_ratio = img.width / img.height
        canvas_ratio = canvas_width / canvas_height
        if img_ratio > canvas_ratio:
            w = canvas_width
            h = int(w/img_ratio)
        else:
            h = canvas_height
            w = int(h*img_ratio)
        display_img = img.resize((w,h), Image.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(display_img)
        self.canvas.delete("all")
        self.canvas.create_image(canvas_width//2, canvas_height//2, image=self.tk_img, anchor="center")
        # Footer
        self.canvas.create_text(canvas_width-10, canvas_height-10, text="v1.0 by [Your Name]", fill="white", anchor="se", font=("Arial",10))

    def save_image(self):
        if not self.images:
            messagebox.showwarning("No Image", "Upload images first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG","*.png"),("JPEG","*.jpg")])
        if path:
            self.images[self.current_index].save(path)
            messagebox.showinfo("Saved", f"Image saved to {path}")

# -----------------------------
# Run App
# -----------------------------
if __name__=="__main__":
    root = tk.Tk()
    app = WatermarkApp(root)
    root.mainloop()