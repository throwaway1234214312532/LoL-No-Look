import aiohttp
import os
import logging
import psutil
import pystray
import threading
from PIL import Image
import tkinter as tk
import willump #if you want to import the class
import asyncio
import sys
import startup
import time
from PIL import Image, ImageDraw
os.chdir(sys._MEIPASS)
global exitflag, running, wllp, tray, status, startstatus
exitflag = False
running = True
icon = Image.open("Icon.png")
status = "Status = On"
if startup.is_running_at_startup("NoLooksies", True):
    startstatus = "Start on Windows startup = On"
else:
    startstatus = "Start on Windows startup = Off"
print (startup.is_running_at_startup("NoLooksies", True))

def stop_client():
    global running, tray
    client = None
    for p in psutil.process_iter(['pid', 'name']):
        if p.info['name'] == 'LeagueClient.exe':
            client = psutil.Process(p.info['pid'])
            print (client)
            break
    if client:
        client.terminate()
    time.sleep(2)
    tray.remove_notification()
    running = True


async def set_event_listener():
	#creates a subscription to the server event OnJsonApiEvent (which is all Json updates)
    all_events_subscription = await wllp.subscribe('OnJsonApiEvent',default_handler=default_message_handler)
	#let's add an endpoint filter, and print when we get messages from this endpoint with our printing listener
    wllp.subscription_filter_endpoint(all_events_subscription, '/lol-ranked/v1/current-lp-change-notification', handler=check_for_lp)
    #wllp.subscription_filter_endpoint(all_events_subscription, '/lol-summoner/v1/', handler=check_test)


async def wllp_start():
    global wllp
    wllp = await willump.start()
    await set_event_listener()

async def wllp_close():
    await wllp.close()

async def check_for_lp(data):
    print("data = ", data)
    print("data['data'] = ", data['data'])
    global wllp
    global lp_data, running
    if running and data['data'] != None:
        print(data['data']['queueType'])
        if data['data']['queueType'] == "RANKED_SOLO_5x5":
             # Load the image
            image = Image.open("Icon.png")
            # Define the coordinates and size of the black box 
            x1, y1 = 100, 100  # Top-left corner of the black box
            x2, y2 = 200, 200  # Bottom-right corner of the black box
            # Create a drawing context on the image
            draw = ImageDraw.Draw(image)
            # Fill the specified region with a black rectangle
            draw.rectangle([x1, y1, x2, y2], fill="black")
            # Save the modified image with the black box
            image.save("Icon_with_black_box.png")

async def check_test(data):

    global wllp
    global tray, queueType
    print (data)  
    if running:
        tray.notify("League Client Closed!", "NoLooksies")
        print("got there")
        stop_client()
#Toggles functionality by inverting the Running value

def toggle_program(tray, loop):
    global running, wllp, status
    print("toggled running to", not running)
    if running:
        tray.remove_notification()
        tray.notify("Functionality turned Off!", "Toggle")
        status = "Status = Off"
        tray.update_menu()
        running = False
        try:
            coroutine = wllp.close()
            loop.call_soon_threadsafe(asyncio.run_coroutine_threadsafe,coroutine, loop)
        except NameError as e:
            print(e)
    else:
        tray.remove_notification()
        tray.notify("Functionality turned back On!", "Toggle")
        status = "Status = On"
        tray.update_menu()
        running = True
        coroutine = wllp_start()
        loop.call_soon_threadsafe(asyncio.run_coroutine_threadsafe,coroutine, loop)    

#Quits program        
def quit(tray, loop):
    global running, wllp, exitflag
    running = False
    try:
        loop.call_soon_threadsafe(asyncio.run_coroutine_threadsafe,wllp.close(), loop)
    except NameError:
        os._exit(1)
    tray.stop()
    exitflag = True
    os._exit(1)

def status_func():
    global status
    return status

def add_to_tray(loop):
    global tray, status
    tray = pystray.Icon("Game Monitor", icon)
    tray.menu = pystray.Menu(pystray.MenuItem(lambda text: status, status_func,enabled=False),pystray.MenuItem('Toggle Program', lambda : toggle_program(tray, loop)),pystray.MenuItem(lambda text: startstatus, on_start),pystray.MenuItem('Quit', lambda : quit(tray,loop)))
    tray.run()

async def default_message_handler(data):
    pass


def on_start():
    global startstatus, tray
    if not startup.is_running_at_startup("NoLooksies", True):
        startup.run_at_startup_set("NoLooksies",user=True)
        startstatus = "Start on Windows startup = On"
        tray.notify("NoLooksies now starting on windows startup!", "NoLooksies")
        
        pass
    else:
        startup.run_at_startup_remove("NoLooksies",True)
        startstatus = "Start on Windows startup = Off"
        tray.notify("NoLooksies no longer starting on windows startup!", "NoLooksies")
    tray.update_menu()

async def main():
    global wllp    
    loop = asyncio.get_running_loop()
    
    tray_thread = threading.Thread(target=add_to_tray, args=(loop,))
    tray_thread.start()
    wllp = await willump.start()
        
    await set_event_listener()
    
    while not exitflag:
        print("waiting")
        if running:
            try:
                response = await wllp.request('get','/riotclient/app-name')
                pass
            except (aiohttp.client_exceptions.ClientConnectorError, aiohttp.client_exceptions.ClientOSError):
                await wllp_close()
                print("wllp has closed")
                await wllp_start()
            except RuntimeError:
                pass
            print("waiting")
        await asyncio.sleep(8)

if __name__ == '__main__':
	# uncomment this line if you want to see willump complain (debug log)
    logging.getLogger().setLevel(level=logging.DEBUG)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        asyncio.run(wllp.close())
        os._exit(1)        