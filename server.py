import serial

# XBee setting
serdev = '/dev/ttyUSB0'
s = serial.Serial(serdev, 9600)

while(True):
    char = s.read()
    if(char.decode() == 'N'):
        print()
    else:
        print(char.decode(), end = '')
s.close()