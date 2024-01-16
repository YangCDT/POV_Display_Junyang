import cv2
import numpy as np
import struct
import serial
import time

video_processing_stop_flag = False

def stop_video_processing():
    global video_processing_stop_flag
    video_processing_stop_flag = True


def frame_to_brg_bytes(frame):
    brg_data = bytearray()

    for y in range(frame.shape[0]):
        for x in range(frame.shape[1]):
            r, g, b = frame[y, x]
            # Scale down to 5 bits per color
            r = (r >> 3) & 0x1F
            g = (g >> 3) & 0x1F
            b = (b >> 3) & 0x1F
            # Pack the 5 bit colors into a 2-byte structure
            brg_pixel = struct.pack('<H', (b << 11) | (g << 6) | (r << 1))
            brg_data.extend(brg_pixel)

    return brg_data


def process_and_display_video(source_video):
    global video_processing_stop_flag
    video_processing_stop_flag = False
    fps=5
    speed_factor=17

    try:
        cap = cv2.VideoCapture(source_video)
        if not cap.isOpened():
            print("Error: Unable to open video file.")


        # Set up serial connection
        ser = serial.Serial('/dev/serial0', 921600, timeout=1)

        # Start and End sequences
        START_SEQ = b'\xFC\x0C'
        END_SEQ = b'\x0F\xFB'
        frame_size = (66, 144)

        frame_counter = 0

        while cap.isOpened() and not video_processing_stop_flag:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_counter % speed_factor == 0:
                # Process the frame
                frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
                resized_frame = cv2.resize(frame, frame_size, interpolation=cv2.INTER_AREA)
                
                brg_bytes = frame_to_brg_bytes(resized_frame)
                
                try:
                    ser.write(START_SEQ)
                    ser.write(brg_bytes)
                    ser.write(END_SEQ)
                except serial.SerialException as e:
                    print(f"Error sending data over UART: {e}")

            frame_counter += 1

    except Exception as e:
        print(f"Error during video processing: {e}")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        ser.close()
