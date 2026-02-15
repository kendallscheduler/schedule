import uvicorn
import webbrowser
import os
import sys
import threading
import time

def open_browser():
    time.sleep(2)  # Wait for server to start
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    # If we are packaged, we need to make sure we serve static content correctly
    # The main.py logic handles looking for static files in sys._MEIPASS
    
    # Launch browser in a separate thread
    threading.Thread(target=open_browser).start()
    
    # Run server
    # workers=1 is standard for desktop apps
    # loop="asyncio" ensures compatibility
    from main import app
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)
