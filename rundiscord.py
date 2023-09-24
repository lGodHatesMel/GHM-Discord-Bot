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

# Create the main window
window = tk.Tk()
window.title("GHM Discord Bot")

# Create "Start" button
start_button = tk.Button(window, text="Discord Start", command=discord_start_script)
start_button.pack()

# Create "Stop" button
stop_button = tk.Button(window, text="Discord Stop", command=discord_stop_script)
stop_button.pack()

# Initialize script_process as None
script_process = None

# Run the GUI
window.mainloop()
