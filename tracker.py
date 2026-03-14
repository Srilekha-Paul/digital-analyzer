import time
import json
import pygetwindow as gw

usage = {}

while True:

    try:
        window = gw.getActiveWindow().title

        if window not in usage:
            usage[window] = 0

        usage[window] += 5

        with open("usage.json","w") as f:
            json.dump(usage,f)

    except:
        pass

    time.sleep(5)