import serial
import struct
from PIL import Image

# Serial settings
PORT = '/dev/serial0'
BAUDRATE = 921600
# Start and End sequences
START_SEQ = b'\xFC\x0C'
END_SEQ = b'\x0F\xFB'


def image_to_brg_array(img_path):
    """Converts an image to a BRG byte array format."""
    img = Image.open(img_path)
    img = img.rotate(90)
    img = img.resize((66, 144))


    img_data = img.convert("RGB").tobytes()
    brg_data = bytearray()

    for i in range(0, len(img_data), 3):
        r, g, b = img_data[i], img_data[i+1], img_data[i+2]
        # Scale down to 5 bits per color
        r = (r >> 3) & 0x1F
        g = (g >> 3) & 0x1F
        b = (b >> 3) & 0x1F
        # Pack the 5 bit colors into a 2-byte structure, leaving 1 bit unused
        brg_pixel = struct.pack('<H', (b << 11) | (g << 6) | (r << 1))
        brg_data.extend(brg_pixel)

    return brg_data


def send_image_data(ser, img_path):
    """Sends the image data to Teensy over the serial port."""
    brg_data = image_to_brg_array(img_path)
    # Print the first 10 pixels (6 bytes per pixel: 2B + 2R + 2G)
    ser.write(START_SEQ)
    ser.write(brg_data)
    ser.write(END_SEQ)


def display_image(img_path):
    # Change 'image_path.png' to the path of display image
    
    # Set up the serial port
    with serial.Serial(PORT, BAUDRATE, bytesize=8) as arduino:
        send_image_data(arduino, img_path)