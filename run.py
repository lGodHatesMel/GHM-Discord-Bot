import tkinter as tk
from PIL import Image, ImageTk
import subprocess

# Function to start the Python script
def discord_start_script():
    global script_process
    print('Starting Discord Bot')
    script_process = subprocess.Popen(["python", "main.py"])

# Function to stop the Python script
def discord_stop_script():
    global script_process
    if script_process:
        print('Stopping Discord Bot')
        script_process.terminate()
        script_process = None

# Create the main window
window = tk.Tk()
window.title("GHM Discord Bot")

# Set initial size of the window
window.geometry("100x100")  # You can adjust the width and height as needed

# Configure background color
window.configure(bg="#FF0000")

# # Add a logo/image
logo_image = Image.open(r"C:\GHM-Discord-Bot\images\Logo.png")  # Use the 'r' prefix to treat the string as a raw string
#logo_photo = ImageTk.PhotoImage(logo_image)
#logo_label = tk.Label(window, image=logo_photo, bg="#FF0000")  # Adjust bg color to match the window
#logo_label.pack()

# Create "Start" button
start_button = tk.Button(window, text="Discord Start", command=discord_start_script, bg="#7289DA", fg="white")
start_button.pack()

# Create "Stop" button
stop_button = tk.Button(window, text="Discord Stop", command=discord_stop_script, bg="#7289DA", fg="white")
stop_button.pack()

# Initialize script_process as None
script_process = None

# Run the GUI
window.mainloop()