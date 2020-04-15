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
								subprocess.call('./h264bitstream-0.2.0/h264_analyze sps.h264', shell=True,stdout =param)							
												
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

	pre.write("videoResolutionClass	HR\n")
	pre.write("ModelMode	CC\n")
	pre.write("pcapFileName	{}\n".format(sys.argv[2]))
	pre.write("transportFormat	MPEG2-TS/RTP/UDP/IP\n")
	pre.write("markerBit	N/A\n")
	
	pre.write("payloadUnitStartIndicator	START\n")

	pre.write("videoPLC	SLICING\n")
	
	

	udpoffset = 34
	rtpoffset = 42
	tsoffset  = 54

	cc = -1
	nts = 0
	tsfile = open("mpeg2.ts", "wb")
	
	pat = [0]*50
	pmt = [0]*50

	with  open(sys.argv[2], "rb") as pcap_file:
		header = pcap_file.read(24)

		while True:
			pkt = pcap_file.read(16)
		
			if not pkt:break

			b1 = bytearray(pkt[9])
			b2 = bytearray(pkt[8])
			lon = b1[0] << 8 | b2[0]

			data = pcap_file.read(lon)
			
			start = 0
			shift = 0
			next = 0
			cc += 1 

			if cc == 0:
				b1 = bytearray(data[udpoffset + 2])
				b2 = bytearray(data[udpoffset + 3])
				udpport = b1[0] << 8 | b2[0]
				pre.write("destPort	{}\n".format(udpport))
			
			while tsoffset + shift + next < lon:
				# read le sequence number du paquet TS
				if bytearray(data[tsoffset + shift + next])[0] == 0x47 and (next == 188 or start == 0):
					
					if cc == 0:
						PUSI = bytearray(data[tsoffset + shift + next+1])[0] & 0x40
						AF   = bytearray(data[tsoffset + shift + next+3])[0] & 0x30
						if AF == 0x30:
							
							if bytearray(data[tsoffset + shift + next+4])[0] > 0:
								RAI  = bytearray(data[tsoffset + shift + next+5])[0] & 0x40
								ESPI = bytearray(data[tsoffset + shift + next+5])[0] & 0x20

					start = 1
																	
					nts += 1
					shift += next
					next = 0											
					
				tsfile.write(data[tsoffset + shift + next])
				next += 1
	
	tsfile.close()

	pre.write("randomAccessIndicator	{}\n".format(RAI))
	pre.write("elementaryStreamPriority	{}\n".format(ESPI))

	nts = 0
	start = 0
	shift = 0
	
	fpat = 0
	fpmt = 0
	prog = 0xff
	mpeg2ts = open("mpeg2.ts", "r")
	while True:
		h0 = mpeg2ts.read(1)
		if not h0:break
		if bytearray(h0)[0] == 0x47 and (shift == 185 or start == 0):
			
			h1 = mpeg2ts.read(1)
			h2 = mpeg2ts.read(1)
			h3 = mpeg2ts.read(1)

			pid = (bytearray(h1)[0] << 8 | bytearray(h2)[0]) & 0x01fff

			nts += 1
			shift = 0
			start = 1

			if pid == 0x00 and fpat == 0:
			
				start = 0 
			
				AF = bytearray(h3)[0] & 0x30
				
				if AF == 0x30:
					aflen = mpeg2ts.read(1)
			
					for k in range(0, bytearray(aflen)[0]):
						stuffing = mpeg2ts.read(1)
			
					pr = mpeg2ts.read(1)

					for k in range(0, 184 - bytearray(aflen)[0] - 1 -1):  					
						pat[k] = mpeg2ts.read(1)

					prnb = bytearray(pat[8])[0] << 8 | bytearray(pat[9])[0]
					prog = (bytearray(pat[10])[0] << 8 | bytearray(pat[11])[0]) & 0x1fff
					fpat = 1

			if pid == prog and fpmt == 0:
				start = 0 
				AF = bytearray(h3)[0] & 0x30

				if AF == 0x30:
					aflen = mpeg2ts.read(1)
			
					for k in range(0, bytearray(aflen)[0]):
						stuffing = mpeg2ts.read(1)
			
					pr = mpeg2ts.read(1)

					for k in range(0, 184 - bytearray(aflen)[0] - 1 -1):  					
						pmt[k] = mpeg2ts.read(1)

					if bytearray(pmt[12])[0] == 0x1b:
						pre.write("videoCodec	H264\n")
					progpid = (bytearray(pmt[13])[0] << 8 | bytearray(pmt[14])[0]) & 0x1fff	
				fpmt = 1	

		shift += 1
	
	mpeg2ts.close()

	mpeg2ts = open("mpeg2.ts", "r")

	b4 = mpeg2ts.read(1)
	b3 = mpeg2ts.read(1)
	b2 = mpeg2ts.read(1)
	b1 = mpeg2ts.read(1)
	b0 = mpeg2ts.read(1)

	sps = 0
	pps = 0

	# create a sps/pps file
	h = open("sps.h264","wb")
	while True:
		
		if  bytearray(b4)[0] == 0x00 and bytearray(b3)[0] == 0x00 and bytearray(b2)[0] == 0x00 and bytearray(b1)[0] == 0x01:
			if bytearray(b0)[0] == 0x67 and sps == 0:
				
				#print "SPS", hex(bytearray(b0)[0]), sps
								
				h.write(b4)
				h.write(b3)
				h.write(b2)
				h.write(b1)
				h.write(b0)
				
				end = 0

				while end == 0:	
	
					b4 = b3 	
					b3 = b2 
					b2 = b1 
					b1 = b0 

					b0 = mpeg2ts.read(1)
					
					if bytearray(b4)[0] == 0x00 and bytearray(b3)[0] == 0x00 and bytearray(b2)[0] == 0x00 and bytearray(b1)[0] == 0x01:
						end = 1
					
					h.write(b0)
				sps = 1

			if bytearray(b0)[0] == 0x68 and pps == 0:
				#print "PPS", hex(bytearray(b0)[0]), pps
									
				end = 0

				while end == 0:		

					b4 = b3 	
					b3 = b2 
					b2 = b1 
					b1 = b0 

					b0 = mpeg2ts.read(1)
					
					if bytearray(b4)[0] == 0x00 and bytearray(b3)[0] == 0x00 and bytearray(b2)[0] == 0x00 and bytearray(b1)[0] == 0x01:
						end = 1
					else: 
						h.write(b0)
				pps = 1

		b4 = b3 	
		b3 = b2 
		b2 = b1 
		b1 = b0 		

		b0 = mpeg2ts.read(1)

		if not b0: break
		
	h.close()



	with open('h264parm.txt', "w") as param:
		subprocess.call('./h264bitstream-0.2.0/h264_analyze sps.h264', shell=True,stdout =param)							
												
	# handle h264param file
	param = open('h264parm.txt', "r") 
	data = param.readlines()
	for i in range(1,len(data)):
		prop = data[i].split(":")
		if len(prop) == 3:
			#print prop[1]
			if  prop[1] == ' sps->frame_mbs_only_flag':
				frame_mbs_only_flag = int(prop[2])
				if frame_mbs_only_flag == 1:
					pre.write("scanningType	Progressive\n")
			elif prop[1] == ' sps->pic_width_in_mbs_minus1':
				pic_width_in_mbs_minus1 = int(prop[2])	
			elif prop[1] == ' sps->frame_mbs_only_flag':
				frame_mbs_only_flag = int(prop[2]) 
			elif prop[1] == ' sps->pic_height_in_map_units_minus1':
				pic_height_in_map_units_minus1 = int(prop[2])
			elif prop[1] == ' sps->vui.num_units_in_tick':
				num_units_in_tick = int(prop[2])
			elif prop[1] == ' sps->vui.time_scale':
				time_scale = int(prop[2])
			elif prop[1].find('frame_mbs_only') > 0:
				print "scan: "				
				frame_mbs_only_flag = int(prop[2])
				if frame_mbs_only_flag == 1:
					pre.write("scanningType	Progressive\n")
			elif prop[1] == ' sps->profile_idc':
				profile_idc =  int(prop[2])
				if profile_idc == 100:
					pre.write("videoCodecProfile	High Profile\n")
			elif prop[1] == ' sps->level_idc':
				level_idc =  int(prop[2])/10.0
				pre.write("videoCodecLevel	{}\n".format(level_idc))
	

							
	height = (pic_width_in_mbs_minus1 + 1)*16
	width = ((2 - frame_mbs_only_flag)*(pic_height_in_map_units_minus1+1)*16)

	form = "N/A"
	if height==1280 and width==720:
		form = "HD720"
	elif height==1920 and width==1080:
		form = "HD1080"
								
	pre.write("videoResolution	{}\n".format(form))

	framerate = time_scale/(2 * num_units_in_tick)
	pre.write("videoFrameRate	{}\n".format(framerate))
	
					
	os.system("rm -f sps.h264")
	os.system("rm -f h264parm.txt")

	cmd = "ffmpeg -i mpeg2.ts -y -map 0 -c copy mpeg2.mp4"
	os.system(cmd)

	cmd = "ffmpeg -i mpeg2.mp4 -y -vcodec copy -bsf h264_mp4toannexb -an -f h264 mpeg2.h264"
	os.system(cmd)

	cmd ="./h264bitstream-0.2.0/h264_analyze mpeg2.h264 > mpeg2.txt"
	os.system(cmd)

	h264 = open("mpeg2.txt", "r")

	slc = []
	data = h264.readlines()

	nbslice = [0]*16

	nbs =0
	for i in range(0, len(data)):
		lig = data[i].split(":")
	
		if len(lig) > 2 and lig[1] == ' sh->frame_num':
			nbs += 1
			nbslice[int(lig[2])] += 1
	
		if len(lig) > 2 and lig[1] == ' sh->first_mb_in_slice':
			slc.append(int(lig[2]))
			
	numframe = 0
	numslc = 0
	for i in range(0, len(slc)):
		if slc[i] == 0:		
			numframe += 1 
		else:
			numslc += 1

	numslc = (numslc + numframe + 1)/numframe

	pre.write("videoNumberOfSlicesPerFrame	{}\n".format(numslc))

	os.system("rm -f mpeg2.mp4")
	os.system("rm -f mpeg2.h264")
	os.system("rm -f mpeg2.txt")

	
	 


