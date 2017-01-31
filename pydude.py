import serial
import time
import argparse
import os
import sys
from types import MethodType
import struct

def parseAck(self, success = None):
    ack = self.read(3) #read back ACK ("OK")
    if (success <> None):
        print "Ack: " + ack;

    if (ack == "OK\0"):
        if success:
            print success
        return True
    else:
        print "Acknowledgement not recieved"
        self.close();
        sys.exit();
        return False


## parse arguments
parser = argparse.ArgumentParser(description='A python re-implementation of the c55x fork of AVRDUDE')
parser.add_argument("f", help="name of file to upload to DSP Shield")
parser.add_argument("port", help="specify a COM port by name")
parser.add_argument("--baud", help="specify a transmit baudrate")
parser.add_argument("--sleep", help="specify time to delay to allow for DSP reset in ms")
args = parser.parse_args()

##port argument
if args.port:
    port = args.port
else:
    from serial.tools import list_ports
    ports = list_ports.comports()
    print "Found ports:"
    for port in ports:
        print port
    port = port[0]
print "Port: " + port;

##baudrate argument
if args.baud:
    baudrate = args.baud
else:
    baudrate = 57600
print "baudrate: " + str(baudrate)

##sleep argument
if args.sleep:
    sleepTime = int(args.sleep)
else:
    sleepTime = 10
print "sleep time: " + str(sleepTime)

##infile
infileName = args.f;
print infileName
## Open target file
try:
    f = open(infileName, "rb")
except:
    print "error, input file could not be opened"
    sys.exit()

fSize = os.path.getsize(infileName); #target file size
checksum = 0;


## initialize connection to DSP
c5517 = serial.Serial(port, baudrate, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, 10, False, False, False, 10, None)
c5517.parseAck = MethodType(parseAck, c5517);
## Release DSP Shield from reset
time.sleep(sleepTime/1000.0)
c5517.setRTS(True)
time.sleep(sleepTime/1000.0)
c5517.setRTS(False)
print "Waiting for the target..."
time.sleep(2);
c5517.write("29"); #command to make DSP Shield go into programming mode.
#c5517.write('9'); #command to make DSP Shield go into programming mode.

time.sleep(sleepTime/1000.0);
#c5517.flush();
c5517.baudrate = 115200; #set serial to max baudrate for data transfer.
#c5517.flush();
c5517.parseAck("Ready");
#time.sleep(sleepTime/1000.0);

print "fSize=" + str(fSize) + " :",
fSizeSTR = struct.pack(">I", fSize)
fSizeSTR = fSizeSTR[::-1];
for letter in fSizeSTR:
    print format(ord(letter),'02x'),
print ""
c5517.write(fSizeSTR); #write file size to DSP.
c5517.parseAck("Target connected, sending data...");
#now write the file out in 512 byte chunks.
while True:
    fileChunk = f.read(512);
    checksum += sum(ord(ch) for ch in fileChunk);
    c5517.write(fileChunk);
    time.sleep(sleepTime/1000.0);
    #c5517.parseAck("Len:" + str(len(fileChunk)) + "\tChecksum: " + str(checksum));
    c5517.parseAck();
    if len(fileChunk) < 512:
        break;

print("done transmitting.");
##finally write the checksum
checkStr = struct.pack(">I", checksum);
checkStr = checkStr[::-1];
c5517.write(checkStr); #write checksum to DSP.
c5517.parseAck("Complete");

c5517.close();
f.close();
