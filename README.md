import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import pystray
import threading
import time
import sys
import traceback

class TaskbarApp:
    def __init__(self):
        """
        Initializes the TaskbarApp.
        """
        self.window = tk.Tk()
        self.window.title("Taskbar Application")
        self.window.geometry("300x200")

        self.label = ttk.Label(self.window, text="Application is running...")
        self.label.pack(pady=20)

        self.start_button = ttk.Button(self.window, text="Start", command=self.start)
        self.start_button.pack(pady=10)
        self.stop_button = ttk.Button(self.window, text="Stop", command=self.stop)
        self.stop_button.pack(pady=10)

        try:
            self.icon_image = Image.open("icon.png")
        except FileNotFoundError:
            print("Error: icon.png not found. Using a placeholder.")
            self.icon_image = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))

        self.icon = None
        self.is_running = False
        self.thread = None
        self.stop_event = threading.Event()
        self.thread_exception = None
        self.main_thread_id = threading.get_ident() # Store main thread ID
        self.is_quitting = False # Add a flag to track quitting state

        self.window.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self.window.withdraw()


    def start(self):
        """Starts the background thread."""
        if self.is_running:
            return
        self.is_running = True
        self.label.config(text="Application started...")
        print("Start button clicked. Application started.")
        self.stop_event.clear()
        self.thread_exception = None
        self.thread = threading.Thread(target=self.background_task)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """Stops the background thread."""
        if not self.is_running:
            return
        self.is_running = False
        self.label.config(text="Application stopped.")
        print("Stop button clicked. Application stopped.")
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
            if self.thread.is_alive():
                print("Warning: Background thread did not stop in time.")
            else:
                self.thread = None

    def background_task(self):
        """Simulates a background task."""
        try:
            while not self.stop_event.is_set():
                print("Background task running...")
                time.sleep(5)
        except Exception as e:
            print(f"Error in background task: {e}")
            self.thread_exception = e
            traceback.print_exc()
        finally:
            print("Background task stopped.")

    def show_window(self):
        """Shows the main window."""
        def _show_window():
            if self.is_quitting:
                return
            self.window.deiconify()
            if self.icon:
                self.icon.visible = False
        if threading.get_ident() != self.main_thread_id:
             self.window.after(0, _show_window)
        else:
             _show_window()

    def hide_to_tray(self):
        """Hides the main window and minimizes to the system tray."""
        def _hide_to_tray():
            if self.is_quitting:
                return
            self.window.withdraw()
            self.icon = pystray.Icon(
                "TaskbarApp",
                self.icon_image,
                "Taskbar Application",
                menu=pystray.Menu(
                    pystray.MenuItem("Show", self.show_window),
                    pystray.MenuItem("Start", self.start),
                    pystray.MenuItem("Stop", self.stop),
                    pystray.MenuItem("Quit", self.quit_app),
                ),
            )
            try:
                self.icon.run_detached()
            except Exception as e:
                print(f"Error running the icon: {e}")
                traceback.print_exc()

        if threading.get_ident() != self.main_thread_id:
            self.window.after(0, _hide_to_tray)
        else:
            _hide_to_tray()

    def quit_app(self, icon=None, item=None):
        """Quits the application."""
        if self.is_quitting:
            return  # Prevent multiple quit attempts
        self.is_quitting = True
        print("Quit requested")
        self.stop() # Stop the background thread.

        def _cleanup(): # Encapsulate cleanup
            if self.icon:
                try:
                    self.icon.stop()
                except Exception as e:
                    print(f"Error stopping icon: {e}")
                    traceback.print_exc()
            self.cleanup_and_destroy()

        if self.icon:
            if threading.get_ident() != self.main_thread_id:
                self.window.after(0, _cleanup)
            else:
                _cleanup()
        else:
            self.window.after(0, _cleanup)

    def cleanup_and_destroy(self):
        """Cleanup."""
        try:
            if self.thread_exception:
                print(f"Exception in background thread: {self.thread_exception}")
                traceback.print_exc()
            self.window.destroy()
        except Exception as e:
            print(f"Error destroying window: {e}")
            traceback.print_exc()
        finally:
            sys.exit(0)

    def run(self):
        """Runs the application."""
        self.hide_to_tray()
        self.window.mainloop()

if __name__ == "__main__":
    app = TaskbarApp()
    app.run()
