#!/usr/bin/python
import serial
import time
import json
import signal
import threading
import subprocess
import os

from wsgiref.simple_server import make_server

def _sleep_handler(signum, frame):
    print "SIGINT Received. Stopping CAF"
    raise KeyboardInterrupt

def _stop_handler(signum, frame):
    print "SIGTERM Received. Stopping CAF"
    raise KeyboardInterrupt

signal.signal(signal.SIGTERM, _stop_handler)
signal.signal(signal.SIGINT, _sleep_handler)


PORT = 6000
HOST = "0.0.0.0"

# A relatively simple WSGI application. It's going to print out the
# environment dictionary after being updated by setup_testing_defaults

import re

sensors = {}
class SerialThread(threading.Thread):
    def __init__(self):
        super(SerialThread, self).__init__()
        self.name = "SerialThread"
        self.setDaemon(True)
        self.stop_event = threading.Event()


    def stop(self):
        self.stop_event.set()

    def run(self):
        serial_dev = os.getenv("HOST_DEV1")
        if serial_dev is None:
            serial_dev="/dev/tty.usbserial"

        sdev = serial.Serial(port=serial_dev, baudrate=9600) 
        sdev.bytesize = serial.EIGHTBITS #number of bits per bytes

        sdev.parity = serial.PARITY_NONE #set parity check: no parity

        sdev.stopbits = serial.STOPBITS_ONE #number of stop bits
        sdev.timeout = 5
        print "Serial:  %s\n" % sdev
        while True:
            if self.stop_event.is_set():
                break
            # get keyboard input
            # send the character to the device
            # (note that I happend a \r\n carriage return and line feed to the characters - this is requested by my device)
            # let's wait one second before reading output (let's give device time to answer)
            while sdev.inWaiting() > 0:
    	        sensVal = sdev.readline()
    	        sensVal=sensVal.split(",")
                print "Temperature:%s Humidity:%s Pressure:%s" % (sensVal[0], sensVal[1], sensVal[2]) 
                sensors["temp"]=sensVal[0]
	        sensors["hum"]=sensVal[1]
	        sensors["pres"]=sensVal[2]
                time.sleep(1)
        sdev.close()

def simple_app(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'application/json')]
    start_response(status, headers)
    ret = json.dumps(sensors)
    return ret

httpd = make_server(HOST, PORT, simple_app)
print "Serving on port %s:%s" % (HOST, str(PORT))
try:
    p = SerialThread()
    p.start()
    httpd.serve_forever()
except KeyboardInterrupt:
    p.stop()
    httpd.shutdown()

