#!/bin/bash

# Port that the wallpaper manager app runs on
PORT=5050
APP_DIR="/home/anas/Projects/hyde-wallpaper-manager"
APP_PATH="$APP_DIR/app.py"

# Function to check if the port is in use
is_port_in_use() {
    # Using python to check port availability since python is guaranteed to be installed
    python3 -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect(('127.0.0.1', $PORT))
    s.close()
    print('busy')
except:
    print('free')
"
}

STATUS=$(is_port_in_use)

if [ "$STATUS" == "busy" ]; then
    # Server is already running, just open the browser
    xdg-open "http://localhost:$PORT"
else
    # Server is not running, launch it
    python3 "$APP_PATH"
fi
