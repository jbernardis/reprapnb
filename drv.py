import subprocess
import time
import socket
from XMLDoc import XMLDoc
from webcamclient import Webcam


#
# Initialization
#
port = 9123

try:
	subprocess.Popen(["python", "webcamserver.py", "%d" % port],
		shell=False, stdin=None, stdout=None, stderr=None, close_fds=True)
except:
	print "unable to spawn"
	exit(1)

time.sleep(1)

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('4.2.2.1', 123))
ip = s.getsockname()[0]

wc = Webcam(ip, port)



#
# connect to a specific camera
#
rc, xml = wc.connect("/dev/video0")
if not rc:
	exit(1)
print "Connect: ", xml



#
# change attributes
#
rc, xml = wc.fnpicture(directory="/tmp")
if not rc:
	exit(1)
print "FNPicture: ", xml


#
# take a picture
#
rc, xml = wc.picture()
if not rc:
	exit(1)
print "Picture: ", xml
xd = XMLDoc(xml).getRoot()
print "Filename: (%s)" % str(xd.filename)


#
# change timelapse parameters at take a burst
#
wc.fntimelapse(prefix="tl1")
rc, xml = wc.timelapse(5, count=10)
if not rc:
	exit(1)
print "Timelapse1: ", xml

print "sleeping for 60"
time.sleep(60)



#
# do it again
#
wc.fntimelapse(prefix="tl2")
rc, xml = wc.timelapse(5, duration=30)
if not rc:
	exit(1)
print "Timelapse2: ", xml

print "sleeping for 60"
time.sleep(60)



# 
# exit
#
wc.exit()
