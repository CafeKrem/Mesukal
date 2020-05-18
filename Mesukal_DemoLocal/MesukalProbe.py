#!/usr/bin/python3

import os
import sys
import csv
import time
import subprocess

import psutil

from scapy.utils import RawPcapReader
from scapy.all import RTP
from scapy.all import rdpcap


import numpy as np


fieldnames = ["x_value", "mos"]

with open('mos_file.csv', 'w') as csv_file:
	csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
	csv_writer.writeheader()


index = 1
start =0
vlc = "ON"
rtp_ssrc_list = []

while vlc == "ON":

	calltshark = ['tshark', '-i', 'lo', '-f', 'udp dst port 5004 or tcp port 8080', '-F', 'libpcap', '-w', 'raw.pcap']
	tsharkProc = subprocess.Popen(calltshark)
	
	time.sleep(10)
	tsharkProc.terminate()

	probe = "tshark -n -r {} -Y \"udp.dstport==5004\" -F libpcap -w rtp.pcap".format("raw.pcap")
	os.system(probe)

	# handle RTP config file
	pkts= rdpcap("rtp.pcap")
	rtp_pt = RTP(pkts[0]["Raw"].load).payload_type
	
	if rtp_pt == 96:
		mode = "LR"
		# dig RTSP exchange 
		probe = "tshark -n -r {} -Y \"http and tcp.port==8080 \" -w rtspconfig.pcap".format("raw.pcap")
		os.system(probe)
		
		extrasdp = "tshark -n -r {} -qz follow,tcp,ascii,0 > sdpdesc.txt".format("rtspconfig.pcap")
		os.system(extrasdp)

		size = os.path.getsize("sdpdesc.txt")

		if size > 201:
			print("An RTSP session is detected...")
			subprocess.call(["./MesukalSession.py", mode, "sdpdesc.txt"])
		
		os.system("rm -f sdpdesc.txt")
				
	elif rtp_pt == 33:
		mode = "HR"

		#call session dissector	MPEG TS verify if it is a new stream
		rtp_ssrc = RTP(pkts[0]["Raw"].load).sourcesync
		
		if len(rtp_ssrc_list) == 0:
		
			rtp_ssrc_list.append(rtp_ssrc)
			subprocess.call(["./MesukalSession.py", mode, "rtp.pcap"])
			
		elif rtp_ssrc not in rtp_ssrc_list:
			
			rtp_ssrc_list.append(rtp_ssrc)
			subprocess.call(["./MesukalSession.py", mode, "rtp.pcap"])
				
	
	vlc = "OFF"
	for process in psutil.process_iter():
		if process.name() == 'vlc':
			print("vlc is running...")
			vlc = "ON"
	
	if vlc == "ON":
		# start data collection process
		print("call quality model ...")	
		sample = time.strftime("%H:%M:%S", time.gmtime())	
		if mode == "LR":
			# call LR model to calculate MOS
			subprocess.call(["./MesukalModel/simple_type_video.py", sample, "rtp.pcap", "config.pre", "mos_file.csv"])		

		elif mode =="HR":
			# call HR model to calculate MOS
			subprocess.call(["./MesukalModel/video_Model_HernA.py", sample, "rtp.pcap", "config.pre", "mos_file.csv"])

			# call HR model to calculate MOS
			#subprocess.call(["./MesukalModel/video_Model_HernB.py", sample, "rtp.pcap", "config.pre", "mos_file.csv"])

			# call HR model to calculate MOS
			#subprocess.call(["./MesukalModel/video_Model_P12012.py", sample, "rtp.pcap", "config.pre", "mos_file.csv"])
			
		
		if start == 0:	
			print("start MOS Graph")	
			#start graphing process csv file and refresh parameter
			grap = subprocess.Popen(["./MesukalGraph/plot_mos_video.py", "mos_file.csv", "1000"])
			start = 1

	elif vlc == "OFF": 
		#print "kill graph plot process"
		grap.kill()
		exit(1)

