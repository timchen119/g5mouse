#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#Pure python code to control logitech G3,G5,G7 and G9's 
#hardware dpi buttons on linux
#
#This code is based on ActiveState python recipe-576834
#G-series mouse commands tooks from http://piie.net/temp/g5_hiddev.c
#
#License: New BSD license
#Author: timchen119.at.gmail.com
#

import sys
import struct
import array
import fcntl
from optparse import OptionParser

class LOGIMOUSE:
    MOUSE_VENDOR=1133
    MOUSE_G5_FIRST=49217
    MOUSE_G5_SECOND=49225
    MOUSE_G7=50458
    MOUSE_G3=49218
    MOUSE_G9=49224

    #DISABLE BUTTONS
    DISABLE_SPEED_BUTTONS = [0x00, 0x80, 0x01, 0x00, 0x00, 0x00]

    #SET MOUSE DPI
    SET_DPI = {
    "400" : [0x00, 0x80, 0x63, 0x80, 0x00, 0x00],
    "800" : [0x00, 0x80, 0x63, 0x81, 0x00, 0x00],
    "1600" : [0x00, 0x80, 0x63, 0x82, 0x00, 0x00],
    "2000" : [0x00, 0x80, 0x63, 0x83, 0x00, 0x00],
    }

    #LED CONTROL
    SET_LED = {
    "1" : [0x00, 0x80, 0x51, 0x11, 0x02, 0x00],
    "2" : [0x00, 0x80, 0x51, 0x21, 0x01, 0x00],
    "3" : [0x00, 0x80, 0x51, 0x12, 0x01, 0x00],
    "NONE" : [0x00, 0x80, 0x51, 0x11, 0x01, 0x00],
    "ALL" : [0x00, 0x80, 0x51, 0x22, 0x02, 0x00],
    }

    #####################CHANGE THIS DEFAULT############################
    MOUSE_SETTINGS=["/dev/usb/hiddev0"]
    ####################################################################

class struxx:
    _fields = None
    _format = None
    _buffer = None
    def __init__(self):
        self.reset()

    def __len__(self):
        """binary represntation length, for fields, use __dict__ or something"""
        return struct.calcsize(self._format)

    def __iter__(self):
        return [getattr(self, field) for field in self._fields.split(";")].__iter__()

    def reset(self):
        for field in self._fields.split(";"):
            setattr(self, field, 0)
        self._buffer = array.array('B', [0]*len(self))

    def pack(self):
        self._buffer = array.array('B', struct.pack(self._format, *self))

    def unpack(self):
        rv = struct.unpack(self._format, self._buffer)
        for i in range(len(rv)):
            setattr(self, self._fields.split(";")[i], rv[i])

    def ioctl(self, fd, ioctlno):
        self.pack()
        rv = fcntl.ioctl(fd, ioctlno, self._buffer, True)
        self.unpack()
        return rv

class uint(struxx):
    _fields = "uint"
    _format = "I"
    def get_version(self, fd): return self.ioctl(fd, HIDIOCGVERSION)
    def get_flags(self, fd): return self.ioctl(fd, HIDIOCGFLAG)
    def set_flags(self, fd): return self.ioctl(fd, HIDIOCSFLAG)

class hiddev_devinfo(struxx):
    _fields = "bustype;busnum;devnum;ifnum;vendor;product;version;num_applications"
    _format = "IIIIHHHI"
    def get(self, fd): return self.ioctl(fd, HIDIOCGDEVINFO)

class hiddev_string_descriptor(struxx):
    _fields = "index;value"
    _format = "i256c"

    def reset(self):
        self.index = 0
        self.value = '\0'*256

    def pack(self):
        tmp = struct.pack("i", self.index) + self.value[:256].ljust(256, '\0')
        self._buffer = array.array('B', tmp)

    def unpack(self):
        self.index = struct.unpack("i", self._buffer[:4])
        self.value = self._buffer[4:].tostring()

    def get_string(self, fd, idx):
        self.index = idx
        return self.ioctl(fd, HIDIOCGSTRING)

class hiddev_report_info(struxx):
    _fields = "report_type;report_id;num_fields"
    _format = "III"
    def get_info(self, fd): return self.ioctl(fd, HIDIOCGREPORTINFO)
    def set_info(self, fd): return self.ioctl(fd, HIDIOCSREPORT)

class hiddev_field_info(struxx):
    _fields = "report_type;report_id;field_index;maxusage;flags;physical;logical;application;logical_minimum;logical_maximum;physical_minimum;physical_maximum;unit_exponent;unit"
    _format = "I"*8+"i"*4+"II"
    def get_info(self, fd): return self.ioctl(fd, HIDIOCGFIELDINFO)

class hiddev_usage_ref(struxx):
    _fields = "report_type;report_id;field_index;usage_index;usage_code;value"
    _format = "I"*5+"i"
    def set_info(self, fd): return self.ioctl(fd, HIDIOCSUSAGE)

class hiddev_collection_info(struxx):
    _fields = "index;type;usage;level"
    _format = "I"*4
    def get_info(self, fd, index):
        self.index = index
        return self.ioctl(fd, HIDIOCGCOLLECTIONINFO)

class hiddev_event(struxx):
    _fields = "hid;value"
    _format = "Hi"

IOCPARM_MASK = 0x7f
IOC_NONE = 0x20000000
IOC_WRITE = 0x40000000
IOC_READ = 0x80000000

def FIX(x): return struct.unpack("i", struct.pack("I", x))[0]
def _IO(x,y): return FIX(IOC_NONE|(ord(x)<<8)|y)
def _IOR(x,y,t): return FIX(IOC_READ|((t&IOCPARM_MASK)<<16)|(ord(x)<<8)|y)
def _IOW(x,y,t): return FIX(IOC_WRITE|((t&IOCPARM_MASK)<<16)|(ord(x)<<8)|y)
def _IOWR(x,y,t): return FIX(IOC_READ|IOC_WRITE|((t&IOCPARM_MASK)<<16)|(ord(x)<<8)|y)

HIDIOCGVERSION         =_IOR('H', 0x01, struct.calcsize("I"))
HIDIOCAPPLICATION      =_IO('H', 0x02)
HIDIOCGDEVINFO         =_IOR('H', 0x03, len(hiddev_devinfo()))
HIDIOCGSTRING          =_IOR('H', 0x04, len(hiddev_string_descriptor()))
HIDIOCINITREPORT       =_IO('H', 0x05)
def HIDIOCGNAME(buflen): return _IOR('H', 0x06, buflen)
HIDIOCGREPORT          =_IOW('H', 0x07, len(hiddev_report_info()))
HIDIOCSREPORT          =_IOW('H', 0x08, len(hiddev_report_info()))
HIDIOCGREPORTINFO      =_IOWR('H', 0x09, len(hiddev_report_info()))
HIDIOCGFIELDINFO       =_IOWR('H', 0x0A, len(hiddev_field_info()))
HIDIOCGUSAGE           =_IOWR('H', 0x0B, len(hiddev_usage_ref()))
HIDIOCSUSAGE           =_IOW('H', 0x0C, len(hiddev_usage_ref()))
HIDIOCGUCODE           =_IOWR('H', 0x0D, len(hiddev_usage_ref()))
HIDIOCGFLAG            =_IOR('H', 0x0E, struct.calcsize("I"))
HIDIOCSFLAG            =_IOW('H', 0x0F, struct.calcsize("I"))
HIDIOCGCOLLECTIONINDEX =_IOW('H', 0x10, len(hiddev_usage_ref()))
HIDIOCGCOLLECTIONINFO  =_IOWR('H', 0x11, len(hiddev_collection_info()))
def HIDIOCGPHYS(buflen): return _IOR('H', 0x12, buflen)

HID_REPORT_TYPE_INPUT   =1
HID_REPORT_TYPE_OUTPUT  =2
HID_REPORT_TYPE_FEATURE =3
HID_REPORT_TYPE_MIN     =1
HID_REPORT_TYPE_MAX     =3
HID_REPORT_ID_UNKNOWN =0xffffffff
HID_REPORT_ID_FIRST   =0x00000100
HID_REPORT_ID_NEXT    =0x00000200
HID_REPORT_ID_MASK    =0x000000ff
HID_REPORT_ID_MAX     =0x000000ff

def send_command(fd,codes):
    ri = hiddev_report_info()
    ri.report_type = HID_REPORT_TYPE_OUTPUT
    ri.report_id = 0x10
    ri.num_fields = 1
    for i in range(6):
        uref = hiddev_usage_ref()
        uref.report_type = HID_REPORT_TYPE_OUTPUT;
        uref.report_id   = 0x10;
        uref.field_index = 0;
        uref.usage_index = i;
        uref.usage_code  = 0xff000001;
        uref.value       = codes[i];
        uref.set_info(fd)
    ri.set_info(fd)

def check_valid_mouse(fd):
    devinfo = hiddev_devinfo()
    devinfo.get(fd)

    if devinfo.vendor == LOGIMOUSE.MOUSE_VENDOR:
        print "LOGITECH MOUSE FOUND!"
    else:
        print "ERROR: NO LOGITECH MOUSE FOUND! EXIT NOW!"
        sys.exit(1)

    if devinfo.product == LOGIMOUSE.MOUSE_G3:
        print ">>  G3 Gaming Mouse detected!\n"
    elif devinfo.product == LOGIMOUSE.MOUSE_G5_FIRST:
        print ">>  G5 1ST Generation Gaming Mouse detected!\n"
    elif devinfo.product == LOGIMOUSE.MOUSE_G5_SECOND:
        print ">>  G5 2ND Generation Gaming Mouse detected!\n"
    elif devinfo.product == LOGIMOUSE.MOUSE_G7:
        print ">>  G7 Gaming Mouse detected!\n"
    elif devinfo.product == LOGIMOUSE.MOUSE_G9:
        print ">>  G9 Gaming Mouse detected!\n"
    else:
        print "ERROR: NO LOGITECH G-SERIES MOUSE FOUND! EXIT NOW!"
        sys.exit(1)

def parse_arguments():
    usage = "usage: %prog [options] /dev/usb/hiddev0\n"
    usage += "\n%prog control logitech G3,G5,G7 and G9's hardware dpi buttons on linux\n"
    usage += "\nExample: g5mouse.py -d 1600 -l 1 /dev/usb/hiddev0\n"
    usage += "\nAuthor: timchen119.at.gmail.com"
    
    parser = OptionParser(usage)

    parser.add_option("-d", "--dpi", dest="dpi",
                      help="set dpi: 400,800,1600,2000")
    parser.add_option("-l", "--led", dest="led",
                      help="set led: NONE,1,2,3,ALL")
    parser.add_option("-n", "--nodpibuttons", action="store_true", dest="nodpibuttons",
                      help="disable + and - DPI speed buttons")
    parser.add_option("-e", "--dpibuttons", action="store_true", dest="dpibuttons",
                      help="enable + and - DPI speed buttons")

    (options, args) = parser.parse_args()

    if len(args) == 0 and (options.dpi or options.led or options.nodpibuttons or options.dpibuttons):
        print "\n\n################ USE DEFAULT CONFIG !!! ################"
        print "\n\nINFO: use defualt device %s" % LOGIMOUSE.MOUSE_SETTINGS[0]
    elif len(args) == 1:
        LOGIMOUSE.MOUSE_SETTINGS[0] = args[0]
    else:
        parser.print_help()
        sys.exit(1)

    if options.dpi and options.dpi in ['400','800','1600','2000']:
        LOGIMOUSE.MOUSE_SETTINGS.append(LOGIMOUSE.SET_DPI[options.dpi])
    else:
        print "use default DPI: 1600DPI"
        LOGIMOUSE.MOUSE_SETTINGS.append(LOGIMOUSE.SET_DPI['1600'])
        
    if options.led and options.led in ['NONE','1','2','3','ALL']:
        LOGIMOUSE.MOUSE_SETTINGS.append(LOGIMOUSE.SET_LED[options.led])
    else:
        print "use default LED settings: NO LEDS"
        LOGIMOUSE.MOUSE_SETTINGS.append(LOGIMOUSE.SET_LED['NONE'])
        
    if options.nodpibuttons and options.nodpibuttons == True:
        LOGIMOUSE.MOUSE_SETTINGS.append(LOGIMOUSE.DISABLE_SPEED_BUTTONS)
    else:
        print "Default: enable hardware speed buttons."

    if options.dpibuttons and options.dpibuttons == True:
        print "Now Enable hardware speed buttons."
        LOGIMOUSE.MOUSE_SETTINGS.append(LOGIMOUSE.ENABLE_SPEED_BUTTONS)

def main():
    parse_arguments()

    try:
        f = open(LOGIMOUSE.MOUSE_SETTINGS[0], "r")
    except:
        print "\n\nERROR: no such device %s\n" % LOGIMOUSE.MOUSE_SETTINGS[0]
        sys.exit(1)
        
    check_valid_mouse(f)

    for cmd in LOGIMOUSE.MOUSE_SETTINGS[1:]:
        send_command(f,cmd)

if __name__=="__main__":
    main()
