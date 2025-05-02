from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import time

class ReloadHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("attendance.py"):
            print("\n🔄 Restarting attendance app...\n")
            subprocess.run(["python", "attendance.py"])

observer = Observer()
event_handler = ReloadHandler()
observer.schedule(event_handler, path='.', recursive=False)
observer.start()

print("👀 Watching for changes in attendance.py...")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()
