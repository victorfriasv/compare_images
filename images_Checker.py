import ctypes
import subprocess
from customtkinter import CTk, CTkFrame, CTkButton
from tkinter import filedialog, messagebox, Label, Text, font as tkFont
from PIL import Image, ImageChops, ImageStat, ImageTk
import tempfile
import os
import webbrowser
import sys
from tkinterdnd2 import DND_FILES, TkinterDnD

def hide_console():
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    ctypes.windll.user32.ShowWindow(hwnd, 0)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class CompareImagesApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Images Checker")
        self.master.geometry("1000x600")
        self.master.configure(bg="#2E2E2E")

        icon_path = resource_path('logo.ico')
        try:
            icon_image = Image.open(icon_path)
            icon_image = icon_image.resize((32, 32))
            self.master.iconphoto(False, ImageTk.PhotoImage(icon_image))
            self.master.iconbitmap(icon_path)
        except Exception as e:
            print(f"Error al cargar el ícono: {e}")

        self.sidebar_frame = CTkFrame(self.master, width=160, fg_color="#2E2E2E")
        self.sidebar_frame.grid(row=0, column=0, sticky="ns", padx=10, pady=10)

        self.content_frame = CTkFrame(self.master, fg_color="#2E2E2E")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        logo_path = resource_path('logo.png')
        self.logo_img = Image.open(logo_path)
        self.logo_img = self.logo_img.resize((160, int(self.logo_img.height * 160 / self.logo_img.width)), Image.LANCZOS)
        self.logo_tk = ImageTk.PhotoImage(self.logo_img)
        self.logo_label = Label(self.sidebar_frame, image=self.logo_tk, bg="#2E2E2E")
        self.logo_label.grid(row=0, column=0, pady=10, padx=5, sticky="ew")

        self.select_button = CTkButton(self.sidebar_frame, text="Select Images", command=self.select_images_compare)
        self.select_button.grid(row=1, column=0, pady=5, padx=5, sticky="ew")

        self.result_text = Text(self.sidebar_frame, height=15, width=25, bg="#2E2E2E", fg="white", 
                                insertbackground="white", highlightthickness=0, bd=0)
        self.result_text.config(font=tkFont.Font(family="Helvetica", size=14, weight="bold"))
        self.result_text.grid(row=2, column=0, pady=10, padx=5, sticky="nsew")

        self.result_text.tag_configure("green", foreground="green")
        self.result_text.tag_configure("red", foreground="red")
        self.result_text.tag_configure("neutral", foreground="white")

        self.master.drop_target_register(DND_FILES)
        self.master.dnd_bind('<<Drop>>', self.on_drop)

        self.image1_path = None
        self.image2_path = None
        self.temp_path = None

        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(1, weight=1)
        self.sidebar_frame.grid_rowconfigure(2, weight=1)

        self.comparison_section = CTkFrame(self.content_frame, fg_color="#2E2E2E")
        self.comparison_section.pack(fill="x", pady=10)

        self.image1_label = Label(self.comparison_section, fg="#FFFFFF", bg="#2E2E2E", anchor="w", wraplength=800)
        self.image1_label.pack(side="left", padx=5, fill="x", expand=True)

        self.vs_label = Label(self.comparison_section, text="VS", fg="#FFFFFF", bg="#2E2E2E", font=("Arial", 16, "bold"))
        self.vs_label.pack(side="left", padx=10)

        self.image2_label = Label(self.comparison_section, fg="#FFFFFF", bg="#2E2E2E", anchor="e", wraplength=800)
        self.image2_label.pack(side="left", padx=5, fill="x", expand=True)

        self.image_label = Label(self.content_frame, bg="#2E2E2E")
        self.image_label.pack(fill="both", expand=True)

        self.open_image_button = CTkButton(self.sidebar_frame, text="Open Result Image", command=self.open_result_image)
        self.open_image_button.grid(row=3, column=0, pady=5, padx=5, sticky="ew")

        self.image_x = 0
        self.image_y = 0
        self.zoom_factor = 1.0

        self.content_frame.bind("<Configure>", self.resize_image_to_fit)
        self.image_label.bind("<ButtonPress-1>", self.start_drag)
        self.image_label.bind("<B1-Motion>", self.drag_image)
        self.image_label.bind("<MouseWheel>", self.zoom_image)

    def on_drop(self, event):
        file_paths = event.data.splitlines()

        for file_path in file_paths:
            file_path = file_path.strip(' {}')
            if not file_path:
                continue

            self.clear_previous_results()
            if self.image1_path is None:
                self.image1_path = file_path
                self.result_text.insert("end", f"Selected: {os.path.basename(self.image1_path)}\n")
            elif self.image2_path is None:
                self.image2_path = file_path
                self.result_text.insert("end", f"Selected: {os.path.basename(self.image2_path)}\n")
                self.compare_images()
            else:
                self.result_text.insert("end", "Resetting selections. Start again.\n")
                self.reset_images()
                self.on_drop(event)

    def clear_previous_results(self):
        self.result_text.delete("1.0", "end")
        if self.temp_path and os.path.exists(self.temp_path):
            os.remove(self.temp_path)
            self.temp_path = None
        self.image_label.config(image='')

    def reset_images(self):
        self.image1_path = None
        self.image2_path = None

    def select_images_compare(self):
        self.clear_previous_results()
        file_paths = filedialog.askopenfilenames(title="Select images to compare",
                                                 filetypes=[("All image files", "*.psd *.jpg *.jpeg *.png *.bmp *.tiff")])

        if len(file_paths) == 1:
            self.image1_path = file_paths[0]
            self.result_text.insert("end", f"Selected: {os.path.basename(self.image1_path)}\n")
            self.select_second_image()
        elif len(file_paths) == 2:
            self.image1_path, self.image2_path = file_paths
            self.result_text.insert("end", f"Selected: {os.path.basename(self.image1_path)} and {os.path.basename(self.image2_path)}\n")
            self.compare_images()
        else:
            messagebox.showerror("Error", "You must select one or two images.")
            return

    def select_second_image(self):
        file_path = filedialog.askopenfilename(title="Select the second image to compare",
                                               filetypes=[("All image files", "*.psd *.jpg *.jpeg *.png *.bmp *.tiff")])
        if file_path:
            self.image2_path = file_path
            self.result_text.insert("end", f"Selected: {os.path.basename(self.image2_path)}\n")
            self.compare_images()
        else:
            self.result_text.insert("end", "No second image was selected.\n")

    def compare_images(self):
        self.result_text.delete("1.0", "end")

        if self.image1_path and self.image2_path:
            image1 = Image.open(self.image1_path).convert('RGB')
            image2 = Image.open(self.image2_path).convert('RGB')

            image1_name = os.path.splitext(os.path.basename(self.image1_path))[0]
            image2_name = os.path.splitext(os.path.basename(self.image2_path))[0]

            if image1_name == image2_name:
                self.result_text.insert("end", "Names: OK\n", "green")
            else:
                self.result_text.insert("end", "Names: FAIL\n", "red")

            # Verificación de dimensiones y ajuste
            if image1.size != image2.size:
                self.result_text.insert("end", "Dimensions: FAIL\n", "red")
                # Redimensionar la imagen más pequeña para realizar la comparación
                max_width = max(image1.width, image2.width)
                max_height = max(image1.height, image2.height)
                image1 = image1.resize((max_width, max_height))
                image2 = image2.resize((max_width, max_height))
            else:
                self.result_text.insert("end", "Dimensions: OK\n", "green")

            rms_value = self.calculate_rms(image1, image2)
            self.result_text.insert("end", f"RMS: {rms_value:.2f}\n", "neutral")

            diff_image = ImageChops.difference(image1, image2).convert("RGB")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                diff_image.save(temp_file)
                self.temp_path = temp_file.name

            self.update_display_image()
            self.image1_label.config(text=os.path.basename(self.image1_path))
            self.image2_label.config(text=os.path.basename(self.image2_path))

    def calculate_rms(self, img1, img2):
        diff = ImageChops.difference(img1, img2)
        stat = ImageStat.Stat(diff)
        return (sum([x**2 for x in stat.mean]) / len(stat.mean)) ** 0.5

    def update_display_image(self):
        if self.temp_path:
            img = Image.open(self.temp_path)
            img_ratio = img.width / img.height
            frame_width = self.content_frame.winfo_width()
            frame_height = self.content_frame.winfo_height()

            if frame_width / frame_height > img_ratio:
                new_width = int(frame_height * img_ratio)
                new_height = frame_height
            else:
                new_width = frame_width
                new_height = int(frame_width / img_ratio)

            img = img.resize((new_width, new_height), Image.LANCZOS)
            self.img_tk = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.img_tk)
            self.image_label.image = self.img_tk

    def resize_image_to_fit(self, event=None):
        if self.temp_path:
            self.update_display_image()

    def open_result_image(self):
        if self.temp_path:
            webbrowser.open(self.temp_path)
        else:
            messagebox.showerror("Error", "No result image available.")

    def start_drag(self, event):
        self.image_x = event.x
        self.image_y = event.y

    def drag_image(self, event):
        dx = event.x - self.image_x
        dy = event.y - self.image_y
        self.image_label.place(x=self.image_label.winfo_x() + dx, y=self.image_label.winfo_y() + dy)
        self.image_x = event.x
        self.image_y = event.y

    def zoom_image(self, event):
        if event.delta > 0:
            self.zoom_factor *= 1.1
        else:
            self.zoom_factor /= 1.1
        self.update_display_image()

if __name__ == "__main__":
    hide_console()
    root = TkinterDnD.Tk()
    app = CompareImagesApp(root)
    root.mainloop()
