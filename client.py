import base64
import io
import os
from socket import socket, AF_INET, SOCK_STREAM
from customtkinter import *
import threading
from tkinter import filedialog
from PIL import Image



class MainWindow(CTk):
    def __init__(self):
        super().__init__()
        self.geometry("400x300")
        self.label = None
        self.username = None
        self.avatar_img = None
        self.avatar_file = None
        self.title("Logitalk")
        self.menu_frame = CTkFrame(self, width=30, height=300)
        self.menu_frame.pack_propagate(False)
        self.menu_frame.place(x=0, y=0)
        self.is_show_menu = False
        self.speed_animate_menu = -5
        self.btn = CTkButton(self, text="⚙", command=self.toggle_show_menu, width=30)
        self.btn.place(x=0, y=0)
        # main
        self.chat_field = CTkScrollableFrame(self)
        self.chat_field.place(x=0, y=0)
        self.message_entry = CTkEntry(
            self, placeholder_text="Введіть повідомлення:", height=40
        )
        self.message_entry.place(x=0, y=0)
        self.send_button = CTkButton(self, text="📤", width=50, height=40, command=self.send_message)
        self.send_button.place(x=0, y=0)
        self.open_img_button = CTkButton(self, text="💾", width=50, height=40, command=self.open_image)
        self.open_img_button.place(x=0, y=0)
        self.adaptive_ui()
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect(("localhost", 8080))
            hello = f"TEXT@{self.username}@[SYSTEM] {self.username} приєднався до чату!\n"
            self.sock.send(hello.encode('utf-8'))

            # отправляем аватарку, если она есть
            if self.avatar_file:
                with open(self.avatar_file, "rb") as f:
                    raw = f.read()
                b64_data = base64.b64encode(raw).decode()
                data = f"AVATAR@{self.username}@{b64_data}\n"
                self.sock.send(data.encode('utf-8'))

            threading.Thread(target=self.recv_message, daemon=True).start()
        except Exception as e:
            self.add_message(f"помилка: {e}")

    def add_message(self, message, img=None):
        message_frame = CTkFrame(self.chat_field, fg_color="grey")
        message_frame.pack(pady=5, anchor="w", fill="x")
        wrapleng_size = self.winfo_width() - self.menu_frame.winfo_width() - 80

        inner_frame = CTkFrame(message_frame, fg_color="transparent")
        inner_frame.pack(padx=5, pady=5, anchor="w", fill="x")

        # если это наше сообщение и есть аватарка
        if self.avatar_img and message.startswith(f"{self.username}:"):
            CTkLabel(inner_frame, image=self.avatar_img, text="", width=40).pack(side="left", padx=5)

        text_label = CTkLabel(
            inner_frame,
            text=message,
            wraplength=wrapleng_size,
            text_color="white",
            justify="left",
        )
        text_label.pack(side="left", padx=5)

        if img:
            CTkLabel(inner_frame, text="", image=img, compound="top").pack(padx=10, pady=5)

    def send_message(self):
        message = self.message_entry.get()
        if message:
            self.add_message(f"{self.username}: {message}")
            data = f"TEXT@{self.username}@{message}\n"
            try:
                self.sock.sendall(data.encode())
            except:
                pass
        self.message_entry.delete(0, END)

    def recv_message(self):
        buffer = ""
        while True:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk.decode(errors='ignore')

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.handle_line(line.strip())
            except:
                break
        self.sock.close()

    def handle_line(self, line):
        if not line:
            return
        parts = line.split("@", 3)
        msg_type = parts[0]
        if msg_type == "TEXT":
            author = parts[1]
            message = parts[2]
            self.add_message(f"{author}: {message}")
        elif msg_type == "IMAGE":
            author = parts[1]
            filename = parts[2]
            b64_img = parts[3]
            try:
                img_data = base64.b64decode(b64_img)
                pil_img = Image.open(io.BytesIO(img_data))
                ctk_img = CTkImage(pil_img, size=(300, 300))
                self.add_message(f"{author}, надіслав зображення: {filename}", img=ctk_img)
            except:
                self.add_message(f"Помилка відображення картинки")
        elif msg_type == "AVATAR":
            author = parts[1]
            b64_img = parts[2]
            try:
                img_data = base64.b64decode(b64_img)
                pil_img = Image.open(io.BytesIO(img_data))
                pil_img.thumbnail((40, 40))
                self.add_avatar(author, pil_img)
            except:
                self.add_message(f"Помилка завантаження аватарки від {author}")

    def add_avatar(self, username, pil_img):
        if not hasattr(self, "avatars"):
            self.avatars = {}
        self.avatars[username] = CTkImage(pil_img, size=(40, 40))

    def open_image(self):
        file_name = filedialog.askopenfilename()
        if not file_name:
            return

        with open(file_name, "rb") as f:
            raw = f.read()
        b64_data = base64.b64encode(raw).decode()
        short_name = os.path.basename(file_name)
        data = f"IMAGE@{self.username}@{short_name}@{b64_data}\n"

        self.sock.sendall(data.encode())

        self.add_message('', CTkImage(light_image=Image.open(file_name), size=(300, 300)))

    def toggle_show_menu(self):
        if self.is_show_menu:
            self.is_show_menu = False
            self.speed_animate_menu *= -1
            self.btn.configure(text="⚙")
            self.show_menu()
        else:
            self.is_show_menu = True
            self.speed_animate_menu *= -1
            self.btn.configure(text="⚙")
            self.show_menu()
            self.label = CTkLabel(self.menu_frame, text="Імʼя")
            self.label.pack(pady=30)
            self.entry = CTkEntry(self.menu_frame, placeholder_text="Ваш нік...")
            self.entry.pack()
            self.save_name_button = CTkButton(self.menu_frame, text="Зберегти", command=self.save_name)
            self.save_name_button.pack()
            self.avatar_button = CTkButton(self.menu_frame, text="Завантажити аватарку", command=self.load_avatar)
            self.avatar_button.pack(pady=10)
            self.toggle_theme_button = CTkButton(self.menu_frame, text="Перемкнути тему", command=self.toggle_theme)
            self.toggle_theme_button.pack(pady=10)

    def load_avatar(self):
        file_name = filedialog.askopenfilename(
            filetypes=[("Зображення", "*.png;*.jpg;*.jpeg;*.gif")]
        )
        if not file_name:
            return
        try:
            pil_img = Image.open(file_name)
            pil_img.thumbnail((40, 40))
            self.avatar_img = CTkImage(pil_img, size=(40, 40))
            self.avatar_file = file_name
            self.add_message("Аватарка успішно завантажена!")
        except Exception as e:
            self.add_message(f"Помилка завантаження аватарки: {e}")

    def save_name(self):
        new_name = self.entry.get().strip()
        if new_name:
            self.username = new_name
            self.add_message(f"Ваш новий нік: {self.username}")

    def show_menu(self):
        self.menu_frame.configure(
            width=self.menu_frame.winfo_width() + self.speed_animate_menu
        )
        if not self.menu_frame.winfo_width() >= 200 and self.is_show_menu:
            self.after(10, self.show_menu)
        elif self.menu_frame.winfo_width() >= 40 and not self.is_show_menu:
            self.after(10, self.show_menu)
            if self.label and self.entry:
                self.label.destroy()
                self.entry.destroy()
                self.save_name_button.destroy()
                self.avatar_button.destroy()
                self.toggle_theme_button.destroy()

    def toggle_theme(self):
        current_mode = get_appearance_mode()
        if current_mode == "Dark":
            set_appearance_mode("light")
        else:
            set_appearance_mode("Dark")

    def adaptive_ui(self):
        self.menu_frame.configure(height=self.winfo_height())
        self.chat_field.place(x=self.menu_frame.winfo_width())
        self.chat_field.configure(
            width=self.winfo_width() - self.menu_frame.winfo_width() - 20,
            height=self.winfo_height() - 40,
        )
        self.send_button.place(x=self.winfo_width() - 50, y=self.winfo_height() - 40)
        self.message_entry.place(
            x=self.menu_frame.winfo_width() - 5, y=self.send_button.winfo_y()
        )
        self.message_entry.configure(
            width=self.winfo_width() - 105
        )
        self.open_img_button.place(x=self.winfo_width() - 105, y=self.send_button.winfo_y())
        self.after(50, self.adaptive_ui)


if __name__ == "__main__":
    win = MainWindow()
    win.mainloop()
