
#define _CRT_SECURE_NO_WARNINGS

#include "mpeg2ex.h"

int media[] = {2, 0, 0, 1, 1, 2, 2, 2, 2, 2, 2,\
	           2, 2, 2, 2, 1, 0, 1, 2, 2, 2, 2,\
			   2, 2, 2, 2, 2, 0, 1, 2, 2, 0, 0,\
			   0, 0, 0, 0, 0, 2, 2, 2};


int search1(psi ps, unsigned int val){
    
	int i = 0;
	while (ps.pmt[i] != val && i < ps.n) {i++;}			
	if(i == ps.n) { return -1; } else { return i;}
}


int search2(tstr ts, unsigned int val) {

	int i = 0;
	while (ts.t[i].PID != val && i < ts.n) { i++; }	
	if(i == ts.n) { return -1; } else { return i;}
}


ts_header ts_header_decode(unsigned char ts_raw_entete[4])
{
	ts_header ts_en;
	
	// extarct information from TS header
	ts_en.sync_byte = ts_raw_entete[0];
	ts_en.transport_error_indicator = (ts_raw_entete[1] & 0x80) >> 7;
	ts_en.payload_start_indicator = (ts_raw_entete[1] & 0x40) >> 6;
	ts_en.transport_priority = (ts_raw_entete[1] & 0x20) >> 5;
	ts_en.PID = ((ts_raw_entete[1] & 31) << 8) | ts_raw_entete[2];
	ts_en.transport_scrambling_control = (ts_raw_entete[3] & 0xC0);
	ts_en.adaption_field_control = (ts_raw_entete[3] & 0x30) >> 4;
	ts_en.continuity_counter = (ts_raw_entete[3] & 0xF);

	// display
	printf("PID			| %x\n",ts_en.PID);		       
	printf("CC			| %x\n", ts_en.continuity_counter);
	printf("payload start indicator	| %x\n", ts_en.payload_start_indicator);
	printf("adaptation field	| %x\n", ts_en.adaption_field_control);
	
	return(ts_en);
}


psi pat_decode(unsigned char *pat, int n) {

	psi clt;
	clt.m = 0; clt.n = 0;

	unsigned short a, b;

	printf("table ID			| %x\n", pat[0]);
	
	a = (unsigned short )pat[1] << 8 | pat[2];	
	printf("section syntax indicator	| %x\n", (a & 0x8000) >> 15);
 	printf("the forced 0			| %x\n", (a & 0x4000) >> 14 );
	printf("section length			| %ld\n", a & 0x0fff);

	a = (unsigned short )pat[3] << 8 | pat[4];
	printf("stream id			| %x\n", a);

	printf("version number			| %d\n", (pat[5] & 0x2e) >> 1);
	printf("current next indicator		| %x\n", pat[5] & 0x01);
	printf("section number			| %x\n", pat[6]);
	printf("section last number		| %x\n", pat[7]);

	int N = (n - 12)/4;
	printf("PSI table number		| %ld\n", N);

	int init = 8;
	while(N > 0) {
	    a = (unsigned short )pat[init] << 8 | pat[init + 1];	    
	    b = (unsigned short )pat[init + 2] << 8 | pat[init + 3];

	 	if(a == 0) {	
		     printf("PID of NIT table	| %x\n", b & (0x1fff));
			 clt.nit[clt.m] = b & (0x1fff); clt.m++;
	    } else {
		     printf("PID of PMT table	| %x\n", b & (0x1fff));
			 clt.pmt[clt.n] = b & (0x1fff); clt.n++;
	    }
		N--; init += 4;
	}

	return(clt);
}


tstr pmt_decode(unsigned char *pmt, int n) {

	unsigned a;
	tstr tres;  tres.n = 0;
	
	printf("table ID			| %x\n", pmt[0]);

	a = (unsigned short )pmt[1] << 8 | pmt[2];	
	printf("section syntax indicator	| %x\n", (a & 0x8000) >> 15);
 	printf("forced 0			| %x\n", (a & 0x4000) >> 14);
	printf("section length			| %ld\n", a & 0x0fff);

	a = (unsigned short )pmt[3] << 8 | pmt[4];
	printf("stream id			| %x\n", a);

	printf("version number			| %d\n", (pmt[5] & 0x2e) >> 1);
	printf("current next indicator		| %x\n", pmt[5] & 0x01);

	printf("section number			| %x\n", pmt[6]);
	printf("section last number		| %x\n", pmt[7]);

	a = (unsigned short )pmt[8] << 8 | pmt[9];
	printf("PCR_PID				| %x\n", a & 0x1fff);

	a = (unsigned short )pmt[10] << 8 | pmt[11];
	printf("program info length		| %x\n", a & 0x0fff);

	int N = (n - 16)/4;
	printf("stream numbers			| %ld\n", N);
	
	int init = 12, k = 0;
	while(N > 0) {
	  
      printf("stream type		| %x\n", pmt[init]);
	  tres.t[k].type = pmt[init];

	   ++init;
	  a = (unsigned short )pmt[init] << 8 | pmt[init+1]; 
	  ++init; ++init;
	  printf("elementary PID stream	| %x\n", a & 0x1fff);
	  tres.t[k].PID = a & 0x1fff;
	 
	  a = (unsigned short )pmt[init] << 8 | pmt[init+1]; 
	  ++init; ++init;
	  printf("ES_info_Length		| %x\n", a & 0x0fff);
	  
	  init += a & 0x0fff; N--; ++tres.n; k++;
	}

	 return(tres);
}


pts_dts pes_decode(unsigned char *pes, int n) {
    
	pts_dts timing; timing.dts = 0; timing.pts = 0;

	printf("	====The decoding of PES header===\n");

	unsigned int a1 = 0x00000000;
	unsigned short a2 = 0x0000, b2 = 0x0000;

	a1 = (pes[0] << 16) | (pes[1] << 8) | pes[2];
	printf("	sync PES byte		| %x\n", a1);
	printf("	stream id		| %x\n", pes[3]);

	a2 = (pes[4] << 8) | pes[5];
	printf("	PES packet lenght	| %x\n", a2);

	printf("	forced '10'		| %x\n", (pes[6] & 0xc0) >> 6);
	printf("	PES scrambling control	| %x\n", (pes[6] & 0x30) >> 4);
	printf("	PES priority		| %x\n", (pes[6] & 0x08) >> 3);
	printf("	alignment indicator	| %x\n", (pes[6] & 0x04) >> 2);
	printf("	copyright		| %x\n", (pes[6] & 0x02) >> 1);
	printf("	original or copy	| %x\n", (pes[6] & 0x01));

	printf("	PTS/DTS flag		| %x\n", (pes[7] & 0xc0) >> 6);
	
	unsigned int v1, v2;
	unsigned __int64 v;		  

	if((pes[7] & 0xc0) >> 6 == 2) {
	    printf("	forced '0010'		| %x\n", (pes[9] & 0xf0) >> 4);

		a2 = (pes[10] << 8) | pes[11];
		b2 = (pes[12] << 8) | pes[13];

		v1 = a2 << 16 | b2;
		v2 = unsigned int(pes[9] & 0x0f); 
		  
		v = combine(v1, v2);

		timing.pts = 0;
        timing.pts |= (v >> 3) & (0x0007 << 30); // top 3 bits, shifted left by 3, other bits zeroed out
		timing.pts |= (v >> 2) & (0x7fff << 15); // middle 15 bits
        timing.pts |= (v >> 1) & (0x7fff <<  0); // bottom 15 bits
        // pts now has correct timestamp without markers in lowest 33 bits
		printf("	PTS value		| %" PRIx64 "\n", timing.pts);

	} else if ((pes[7] & 0xc0) >> 6 == 3) {
	      printf("	forced '0011'		| %x\n", (pes[9] & 0xf0) >> 4);
		  
		  a2 = (pes[10] << 8) | pes[11];
		  b2 = (pes[12] << 8) | pes[13];

		  v1 = a2 << 16 | b2;
		  v2 = unsigned int(pes[9] & 0x0f); 

		  v = combine(v1, v2);

		  timing.pts = 0;
		  timing.pts |= (v >> 3) & (0x0007 << 30); // top 3 bits, shifted left by 3, other bits zeroed out
		  timing.pts |= (v >> 2) & (0x7fff << 15); // middle 15 bits
          timing.pts |= (v >> 1) & (0x7fff <<  0); // bottom 15 bits
          // pts now has correct timestamp without markers in lowest 33 bits
		  printf("	PTS value		| %" PRIx64 "\n", timing.pts);

		  printf("	forced '0001'		| %x\n", (pes[14] & 0xf0) >> 4);
		  		  
		  a2 = (pes[15] << 8) | pes[16];
		  b2 = (pes[17] << 8) | pes[18];

		  v1 = a2 << 16 | b2;
		  v2 =  unsigned int(pes[14] & 0x0f); 

		  v = combine(v1, v2);

		  timing.dts = 0;
          timing.dts |= (v >> 3) & (0x0007 << 30); // top 3 bits, shifted left by 3, other bits zeroed out
		  timing.dts |= (v >> 2) & (0x7fff << 15); // middle 15 bits
          timing.dts |= (v >> 1) & (0x7fff <<  0); // bottom 15 bits
         // pts now has correct timestamp without markers in lowest 33 bits

		  printf("	DTS value		| %" PRIx64 "\n", timing.dts);	
  }		 
	return(timing);
}


unsigned __int64 combine (unsigned int lo, unsigned int hi) {

	// try the following line instead
    return ( (unsigned __int64)hi << 32) | lo;
}


void read_tstream(const char *pcap, GlobalInfo* GI){


	FILE *fip = fopen(pcap, "rb");
	
	long wh[4]; wh[2] = 0;
	int nb = 0, nbpkt = 0, i, j, k, pos = WS_H, m = 0;
	ts_header en;
	unsigned char value, adapt_len, adapt_flag, pointeur, tsh[4], clock[6];
	unsigned char* pkt, *pat, *pmt, *pay;
	
	short sport, dport;
	int sync_byte[10];

	psi clt; tstr tpmt; pts_dts pre;

	// decode TS stream 
	while (!feof(fip)) {
	    
	// point at the start of next media packet
	fseek(fip, pos, SEEK_SET);
	fread(wh, sizeof(wh), 1, fip); nb = 0; 
	printf("==== Processing packet number: %ld | length %ld | position %ld====\n", nbpkt, wh[2], pos);
	pkt = (unsigned char*)malloc(wh[2]*sizeof(unsigned char));
	
	//look for UDP port
	k = 0;
	while(k < ETH_H + IP_H) { fread(&value, 1, 1, fip); k++;}

	fread(&value, 1, 1, fip); 
	sport = value << 8;
	fread(&value, 1, 1, fip);
	sport |= value;
	
	fread(&value, 1, 1, fip); 
	dport = value << 8;
	fread(&value, 1, 1, fip);
	dport |= value;
	printf("	source port %ld : desination port: %ld\n", sport, dport);
	
	if(GI->a.dport == dport || GI->v.dport == dport) {

	  for(i = ETH_H + IP_H + UDP_H; i < wh[2]; i++ ) {
	    fread(&value, 1, 1, fip);

	    if(value == 0x47 && i >= 54) {
		  printf("===The processing of a TS number {%ld}===\n", nb);
	      sync_byte[nb] = i;	
		  tsh[0] = value;
		  i += 1; fread(&value, 1, 1, fip); tsh[1] = value;
		  i += 1; fread(&value, 1, 1, fip); tsh[2] = value;
		  i += 1; fread(&value, 1, 1, fip); tsh[3] = value;		     
		    
		  printf("PID --> %x:%x:%x:%x\n", tsh[0], tsh[1], tsh[2], tsh[3]);
		  en = ts_header_decode(tsh);
		  en.random_access = 0;

		  // handle the adaptation field
		  if(en.adaption_field_control == 0x00 || en.adaption_field_control == 0x01) {				
			  en.paylen = TS_L - TS_H; 
			  en.stuffing = 0;
		  } else if(en.adaption_field_control == 0x02 || en.adaption_field_control == 0x03) {				
			  fread(&adapt_len, 1, 1, fip); 
			  fread(&adapt_flag, 1, 1, fip); 
				
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

			  if(en.pcr == 1) { printf(" =================== The clock rate is found\n"); }

				if(en.PID == 0 || (search1(clt, en.PID) >= 0 && clt.n > 0)) {
					fread(&pointeur, 1, 1, fip);
			        en.paylen = TS_L - TS_H - 1 - adapt_len - 1 - pointeur;
			        en.stuffing = adapt_len + 1 + pointeur; 				
				} else {
				    en.paylen = TS_L - TS_H - 1 - adapt_len - 1;
			        en.stuffing = adapt_len + 1;
				}

			   printf("TS payload size		| %ld\n", en.paylen);
			   printf("TS stuffing size	| %ld\n", en.stuffing);

			}
			if(en.PID == 0) {
              printf("******************************PAT table decoding**\n");			 

			  pat = (unsigned char*)malloc(en.paylen*sizeof(unsigned char));			  
			  k = 0;
				// read in PAT table form file
	                while(k < en.paylen) {
					  i += 1; fread(&value, 1, 1, fip); 
					  pat[k] = value; k++;
					}
			  clt = pat_decode(pat, en.paylen);

			  printf("TS payload size		| %ld\n", en.paylen);
			  printf("TS stuffing size	| %ld\n", en.stuffing);

		    } else if (search1(clt, en.PID) >= 0 && clt.n > 0) {
		       printf("******************************PMT table decoding**\n");	   
			     
			   pmt = (unsigned char*)malloc(en.paylen*sizeof(unsigned char));

			   k= 0;
				  // read in pmt table form file
	              while(k < en.paylen) { 
					   i += 1; fread(&value, 1, 1, fip); 
					   pmt[k] = value; k++;
				  }					
			   tpmt = pmt_decode(pmt, en.paylen);

			   printf("TS payload size		| %ld\n", en.paylen);
			   printf("TS stuffing size	| %ld\n", en.stuffing);
     		} else if ( (j = search2(tpmt, en.PID)) >= 0 && tpmt.n > 0) {
			   printf("***A normal TS packet***\n");  
			   		
			   printf("media type		| %x\n", tpmt.t[j].type);
			   printf("media type A/V		| %x\n", media[tpmt.t[j].type]);

			   GI->strippedUDPPackets[nbpkt].strippedTSPackets[nb].MediaIndex = media[tpmt.t[j].type];
			   GI->strippedUDPPackets[nbpkt].strippedTSPackets[nb].CC = en.continuity_counter;
			   GI->strippedUDPPackets[nbpkt].strippedTSPackets[nb].payloadStart = en.payload_start_indicator;
			   GI->strippedUDPPackets[nbpkt].strippedTSPackets[nb].payloadLength = en.paylen;
			   GI->strippedUDPPackets[nbpkt].strippedTSPackets[nb].randomAccess = en.random_access;

			   if(en.stuffing > 0) {
				    GI->strippedUDPPackets[nbpkt].strippedTSPackets[nb].assumedFrameEnd = 1;
			   } else {
			        GI->strippedUDPPackets[nbpkt].strippedTSPackets[nb].assumedFrameEnd = 0;			   
			   }
			   			   
			   // look for PTS and DTS field in PES header
			   GI->strippedUDPPackets[nbpkt].strippedTSPackets[nb].PTS = 0;
			   GI->strippedUDPPackets[nbpkt].strippedTSPackets[nb].DTS = 0;
			   if(en.payload_start_indicator == 1) {
				   pay = (unsigned char*)malloc(en.paylen*sizeof(unsigned char));
			       k = 0;
				   // read in payload table from ip file
	               while(k < en.paylen) { 
					   i += 1; fread(&value, 1, 1, fip); 
					   pay[k] = value; k++;
				   }					
			       pre = pes_decode(pay, en.paylen);

				   if( media[tpmt.t[j].type] == 1) {
				     GI->strippedUDPPackets[nbpkt].strippedTSPackets[nb].PTS = pre.pts;
			         GI->strippedUDPPackets[nbpkt].strippedTSPackets[nb].DTS = pre.pts;
				   } else {
				     GI->strippedUDPPackets[nbpkt].strippedTSPackets[nb].PTS = pre.pts;
			         GI->strippedUDPPackets[nbpkt].strippedTSPackets[nb].DTS = pre.dts;
				   }
			   }
			  }
			  nb++; *tsh = NULL;
		   }			
	   }
        GI->strippedUDPPackets[nbpkt].nbts = nb;
	    printf("pkt: %ld\t includes %ld PES packets\n", nbpkt, nb); nbpkt++; 
	}
	pos += wh[2] + WS_FH;	
    }
	fclose(fip);
}