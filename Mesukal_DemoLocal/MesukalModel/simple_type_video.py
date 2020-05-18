#!/usr/bin/python3

import math
import os.path


trace = "10"

pre_name = "./P1201LR/vecteurs/P1201_LR_TV"+trace+".pre"

pre_file = open(pre_name, "r")

class BasicVideoParam:
	def __init__(self):
		self.videoCodec = ""
		self.videoResolution = ""
		self.videoFrameRate = 0.0
		self.videoPLC = ""
		self.videoRTPPayloadType=0
		self.videoDestPort=0

bvp = BasicVideoParam()

for line in pre_file:	
	
	if line.split( )[0] == "videoCodec": 
		bvp.videoCodec = line.split( )[1]
		
	elif line.split( )[0] == "videoResolution":
		bvp.videoResolution = line.split( )[1]
		
	elif line.split( )[0] == "videoFrameRate":
		bvp.videoFrameRate = float(line.split( )[1])

	elif line.split( )[0] == "videoPLC":
		bvp.videoPLC = line.split( )[1]

	elif line.split( )[0] == "videoRTPPayloadType":
		bvp.videoRTPPayloadType = line.split( )[1]

	elif line.split( )[0] == "videoDestPort":
		bvp.videoDestPort = line.split( )[1]

#print "video codec: ", bvp.videoCodec
#print "video resolution: ", bvp.videoResolution
#print "video frame rate: ", bvp.videoFrameRate
#print "video PLC: ", bvp.videoPLC
#print "video RTP payload type: ", bvp.videoRTPPayloadType
#print "video dest port: ", bvp.videoDestPort

MOS_MAX = 5.0
MOS_MIN = 1.0

# coefficients used to calculate quality degradation caused by compression
if bvp.videoCodec == "H264":
	if bvp.videoResolution == "QCIF":
		v1 = 3.4
		v2 = 0.969
		v3 = 104.0
		v4 = 1.0
		v5 = 0.01
		v6 = 1.1

	elif bvp.videoResolution == "QVGA":
		v1 = 2.49
		v2 = 0.7094
		v3 = 324.0
		v4 = 3.3
		v5 = 0.5
		v6 = 1.2

	elif bvp.videoResolution == "HVGA":
		v1 = 2.505
		v2 = 0.7144
		v3 = 170.0
		v4 = 130.0
		v5 = 0.05
		v6 = 1.1

elif bvp.videoCodec == "MPEG4":
	if bvp.videoResolution == "QCIF":
		v1 = 2.43
		v2 = 0.692
		v3 = 0.01
		v4 = 134.0
		v5 = 0.01
		v6 = 1.7

	elif bvp.videoResolution == "QVGA":
		v1 = 1.6184
		v2 = 0.4611
		v3 = 280.0
		v4 = 11.0
		v5 = 1.69
		v6 = 0.02

	elif bvp.videoResolution == "HVGA":
		v1 = 1.6184
		v2 = 0.4611
		v3 = 280.0
		v4 = 11.0
		v5 = 1.69
		v6 = 0.02

# coefficient to calculate degradation caused by packet loss 
if bvp.videoPLC == "SLICING":
	if bvp.videoCodec == "H264":
		if bvp.videoResolution == "QCIF":
			v7 = -0.63
			v8 = 1.4
			v9 = 0.01
			v10 = -14.4
			v11 = 19.0
			v12 = 1.04

		elif bvp.videoResolution == "QVGA":
			v7 = -0.64
			v8 = 0.81
			v9 = 0.4
			v10 = -9.0
			v11 = 11.5
			v12 = 0.4

		elif bvp.videoResolution == "HVGA":
			v7 = -0.05
			v8 = 0.42
			v9 = 0.72
			v10 = -3.3
			v11 = 7.0
			v12 = 0.49

	elif bvp.videoCodec == "MPEG4":
		if bvp.videoResolution == "QCIF":
			v7 = -0.01
			v8 = 0.99
			v9 = 0.34
			v10 = -0.1
			v11 = 15.5
			v12 = 0.66

		elif bvp.videoResolution == "QVGA":
			v7 = -0.01
			v8 = 0.76
			v9 = 0.39
			v10 = -0.01
			v11 = 10.0
			v12 = 0.86

		elif bvp.videoResolution == "HVGA":
			v7 = -0.01
			v8 = 0.76
			v9 = 0.39
			v10 = -0.01
			v11 = 10.0
			v12 = 0.86

elif bvp.videoPLC == "FREEZING":
	if bvp.videoCodec == "H264":
		if bvp.videoResolution == "QCIF":
			v7 = -0.115
			v8 = 0.25
			v9 = 2.05
			v10 = -0.7
			v11 = 1.5
			v12 = 0.45

		elif bvp.videoResolution == "QVGA":
			v7 = -0.05
			v8 = 0.53
			v9 = 0.6
			v10 = -0.1
			v11 = 11.5
			v12 = 0.01

		elif bvp.videoResolution == "HVGA":
			v7 = -0.05
			v8 = 0.32
			v9 = 0.24
			v10 = -0.1
			v11 = 1.0
			v12 = 1.16

	elif bvp.videoCodec == "MPEG4":
		if bvp.videoResolution == "QCIF":
			v7 = -0.115
			v8 = 0.25
			v9 = 2.05
			v10 = -0.7
			v11 = 1.5
			v12 = 0.45

		elif bvp.videoResolution == "QVGA":
			v7 = -0.01
			v8 = 0.53
			v9 = 0.6
			v10 = -0.1
			v11 = 11.5
			v12 = 0.01

		elif bvp.videoResolution == "HVGA":
			v7 = -0.05
			v8 = 0.32
			v9 = 0.24
			v10 = -0.1
			v11 = 1.0
			v12 = 1.16

rtpoffset = 42
udpoffset = 34

ts = []
sn = []
mb = []
v_received = []
lostbytes = []
a_pll = []
a_received = []
a_lostbytes = []

nb = 0
v_tsm = 1000000
v_nts = 1

a_pllf = 0
a_tsm = 1000000
a_nts = 1

pcap_name = "./P1201LR/vecteurs/P1201_LR_TV"+trace+".pcap"

with  open(pcap_name, "rb") as pcap_file:
	header = pcap_file.read(24)

	while True:
		pkt = pcap_file.read(16)
		
		if not pkt:break
			
		b1 = bytearray(pkt[9])
		b2 = bytearray(pkt[8])
		lon = b1[0] << 8 | b2[0]

		data = pcap_file.read(lon)
		
		# longueur du datagramme UDP
		b1 = bytearray(data[udpoffset + 4])
		b2 = bytearray(data[udpoffset + 5])
		udplon = b1[0] << 8 | b2[0]

		b1 = bytearray(data[udpoffset + 2])
		b2 = bytearray(data[udpoffset + 3])
		udpport = b1[0] << 8 | b2[0]

		#print "len:", lon, "lenght UDP:", udplon, "udp port:", udpport

		if nb == 0:
			port = udpport	
	
		if udpport == port:
			# read le sequence number du paquet RTP
			b1 = bytearray(data[rtpoffset + 2])
			b2 = bytearray(data[rtpoffset + 3])
			sn.append(b1[0] << 8 | b2[0])
			#print 'seqeunce number:', sn[nb]


			# read le timestamp du paquet RTP			
			b1 = bytearray(data[rtpoffset + 4])
			b2 = bytearray(data[rtpoffset + 5])
			b3 = bytearray(data[rtpoffset + 6])
			b4 = bytearray(data[rtpoffset + 7])
			ts.append(b1[0] << 24 | b2[0] << 16 | b3[0] << 8 | b4[0])
			#print 'timestamp:', ts[nb]
	

			# compute length of each audio/video RTP paquet
			v_received.append(udplon - 20)
			a_received.append(udplon - 20)
			#print "charge utile: ", udplon - 8 - 12
		

			# read MB
			b1 = bytearray(data[rtpoffset + 1])
			mb.append(b1[0] >> 7)
			#print 'mark bit:', mb[nb]


			if nb >= 1: 
				if v_tsm > ts[nb] - ts[nb-1] and ts[nb] - ts[nb-1]>0:
					v_tsm = ts[nb]-ts[nb-1]
				if ts[nb] > ts[nb-1]:
					v_nts = v_nts + 1
				
				if a_tsm > ts[nb] - ts[nb-1] and ts[nb] - ts[nb-1]>0:
					a_tsm = ts[nb] - ts[nb-1]

				if ts[nb] > ts[nb-1]:
					a_nts = a_nts + 1


			if nb>=1 and sn[nb] > sn[nb-1] + 1:	
				a_pllf += 1
				a_pll.append(sn[nb] - sn[nb-1] - 1)
			
				missing = ((udplon - 20) + a_received[nb-1] + 1)/2

				for i in range(0, sn[nb] - sn[nb-1]-1):
					a_lostbytes.append(missing)

			# sequence number wrap-up
			elif sn[nb] - sn[nb-1] < 0:
				if sn[nb] + 65636 > sn[nb-1] + 1: 
					a_pllf = a_pllf + 1
					a_pll.append(sn[nb] - sn[nb-1] - 1)	
			
			nb += 1

########
#v_tsm = 3000: traces 20 et 22
########

v_tsm = round(v_tsm/3000.0)*3000

v_cr = bvp.videoFrameRate*v_tsm

if(ts[nb-1] > ts[0]):
	v_mt = (ts[nb-1] - ts[0] + v_tsm)/v_cr
else:
	v_mt = (ts[nb-1] + 4294967296 - ts[0] + v_tsm)/v_cr

#print (v_tsm, "clock rate:", v_cr, "\ntvf:", v_nts, "\nv_mt: ", v_mt)

# ordered sequence number
for i in range(1, len(sn)):
	if sn[i] < sn[i-1]:
		print ("Out-Of-Order :", i, sn[i])


tfv = 1

RB = [0]*500
LB = [0]*500
DB = [0]*500
lostP = [0]*500


RB[1] = v_received[0]

lostframes = 0



mysnb =  iter(range(1, len(sn)))
for i in mysnb:		
	
	# compute lost packet lenght
	if sn[i] > sn[i-1]:
		lostpackets = sn[i]-sn[i-1]-1
	else:
		lostpackets = sn[i] + 65536 - sn[i-1] - 1
	
	
	if lostpackets == 0:
		# is it a new video frame
		if ts[i] - ts[i-1] != 0 and mb[i-1] == 1:
			tfv += 1			
			RB[tfv] = v_received[i]
			
		else:
			RB[tfv] += v_received[i] 
	# handle a loss sequence of packets	
	else:
		lostbytes =  (v_received[i] + v_received[i-1] + 1)/2
		lostframes = int((ts[i] - ts[i-1])*bvp.videoFrameRate/v_cr - 1)

		# case 1: lost packets belong to the same frames
		if lostframes == -1:
			#print ("entering case 1:")
			lostP[tfv] += lostpackets
			LB[tfv] += lostpackets*lostbytes
			
			# discarded packet
			DB[tfv] = v_received[i]
			while ts[i] - ts[i+1] == 0 and sn[i+1]-sn[i]-1 == 0:
				next(mysnb, None)
				i += 1
				DB[tfv] += v_received[i]

		# case 2: last packet of the last frame is received
		elif lostframes == 0 and mb[i-1] == 1:
			#print ("entering case 2:")
			tfv += 1
			lostP[tfv] = lostpackets
			LB[tfv] = lostpackets*lostbytes

			# discarded packet
			DB[tfv] = v_received[i]
			while ts[i]-ts[i+1] == 0 and sn[i+1]-sn[i]-1 == 0:
				next(mysnb, None)
				i += 1
				DB[tfv] += v_received[i]

		# case 3:
		elif lostframes == 0:
			#print ("entering case 3:")
			
			lostP[tfv] += lostpackets/2 + lostpackets%2
			LB[tfv] += (lostpackets/2 + lostpackets%2) *lostbytes

			tfv += 1			
			lostP[tfv] = lostpackets/2
			LB[tfv] = (lostpackets/2)*lostbytes

			if lostP[tfv] == 0:
				RB[tfv] = v_received[i]
			else:
				DB[tfv] = v_received[i]
				while ts[i]-ts[i+1] == 0 and sn[i+1]-sn[i]-1 == 0:
					next(mysnb, None)
					i += 1
					DB[tfv] += v_received[i]

				

			
		# case 4:
		elif lostframes >= 1 and mb[i-1] == 1:
			#print ("entering case 4:")
			
			for k in range(tfv + 1, tfv+lostframes+1):
					lostP[k] = lostpackets/lostframes
					LB[k] = lostP[k] *lostbytes
					
			tfv += lostframes + 1
			lostP[tfv] = lostpackets%lostframes
			LB[tfv] = (lostpackets%lostframes) *lostbytes

			if lostP[tfv] == 0:
				RB[tfv] = v_received[i]
			else:
				DB[tfv] = v_received[i]
				while ts[i]-ts[i+1] == 0 and sn[i+1]-sn[i]-1 == 0:
					next(mysnb, None)
					i += 1
					DB[tfv] += v_received[i]	
			
		# case 5
		elif lostframes >= 1:
			#print ("entering case 5:")

			lostP[tfv] = 1

			for k in range(tfv+1, tfv+lostframes+1):
					lostP[k] = (lostpackets-1)/lostframes
					LB[k] = lostP[k] *lostbytes

			tfv += lostframes + 1

			lostP[tfv] = (lostpackets - 1)%lostframes
			LB[tfv] = lostP[tfv] *lostbytes

			if lostP[tfv] == 0:
				RB[tfv] = v_received[i]
			else:
				DB[tfv] = v_received[i]
				while ts[i]-ts[i+1] == 0 and sn[i+1]-sn[i]-1 == 0:
					next(mysnb, None)
					i += 1
					DB[tfv] += v_received[i]	


TLB = [0]*500
TB = [0]*500
PLR = [0.0]*500

for i in range(1, tfv+1):

	TLB[i] = LB[i] + DB[i]
	TB[i]  = RB[i] + TLB[i]
	PLR[i] = 1.0*TLB[i]/TB[i]

# detection de frame I

t_frame_size = 0
t_1_frame_size = 0
t_2_frame_size = 0

FG = [0]*500
FT = [0]*500
IThersh = [0]*500

NIF = 0
NBF = 0
NPF = 0
FDI = 0
TIFB = 0

NLI = 0
NLP = 0
NLB = 0

for i in range(1, tfv+1):
	if i == 1:
		t_frame_size = TB[i]
		t_1_frame_size = t_frame_size
		t_2_frame_size = t_1_frame_size
		
	elif i == 2:
		t_frame_size = TB[i]
		t_1_frame_size = TB[i-1]
		t_2_frame_size = t_1_frame_size
	else: 
		t_frame_size = TB[i]
		t_1_frame_size = TB[i-1]
		t_2_frame_size = TB[i-2]
		
	# compute difference in size
	if i == 1:
		FG[i] = int(t_frame_size*2.0/3.0)
	else:	
		FG[i] = abs(t_frame_size - t_1_frame_size)	

	# compute the threshold
	if i == 1:
		IThersh[i] = FG[i]
	else:
		if FT[i-2] == 1:
			FDI = 2
			IThersh[i] = int(t_2_frame_size*2.0/3.0)
		else:
			if FDI <= bvp.videoFrameRate:
				IThersh[i] = int(IThersh[i-1]*0.985)
				FDI += 1
	
			else:
				IThersh[i] = int(max(IThersh[i-1]*0.995, 500))
				FDI += 1
	# module de sortie
	if i == 1:
		print ("nothing", i)
	else:
		
		if FG[i] > IThersh[i] and FG[i-1] > IThersh[i] and (1.0*t_1_frame_size/t_2_frame_size > 1.5 or 1.0*t_1_frame_size/t_frame_size > 1.5):
			FT[i-1] = 1
			NIF += 1
			TIFB += t_1_frame_size
		else:
			if i-1 == 1:
				FT[i-1] = 1
				NIF += 1
				TIFB += t_1_frame_size
			
			if t_1_frame_size > 2000:
				NPF += 1
				FT[i] = 2
				
			else:
				NBF += 1
				
	# last frame	
	if i == tfv:
		ABIF = 1.0*TIFB/NIF
		#print TIFB, NIF 
		if t_frame_size/ABIF > 0.75:
			FT[i] = 1
			NIF += 1
			TIFB += t_frame_size
			ABIF = 1.0*TIFB/NIF
	
IRpF = [0]*500
NDF = 0
IR = 0

for i in range(1, tfv+1):
	if FT[i] == 1:
		IRpF[i] = PLR[i]
	else:
		IRpF[i] = max(IRpF[i-1], PLR[i])

	#print "frame number: ", i, "IR:", IRpF[i], "PLR:", PLR[i], "frame type:", FT[i]
	if IRpF[i] > 0:
		NDF += 1
		IR += IRpF[i]
		

#print "somme IR:", IR

for i in range(1, tfv+1):
	if FT[i] == 1:
		if IRpF[i] > 0:
			NLI += 1
	elif FT[i] == 2:
		if IRpF[i] > 0:
			NLP += 1
	else:
		if IRpF[i] > 0:
			NLB += 1
	#print "frame number: ", i, "loss rate:", PLR[i], "frame type:", FT[i]

if NIF > 0: 
	NLI = 1.0*NLI/NIF
if NLP > 0:
	NLP = 1.0*NLP/NPF
if NLB > 0:
	NLB = 1.0*NLB/NBF

#print (tfv)

print "number of I-Frames: ", NIF, "\nnumber of P-Frames: ", NPF, "\nnumber of B-Frames: ", NBF
print "ILR: ", NLI, "\nPLR: ", NLP, "\nBLR: ", NLB


MOS = 4.9437 - 17.5488*NLI - 0.8657*NLB + 1.6701*NLP 

print "Account for image type:", MOS






