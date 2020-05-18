#!/usr/bin/python

import math
import sys
import csv

index = sys.argv[1]
pcap_name = sys.argv[2]
pre_name = sys.argv[3]
csv_name = sys.argv[4]

pre_file = open(pre_name, "r")

class BasicAudioParam:
	def __init__(self):
		self.audioCodec = ""
		self.audioFrameLength = 0
		self.cr = 0

bap = BasicAudioParam()

for line in pre_file:	
	
	if line.split( )[0] == "audioCodec": 
		bap.audioCodec = line.split( )[1]
		
	elif line.split( )[0] == "audioFrameLength":
		bap.audioFrameLength = float(line.split( )[1])
		bap.cr= 1024*1000/float(line.split( )[1])
		
print("cr: ", bap.cr)
if bap.audioCodec == "AMRNB":
	bap.cr = 8000.0
elif bap.audioCodec == "AMRWB":
	bap.cr = 16000.0
elif bap.audioCodec == "AMRWBP":
	bap.cr = 72000.0
 

if bap.audioCodec == "AAC-LC":
	a1 = 3.36209
	a2 = 16.46062
	a3 = 2.08184
	a4 = 0.352
	a5 = 508.83419
	a6 = 37.78354
elif bap.audioCodec == "AMRNB":
	a1 = 1.33483
	a2 = 6.42499
	a3 = 3.49066
	a4 = 0
	a5 = 723.3661
	a6 = 1
elif bap.audioCodec == "AMRWBP":
	a1 = 3.19158
	a2 = 5.7193
	a3 = 1.63208
	a4 = 0
	a5 = 826.7936
	a6 = 1
elif bap.audioCodec == "AAC-HEv1":
	a1 = 3.19135
	a2 = 4.17393
	a3 = 1.28241
	a4 = 0.68955
	a5 = 6795.99773
	a6 = 186.766920
elif bap.audioCodec == "AAC-HEv2":
	a1 = 3.13637
	a2 = 7.45884
	a3 = 2.15819
	a4 = 0.61993
	a5 = 3918.639
	a6 = 153.3399




nb = 0
a_pllf = 0
a_tsm = 1000000
a_nts = 1
rtpoffset = 42
udpoffset = 34

ts = []
sn = []
a_pll = []
a_received = []
lostbytes = []

with  open(pcap_name, "rb") as pcap_file:
    
	header = pcap_file.read(24)

	while True:
		pkt = pcap_file.read(16)
		if not pkt:break
			
		b1 = bytearray(pkt[9])
		b2 = bytearray(pkt[8])

		lon = b1[0] << 8 | b2[0]
		
		#print("b1:", b1, "\tb2:", b2, "\tlon:", lon)

		data = pcap_file.read(lon)
		
		# longueur du datagramme UDP
		b1 = bytearray(data[udpoffset + 4])
		b2 = bytearray(data[udpoffset + 5])
		udplon = b1[0] << 8 | b2[0]
		#print "nb: ", nb, "longueur totale:", lon, "lenght UDP:", udplon


		# read le timestamp du paquet RTP			
		b1 = bytearray(data[rtpoffset + 4])
		b2 = bytearray(data[rtpoffset + 5])
		b3 = bytearray(data[rtpoffset + 6])
		b4 = bytearray(data[rtpoffset + 7])
		ts.append(b1[0] << 24 | b2[0] << 16 | b3[0] << 8 | b4[0])
		#print 'timestamp:', hex(ts[nb])

		if nb >= 1: 
			if a_tsm > ts[nb] - ts[nb-1] and ts[nb] - ts[nb-1]>0:
				a_tsm = ts[nb] - ts[nb-1]

			if ts[nb] > ts[nb-1]:
				a_nts = a_nts + 1

		# read le sequence number du paquet RTP
		b1 = bytearray(data[rtpoffset + 2])
		b2 = bytearray(data[rtpoffset + 3])
		sn.append(b1[0] << 8 | b2[0])
		#print 'seqeunce number:', hex(sn[nb])

		# compute length of each audio RTP paquet
		a_received.append(udplon - 20)
		#print "charge utile: ", udplon - 8 - 12

		if nb>=1 and sn[nb] > sn[nb-1] + 1:	
			a_pllf += 1
			a_pll.append(sn[nb] - sn[nb-1] - 1)
			
			missing = ((udplon - 20) + a_received[nb-1] + 1)/2

			for i in range(0, sn[nb] - sn[nb-1]-1):
				lostbytes.append(missing)

		# sequence number wrap-up
		elif sn[nb] - sn[nb-1] < 0:
			if sn[nb] + 65636 > sn[nb-1] + 1: 
				a_pllf = a_pllf + 1
				a_pll.append(sn[nb] - sn[nb-1] - 1)		

		nb += 1

 
if(ts[nb-1] > ts[0]):
	a_mt = (ts[nb-1] - ts[0] + a_tsm)/bap.cr
else:
	a_mt = (ts[nb-1] + 4294967296 - ts[0] + a_tsm)/bap.cr



lflpp = (1000*a_tsm)/bap.cr

nppts = nb/a_nts

sumrcv = 0
sumlost = 0
sumpll = 0

for i in range(0, len(a_received)):
	sumrcv += a_received[i]

for j in range(0, len(lostbytes)):
	sumlost += lostbytes[j]

for k in range(0, len(a_pll)):
	sumpll += a_pll[k]


a_br= ((8*0.001)/a_mt)*(sumrcv + sumlost)   

a_abpll = 0

if a_pllf != 0: 
	a_abpll =(1.0*sumpll)/a_pllf

a_lfl = a_pllf*max(bap.audioFrameLength,lflpp*(a_abpll+nppts-1/nppts))



ma = (1-a4)*math.exp(-(10*a_lfl)/(a5*a_mt)) + a4*math.exp(-(10*a_lfl)/(a6*a_mt))
a_mosc = 1 +(a1 - a1/(1+((a_br/a2)**a3)))
a_mos = 1 + (a_mosc - 1)*ma


print ("RP:",  nb )
print ("CR:", bap.cr)
print ("a_MT: ", a_mt)
print ("a_NTS: ", a_nts)
print ("a_plef: ", a_pllf)
print ("lflpp: ", lflpp)
print ("nppts: ", nppts)
print ("a_br: ", a_br)
print ("a_abpll: ", a_abpll)
print ("a_lfl: ", a_lfl)
print ("A_MOSC:", a_mosc)
print ("A_MOS:", a_mos)

with open(csv_name, mode='a') as mos_file:
	mos_writer = csv.writer(mos_file)
	mos_writer.writerow([str(index), str(a_mos)])

exit(1)