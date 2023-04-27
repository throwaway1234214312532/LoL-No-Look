import requests
import time
import psutil
import pystray
import threading
from PIL import Image
import tkinter as tk
import tkinter.simpledialog

REGION = None
REGION_ID = None



def input_to_region(region_input):
    global REGION, REGION_ID
    if region_input == "euw":
        REGION = "europe"
        REGION_ID = "EUW1"
    elif region_input == "na":
        REGION = "americas"
        REGION_ID = "NA1"
    elif region_input == "oce":
        REGION = "Oceania"
        REGION_ID = "OCE1"
    elif region_input == "eune":
        REGION = "EUROPE"
        REGION_ID = "EUN1" 


def read_summoner_info():
    with open('summoner_info.txt', 'r') as f:
        summoner_name, region = f.read().splitlines()
        input_to_region(region)
    return summoner_name

SUMMONER_NAME = read_summoner_info()


# The base URL for my API
BASE_URL = "https://woedwoef.pythonanywhere.com/"

def get_summoner_id():
    return requests.get(f"{BASE_URL}summonerId/{SUMMONER_NAME}/{REGION_ID}").json()["id"]

def get_active_game():
    return requests.get(f"{BASE_URL}currentMatch/{SUMMONER_ID}/{REGION_ID}")

def get_finished_game(matchId):
    return requests.get(f"{BASE_URL}Match/{matchId}/{REGION}")
  
# Default name to get id from

# The ID of the summoner you want to track
SUMMONER_ID = get_summoner_id()
print (SUMMONER_ID)

def set_summoner_id():
    global SUMMONER_ID
    SUMMONER_ID = get_summoner_id()

# Icon used for the tray icon
icon = Image.open("icon.png")

# Initial value for running
running = True

#function to stop client
def stop_client():
    client = None
    for p in psutil.process_iter(['pid', 'name']):
        if p.info['name'] == 'LeagueClient.exe':
            client = psutil.Process(p.info['pid'])
            print (client)
            break
    if client:
        client.terminate()


def write_to_file(x,input):
    with open("summoner_info.txt", "r") as f:
        lines = f.readlines()
    lines[x] = input + "\n"
    with open("summoner_info.txt", "w") as f:
        f.writelines(lines)

def monitor_league(quit_event, restart_event):
    while True:
        while running:
            print(threading.current_thread().name)
            # Make the API request to get the summoner's current game information
            response = get_active_game()
            print ("Is player in game? ",response)
            print ("Summoner name = ", SUMMONER_NAME)
            
            # Check if the summoner is currently in a game
            if response.status_code == 200:
                game_info = response.json()
                print(game_info)
                game_mode = game_info["gameMode"]
                match_id = "{}_{}".format(REGION_ID,game_info["gameId"])
                
                print (match_id)
                print("Summoner in game")
                # Check if the game mode is Classic and the game has ended
                if game_info["gameQueueConfigId"] == 420:
                    while running:
                        print("checking if game is ongoing")
                        response = get_finished_game(match_id)
                        print(response.status_code)
                        if response.status_code == 200:
                            stop_client()
                            print("Terminated client because game ended")
                            break
                        else:
                            time.sleep(1)   
                        

                # Wait 10 seconds before checking again
                quit_event.wait(timeout=20)
        
            # If the summoner is not in a game, wait 10 seconds before checking again
            else:
                print("Summoner not in game")

                quit_event.wait(timeout=20)
        if quit_event.is_set():
            break

# Turns user input to usable region values
   

#Restarts the functionality by setting the running value to false and waiting 2 seconds before setting it to true.
def restart():
    global running
    if running:
        running = False
        restart_event.set()
        time.sleep(2)
        running = True
        restart_event.clear()

#Toggles functionality by inverting the Running value
def toggle_program():
    global running
    if running:
        running = False
    else:
        running = True

#Quits program        
def quit(tray):
    global running
    running = False
    quit_event.set()
    tray.stop()

#Gets userinput for their region
def set_region():
    root = tk.Tk()
    root.withdraw()
    # create a simple dialog box to get the summoner name from the user
    region_input = tkinter.simpledialog.askstring("REGION", "Enter your region (euw,na,eune,oce,etc...):")
    input_to_region(region_input)
    write_to_file(1,region_input)    
    set_summoner_id()
    restart()
    


#Gets userinput for their summonername
def set_summoner():
    global SUMMONER_NAME, running, SUMMONER_ID
    root = tk.Tk()
    root.withdraw()
    # create a simple dialog box to get the summoner name from the user
    SUMMONER_NAME = tkinter.simpledialog.askstring("Summoner Name", "Enter your summoner name:")
    write_to_file(0,SUMMONER_NAME) 
    set_summoner_id()
    restart()


#Function to add the system tray icon
def add_to_tray():
    tray = pystray.Icon("Game Monitor", icon)
    tray.menu = pystray.Menu(pystray.MenuItem('Set Region', set_region), pystray.MenuItem('Set Summoner', set_summoner),pystray.MenuItem('Toggle Program', toggle_program),pystray.MenuItem('Quit', lambda : quit(tray)))
    tray.run()



if __name__ == "__main__":
    quit_event = threading.Event()
    restart_event = threading.Event()
    tray_thread = threading.Thread(target=add_to_tray)
    program_thread = threading.Thread(target=monitor_league, args=(quit_event,restart_event,))
    program_thread.start()
    tray_thread.start()
    