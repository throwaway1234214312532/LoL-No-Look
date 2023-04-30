from win32api import (GetModuleFileName, RegCloseKey, RegDeleteValue,
                    RegOpenKeyEx, RegSetValueEx, RegEnumValue)
from win32con import (HKEY_LOCAL_MACHINE, HKEY_CURRENT_USER, KEY_WRITE,
                    KEY_QUERY_VALUE, REG_SZ)
from winerror import ERROR_NO_MORE_ITEMS
import pywintypes


# The registry path where the applications that must run at startup
# are stored.
STARTUP_KEY_PATH = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"


def run_at_startup_set(appname, path=None, user=False):
    """
    Store the entry in the registry for running the application
    at startup.
    """
    # Open the registry key where applications that run
    # at startup are stored.
    key = RegOpenKeyEx(
        HKEY_CURRENT_USER if user else HKEY_LOCAL_MACHINE,
        STARTUP_KEY_PATH,
        0,
        KEY_WRITE | KEY_QUERY_VALUE
    )
    # Make sure our application is not already in the registry.
    i = 0
    while True:
        try:
            name, _, _ = RegEnumValue(key, i)
        except pywintypes.error as e:
            if e.winerror == ERROR_NO_MORE_ITEMS:
                break
            else:
                raise
        if name == appname:
            RegCloseKey(key)
            return
        i += 1
    # Create a new entry or key.
    RegSetValueEx(key, appname, 0, REG_SZ, path or GetModuleFileName(0))
    # Close the key when no longer used.
    RegCloseKey(key)



def is_running_at_startup(appname, user=False):
    
    key = RegOpenKeyEx(
        HKEY_CURRENT_USER if user else HKEY_LOCAL_MACHINE,
        STARTUP_KEY_PATH,
        0,
        KEY_WRITE | KEY_QUERY_VALUE
    )

    i = 0
    while True:
        try:
            name, _, _ = RegEnumValue(key, i)
        except pywintypes.error as e:
            if e.winerror == ERROR_NO_MORE_ITEMS:
                break
            else:
                raise
        if name == appname:
            RegCloseKey(key)
            return True
        i += 1
    return False

def run_script_at_startup_set(appname, user=False):
    """
    Like run_at_startup_set(), but for applications released as
    source code files (.py).
    """
    run_at_startup_set(
        appname,
        # Set the interpreter path (returned by GetModuleFileName())
        # followed by the path of the current Python file (__file__).
        '{} "{}"'.format(GetModuleFileName(0), __file__),
        user
    )


def run_at_startup_remove(appname, user=False):
    """
    Remove the registry application passed in the first param.
    """
    key = RegOpenKeyEx(
        HKEY_CURRENT_USER if user else HKEY_LOCAL_MACHINE,
        STARTUP_KEY_PATH,
        0,
        KEY_WRITE
    )
    RegDeleteValue(key, appname)
    RegCloseKey(key)