#!/usr/bin/python3

import math
import os.path
import sys
import csv

index = sys.argv[1]
pcap_name = sys.argv[2]
pre_name = sys.argv[3]
csv_name = sys.argv[4]

buf_name = ""

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


print ("video codec: ", bvp.videoCodec)
print ("video resolution: ", bvp.videoResolution)
print ("video frame rate: ", bvp.videoFrameRate)
print ("video PLC: ", bvp.videoPLC)
print ("video RTP payload type: ", bvp.videoRTPPayloadType)
print ("video dest port: ", bvp.videoDestPort)


rtpoffset = 42
udpoffset = 34

ts = []
sn = []
mb = []
v_received = []
lostbytes = []

nb = 0
v_tsm = 1000000
v_nts = 1


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
	

			# compute length of each audio RTP paquet
			v_received.append(udplon - 20)
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

print (v_tsm, "clock rate:", v_cr, "\ntvf:", v_nts, "\nv_mt: ", v_mt)

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
			print ("entering case 1:")
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
			print ("entering case 2:")
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
			print ("entering case 3:")
			
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
			print ("entering case 4:")
			
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
			print ("entering case 5:")

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
FDI = 0
TIFB = 0

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
		

print ("somme IR:", IR)
#for i in range(1, tfv+1):
#	print "frame number: ", i, "loss rate:", PLR[i], "frame type:", FT[i]

print (tfv)

print ("number of I-Frames: ", NIF, "\nTIFB:", TIFB, "\nAIBF:", ABIF, "\nNDF:", NDF)

# compute BR et NBR
BR = 0
for i in range(1, tfv+1):
	BR += TB[i]

BR = 1.0*BR/v_mt
NBR = (8*30.0*BR)/(1000*min(30, bvp.videoFrameRate))

# compute CCF
CCF = 0.5
if ABIF > 0:
	CCF = min(math.sqrt(BR/(ABIF*15)), 1.0)


# compute AIRF et ratio of Impaired images 
if NDF == 0:
	AIRF = 0.0
else:
	AIRF = IR/NDF

IRatio = 1.0*NDF/tfv

# compute PELF

FREEZ = 0
PLEF = 0

if bvp.videoPLC == "SLICING":
	for i in range(1, tfv + 1):
		if PLR[i] > 0.0:
			PLEF += 1

elif bvp.videoPLC == "FREEZING":
	for i in range(1, tfv + 1):
		if FREEZ == 1:
			if FT[i] == 1 and PLR[i] == 0.0:
				FREEZ = 0
		else:
			if PLR[i] > 0.0:
				PLEF += 1
				FREEZ = 1

print ("bit rate:", BR, "\nNormlized bitrate: ", NBR, "\nAIRF", AIRF, "\nIR ratio:", IRatio, "\nCCF:", CCF, "\nPLEF:", PLEF )


MOS_MAX = 5.0
MOS_MIN = 1.0

# compute MOSC --> quality degradation caused by compression
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

DC = (MOS_MAX-MOS_MIN)/(1 + math.pow(NBR/(v3*CCF + v4), v5*CCF + v6))

if bvp.videoFrameRate >= 24:
	MOSC = MOS_MAX - DC
else:
	print ("herer")
	MOSC =(MOS_MAX-DC)*(1+v1*CCF-v2*CCF*math.log(1000/bvp.videoFrameRate))


print ("DC", DC, "\nMOSC:", MOSC)

# compute MOSP --> MOS caused by packet loss 
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

DP = 0.0

if bvp.videoPLC == "SLICING":

	DP = (MOSC-MOS_MIN)*pow((AIRF*IRatio)/(v7*CCF+v8), v9) *pow(PLEF/(v10*CCF+v11), v12)/(1+pow((AIRF*IRatio)/(v7*CCF+v8), v9) * pow(PLEF/(v10*CCF+v11), v12))


elif  bvp.videoPLC == "FREEZING":
	print ("FREEZING")
	DP = (MOSC-MOS_MIN)*pow(IRatio/(v7*CCF+v8), v9)*pow(PLEF/(v10*CCF+v11), v12)/(1+pow(IRatio/(v7*CCF+v8), v9)*pow(PLEF/(v10*CCF+v11), v12))

MOSP = MOSC - DP

print ("DP:", DP, "\nMOSP:", MOSP)

#buf_name = "./vecteurs/P1201_LR_TV"+trace+".buf"

if os.path.isfile(buf_name):

	buf = open(buf_name)

	NRE = 0
	ARL = 0
	MREEF = 0
	for line in buf:		
		NRE += 1
		ARL += float(line.split( )[1])
		if NRE > 1:
			MREEF +=  float(line.split( )[0]) - (last_start + last_length)
		last_start = float(line.split( )[0])
		last_length = float(line.split( )[1])
		
	ARL = ARL/NRE

	VideoQual = 0
	if NRE == 1:
		if bvp.videoResolution == "QCIF":
			v13 = 1.0
			v14 = 0.0
			v15 = 9.8
			v16 = 0.85
			v17 = 1.0
			v18 = 0.0

		elif bvp.videoResolution == "QVGA":
			v13 = 1.0
			v14 = 0.0
			v15 = 20.6
			v16 = 0.37
			v17 = 1.0
			v18 = 0.0

		elif bvp.videoResolution == "HVGA":
			v13 = 1.0
			v14 = 0.0
			v15 = 52.0
			v16 = 0.42
			v17 = 1.0
			v18 = 0.0
	elif NRE > 1:
		MREEF = MREEF/(NRE -1)
		if bvp.videoResolution == "QCIF":
			
			v13 = 2.5
			v14 = 1.1
			v15 = 2.5
			v16 = 0.15
			v17 = 4.65
			v18 = 0.35

		elif bvp.videoResolution == "QVGA":
			v13 = 2.1
			v14 = 1.8
			v15 = 2.7
			v16 = 0.55
			v17 = 7.6
			v18 = 0.05

		elif bvp.videoResolution == "HVGA":
			v13 = 3.4
			v14 = 0.79
			v15 = 3.71
			v16 = 0.39
			v17 = 7.25
			v18 = 0.1

	if NRE > 0 and IRatio > 0:
		VideoQual = MOSP
	elif NRE > 0 and IRatio == 0:
		VideoQual = MOSC
	
	print ("Video Quality:", VideoQual )
	DR = (VideoQual-MOS_MIN)*pow(NRE/v13,v14)*pow(ARL/v15, v16)*pow(MREEF/v17, v18)/(1+pow(NRE/v13,v14)*pow(ARL/v15,v16)*pow(MREEF/v17,v18))
	MOSR = VideoQual - DR

else:
	NRE = 0
	ARL = 0
	MREEF = 0

	MOSR = 0
	DR = 0

print ("NRE:", NRE, "ARL:", ARL, "MREEF:", MREEF, "DR:", DR, "MOSR:", MOSR)

if IRatio == 0 and NRE == 0:
	MOS = MOSC
elif IRatio >= 0 and NRE == 0:
	MOS = MOSP
elif IRatio == 0 and NRE > 0: 
	MOS = MOSR
else:
	MOS = MOSR

print ("MOS:", MOS)

with open(csv_name, mode='a') as mos_file:
	mos_writer = csv.writer(mos_file)
	mos_writer.writerow([str(index), str(MOS)])

exit(1)

