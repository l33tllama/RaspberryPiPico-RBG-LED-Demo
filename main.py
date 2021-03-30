import array, time
from machine import Pin
import rp2
from lcd import HD44780

# Configure the number of WS2812 LEDs, pins and brightness.
NUM_LEDS = 1
PIN_NUM = 16
brightness = 0.1
btn_1_pin = machine.Pin(6, machine.Pin.IN)
btn_2_pin = machine.Pin(7, machine.Pin.IN)
pot_pin = machine.ADC(28)
 
 
@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
def ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")          .side(1)    [T2 - 1]
    label("do_zero")
    nop()                   .side(0)    [T2 - 1]
    wrap()
 
 
# Create the StateMachine with the ws2812 program, outputting on Pin(16).
sm = rp2.StateMachine(0, ws2812, freq=8_000_000, sideset_base=Pin(PIN_NUM))
 
# Start the StateMachine, it will wait for data on its FIFO.
sm.active(1)
 
# Display a pattern on the LEDs via an array of LED RGB values.
ar = array.array("I", [0 for _ in range(NUM_LEDS)])
 
def pixels_show():
    dimmer_ar = array.array("I", [0 for _ in range(NUM_LEDS)])
    for i,c in enumerate(ar):
        r = int(((c >> 8) & 0xFF) * brightness)
        g = int(((c >> 16) & 0xFF) * brightness)
        b = int((c & 0xFF) * brightness)
        dimmer_ar[i] = (g<<16) + (r<<8) + b
    sm.put(dimmer_ar, 8)
    time.sleep_ms(10)
 
def pixels_set(i, color):
    ar[i] = (color[1]<<16) + (color[0]<<8) + color[2]
 
def pixels_fill(color):
    for i in range(len(ar)):
        pixels_set(i, color)
 
 
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 150, 0)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
PURPLE = (180, 0, 255)
WHITE = (255, 255, 255)
COLORS = (BLACK, RED, YELLOW, GREEN, CYAN, BLUE, PURPLE, WHITE)

interact_modes = {"cycle" : 0, "set" : 1, "show" : 2}
colour_modes = {"red" : 0, "green" :1 , "blue" :2 }
interact_mode_i = 1
picking_colour_i = 0

interact_mode = "set"

lcd = HD44780()

lcd.PINS = [0,1,2,3,4,5]

lcd.init()

lcd.clear() # Clear the display

lcd.set_line(0) # First line
lcd.set_string("Hello Raspberry") # Send a string
lcd.set_line(1) # Second line
lcd.set_string("Pi Pico") # Again

#time.sleep_ms(3000) # 3 second delay

for color in COLORS:
    pixels_fill(color)
    pixels_show()
    time.sleep(0.1)
    
colour = (0, 0, 0)

red_v = 0
green_v = 0
blue_v = 0

colour_cycle_i = 0
colour_cycle_val = 0

lcd.set_line(0)
lcd.set_string("Setting Colour")

while True:
    # Colour set
    if interact_mode_i == interact_modes["set"]:
        if picking_colour_i == colour_modes["red"]:
            green_v = (pot_pin.read_u16() / 65535.0) * 255.0
            colour = (int(green_v), 0, 0)
            pixels_fill(colour)
            lcd.set_line(1)
            lcd.set_string("Green " + str(int(green_v)))
            time.sleep(0.05)
        elif picking_colour_i == colour_modes["green"]:
            red_v = (pot_pin.read_u16() / 65535.0) * 255.0
            colour = (0, int(red_v), 0)
            pixels_fill(colour)
            lcd.set_line(1)
            lcd.set_string("Red " + str(int(red_v)))
            time.sleep(0.05)
        elif picking_colour_i == colour_modes["blue"]:
            blue_v = (pot_pin.read_u16() / 65535.0) * 255.0
            colour = (0, 0, int(blue_v))
            pixels_fill(colour)
            lcd.set_line(1)
            lcd.set_string("Blue " + str(int(blue_v)))
            time.sleep(0.05)
        pixels_show()
        if not btn_2_pin():
            picking_colour_i = 0 if picking_colour_i == 2 else picking_colour_i + 1
            print("Next colour " + str(picking_colour_i))
            time.sleep(0.25)
    
    # Colour show (after setting)
    elif interact_mode_i == interact_modes["show"]:
        colour = (int(green_v), int(red_v), int(blue_v))
        pixels_fill(colour)
        pixels_show()
    
    # Colour cycle
    elif interact_mode_i == interact_modes["cycle"]:
        if colour_cycle_i == 0:
            colour = (0, colour_cycle_val, 0)
        elif colour_cycle_i == 1:
            colour = (colour_cycle_val, 0, 0)
        elif colour_cycle_i == 2:
            colour = (0, 0, colour_cycle_val)
        colour_cycle_val += 1
        
        if colour_cycle_val == 256:
            colour_cycle_val = 0
            colour_cycle_i += 1
            if colour_cycle_i == 3:
                colour_cycle_i = 0
        
        pixels_fill(colour)
        pixels_show()
        #time.sleep(0.001)
    
    # Change modes
    if not btn_1_pin():
        interact_mode_i = 0 if interact_mode_i == 2 else interact_mode_i + 1
        print("Next mode " + str(interact_mode_i))
        time.sleep(0.25)
        if interact_mode_i == interact_modes["set"]:
            lcd.set_line(0)
            lcd.set_string("Setting Colour")
        elif interact_mode_i == interact_modes["show"]:
            lcd.set_line(0)
            lcd.set_string("Showing Colour")
            lcd.set_line(1)
            lcd.set_string(str(int(red_v)) + " " + str(int(green_v)) + " " +str(int(blue_v)))
        elif interact_mode_i == interact_modes["cycle"]:
            lcd.set_line(0)
            lcd.set_string("Colour cycle!")
        

