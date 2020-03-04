
#define _CRT_SECURE_NO_WARNINGS

#include "globalInfo.h"


int media[] = {2, 0, 0, 1, 1, 2, 2, 2, 2, 2,\
	           2, 2, 2, 2, 2, 1, 0, 1, 2, 2,\
			   2, 2, 2, 2, 2, 2, 2, 0, 1, 2,\
			   2, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2};

// initialisation function
void init(globalInfo *gi, const char *pcap) {
	// intialisation of video part
	gi->vd.frameRate = 50;
	strcpy(gi->vd.concealmentType, "FREEZING");
	strcpy(gi->vd.resolution, "HD720");
	gi->vd.numSlices = 1;
	strcpy(gi->vd.isInterlaced, "PROGRESSIVE");
	// initialisation of audio parts
	gi->ad.sampleRate = 48000;

	gi->isTS = 1;
	gi->ts_level_enc = 0;
}


int rtp_nbkt(const char *pcap, globalInfo gi){
	
	FILE *fip = fopen(pcap, "rb");
	
	long wh[4];
	int k, pos = WS_H, nbkt = 0;
	unsigned char *pkt, value, udp[8];

	udp_info en_udp;
	
	while (!feof(fip) ) {
	  // point at the start of next media packet in the pcap file  
	  fseek(fip, pos, SEEK_SET);
	  fread(wh, sizeof(wh), 1, fip);

	  pkt = (unsigned char*)malloc(wh[2]*sizeof(unsigned char));
	
	  // read UDP header
	  k = 0;
	  while(k < ETH_H + IP_H) { fread(&value, 1, 1, fip); k++;}
	  for(k = 0; k < 8; k++) {
		fread(&value, 1, 1, fip); udp[k] = value;
	  }
	
	  en_udp = udp_header_decode(udp);	
	  if(gi.ad.dport == en_udp.dport || gi.vd.dport == en_udp.dport) {
		  nbkt++;
	  }
	  pos += wh[2] + WS_FH; 
		
    }

	fclose(fip);
	return(nbkt);
}



int search1(psi ps, unsigned int val){
    int i = 0;
	while (ps.pmtPID[i] != val && i < ps.n_PMT_PID) {i++;}			
	if(i == ps.n_PMT_PID) { return -1; } else { return i;}
}


int search2(pmt ts, unsigned int val) {

	int i = 0;
	while (ts.str[i].elementrery_PID != val && i < ts.nb_stream) { i++; }	
	if(i == ts.nb_stream) { return -1; } else { return i;}
}


unsigned __int64 combine (unsigned int lo, unsigned int hi) {

	// try the following line instead
    return ( (unsigned __int64)hi << 32) | lo;
}

double arrival(unsigned int sec, unsigned int usec) {
	     
	char tmp[40], tmp1[20], tmp2[20]; *tmp = NULL;
	double ctime;
	sprintf(tmp1,"%d",sec); 
	sprintf(tmp2,"%d",usec);
	strcpy(tmp, tmp1); 
	strcat(tmp, "."); 
	strcat(tmp, tmp2);
	ctime = strtod(tmp, NULL);
		 
	return(ctime);
}


udp_info udp_header_decode(unsigned char *udp) {

	udp_info udp_en;
	udp_en.sport = udp[0] << 8 | udp[1];
	udp_en.dport = udp[2] << 8 | udp[3];
	udp_en.len = udp[4] << 8 | udp[5];
	return(udp_en);
}

void udp_display(udp_info udp_en) {
	printf(" source port	|%ld\n", udp_en.sport);
	printf(" desination port	|%ld\n",  udp_en.dport);
	printf(" packet length	| %ld\n", udp_en.len);
}


rtp_info rtp_header_decode(unsigned char *rtp) {

	rtp_info rtp_en;

	rtp_en.seq = rtp[2] << 8 | rtp[3];
	rtp_en.ts =  rtp[4] << 24 | rtp[5] << 16 | rtp[6] << 8 | rtp[7];

	return(rtp_en);

}

void rtp_display(rtp_info rtp_en) {
	printf("sequence number		|%ld\n" , rtp_en.seq);
	printf("timestamp		|%lu\n" , rtp_en.ts);
}


ts_header ts_header_decode(unsigned char ts_raw_entete[4])
{
	ts_header ts_en;
	
	/* printf("PID --> %x:%x:%x:%x\n", ts_raw_entete[0], ts_raw_entete[1],ts_raw_entete[2], ts_raw_entete[3]);*/

	// extract TS (transport stream) information 
	ts_en.sync_byte = ts_raw_entete[0];
	ts_en.transport_error_indicator = (ts_raw_entete[1] & 0x80) >> 7;
	ts_en.payload_start_indicator = (ts_raw_entete[1] & 0x40) >> 6;
	ts_en.transport_priority = (ts_raw_entete[1] & 0x20) >> 5;
	ts_en.PID = ((ts_raw_entete[1] & 31) << 8) | ts_raw_entete[2];
	ts_en.transport_scrambling_control = (ts_raw_entete[3] & 0xC0);
	ts_en.adaption_field_control = (ts_raw_entete[3] & 0x30) >> 4;
	ts_en.continuity_counter = (ts_raw_entete[3] & 0xF);
	
	return(ts_en);
}

void ts_header_display (ts_header ts_en) {
	
	printf("PID			| %x\n",ts_en.PID);		       
	printf("CC			| %x\n", ts_en.continuity_counter);
	printf("payload start indicator	| %x\n", ts_en.payload_start_indicator);
	printf("adaptation field	| %x\n", ts_en.adaption_field_control);
	printf("TS payload size		| %ld\n", ts_en.paylen);
	printf("TS stuffing size	| %ld\n", ts_en.stuffing);
	printf("TS random access	| %ld\n", ts_en.random_access);

	if(ts_en.pcr == 1) { 
		printf("***The clock rate is found in adaptation field***\n"); 
	}

}


psi pat_decode(unsigned char *pat, int n) {

	psi clt;
	clt.n_NIT_PID = 0; clt.n_PMT_PID = 0;

	unsigned short a, b;

	clt.tabID = pat[0];
	a = (unsigned short )pat[1] << 8 | pat[2];	
	clt.section_syntax_indicator = (a & 0x8000) >> 15;
    clt.section_length = a & 0x0fff;

	a = (unsigned short )pat[3] << 8 | pat[4];
	clt.stream_id = a;

	clt.version = (pat[5] & 0x2e) >> 1;
	clt.current_next_indicator = pat[5] & 0x01;
	clt.section_number = pat[6];
	clt.section_last_number = pat[7];

	int N  = (n - 12)/4; clt.nb_PID = N;
	int init = 8;
	while(N > 0) {
	    a = (unsigned short )pat[init] << 8 | pat[init + 1];	    
	    b = (unsigned short )pat[init + 2] << 8 | pat[init + 3];

	 	if(a == 0) {			  
			 clt.nitPID[clt.n_NIT_PID] = b & (0x1fff); clt.n_NIT_PID++;
	    } else {		    
			 clt.pmtPID[clt.n_PMT_PID] = b & (0x1fff); clt.n_PMT_PID++;
	    }
		N--; init += 4;
	}

	return(clt);
}

void pat_display(psi clt) {

	int i;

	printf("******************************decode PAT table**\n");
	printf("table ID			| %x\n", clt.tabID);
	printf("section syntax indicator	| %x\n", clt.section_syntax_indicator);
	printf("section length			| %ld\n", clt.section_length);
	printf("transport stream id 		| %x\n", clt.stream_id);
	printf("version number			| %d\n", clt.version);
	printf("current next indicator		| %x\n", clt.current_next_indicator);
	printf("section number			| %x\n", clt.section_number);
	printf("section last number		| %x\n", clt.section_last_number);
	printf("PSI table number		| %ld\n", clt.nb_PID);

	for(i = 0; i < clt.n_NIT_PID; i++) {
		  printf("PID of NIT table	| %x\n", clt.nitPID[i]);
	}
	
	for(i = 0; i < clt.n_PMT_PID; i++) {
		  printf("PID of PMT table	| %x\n", clt.pmtPID[i]);
	}
}

pmt pmt_decode(unsigned char *tabpmt, int n) {

	unsigned a;
	int init, k;
	pmt pm;	

	pm.tabID = tabpmt[0];

	a = (unsigned short )tabpmt[1] << 8 | tabpmt[2];
	pm.section_syntax_indicator = (a & 0x8000) >> 15;
	pm.section_length = a & 0x0fff;

	a = (unsigned short )tabpmt[3] << 8 | tabpmt[4];
	pm.program_number = a;

	pm.version = (tabpmt[5] & 0x2e) >> 1;
	pm.current_next_indicator = tabpmt[5] & 0x01;
	pm.section_number = tabpmt[6];
	pm.section_last_number = tabpmt[7];

	a = (unsigned short )tabpmt[8] << 8 | tabpmt[9];
	pm.PCR_PID = a & 0x1fff;
	
	a = (unsigned short )tabpmt[10] << 8 | tabpmt[11];
	pm.program_info_length = a & 0x0fff;

	init = 12 + pm.program_info_length;
	k = 0;

	int N = n - init - 4;	
	
	while(N > 0) {
	   
	  pm.str[k].stream_type = tabpmt[init];
	  ++init; N -= 1;
	  
	  a = (unsigned short )tabpmt[init] << 8 | tabpmt[init+1]; 
	  ++init; ++init; N -= 2;
	 
	  pm.str[k].elementrery_PID = a & 0x1fff;
	 
	  a = (unsigned short )tabpmt[init] << 8 | tabpmt[init+1];
	  pm.str[k].ES_info_length = a & 0x0fff;

	  ++init; ++init; N -= 2;
	 	  
	  init += a & 0x0fff; N -= a & 0x0fff; k++;
	}

	pm.nb_stream = k; 

	return(pm);
}


void pmt_display(pmt pm) {

	int i;
	
	printf("******************************decode PMT table**\n");
	printf("table ID			| %x\n", pm.tabID);
	printf("section syntax indicator	| %x\n", pm.section_syntax_indicator);
	printf("section length			| %ld\n", pm.section_length);
	printf("program number			| %x\n", pm.program_number);
	printf("version number			| %d\n", pm.version);
	printf("current next indicator		| %x\n", pm.current_next_indicator);
	printf("section number			| %x\n", pm.section_number);
	printf("section last number		| %x\n", pm.section_last_number);
	printf("PCR_PID				| %x\n", pm.PCR_PID);
	printf("program info length		| %x\n", pm.program_info_length);

	printf("stream numbers			| %ld\n", pm.nb_stream);

	for(i = 0; i < pm.nb_stream; i++) {
	   printf("stream type		| %x\n", pm.str[i].stream_type);
	   printf("elementary PID stream	| %x\n", pm.str[i].elementrery_PID);
	   printf("ES_info_Length		| %x\n", pm.str[i].ES_info_length);
	}

}

pes_header pes_decode(unsigned char *pes, int n) {
    
	pes_header en_pes; en_pes.dts = 0; en_pes.pts = 0;
	unsigned int v1, v2, a1 = 0x00000000;
	unsigned __int64 v;		
	unsigned short a2 = 0x0000, b2 = 0x0000;

	/* printf("***A normal TS packet***\n");*/  

	a1 = (pes[0] << 16) | (pes[1] << 8) | pes[2];
	
	en_pes.sync_byte = a1;
	en_pes.stream_id = pes[3];

	a2 = (pes[4] << 8) | pes[5];
	en_pes.pes_pkt_len = a2;
	
    en_pes.ptsdtsFlags = (pes[7] & 0xc0) >> 6;
	
	if((pes[7] & 0xc0) >> 6 == 2) {
	   
		a2 = (pes[10] << 8) | pes[11];
		b2 = (pes[12] << 8) | pes[13];

		v1 = a2 << 16 | b2;
		v2 = unsigned int(pes[9] & 0x0f); 
		v = combine(v1, v2);

		en_pes.pts = 0;
        en_pes.pts |= (v >> 3) & (0x0007 << 30); // top 3 bits, shifted left by 3, other bits zeroed out
		en_pes.pts |= (v >> 2) & (0x7fff << 15); // middle 15 bits
        en_pes.pts |= (v >> 1) & (0x7fff <<  0); // bottom 15 bits
        // pts now has correct timestamp without markers in lowest 33 bits
	
	} else if ((pes[7] & 0xc0) >> 6 == 3) {
		  
		  a2 = (pes[10] << 8) | pes[11];
		  b2 = (pes[12] << 8) | pes[13];

		  v1 = a2 << 16 | b2;
		  v2 = unsigned int(pes[9] & 0x0f); 
		  v = combine(v1, v2);

		  en_pes.pts = 0;
		  en_pes.pts |= (v >> 3) & (0x0007 << 30); // top 3 bits, shifted left by 3, other bits zeroed out
		  en_pes.pts |= (v >> 2) & (0x7fff << 15); // middle 15 bits
          en_pes.pts |= (v >> 1) & (0x7fff <<  0); // bottom 15 bits
          // pts now has correct timestamp without markers in lowest 33 bits
		 		  		  
		  a2 = (pes[15] << 8) | pes[16];
		  b2 = (pes[17] << 8) | pes[18];

		  v1 = a2 << 16 | b2;
		  v2 =  unsigned int(pes[14] & 0x0f); 
		  v = combine(v1, v2);

		  en_pes.dts = 0;
          en_pes.dts |= (v >> 3) & (0x0007 << 30); // top 3 bits, shifted left by 3, other bits zeroed out
		  en_pes.dts |= (v >> 2) & (0x7fff << 15); // middle 15 bits
          en_pes.dts |= (v >> 1) & (0x7fff <<  0); // bottom 15 bits
         // pts now has correct timestamp without markers in lowest 33 bits
	  
  }		 
	return(en_pes);
}

void pes_display(pes_header en_pes) {

	printf("	sync PES byte		| %x\n", en_pes.sync_byte);
	printf("	stream id		| %x\n", en_pes.stream_id);
	printf("	PES packet lenght	| %x\n", en_pes.pes_pkt_len);
	printf("	PTS/DTS flag		| %x\n", en_pes.ptsdtsFlags);
	printf("	PTS value		| %" PRIx64 "\n", en_pes.pts);
	printf("	DTS value		| %" PRIx64 "\n", en_pes.dts);	
}

/* elementery stream flags */
void esflags(globalInfo* gi, int nbkt, int nbts) {
	
	gi->udpPkt[nbkt].tsPkt[nbts].ESFlagsVideo = 0xff;
    gi->udpPkt[nbkt].tsPkt[nbts].ESFlagsAudio = 0xff;
	
	if(gi->udpPkt[nbkt].tsPkt[nbts].MediaIndex == 0) { 
	// resolution (6 bits) && frame rate for video (2 bits)
	   if(gi->vd.frameRate == 30) {
		  if(strcmp(gi->vd.resolution, "SD") == 0) {
	          gi->udpPkt[nbkt].tsPkt[nbts].ESFlagsVideo = 0x1e;
		   } else if(strcmp(gi->vd.resolution, "HD720") == 0) {
		      gi->udpPkt[nbkt].tsPkt[nbts].ESFlagsVideo = 0x5e;
		   } else if(strcmp(gi->vd.resolution, "HD1080") == 0) {
		      gi->udpPkt[nbkt].tsPkt[nbts].ESFlagsVideo = 0xde;
		   }
	    } else if (gi->vd.frameRate == 60) {
		   if(strcmp(gi->vd.resolution, "SD") == 0) {
	          gi->udpPkt[nbkt].tsPkt[nbts].ESFlagsVideo = 0x3c;
		   } else if(strcmp(gi->vd.resolution, "HD720") == 0) {
		      gi->udpPkt[nbkt].tsPkt[nbts].ESFlagsVideo = 0x7c;
		   } else if(strcmp(gi->vd.resolution, "HD1080") == 0) {
		      gi->udpPkt[nbkt].tsPkt[nbts].ESFlagsVideo = 0xbc;
		   }
	    }
	} else if(gi->udpPkt[nbkt].tsPkt[nbts].MediaIndex == 0) {

	   // sample rate (2 bits) && audio channel (2 bits)
	   if(gi->ad.sampleRate = 48000) {
		 if(gi->ad.channel = 2) {
			  gi->udpPkt[nbkt].tsPkt[nbts].ESFlagsAudio = 0x01; 
		 } else if(gi->ad.channel = 1) {
		     gi->udpPkt[nbkt].tsPkt[nbts].ESFlagsAudio = 0x0d; 
		 }
	   } else if  (gi->ad.sampleRate = 41100) {
	     if(gi->ad.channel = 2) {
			 gi->udpPkt[nbkt].tsPkt[nbts].ESFlagsAudio = 0x00; 
		 } else if(gi->ad.channel = 1) {
		    gi->udpPkt[nbkt].tsPkt[nbts].ESFlagsAudio = 0x0c; 
		 }
	  }
	}
}

void read_tstream(const char *pcap, globalInfo* gi, pmt *map){
	
	// allocate memory space using heap method
	gi->udpPkt = (strippedUDPPacket*) malloc (sizeof(strippedUDPPacket) * rtp_nbkt(pcap, *gi));
	ts_nbkt(pcap, gi);

	FILE *fip = fopen(pcap, "rb");
	
	long wh[4]; wh[2] = 0;
	int nb = 0, nbpkt = 0, i, j, k, pos = WS_H, m = 0, sync_byte[10];
	long sec, usec;
	udp_info en_udp;
	rtp_info en_rtp;
	ts_header en; 
	pes_header en_pes;
	unsigned char value, adapt_len, adapt_flag, pointeur, tsh[4], clock[6], udp[8], rtp[12];
	unsigned char* pkt, *pat, *tabpmt, *pay;
	
	double ctime, ltime, delta;
	psi clt; 
	
	 // read in initial arrival time
	fseek(fip, pos, SEEK_SET);
	fread(&sec, sizeof(long), 1, fip); 
	fread(&usec, sizeof(long), 1, fip);
	ctime = arrival(sec, usec); 
	ltime = ctime;


	// decode TS stream 
	while (!feof(fip)) {
	  // point at the start of next media packet  
	  fseek(fip, pos, SEEK_SET);
	  fread(wh, sizeof(wh), 1, fip); nb = 0; 

	  ctime = arrival(wh[0], wh[1]); 
	  delta = ctime - ltime;

	  pkt = (unsigned char*)malloc(wh[2]*sizeof(unsigned char));
	
	  // read UDP header
	  k = 0;
	  while(k < ETH_H + IP_H) { fread(&value, 1, 1, fip); k++;}
	  for(k = 0; k < 8; k++) {
		fread(&value, 1, 1, fip); udp[k] = value;
	  }
	
	  en_udp = udp_header_decode(udp);	
	  if(gi->ad.dport == en_udp.dport || gi->vd.dport == en_udp.dport) {

        // read RTP packet header 
        for(k = 0; k < 12; k++) {
		  fread(&value, 1, 1, fip); rtp[k] = value;
	    }
	    
	    en_rtp = rtp_header_decode(rtp);
	  	//rtp_display(en_rtp);
	    
		gi->udpPkt[nbpkt].payloadSize = en_udp.len - UDP_H - RTP_H; 
        gi->udpPkt[nbpkt].sequenceNr = en_rtp.seq; 
	    gi->udpPkt[nbpkt].RTPTimestamp = en_rtp.ts;
	    gi->udpPkt[nbpkt].packetArrivalTime = delta;
     	
		//printf("(1) ==== Processing packet number: %ld | length %ld | pos %ld====\n", nbpkt, wh[2], pos);

	  	   for(i = ETH_H + IP_H + UDP_H + RTP_H; i < wh[2]; i++ ) {
	         fread(&value, 1, 1, fip);

			 if(value == 0x47) {

				sync_byte[nb] = i;	
		        tsh[0] = value;
		        i += 1; fread(&value, 1, 1, fip); tsh[1] = value;
		        i += 1; fread(&value, 1, 1, fip); tsh[2] = value;
		        i += 1; fread(&value, 1, 1, fip); tsh[3] = value;		     
		    
		        en = ts_header_decode(tsh);			

		        en.random_access = 0;
				gi->udpPkt[nbpkt].tsPkt[nb].PID = en.PID;

		        // handle the adaptation field
		        if(en.adaption_field_control == 0x00 || en.adaption_field_control == 0x01) {				
			           en.paylen = TS_L - TS_H; 
			           en.stuffing = 0;
		        } else if(en.adaption_field_control == 0x02 || en.adaption_field_control == 0x03) {				
			           i += 1; fread(&adapt_len, 1, 1, fip);
					     if(adapt_len == 0) {
							 
							 if(en.PID == 0 || (search1(clt, en.PID) >= 0 && clt.n_PMT_PID > 0)) {
					              i += 1; fread(&pointeur, 1, 1, fip);
			                      en.paylen = TS_L - TS_H - adapt_len - 1 - pointeur;
			                      en.stuffing =  TS_L - TS_H  - en.paylen; 				
			                  } else {
                                  en.paylen = TS_L - TS_H - adapt_len - 1;
			                      en.stuffing = TS_L - TS_H  - en.paylen;
			                  }
						 } else {				 					 
			                 i += 1; fread(&adapt_flag, 1, 1, fip); 
				
			                 en.random_access = adapt_flag & 0x40 >> 6;
			                 en.pcr = 0; 
			                 en.pcr = adapt_flag & 0x10 >> 4;

			                 k = 0; m = 0;
			                 // read in remaining parts of the adaption field
			                 while(k < adapt_len - 1) {
					             i += 1; fread(&value, 1, 1, fip);
					             if(en.pcr == 1 && m < 6) {
					                clock[m] = value; m++;
					             }
					         k++;
			                 }

			                 if(en.PID == 0 || (search1(clt, en.PID) >= 0 && clt.n_PMT_PID > 0)) {
					            i += 1; fread(&pointeur, 1, 1, fip);
			                    en.paylen = TS_L - TS_H - adapt_len - 1 - pointeur;
			                    en.stuffing =  TS_L - TS_H  - en.paylen; 				
			                 } else {
                                en.paylen = TS_L - TS_H - adapt_len - 1;
			                    en.stuffing = TS_L - TS_H  - en.paylen;
			                 }
			            }
			   }

               gi->udpPkt[nbpkt].tsPkt[nb].CC = en.continuity_counter;
			   gi->udpPkt[nbpkt].tsPkt[nb].payloadStart = en.payload_start_indicator;
			   gi->udpPkt[nbpkt].tsPkt[nb].payloadLength = en.paylen;
			   gi->udpPkt[nbpkt].tsPkt[nb].randomAccess = en.random_access;

			   if(en.stuffing > 0) {
				    gi->udpPkt[nbpkt].tsPkt[nb].assumedFrameEnd = 1;
			   } else {
			        gi->udpPkt[nbpkt].tsPkt[nb].assumedFrameEnd = 0;			   
			   }
			   
			if(en.PID == 0) {       		 
			  pat = (unsigned char*)malloc(en.paylen*sizeof(unsigned char));			  
			  k = 0;
				// read in PAT table form file
	                while(k < en.paylen - 1) {
					  i += 1; fread(&value, 1, 1, fip); 
					  pat[k] = value; k++;
					}
			  clt = pat_decode(pat, en.paylen);
			  // pat_display(clt);
			  gi->udpPkt[nbpkt].tsPkt[nb].MediaIndex = 2;
		    } else if (search1(clt, en.PID) >= 0 && clt.n_PMT_PID > 0) {    	   
			   tabpmt = (unsigned char*)malloc(en.paylen*sizeof(unsigned char));
			   k= 0;
				  // read in pmt table form file
	              while(k < en.paylen - 1) { 
					   i += 1; fread(&value, 1, 1, fip); 
					   tabpmt[k] = value; k++;
				  }					
			   *map = pmt_decode(tabpmt, en.paylen);
			   // pmt_display(*map);
			   gi->udpPkt[nbpkt].tsPkt[nb].MediaIndex = 2;
     		} else if ( (j = search2(*map, en.PID)) >= 0 && map->nb_stream > 0) {		 
			   
			   gi->udpPkt[nbpkt].tsPkt[nb].MediaIndex = media[map->str[j].stream_type];				   
			   
			   if(map->str[j].stream_type == 0x81)   gi->udpPkt[nbpkt].tsPkt[nb].MediaIndex = 1;
			   

			   // look for PTS and DTS field in PES header
			   gi->udpPkt[nbpkt].tsPkt[nb].PTS = 0;
			   gi->udpPkt[nbpkt].tsPkt[nb].DTS = 0;

			   if(en.payload_start_indicator == 1) {
				   pay = (unsigned char*)malloc(en.paylen*sizeof(unsigned char));
			       k = 0;
				   // read in payload table from ip file
	               while(k < en.paylen - 1) { 
					   i += 1; fread(&value, 1, 1, fip); 
					   pay[k] = value; k++;
				   }				
				   
			       en_pes = pes_decode(pay, en.paylen);

				   if(media[map->str[j].stream_type] == 1) {
				     gi->udpPkt[nbpkt].tsPkt[nb].PTS = en_pes.pts;
			         gi->udpPkt[nbpkt].tsPkt[nb].DTS = en_pes.pts;

					 //printf("ohh %ld \t PTS %ld\n",  gi->udpPkt[nbpkt].sequenceNr, en_pes.pts);
					 // sample rate and channel number
					 esflags(gi, nbpkt, nb);
				   } else if (media[map->str[j].stream_type] == 0) {
				     gi->udpPkt[nbpkt].tsPkt[nb].PTS = en_pes.pts;
			         gi->udpPkt[nbpkt].tsPkt[nb].DTS = en_pes.dts;
					 // resolution and frame rate
					 esflags(gi, nbpkt, nb);
				   }
				   
			   }
			    //pes_display(en_pes);
			  }		  

			   //ts_header_display(en);
			   nb++; *tsh = NULL;

			
		   }			
	   }
	    //printf("numTS t: %ld\t%ld seq %ld nbpkt %ld\n", gi->udpPkt[nbpkt].nbts, nb, en_rtp.seq, nbpkt);
        gi->udpPkt[nbpkt].nbts = nb; 
		nbpkt++; 
	}
	pos += wh[2] + WS_FH;	
    }
		
	gi->nbpkt = --nbpkt; 
	nb_pes(*gi);
	//printf("The number of received packets	|%ld\n", nbpkt); 
	fclose(fip);

}


void ts_nbkt(const char *pcap, globalInfo* gi){
	
	FILE *fip = fopen(pcap, "rb");
	
	long wh[4]; wh[2] = 0;
	int nb = 0, nbpkt = 0, i, k, pos = WS_H, dist = 0;
	udp_info en_udp;
	unsigned char *pkt, value, udp[8];
	
	// decode TS stream 
	while (!feof(fip)) {
	  // point at the start of next media packet  
	  fseek(fip, pos, SEEK_SET);
	  fread(wh, sizeof(wh), 1, fip); nb = 0; 
	  
	  //printf("(2) ==== Processing packet number: %ld | length %ld | position %ld====\n", nbpkt, wh[2], pos); 
	  pkt = (unsigned char*)malloc(wh[2]*sizeof(unsigned char));
	
	  // read UDP header
	  k = 0;
	  while(k < ETH_H + IP_H) { fread(&value, 1, 1, fip); k++;}
	  for(k = 0; k < 8; k++) {
		 fread(&value, 1, 1, fip); udp[k] = value;
	  }
	
	  en_udp = udp_header_decode(udp);	
	  if(gi->ad.dport == en_udp.dport || gi->vd.dport == en_udp.dport) {
          
	  	 for(i = ETH_H + IP_H + UDP_H; i < wh[2]; i++) {
	         fread(&value, 1, 1, fip); dist++;
			 if(value == 0x47 && i >= 54) { 
				 if(dist > 183 || nb == 0) {
			           nb++; dist = 0;
				 }
			  }

	      }
	    gi->udpPkt[nbpkt].nbts = nb;
		gi->udpPkt[nbpkt].tsPkt = (strippedTSPacket*)malloc(nb*sizeof(strippedTSPacket));
		
		//printf("pkt: %ld\t includes %ld PES packets\n", nbpkt, nb); 
		nbpkt++;
	  }
	  pos += wh[2] + WS_FH;	
    }
		
	fclose(fip);
}


void nb_pes(globalInfo gi) {
	int nb_audio_frame = 0, nb_video_frame = 0, a_nbperpacket = 0,  v_nbperpacket = 0, i, j; 
	
	for(i = 0; i <= gi.nbpkt; i++) {
		a_nbperpacket = 0; v_nbperpacket = 0;
        for(j = 0; j < gi.udpPkt[i].nbts; j++) {
		   if(gi.udpPkt[i].tsPkt[j].PID == 0x101 && gi.udpPkt[i].tsPkt[j].payloadStart == 1)
		     a_nbperpacket++;
		   if(gi.udpPkt[i].tsPkt[j].PID == 0x100 && gi.udpPkt[i].tsPkt[j].payloadStart == 1)
		     v_nbperpacket++;		   
		}
		nb_audio_frame += a_nbperpacket;
		nb_video_frame += v_nbperpacket;
		//printf("rcv : %ld sequence number |%ld audio %ld video %ld\n", i, gi.udpPkt[i].sequenceNr, a_nbperpacket, v_nbperpacket); 
    }
	printf("number of revieved frames are : audio %ld\tvideo %ld\n", nb_audio_frame, nb_video_frame);
}



