#include <SPI.h>
#include <Adafruit_DotStar.h>
#include <stdint.h>


// * Defining out LED strip object and its parameters.
#define NUMLED 132
#define BRIGHTNESS 30

Adafruit_DotStar strip = Adafruit_DotStar(NUMLED, DOTSTAR_BRG);

// * Our image dimensions
// * IMG_W can be changed while IMG_H is based on the number of physical
// * LEDs that we have. 
#define IMG_H 66
#define IMG_W 144

// => assert NUMLED/2 == IMG_H

const int position_pulse_pin = 4;
const int motor_control_pin = 2;
const int hall_sensor_pin = 3;

volatile byte position_counter = 0;
volatile bool hall_sensor_triggered = false;

int set_duty;

int starting_duty = 300;
const int target_RPM = 700;

const uint8_t START_SEQ[] = {0xFC, 0x0C};
const uint8_t END_SEQ[] = {0x0F, 0xFB};

// Buffer to store incoming data
uint8_t dataBuffer[144 * 66 * 2];  // 6 bytes per pixel (BRG format)

static uint32_t combinedPixelData[144] [66]; // Each entry will store the combined pixel data

unsigned int bufferIndex = 0;
bool capturingData = false;

void setColumnSide(uint32_t pixelColumn [], bool front){
  
  int ledOffset = NUMLED/2;
  for (int led = 0; led < IMG_H; led++){
    uint32_t color = pixelColumn[led];
    if(front){
      strip.setPixelColor(ledOffset - led, color);
    } else {
      strip.setPixelColor(ledOffset + led, color);
    }
  }
}

void allColours(uint32_t colour){
  uint32_t fullColour[NUMLED/2] = {colour};
  setColumnSide(fullColour, true);
  setColumnSide(fullColour, false);
}

// * Increment position counter
void incPosition() {
  position_counter = position_counter + 1;
}

void setup() {
    // Serial Initialization
    Serial1.begin(921600); // Initialize Serial1 for UART GPIO communication

    // Motor and position pulse pin Initialization
    pinMode(motor_control_pin, OUTPUT);
    pinMode(position_pulse_pin, INPUT);
    pinMode(hall_sensor_pin, INPUT);

    // PWM Initialization
    analogWriteResolution(12); // [0, 4095]
    analogWriteFrequency(motor_control_pin, 1000);

    // LED strip Initialization
    strip.begin();
    strip.setBrightness(BRIGHTNESS);
    allColours(0x00FFFF);
    strip.show();

    set_duty = 718; // ~700 RPM;

    allColours(0x000000);
    strip.show();

    delay(1000);
}



bool showing_led = false;
bool prev_state = LOW;

void loop() {
    processIncomingData();
    updateLEDs();
}

void processIncomingData() {
  while (Serial1.available()) {
    uint8_t incomingByte = Serial1.read();
    
    if (!capturingData) {
      // Check for start sequence
      if (checkForSequence(START_SEQ, sizeof(START_SEQ), incomingByte)) {
        capturingData = true;
        bufferIndex = 0; // Reset buffer index
      }
    } else {
      if (bufferIndex < sizeof(dataBuffer)) {
        dataBuffer[bufferIndex++] = incomingByte;
      }

      // Check for end sequence
      if (checkForSequence(END_SEQ, sizeof(END_SEQ), incomingByte)) {
        capturingData = false;
        
        // Convert buffer data to combined pixel data
        for (int row = 0; row < 144; row++) {
            for (int col = 0; col < 66; col++) {
                int index = (row * 66 + col) * 2; // 2 bytes per pixel
                uint16_t twoBytes = (dataBuffer[index] << 8) | dataBuffer[index + 1]; // Combine two bytes
                
                // Extract 5-bit values and scale them to 8 bits
                uint8_t b = (twoBytes >> 11) & 0x1F;
                uint8_t r = (twoBytes >> 6) & 0x1F;
                uint8_t g = (twoBytes >> 1) & 0x1F;
                
                // Scale 5-bit to 8-bit
                b = (b << 3) | (b >> 2);
                r = (r << 3) | (r >> 2);
                g = (g << 3) | (g >> 2);

                // Store in the buffer, assuming combinedPixelData is a 32-bit buffer to hold RGB888
                combinedPixelData[row][col] = (b << 16) | (r << 8) | g;
            }
        }
        // Print the first 10 combined pixel values to the Serial Monitor
        int count = 0;
      }
    }
  }
}


void updateLEDs() {
    if ((digitalRead(position_pulse_pin) == HIGH && prev_state == LOW) ||
        (digitalRead(position_pulse_pin) == LOW && prev_state == HIGH)) {
        incPosition();
        prev_state = (prev_state + 1) % 2;
        showing_led = false;
    }
  
    if (showing_led == false) {
        setColumnSide(combinedPixelData[position_counter], true);
        setColumnSide(combinedPixelData[(position_counter + IMG_W/2) % IMG_W], false);

        strip.show();
        showing_led = true;
    }

      if (digitalRead(hall_sensor_pin) == LOW && !hall_sensor_triggered) {
    position_counter = 0; // Reset position counter at the start of rotation
    hall_sensor_triggered = true; // Prevent further resets in this rotation
  }

  // Reset the flag when the magnet is not near the sensor
  if (digitalRead(hall_sensor_pin) == HIGH) {
    hall_sensor_triggered = false; // Ready for the next rotation
  }
  
    // Write the PWM for the motor speed
    analogWrite(motor_control_pin, set_duty);
}

bool checkForSequence(const uint8_t* sequence, uint8_t seqLength, uint8_t incomingByte) {
  static uint8_t seqIndex = 0;
  
  if (incomingByte == sequence[seqIndex]) {
    seqIndex++;
    if (seqIndex == seqLength) {
      seqIndex = 0;
      return true;
    }
  } else {
    seqIndex = 0;
  }

  return false;
}
