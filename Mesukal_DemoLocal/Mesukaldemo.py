#!/usr/bin/python3

import os
import subprocess
import time
import argparse
import signal
import sys

def signal_handler(sig, frame):
		os.system("killall vlc")
		os.system("sudo tc qdisc del dev lo root")
		sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
# Transcode video file to suitable format

# Low resolution: QCIF (176x144, 30fps), QVGA (320x240, 30fps), HVGA (480x320, 30fps)
# 2 High resolution mode : TV(1280x720), TV (1920x1080), Frame rate, 15, 30, 60

parser = argparse.ArgumentParser(description='mesukal option')
parser.add_argument('-c','--codec', help='select your codec',choices=["h264","mp4v" , "youtube"], required=False)
parser.add_argument('-f','--form', help='select the quality',choices= ["HD720" , "HVGA" , "QGVA" , "QCIF","HD1080"], required=False)
parser.add_argument('-plr', help="use to simulate interference" , required=False)
parser.add_argument('-vi' ,'--videoInput' , help= 'insert the path of your video' , required=False)
args = parser.parse_args()

in_video = (lambda vPath: "../video/bbb_origine.mp4" if vPath == None  else vPath)(args.videoInput)
codec = (lambda codec: "h264" if codec == None  else codec)(args.codec) 
form = (lambda form: "HD720" if form == None  else form)(args.form)
plr = (lambda plr: "0.5%" if plr == None  else plr+"%")(args.plr)

# add packet loss
if(plr == "0%"):
	# do nothing
	1 +2  
else:

	loss = "sudo tc qdisc del dev lo root"
	os.system(loss)
	loss = "sudo tc qdisc add dev lo root netem loss {}".format(plr)
	os.system(loss)


if codec == "h264":
	profile = "baseline"
	case = 0
	if form[0:2] == "HD": 
		profile = "high"
		case = 1
	out_video = "../video/bbb_"+profile+"_"+codec+"_"+form+".mp4"
elif codec == "mp4v":
	out_video = "../video/bbb_"+codec+"_"+form+".mp4"
elif codec == "youtube":
	case = 2
	# video on demand from sky
	out_video = "https://www.youtube.com/watch?v=hanE_bysWro"
	# live video france inter
	#out_video = "https://www.youtube.com/watch?v=wwNZKfBLAsc"


if form == "QCIF":
	size = "width=176,height=144"
elif form == "QVGA":
	size = "width=320,height=240"
elif form == "HVGA":
	size = "width=480,height=320"
elif form == "HD720":
	size = "width=1280,height=720"
elif form == "HD1080":
	size = "width=1920,height=1080"


def transcode(in_video,out_video,codec,form):

	if codec == "h264":
		if form == "QCIF":		
			command = "vlc -I dummy {} --sout=#'transcode{{acodec=none,scodec=none,venc=x264{{preset=ultrafast,profile={}}},vcodec={},fps=30,{}}}:file{{mux=mp4,dst={}}}'".format(in_video,profile,codec,size,out_video)
				
		elif form == "QVGA":
			command = "vlc -I dummy {} --sout=#'transcode{{acodec=none,scodec=none,venc=x264{{preset=ultrafast,profile={}}},vcodec={},fps=30,{}}}:file{{mux=mp4,dst={}}}'".format(in_video,profile,codec,size,out_video)
			
		elif form == "HVGA":
			command = "vlc -I dummy {} --sout=#'transcode{{acodec=none,scodec=none,venc=x264{{preset=ultrafast,profile={}}},vcodec={},fps=30,{}}}:file{{mux=mp4,dst={}}}'".format(in_video,profile,codec,size,out_video)
		
		elif form == "HD720":
			command = "vlc -I dummy {} --sout=#'transcode{{acodec=none,scodec=none,venc=x264{{preset=fast,profile={}}},vcodec={},fps=30,{}}}:file{{mux=mp4,dst={}}}'".format(in_video,profile,codec,size,out_video)
		
		elif form == "HD1080":
			command = "vlc -I dummy {} --sout=#'transcode{{acodec=none,scodec=none,venc=x264{{preset=fast,profile={}}},vcodec={},fps=30,{}}}:file{{mux=mp4,dst={}}}'".format(in_video,profile,codec,size,out_video)

			
	elif codec == "mp4v":
		if form == "QCIF":		
			command = "vlc -I dummy {} --sout=#'transcode{{acodec=none,scodec=none,vcodec={},venc=ffmpeg{{bframes=0}},fps=30,{}}}:file{{mux=mp4,dst={}}}'".format(in_video,codec,size,out_video)
		
		elif form == "QVGA":
			command = "vlc -I dummy {} --sout=#'transcode{{acodec=none,scodec=none,vcodec={},venc=ffmpeg{{bframes=0}},fps=30,{}}}:file{{mux=mp4,dst={}}}'".format(in_video,codec,size,out_video)
			
		elif form == "HVGA":
			command = "vlc -I dummy {} --sout=#'transcode{{acodec=none,scodec=none,vcodec={},venc=ffmpeg{{bframes=0}},fps=30,{}}}:file{{mux=mp4,dst={}}}'".format(in_video,codec,size,out_video)
	
	elif codec == "youtube":
		command = None
	return command

cmd = transcode(in_video, out_video, codec, form)
#os.system(cmd)

# Test for LR - Low Resolution sans TS, QCIF (176x144, 30fps), QVGA (320x240, 30fps), HVGA (480x320, 30fps)
# Tranmission over RTP using RTSP/SDP protocols. Two video codecs may be used H.264 et MP4

if case == 0:
	# mode push RTP using RTSP

	#start a server
	server="vlc {} --sout=#duplicate{{dst=display,dst=rtp{{sdp=rtsp://localhost:8080/bbb.sdp}}}} --rtsp-timeout=0 --loop &".format(out_video)

	print(server)
	os.system(server)

	time.sleep(1)
	
	windowS = "wmctrl -r bbb_baseline_{}_{}.mp4 - Lecteur multimedia VLC -e 1,800,100,480,320".format(codec,form)
	os.system(windowS)

	# start mesukal probe before starting streaming client
	subprocess.Popen(["./MesukalProbe.py"])
	time.sleep(3)
	
	# start a client
	# istic.stream.fr
	client = "vlc --sout-stats-output=./log rtsp://localhost:8080/bbb.sdp --rtp-client-port=5004 &"
	os.system(client)
	
	time.sleep(1)
	windowC = "wmctrl -r bbb.sdp - Lecteur multimedia -e 1,800,600,480,320"
	os.system(windowC)

	

# Test for HR - High Resolution, HD720(1280x720), HD1080(1920x1080), Frame rate 30
# need to use MPEG TS over RTP for that case, 2 codec may be used H.264

elif case == 1 :
	# mode push using MPEG/TS
	
	server = "vlc -I dummy {} --sout=\"#duplicate{{dst=rtp{{dst=127.0.0.1,port=5004,mux=ts,sap,name=SER}},dst=display}}\" --sout-keep --loop &".format(out_video)

	os.system(server)

	time.sleep(1)

	windowS = "wmctrl -r Lecteur multimedia VLC -e 1,800,0,640,480"
	os.system(windowS)
	
	# start mesukal probe before starting streaming client
	subprocess.Popen(["./MesukalProbe.py"])
	time.sleep(3)

	# start a client
	client = "vlc rtp://127.0.0.1:5004 &"

	os.system(client)
	time.sleep(1)

	windowC = "wmctrl -r rtp://127.0.0.1:5004 - Lecteur multimedia VLC -e 1,800,600,640,480"
	os.system(windowC)


# HTTP YouTube stream
elif case == 2 :
	
	# start a client
	print("start youtube streaming")
	client = "vlc  {} &".format(out_video)
	print(client)
	os.system(client)
	time.sleep(10)

	windowL = "wmctrl -l > windowlist.txt"
	os.system(windowL)

	wins = open("windowlist.txt", "r")
	line = wins.readline()
	wname = "EMPTY"
	while line:
		line = wins.readline()
		if len(line.split("- Lecteur")) == 2:
			
			wname = line.split("- Lecteur")[0].split("N/A")[1]

	print("window name " + wname[1:20])

	windowC = "wmctrl -r {} -e 1,400,50,640,480".format(wname[1:20])
	os.system(windowC)

	os.system("rm -r windowlist.txt")



