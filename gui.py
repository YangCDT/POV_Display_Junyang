import tkinter as tk
from tkinter import Toplevel, filedialog
import threading
from PIL import Image, ImageTk
import multiprocessing
from snake_game import play_snake_game, Game
from video import process_and_display_video, frame_to_brg_bytes, stop_video_processing
from image_display import display_image


def start_game():
    global game_process
    if game_process is None or not game_process.is_alive():
        game_process = multiprocessing.Process(target=play_snake_game)
        game_process.start()

def show_video_selection():
    main_frame.pack_forget()  # Hide the main frame
    video_selection_frame.pack(fill="both", expand=True)


def play_selected_video(video_path):
    global video_thread
    video_thread = threading.Thread(target=lambda: process_and_display_video(video_path))
    video_thread.start()
    show_main_frame()  # Go back to main frame after selecting a video


def show_main_frame():
    video_selection_frame.pack_forget()  # Hide the video selection frame
    main_frame.pack(fill="both", expand=True)
                               

def show_image_selection():
    main_frame.pack_forget()  # Hide the main frame
    image_selection_frame.pack(fill="both", expand=True)


def display_selected_image(image_path):
    global image_thread
    image_thread = threading.Thread(target=lambda: display_image(image_path))
    image_thread.start()
    show_main_frame()  # Go back to main frame after selecting a video


def show_main_frame_img():
    image_selection_frame.pack_forget()  # Hide the video selection frame
    main_frame.pack(fill="both", expand=True)


def exit_current_process():
    global game_process, video_thread
    if game_process is not None:
        game_process.terminate()  # Stop the game if it's running
        game_process.join()
        game_process = None
    if video_thread and video_thread.is_alive():
        stop_video_processing()  # Stop video processing if it's running
        video_thread.join()
        video_thread = None


# Main Tkinter window
root = tk.Tk()
root.title("Snake Game and Video Processing Controller")
root.geometry("600x600")

# Main frame
main_frame = tk.Frame(root)
start_snake_button = tk.Button(main_frame, text="Start Snake Game", command=start_game, height=2, width=20, font=("Helvetica", 16))
start_snake_button.pack(pady=20)
start_video_button = tk.Button(main_frame, text="Choose Video", command=show_video_selection, height=2, width=20, font=("Helvetica", 16))
start_video_button.pack(pady=20)
image_button = tk.Button(main_frame, text="Choose Image", command=show_image_selection, height=2, width=20, font=("Helvetica", 16))
image_button.pack(pady=20)
exit_button = tk.Button(main_frame, text="Exit Current Process", command=exit_current_process, height=2, width=20, font=("Helvetica", 16))
exit_button.pack(pady=20)
main_frame.pack(fill="both", expand=True)

# Video selection frame
video_selection_frame = tk.Frame(root)
back_button = tk.Button(video_selection_frame, text="Back", command=show_main_frame)
back_button.pack()

# Display video list
videos = [
    {"path": "Map.mp4", "name": "Map", "thumbnail": "map.jpg"},
    {"path": "minecraft.mp4", "name": "Minecraft", "thumbnail": "Minecraft.jpeg"},
    {"path": "Battery.mp4", "name": "Battery Demo", "thumbnail": "Battery.jpg"}
]

for video in videos:
    frame = tk.Frame(video_selection_frame)
    frame.pack(padx=10, pady=10)

    img = Image.open(video["thumbnail"])
    img.thumbnail((150, 150))
    img = ImageTk.PhotoImage(img)
    img_label = tk.Label(frame, image=img)
    img_label.image = img
    img_label.pack(side="top")

    btn = tk.Button(frame, text=video["name"], command=lambda v=video: play_selected_video(v["path"]))
    btn.pack(side="left")
    
# image selection frame
image_selection_frame = tk.Frame(root)
back_button = tk.Button(image_selection_frame, text="Back", command=show_main_frame_img)
back_button.pack()

# Display image list
images = [
    {"path": "map.jpg", "name": "Map"},
    {"path": "scotland.jpg", "name": "Scottish Flag"},
    {"path": "mario.jpg", "name": "mario"}
]

for image in images:
    frame = tk.Frame(image_selection_frame)
    frame.pack(padx=10, pady=10)

    img = Image.open(image["path"])
    img.thumbnail((150, 150))
    img = ImageTk.PhotoImage(img)
    img_label = tk.Label(frame, image=img)
    img_label.image = img
    img_label.pack(side="top")

    btn = tk.Button(frame, text=image["name"], command=lambda v=image: display_selected_image(v["path"]))
    btn.pack(side="left")

game_process = None
video_thread = None

root.mainloop()
