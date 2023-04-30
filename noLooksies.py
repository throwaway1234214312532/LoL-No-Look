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

global exitflag
exitflag = False
running = True
condition = threading.Condition()
icon = Image.open("icon.png")
global wllp
global queuetype
global lp_data

def stop_client():
    client = None
    for p in psutil.process_iter(['pid', 'name']):
        if p.info['name'] == 'LeagueClient.exe':
            client = psutil.Process(p.info['pid'])
            print (client)
            break
    if client:
        client.terminate()


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
    global queueType
    global wllp
    global lp_data
    if running and data['data'] != None:
        print(data['data']['queueType'])
        if data['data']['queueType'] == "RANKED_SOLO_5x5":
            
            stop_client()

async def check_test(data):
    global queueType
    global wllp
    global lp_data
    print (data)
    queueType = data['data']['regalia']
    print (queueType[1],type(queueType))
    lp_data = data
    print(queueType == 2)
    
    if running:
        print("got there")
        stop_client()
#Toggles functionality by inverting the Running value

def toggle_program(loop):
    global running, wllp
    print("toggled running to", not running)
    if running:
        print("Turn off")
        running = False
        coroutine = wllp.close()
        loop.call_soon_threadsafe(asyncio.run_coroutine_threadsafe,coroutine, loop)
        print(wllp)
    else:
        print("back on!")
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
        os._exit()
    tray.stop()
    loop.stop()
    exitflag = True
    os._exit()

def add_to_tray(loop):
    tray = pystray.Icon("Game Monitor", icon)
    tray.menu = pystray.Menu(pystray.MenuItem('Toggle Program', lambda : toggle_program(loop)),pystray.MenuItem('Quit', lambda : quit(tray,loop)))
    tray.run()

async def default_message_handler(data):
    pass

async def main():
    global wllp    
    print(" hello")
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
            except aiohttp.client_exceptions.ClientConnectorError:
                await wllp_close()
                print("wllp has closed")
                await wllp_start()
            print("waiting")
        await asyncio.sleep(8)

if __name__ == '__main__':
	# uncomment this line if you want to see willump complain (debug log)
    logging.getLogger().setLevel(level=logging.DEBUG)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        asyncio.run(wllp.close())
        os._exit()        
