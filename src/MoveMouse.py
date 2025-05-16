import tkinter as tk
from tkinter import ttk
from PIL import Image
import pystray
import threading
import time
import sys
import traceback
import pyautogui 
import time
import base64
from io import BytesIO
from images import base64image


def image_to_base64_string(image_path):
    """Converts an image to a base64 encoded string.

    Args:
        image_path (str): The path to the image file.

    Returns:
        str: The base64 encoded string of the image.
    """
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return encoded_string
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

class TaskbarApp:
    def __init__(self):
        """
        Initializes the TaskbarApp.
        """
        self.window = tk.Tk()
        self.window.title("Taskbar Application")
        self.window.geometry("300x200")

        # Set the window icon
        try:
            img_bytes = base64.b64decode(base64image)
            img = Image.open(BytesIO(img_bytes))
            buffer = BytesIO()
            img.save(buffer, format="png")  # You can choose other formats if Tkinter supports them
            buffer.seek(0)
            icon_img = tk.PhotoImage(data=buffer.read())  # Use a .png file
            self.window.iconphoto(True, icon_img)
        except Exception as e:
            print(f"Error setting window icon: {e}")
            # Don't raise an exception here; just print a message

        self.label = ttk.Label(self.window, text="Application is running...")
        self.label.pack(pady=20)

        self.start_button = ttk.Button(self.window, text="Start", command=self.start)
        self.start_button.pack(pady=10)
        self.stop_button = ttk.Button(self.window, text="Stop", command=self.stop)
        self.stop_button.pack(pady=10)
        self.stop_button.state(["disabled"]) 
        self.quit_button = ttk.Button(self.window, text="Quit", command=self.quit_app)
        self.quit_button.pack(pady=10)

        try:
            img_bytes = base64.b64decode(base64image)
            self.icon_image = Image.open(BytesIO(img_bytes))
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
        self.start_button.state(["disabled"]) 
        self.is_running = True
        self.label.config(text="Application started...")
        print("Start button clicked. Application started.")
        self.stop_event.clear()
        self.thread_exception = None
        self.thread = threading.Thread(target=self.background_task, daemon=True)
        self.thread.start()
        self.stop_button.state(["!disabled"]) 

    def stop(self):
        """Stops the background thread."""
        if not self.is_running:
            return
        self.stop_button.state(["disabled"]) 
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
        self.start_button.state(["!disabled"]) 

    def background_task(self):
        """Simulates a background task."""
        try:
            while not self.stop_event.is_set():
                print("Background task running...")
                pyautogui.move(1,1)
                pyautogui.press('shift')
                time.sleep(10)
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
            if self.icon is None:
                self.buttons = {
                    "Show" : pystray.MenuItem("Show", self.show_window),
                    "Start": pystray.MenuItem("Start", self.start, enabled=lambda x: not self.is_running),
                    "Stop": pystray.MenuItem("Stop", self.stop, enabled=lambda x: self.is_running),
                    "Quit": pystray.MenuItem("Quit", self.quit_app)
                }
                self.icon = pystray.Icon(
                    "TaskbarApp",
                    self.icon_image,
                    "Taskbar Application",
                    menu=pystray.Menu(
                        self.buttons["Show"],
                        self.buttons["Start"],
                        self.buttons["Stop"],
                        self.buttons["Quit"]
                    ),
                )
                try:
                    self.icon.run_detached()
                except Exception as e:
                    print(f"Error running the icon: {e}")
                    traceback.print_exc()
            elif self.icon:
                self.icon.visible = True

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
