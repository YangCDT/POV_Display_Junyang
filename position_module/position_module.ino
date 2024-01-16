#include <Arduino.h>

/** This code deals takes a naive approach to the problem of frequency interpolation
 *  which is necessary to determine the position of image column around the beach ball.
 * 
 *      ____ 
 * ____|    |____|
 *     ^    ^    
 *     p_0  p_n  
 * 
 * PULSE_PER_ROTATION * pow(scale_shift, 2) should be equal to N_COLS
**/

#define N_COLS 144
#define PULSE_PER_ROTATION 18

const int scale_shift = 3; // 8 = 2^3 output pulses inbetween input pulses

const int pwm_motor_pin = 5;
const int pwm_pin_out = 4; 

unsigned long p_0;
unsigned long p_1;
unsigned long p_n;

unsigned long lambda;

unsigned long t;
unsigned long interp_time;


bool prev_state = false;
bool interp_flag = false;

void setup() {
  pinMode(pwm_pin_out, OUTPUT);  
  pinMode(pwm_motor_pin, INPUT);
}

void loop() {

  // * Triggers on RISING or FALLING edge
  if ( (digitalRead(pwm_motor_pin) == HIGH && prev_state == LOW)  || 
       (digitalRead(pwm_motor_pin) == LOW  && prev_state == HIGH)    ){

    p_n = micros();
    lambda = (p_n - p_0) >> scale_shift;
    p_0 = p_n;

    // * Flip flags so we only catch edges
    prev_state = (prev_state + 1) % 2; // HIGH (1) -> LOW (0) or LOW (0) -> HIGH (1)
    interp_flag = false; 
  }

  t = micros();
  if (t != interp_time){
    interp_time = t;

    int remainder = (t - p_n)/lambda;

    if (remainder % 2 == 0 && interp_flag == false){
      digitalWrite(pwm_pin_out, HIGH);
      interp_flag = true;

    } else if (remainder % 2 == 1 && interp_flag == true){
      digitalWrite(pwm_pin_out, LOW);
      interp_flag = false;

    }
  }
}
