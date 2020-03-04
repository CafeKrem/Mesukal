#!/usr/bin/python

import os
import sys
import time
import base64
import binascii
import subprocess

pre ="touch config.pre"
os.system(pre)

rights = "chmod o+rw config.pre"
os.system(rights)

pre=open("config.pre", "w")

if sys.argv[1] == "LR":	

	pre.write("videoResolutionClass	LR\n")
	pre.write("modelMode	CC\n")
	pre.write("markerBit	END\n")
	pre.write("scanningType	PROGRESSIVE\n")
	

	sdp = open(sys.argv[2], "r")
	
	# extraire message RTSP et creation du fichier pre

	line = sdp.readline()
	while line:
		line = sdp.readline()
			
		if line != "\n":
			
			# detect a new media
			if  line.split("=")[0] == "m":
				media = line.split("=")[1]
				if media.split(" ")[0] == "video":

					pre.write("videoRTPPayloadType	{}".format(media.split(" ")[3]))
					pre.write("transportFormat		{}\n".format(media.split(" ")[2]))
					
					line = sdp.readline()

					while line.split("=")[0] != "m" and line !="\n":
						
						if line.split(":")[0] == "a=rtpmap": 

							pre.write("videoCodec	{}\n".format(line.split(" ")[1].split('/')[0]))
							pre.write("videoClockRate	{}".format(line.split(" ")[1].split('/')[1]))

						if line.split(":")[0] == "a=fmtp":

							# packetization mode 0 a single NALU sent in a single RTP
							# packetization mode 1 multiple NALU can be sent in decoding order
							# packetization mode 2 multiple NALU can be sent out of decoding order
							pre.write("videoPacketizationMode	{}\n".format(line.split(";")[0].split("mode=")[1]))

							pcklevelid = line.split(";")[1].split("=")[1]
																
							if pcklevelid[0:2] == "42":
								pre.write("videoCodecProfile	Baseline\n")								

							elif pcklevelid[0:2] == "4D" :
								pre.write("videoCodecProfile	Main\n")

							elif pcklevelid[0:2] == "58" :
								pre.write("videoCodecProfile	Extended\n")
							
							elif pcklevelid[0:2] == "64" :
								pre.write("videoCodecProfile	High\n")

							if pcklevelid[4:6] == "0A" : #level 1.0
								pre.write("videoLevel		1.0\n")
							
							elif pcklevelid[4:6] == "0B" : #level 1.1
								pre.write("videoLevel		1.1\n")

							elif pcklevelid[4:6] == "0C": #level 1.2
								pre.write("videoLevel		1.2\n")

							elif pcklevelid[4:6] == "0D": #level 1.3
								pre.write("videoLevel		1.3\n")

							elif pcklevelid[4:6] == "14" : #level 2.0
								pre.write("videoLevel		2.0\n")

							elif pcklevelid[4:6] == "15" : #level 2.1
								pre.write("videoLevel		2.1\n")

							# to get videoFrameRate and videoResolution need to decode for "sprop-parameter-sets"
							sps = line.split("sprop-parameter-sets=")[1].split(",")[0]
							pps = line.split("sprop-parameter-sets=")[1].split(",")[1].split(";")[0]
							
							#create a sps/pps nalu	
							bsps = binascii.a2b_base64(sps)
							bpps = binascii.a2b_base64(pps)

							nlu = binascii.unhexlify('00000001')
					
							h = open("sps.h264","wb")
							h.write(nlu) 
							h.write(bsps)
							h.write(nlu)
							h.write(bpps)
							h.write(nlu)
							h.close()

							with open('h264parm.txt', "w") as param:
								subprocess.call('./h264bitstream-0.2.0/h264_analyze sps.h264', shell=True,stdout = param)							
												
							# handle h264param file
							param = open('h264parm.txt', "r") 
							data = param.readlines()
							for i in range(1,len(data)):
								prop = data[i].split(":")
								if len(prop) == 3:
									#print prop
									if prop[1] == ' sps->pic_width_in_mbs_minus1':
										pic_width_in_mbs_minus1 = int(prop[2])	
									elif prop[1] == ' sps->frame_mbs_only_flag':
										frame_mbs_only_flag = int(prop[2]) 
									elif prop[1] == ' sps->pic_height_in_map_units_minus1':
										pic_height_in_map_units_minus1 = int(prop[2])
									elif prop[1] == ' sps->vui.num_units_in_tick':
										num_units_in_tick = int(prop[2])
									elif prop[1] == ' sps->vui.time_scale':
										time_scale = int(prop[2])

							
							height = (pic_width_in_mbs_minus1 + 1)*16
							width = ((2 - frame_mbs_only_flag)*(pic_height_in_map_units_minus1+1)*16)

							form = "N/A"
							if height==176 and width==144: 
								form = "QCIF"
							elif height==320 and width==240:
								form = "QVGA"
							elif height==480 and width==320:
								form = "HVGA"
							elif height==1280 and width==720:
								form = "HD720"
							elif height==1920 and width==1080:
								form = "HD1080"
								
							pre.write("videoResolution	{}\n".format(form))

							framerate = time_scale/(2 * num_units_in_tick)
							pre.write("videoFrameRate	{}\n".format(framerate))
							
							os.system("rm -f sps.h264")
							os.system("rm -f h264parm.txt")
	
							#print binascii.hexlify(bsps)	
						


						line = sdp.readline()			
			
			elif line.split(" ")[0] == "Transport:":
				
				if len(line.split(";")) > 3:
					pre.write("videoDestPort		{}\n".format(line.split("=")[2].split("-")[0]))


	

	
# handle config information of MPEG/TS
 
elif sys.argv[1] == "HR":
	print "handle MPEG TS"
	pre.write("videoResolutionClass	HR\n")

