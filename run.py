import json
import requests
from io import BytesIO
import tkinter as tk
from PIL import Image, ImageTk
import subprocess
import os
import time


with open('config.json') as f:
    config = json.load(f)

import tkinter as tk
from PIL import Image, ImageTk
import time

class Debouncer:
    def __init__(self, wait):
        self.wait = wait
        self.last_call = time.time()

    def should_proceed(self):
        now = time.time()
        if now - self.last_call > self.wait:
            self.last_call = now
            return True
        return False

def resize_logo(event):
    if not debouncer.should_proceed():
        return

    width_ratio = event.width / logo_image.width
    height_ratio = event.height / logo_image.height
    new_ratio = min(width_ratio, height_ratio)
    new_width = int(logo_image.width * new_ratio)
    new_height = int(logo_image.height * new_ratio)
    resized_image = logo_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    logo_label.logo_photo = ImageTk.PhotoImage(resized_image)
    logo_label.config(image=logo_label.logo_photo)

debouncer = Debouncer(0.1) 

def discord_start_script():
    global script_process
    print('Starting Discord Bot')
    script_process = subprocess.Popen([os.sys.executable, os.path.join(os.path.dirname(os.path.realpath(__file__)), "main.py")])

def discord_stop_script():
    global script_process
    if script_process:
        print('Stopping Discord Bot')
        script_process.terminate()
        script_process = None

window = tk.Tk()
window.title("GHM Discord Bot")
window.geometry("300x200")
window.configure(bg="#222222")
response = requests.get(config['logo_url'])
logo_image = Image.open(BytesIO(response.content))

global logo_photo
logo_photo = ImageTk.PhotoImage(logo_image)

logo_label = tk.Label(window, image=logo_photo, bg="#222222")
logo_label.image = logo_photo
logo_label.place(relx=0.5, rely=0.3, anchor='center')

## NEED TO FIGURE OUT HOW TO MAKE THE IMAGE RESIZE PROPERLY WITH OUT SPAMMING THE CONSOLE
## `Vnew_photo = ImageTk.PhotoImage(width=width, height=height)` SEEMS WITH OUT THIS THE LOGO WONT SHOW
# def resize_logo(event):
#     global logo_photo, logo_image
#     width = event.width // 3
#     height = event.height // 3
#     new_photo = ImageTk.PhotoImage(width=width, height=height)
#     resized_image = logo_image.resize((width, height), Image.Resampling.LANCZOS)
#     new_photo.paste(resized_image)
#     logo_photo = new_photo
#     logo_label.config(image=logo_photo)

# def resize_logo(event):
#     global logo_photo, logo_image
#     width = event.width // 3
#     height = event.height // 3
#     resized_image = logo_image.resize((width, height), Image.Resampling.LANCZOS)
#     new_photo = ImageTk.PhotoImage(resized_image)
#     logo_photo = new_photo
#     logo_label.config(image=logo_photo)


window.bind('<Configure>', resize_logo)

custom_font = ("Helvetica", 14)
start_button = tk.Button(window, text="Discord Start", command=discord_start_script, bg="#7289DA", fg="white", font=custom_font)
start_button.place(relx=0.25, rely=0.7, anchor='center', width=120, height=30)

stop_button = tk.Button(window, text="Discord Stop", command=discord_stop_script, bg="#7289DA", fg="white", font=custom_font)
stop_button.place(relx=0.75, rely=0.7, anchor='center', width=120, height=30)

script_process = None

window.mainloop()