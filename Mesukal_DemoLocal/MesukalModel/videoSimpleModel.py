#!/usr/bin/python3

import math
import sys
import csv
import os.path

# generic and simple video model

index = sys.argv[1]
pcap_name = sys.argv[2]


MOS_MAX = 5.0
MOS_MIN = 1.0


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
			#print 'timestamp:', sn[nb], ",", ts[nb-1],  " : ", ts[nb], " diff: ", ts[nb] - ts[nb-1]
	

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

v_cr = 90000

if(ts[nb-1] > ts[0]):
	v_mt = (ts[nb-1] - ts[0] + v_tsm)/v_cr
else:
	v_mt = (ts[nb-1] + 4294967296 - ts[0] + v_tsm)/v_cr

print(v_tsm, "clock rate:", v_cr, "\ntvf:", v_nts, "\nv_mt: ", v_mt)

# ordered sequence number
for i in range(1, len(sn)):
	if sn[i] < sn[i-1]:
		print("Out-Of-Order :", i, sn[i])


tfv = 1

RB = [0]*2000
LB = [0]*2000
DB = [0]*2000
lostP = [0]*2000


RB[1] = v_received[0]

lostframes = 0

videoFrameRate = 30

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
		lostframes = int((ts[i] - ts[i-1])*videoFrameRate/v_cr - 1)

		#print "lost frame:", ts[i], ts[i-1], sn[i-1], sn[i], lostframes
		# case 1: lost packets belong to the same frames
		if lostframes == -1:
			#print ("entering case 1:")
			lostP[tfv] += lostpackets
			LB[tfv] += lostpackets*lostbytes
			
			# discarded packet
			DB[tfv] = v_received[i]

			while i < len(sn)-2 and ts[i] - ts[i+1] == 0 and sn[i+1]-sn[i]-1 == 0:
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


TLB = [0]*2000
TB = [0]*2000
PLR = [0.0]*2000

# Average Loss Rate
ALR = 0
for i in range(1, tfv+1):

	TLB[i] = LB[i] + DB[i]
	TB[i]  = RB[i] + TLB[i]
	PLR[i] = 1.0*TLB[i]/TB[i]
	ALR    =  ALR + PLR[i] 

ALR = 100.0 * ALR/tfv

print("average loss rate:", ALR)
# Test simple model (to do with number of lost frames instead)
SMOS = 4.9442 - 0.1642 * ALR

if SMOS < 0:
	SMOS = 1
elif SMOS > 5:
	SMOS = 5

csvfile = sys.argv[4]
with open(csvfile, mode='a') as mos_file:
	mos_writer = csv.writer(mos_file)
	
	mos_writer.writerow([str(index), str(SMOS)])


