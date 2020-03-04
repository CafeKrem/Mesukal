
#define _CRT_SECURE_NO_WARNINGS

#include "rtp.h"

int read_rtp_nb(const char *fpcap, int dport)
{
	pcap_t *fp;
	char errbuf[PCAP_ERRBUF_SIZE];
	
	struct pcap_pkthdr *header;
	const u_char *pkt_data;
	int res, pkt_count = 0;


	ip_header *ih;
    udp_header *uh;
	u_int ip_len;

	fp = pcap_open_offline(fpcap, errbuf);	

	/* Retrieve the packets from the file */
	while((res = pcap_next_ex(fp, &header, &pkt_data)) >= 0) { 

		/* retireve the position of the ip header */
		ih = (ip_header *) (pkt_data +  14); //length of ethernet header
		
		/* retireve the position of the udp header */
        ip_len = (ih->ver_ihl & 0xf) * 4;
        uh = (udp_header *) ((u_char*)ih + ip_len);

		if( ntohs(uh->dport) ==	dport) { pkt_count++;} 
	
	}
	
	pcap_close(fp);
	return pkt_count;
}

unsigned int* read_rtp_ts(const char *fpcap, int dport, int n)
{
	pcap_t *fp;
	char errbuf[PCAP_ERRBUF_SIZE];
	struct pcap_pkthdr *header;
	const u_char *pkt_data;
	
	unsigned int timestamp;
	int res, i = 0;

	ip_header *ih;
    udp_header *uh;
	u_int ip_len;


	unsigned int* ts = (unsigned int*)malloc(n*sizeof(unsigned int)); 

	fp = pcap_open_offline(fpcap, errbuf);
	
	/* Retrieve the packets from the file */
	while((res = pcap_next_ex(fp, &header, &pkt_data)) >= 0)
	{   	
		/* retireve the position of the ip header */
		ih = (ip_header *) (pkt_data +  14); //length of ethernet header
		
		/* retireve the position of the udp header */
        ip_len = (ih->ver_ihl & 0xf) * 4;
        uh = (udp_header *) ((u_char*)ih + ip_len);

		if( ntohs(uh->dport) ==	dport) { 		
		    memcpy (&timestamp, pkt_data + 46, 4);
	 	    ts[i] = ntohl(timestamp);
		    i++;
		}

	}
	pcap_close(fp);
	return ts;
}


unsigned int* read_rtp_seq(const char *fpcap, int dport, int n)
{
	pcap_t *fp;
	char errbuf[PCAP_ERRBUF_SIZE];
	struct pcap_pkthdr *header;
	const u_char *pkt_data;
	
	unsigned int seq;
	int res, i = 0;

	ip_header *ih;
    udp_header *uh;
	u_int ip_len;


	unsigned int* tseq = (unsigned int*)malloc(n*sizeof(unsigned int)); 

	fp = pcap_open_offline(fpcap, errbuf);
	
	/* Retrieve the packets from the file */
	while((res = pcap_next_ex(fp, &header, &pkt_data)) >= 0)
	{
		/* retireve the position of the ip header */
		ih = (ip_header *) (pkt_data +  14); //length of ethernet header
		
		/* retireve the position of the udp header */
        ip_len = (ih->ver_ihl & 0xf) * 4;
        uh = (udp_header *) ((u_char*)ih + ip_len);

		if( ntohs(uh->dport) ==	dport) { 
		    memcpy (&seq, pkt_data + 44, 2);
		    tseq[i] = ntohs(seq);
		    i++;
		}
	}
	pcap_close(fp);

	return tseq;
}


unsigned int* read_rtp_size(const char *fpcap, int dport, int n)
{
	pcap_t *fp;
	char errbuf[PCAP_ERRBUF_SIZE];
	struct pcap_pkthdr *header;
	const u_char *pkt_data;
	
    ip_header *ih;
    udp_header *uh;
	u_int ip_len;

	int res, i = 0, size = 0;

	unsigned int* tsize = (unsigned int*)malloc(n*sizeof(unsigned int)); 

	fp = pcap_open_offline(fpcap, errbuf);
	
	/* Retrieve the packets from the file */
	while((res = pcap_next_ex(fp, &header, &pkt_data)) >= 0)
	{	
		 /* retireve the position of the ip header */
		ih = (ip_header *) (pkt_data +  14); //length of ethernet header
		
		/* retireve the position of the udp header */
        ip_len = (ih->ver_ihl & 0xf) * 4;
        uh = (udp_header *) ((u_char*)ih + ip_len);

		if( ntohs(uh->dport) ==	dport) { 
		tsize[i] = ntohs(uh->len) - 20;  i++;
		}
	}

	pcap_close(fp);
	return tsize;
}


double* read_rtp_atime(const char *fpcap, int dport, int n) {

	pcap_t *fp; FILE *at;
	char errbuf[PCAP_ERRBUF_SIZE];
	struct pcap_pkthdr *header;
	const u_char *pkt_data;

	ip_header *ih;
    udp_header *uh;
	u_int ip_len;

   	long res, i = 0, size = 0;

	double *tatime = (double*)malloc(n*sizeof(double)); 

	long csec[1], cusec[1];
	long clon[1], colon[1];

	double ctime, ltime, delta;

	char tmp[40], tmp1[20], tmp2[20]; *tmp = NULL;
	at = fopen(fpcap, "r"); 
	
	fseek(at, 24, SEEK_CUR);
	
	fread(csec, sizeof(long), 1, at); fread(cusec, sizeof(long), 1, at);
	fread(clon, sizeof(long), 1, at); fread(colon, sizeof(long), 1, at);

	int count = 0; 	
	    
    sprintf(tmp1,"%d",csec[0]); 
	sprintf(tmp2,"%d",cusec[0]);
	strcpy(tmp, tmp1); 
	strcat(tmp, "."); 
	strcat(tmp, tmp2);
	ctime = strtod(tmp, NULL);
	
	ltime = ctime;
	*tmp1 = NULL; *tmp2 = NULL; *tmp = NULL;

	fseek(at, -16, SEEK_CUR);
	long fpos = 24;

	fp = pcap_open_offline(fpcap, errbuf);

	/* Retrieve the packets from the file */
	while((res = pcap_next_ex(fp, &header, &pkt_data)) >= 0)
	{	
      fread(csec, sizeof(long), 1, at); fread(cusec, sizeof(long), 1, at);
	  fread(clon, sizeof(long), 1, at); fread(colon, sizeof(long), 1, at);
      
	
	  sprintf(tmp1,"%d",csec[0]); 
	  sprintf(tmp2,"%d",cusec[0]);
	  strcpy(tmp, tmp1); 
	  strcat(tmp, "."); 
	  strcat(tmp, tmp2);
	  ctime = strtod(tmp, NULL);

	  delta = ctime - ltime;
	  
	  /* retireve the position of the ip header */
      ih = (ip_header *) (pkt_data +  14); //length of ethernet header
		
	  /* retireve the position of the udp header */
      ip_len = (ih->ver_ihl & 0xf) * 4;
      uh = (udp_header *) ((u_char*)ih + ip_len);

	  if(ntohs(uh->dport) == dport) {
		tatime[count] = delta; count++;
		//printf("\n%d\t%ld\t%lf\t%lf", count, clon[0], ctime, delta);
	  }
 
	  fpos = fpos + clon[0] + 4*sizeof(long);
	  fseek(at, fpos, SEEK_SET);

	}

	return(tatime);
}




//unsigned int* read_rtp_marker(const char *fpcap, int dport, int n) {
//
//	pcap_t *fp;
//	char errbuf[PCAP_ERRBUF_SIZE];
//	struct pcap_pkthdr *header;
//	const u_char *pkt_data;
//
//	ip_header *ih;
//    udp_header *uh;
//	u_int ip_len;
//
//	unsigned int m;
//
//	int res, i = 0, size = 0;
//
//	unsigned int* tmarker = (unsigned int*)malloc(n*sizeof(unsigned int)); 
//
//	fp = pcap_open_offline(fpcap, errbuf);
//
//	/* Retrieve the packets from the file */
//	while((res = pcap_next_ex(fp, &header, &pkt_data)) >= 0)
//	 {	
//		
//		 /* retireve the position of the ip header */
//		ih = (ip_header *) (pkt_data +  14); //length of ethernet header
//		
//		/* retireve the position of the udp header */
//        ip_len = (ih->ver_ihl & 0xf) * 4;
//        uh = (udp_header *) ((u_char*)ih + ip_len);
//
//		if( ntohs(uh->dport) ==	dport) {
//		 
//		 memcpy (&m, pkt_data + 42, 2);
//		
//		// payload type
//		//printf("here : %d \t ", ntohs(m) & 0x007F);
//
//		// marker bit
//		//printf("here : %d \t ", (ntohs(m) & 0x0080) >> 7);
//
//		tmarker[i] = (ntohs(m) & 0x0080) >> 7 ; i++;
//		//printf("here : %d\n", tmarker[i]);
//	 
//		}
//	}
//
//	pcap_close(fp);
//	return(tmarker);
//
//}
