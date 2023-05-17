from machine import I2C, ADC, Pin, SPI, Timer
import time
from pico_i2c_lcd import I2cLcd
from neopixel import Neopixel
import random


spi = SPI(0, baudrate=20000000,polarity = 0, phase = 0, bits = 8, sck = Pin(18), mosi = Pin(19))
cs = Pin(17, mode=Pin.OUT, value=1)
HB = 0
LB = 0
frequency = 44000
sin_wave = [512,639,758,862,943,998,1022,1014,974,906,812,700,576,447,323,211,117,49,9,1,25,80,161,265,384]
def generate_sine_wave(timer):
    global sin_wave, spi, cs
    w = int(1 / frequency * 100000)
    for i in range(25):
        LB = (sin_wave[i] << 2)
        HB = (144 | (sin_wave[i] >> 6))
        txdata = bytearray([HB, LB])
        cs(0)
        spi.write(txdata)
        cs(1)
        time.sleep_us(w)

# Create a Timer object and start the timer
sine_wave_timer = Timer()
sine_wave_timer.init(period=10, mode=Timer.PERIODIC, callback=generate_sine_wave)

#button setup
button0 = Pin(14, Pin.IN, Pin.PULL_UP)
button1 = Pin(15, Pin.IN, Pin.PULL_UP)
debounce_time0 = 0
interrupt_flag0 = 0
debounce_time1 = 0
interrupt_flag1 = 0

#light sensor
light=ADC(machine.Pin(28))
conv_factor = 5 / 65535


#LCD Setup
i2c=I2C(0,scl=Pin(1),sda=Pin(16),freq=400000)
I2C_ADDR=i2c.scan()[0]
lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)
lcd.clear()

#Wifi board connections
Motion_detect=machine.Pin(10, Pin.IN)
W_EN=machine.Pin(11)
W_RST=machine.Pin(12)
W_WAKE=machine.Pin(21)
LED_Out=machine.Pin(22, Pin.OUT)
LED_Out.value(0)

# LED Strip setup
numpix = 20
strip = Neopixel(numpix, 0, 9, "RGB")
white = (255, 255, 255)
red = (255, 0, 0)
orange = (255, 50, 0)
yellow = (255, 100, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
indigo = (100, 0, 90)
violet = (200, 0, 100)
colors_rgb = [white, red, orange, yellow, green, blue, indigo, violet]
delay = 300
strip.brightness(42)
blank = (0,0,0)



#Button interrupt routine for debouncing:
def callback0(button0):
    global interrupt_flag0, debounce_time0
    if (time.ticks_ms()-debounce_time0)>250:
        debounce_time0=time.ticks_ms()
        if interrupt_flag0==1:
            sine_wave_timer.init(period=10, mode=Timer.PERIODIC, callback=generate_sine_wave)
        if interrupt_flag0==0:
            sine_wave_timer.deinit()
        interrupt_flag0 = not interrupt_flag0

def callback1(button1):
    global interrupt_flag1, debounce_time1
    if (time.ticks_ms()-debounce_time1)>250:
        debounce_time1=time.ticks_ms()
        if interrupt_flag1==1:
            lcd.backlight_off()
        elif interrupt_flag1==0:
            lcd.backlight_on()            
        interrupt_flag1= not interrupt_flag1
            
button0.irq(trigger=Pin.IRQ_FALLING, handler=callback0)    
button1.irq(trigger=Pin.IRQ_FALLING, handler=callback1)
status = "Startup"


while True:
    w = int(  (1/frequency)*100000  )
    strip.clear()
    room_light=0.0
    old_status = status
    for i in range(100):
        room_light = room_light+light.read_u16() * conv_factor


    if Motion_detect.value()==1:
        LED_Out.value(1)

        
        if room_light > 100:
            strip.set_pixel(0, colors_rgb[0])
            strip.set_pixel(1, colors_rgb[0])
            strip.set_pixel(2, colors_rgb[0])
            strip.set_pixel(3, colors_rgb[0])
            strip.set_pixel(4, colors_rgb[0])
            strip.show()
            frequency = 10000
            status = "LED Active"
            
        elif room_light < 30:
            strip.clear()
            strip.show()
            sine_wave_timer.init(period=1, mode=Timer.PERIODIC, callback=generate_sine_wave)
            status = "Music Only"
        else:
            strip.set_pixel(random.randint(0, numpix-1), colors_rgb[random.randint(0, len(colors_rgb)-1)])
            strip.set_pixel(random.randint(0, numpix-1), colors_rgb[random.randint(0, len(colors_rgb)-1)])
            strip.set_pixel(random.randint(0, numpix-1), colors_rgb[random.randint(0, len(colors_rgb)-1)])
            strip.set_pixel(random.randint(0, numpix-1), colors_rgb[random.randint(0, len(colors_rgb)-1)])
            strip.set_pixel(random.randint(0, numpix-1), colors_rgb[random.randint(0, len(colors_rgb)-1)])
            strip.show()
            time.sleep_ms(delay)
            strip.fill((0,0,0))
            frequency = 100000
            status = "Light show!"
            sine_wave_timer.init(period=50, mode=Timer.PERIODIC, callback=generate_sine_wave)
            

    else:
        LED_Out.value(0)
        strip.clear()
        strip.show()
        status = "Standby"
    
    if old_status != status:
        lcd.clear()
        lcd.putstr("Status: \n")
        lcd.putstr(status)
        time.sleep_ms(200)

    
  