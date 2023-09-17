import tkinter as tk
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

def twitch_start_script():
    global script_process2
    print('Starting Twitch Bot')
    script_process2 = subprocess.Popen(["python", "TwitchBot.py"])

# Function to stop the Python script
def twitch_stop_script():
    global script_process2
    if script_process2:
        print('Stopping Twitch Bot')
        script_process2.terminate()
        script_process2 = None

# Create the main window
window = tk.Tk()
window.title("Discord Py")

# Create "Start" button
start_button = tk.Button(window, text="Discord Start", command=discord_start_script)
start_button.pack()

# Create "Stop" button
stop_button = tk.Button(window, text="Discord Stop", command=discord_stop_script)
stop_button.pack()

# Create "Start" button
start_button = tk.Button(window, text="Twitch Start", command=twitch_start_script)
start_button.pack()

# Create "Stop" button
stop_button = tk.Button(window, text="Twitch Stop", command=twitch_stop_script)
stop_button.pack()

# Initialize script_process as None
script_process = None
script_process2  = None

# Run the GUI
window.mainloop()
