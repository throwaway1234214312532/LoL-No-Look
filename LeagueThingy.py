import psutil
import threading
import os
from PIL import Image
import pystray
import tkinter as tk
from tkinter import messagebox
from threading import Thread

def on_clicked(icon, item):
    if item.text == "Start":
        start_checking()
    elif item.text == "Stop":
        stop_checking()
    elif item.text == "Exit":
        os._exit(1)
        icon.stop()
        root.destroy()
        quit()
        
    elif item.text == "Bring to Foreground":
        root.deiconify()
        root.lift()
        

def create_menu():
    menu_items = [
        pystray.MenuItem("Start", on_clicked),
        pystray.MenuItem("Stop", on_clicked),
        pystray.MenuItem("Exit", on_clicked),
        pystray.MenuItem("Bring to Foreground", on_clicked),
    ]
    return pystray.Menu(*menu_items)
image = Image.open("icon.png")
def create_tray_icon():
    menu = create_menu()
    
    return pystray.Icon("Game Monitor", image, "Game Monitor", menu)

def find_process(name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.name() == name:
            return proc
    return None

def stop_client():
    client = None
    for p in psutil.process_iter(['pid', 'name']):
        if p.info['name'] == 'LeagueClient.exe':
            client = psutil.Process(p.info['pid'])
            print (client)
            break
    if client:
        client.terminate()

print ()
def check_game():
    global stop_flag 
    stop_flag = False
    while not stop_flag:
        
        game_proc = find_process("League of Legends.exe")
        
        if not game_proc is None:
            game = psutil.Process(game_proc.pid)   
            while True:
                if not game.is_running():
                    stop_client()
                    break
                else:
                    continue

        else:
            continue


def start_checking():
    global monitor_thread, start_button, stop_button, my_label
    my_label.config(text="Checking for the end of Games now")
    monitor_thread = Thread(target=check_game)
    monitor_thread.start()
    start_button.config(state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL)

    


def stop_checking():
    global monitor_thread, start_button, stop_button, stop_flag, my_label
    my_label.config(text="No longer checking for the end of Games")
    stop_flag = True
    if monitor_thread is not None and monitor_thread.is_alive():
        monitor_thread.join()
    monitor_thread = None
    start_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)

def tray_thread():
    icon = create_tray_icon()
    icon.run()

monitor_thread = None
root = tk.Tk()
root.title("Game Monitor")

start_button = tk.Button(root, text="Start Monitoring",default=tk.DISABLED, command=start_checking)
start_button.pack(pady=10)

my_label = tk.Label(root, text="Hello, world!")
my_label.pack()
my_label.config(text="Starting", width=40,height=2)

stop_button = tk.Button(root, text="Stop Monitoring", command=stop_checking, state=tk.DISABLED)
stop_button.pack(pady=10)

tray_thread = threading.Thread(target=tray_thread)
tray_thread.start()
monitoring_thread = Thread(target=start_checking)
monitoring_thread.start()
root.withdraw()


root.mainloop()
tray_thread.join()
