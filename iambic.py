#!/usr/bin/env python
''' An Iambic Keyer for Raspberry Pi'''
''' Based on https://github.com/swilcox/raspi-iambickey/ '''
''' Sound from https://www.mail-archive.com/pygame-users@seul.org/msg16140.html'''
''' Enable RPi headphone jack with sudo amixer -c 0 cset numid=3 1 '''

from RPi import GPIO
from time import time
import pygame
import numpy
import math
import sys

LEFT_PIN = 2
RIGHT_PIN = 3
LED_PIN = 17

WPM = 15.0
DIT_LENGTH = WPM / 200.0
DAH_LENGTH = DIT_LENGTH * 3.0

SAMPLE_RATE = 22500 
BITS = 16 

CHARS = {
            ".-": "A",
            "-...": "B",
            "-.-.": "C",
            "-..": "D",
            ".": "E",
            "..-.": "F",
            "--.": "G",
            "....": "H",
            "..": "I",
            ".---": "J",
            "-.-": "K",
            ".-..": "L",
            "--": "M",
            "-.": "N",
            "---": "O",
            ".--.": "P",
            "--.-": "Q",
            ".-.": "R",
            "...": "S",
            "-": "T",
            "..-": "U",
            "...-": "V",
            ".--": "W",
            "-..-": "X",
            "-.--": "Y",
            "--..": "Z",
            ".----": "1",
            "..---": "2",
            "...--": "3",
            "....-": "4",
            ".....": "5",
            "-....": "6",
            "--...": "7",
            "---..": "8",
            "----.": "9",
            "-----": "0",
        }


def make_buf(duration=1.0, sample_rate=SAMPLE_RATE, bits=BITS):
    n_samples = int(round(duration*sample_rate))
    buf = numpy.zeros((n_samples, 2), dtype=numpy.int16)
    max_sample = 2**(bits - 1) - 1
    for s in range(n_samples):
        t = float(s)/sample_rate
        buf[s][0] = int(round(max_sample*math.sin(2*math.pi*440*t)))
        buf[s][1] = int(round(max_sample*0.5*math.sin(2*math.pi*440*t)))
    
    return buf

def make_tone(buf, duration):
    sound = pygame.sndarray.make_sound(buf)
    sound.play()
    pygame.time.wait(int(round(1000*duration)))

DIT_BUF = make_buf(duration=DIT_LENGTH)
DAH_BUF = make_buf(duration=DAH_LENGTH)


class Paddles():
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(LEFT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(RIGHT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(LED_PIN, GPIO.OUT)

    def dit_paddle(self):
        return not GPIO.input(LEFT_PIN)

    def dah_paddle(self):
        return not GPIO.input(RIGHT_PIN)

class Sequence():
    def __init__(self):
        self.seq = []
        self.last = ""
        self.char = ""
        self.last_time = time()

    def add_dit(self):
        self.seq.append(".")
        self.char += "."
        self.last_time = time()

    def add_dah(self):
        self.seq.append("-")
        self.char += "-"
        self.last_time = time()
    
    def last_is_dit(self):
        return self.last == "."

    def last_is_dah(self):
        return self.last == "-"

    def dequeue(self):
        if len(self.seq) > 0:
            tone = self.seq.pop(0)
            self.last = tone
        else:
            tone = ""

        if time() - self.last_time > DAH_LENGTH:
            chars = self.char
            if self.char in CHARS:
                letter = CHARS[self.char]
            else:
                letter = ""
            self.char = ""
        else:
            chars = ""
            letter = ""
            
        return tone, chars, letter

class Keyer():
    def __init__(self):
        self.q = Sequence()

    def dequeue(self):
        tone, chars, letter = self.q.dequeue()
        if tone == ".":
            GPIO.output(LED_PIN, GPIO.HIGH)
            make_tone(buf=DIT_BUF, duration=DIT_LENGTH)
            GPIO.output(LED_PIN, GPIO.LOW)
        elif tone == "-":
            GPIO.output(LED_PIN, GPIO.HIGH)
            make_tone(buf=DAH_BUF, duration=DAH_LENGTH)
            GPIO.output(LED_PIN, GPIO.LOW)
        if len(chars) > 0:
            print(chars)

        if len(letter) > 0:
            print(letter)

        pygame.time.wait(int(round(1000*DIT_LENGTH)))

    def queue(self, left, right):
        if left and right:
            if self.q.last_is_dit():
                self.q.add_dah()
            elif self.q.last_is_dah():
                self.q.add_dit()
            self.dequeue()
        elif left:
            self.q.add_dit()
            self.dequeue()
        elif right:
            self.q.add_dah()
            self.dequeue()
        else:
            self.dequeue()

def start_audio():
    pygame.mixer.pre_init(frequency=SAMPLE_RATE, size=-BITS, channels=2, buffer=64)
    pygame.mixer.init()
    pygame.init()

def quit():
    pygame.mixer.quit()
    sys.exit(0)

def main():
    start_audio()
    
    p = Paddles()
    k = Keyer()
    
    while True:
        k.queue(p.dit_paddle(), p.dah_paddle())

if __name__ == "__main__":
    main()
