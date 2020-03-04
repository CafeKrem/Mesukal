
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include "rtp.h"


#ifndef H_GLOBAL
#define H_GLOBAL

// wireshark headers
#define WS_H 24
#define WS_FH 16

// Transport stream 
#define TS_L 188
#define TS_H 4

// IP packet header
#define ETH_H 14
#define IP_H 20
#define UDP_H 8
#define RTP_H 12


typedef struct strippedTSPacket {
	    int PID;
	    int MediaIndex;
	    int CC;
	    int payloadStart;
	    int payloadLength;
	    int randomAccess;
	    int PTS;
	    int DTS;
	    int ESFlagsVideo;
	    int ESFlagsAudio;
	    int assumedFrameEnd;
} strippedTSPacket;

typedef struct strippedUDPPacket {
		double packetArrivalTime; 
	    int payloadSize;
	    int sequenceNr;
	    int RTPTimestamp;
	    int nbts;
	    strippedTSPacket *tsPkt;  
} strippedUDPPacket;


struct globalInfo {

	struct video {
	   char codec[10];
	   char resolution[10];
	   int frameRate;
	   char concealmentType[10];
	   int numSlices;
	   char isInterlaced[20];
	   int dport;
	} vd;

	struct audio {
	   char codec[10];
	   long sampleRate;
	   int frameLength;
	   double frameDuration;
	   long bitRate;
	   int dport;
	   int channel;
	} ad;

	strippedUDPPacket *udpPkt;

	int nbpkt;
	int isTS;
	int ts_level_enc;
};


/* UDP header*/
typedef struct udp_info{
   u_short sport;          // Source port
   u_short dport;          // Destination port
   u_short len;            // Datagram length
   u_short crc;            // Checksum
}udp_info;


/* RTP header */
typedef struct rtp_info {
   unsigned int version:2;   /* protocol version */
   unsigned int p:1;         /* padding flag */
   unsigned int x:1;         /* header extension flag */
   unsigned int cc:4;        /* CSRC count */
   unsigned int m:1;         /* marker bit */
   unsigned int pt:7;        /* payload type */
   unsigned short seq;       /* sequence number */
   unsigned int ts;          /* timestamp */
   unsigned int ssrc;        /* synchronization source */
   unsigned int csrc[1];     /* optional CSRC list */
 } rtp_info;


/* TS header */
typedef struct ts_header {
	unsigned char sync_byte;
	unsigned char transport_error_indicator;
	unsigned char payload_start_indicator;
	unsigned char transport_priority;
	unsigned int  PID;
	unsigned char transport_scrambling_control;
	unsigned char adaption_field_control;
	unsigned char continuity_counter;
	unsigned int  paylen;
	unsigned int  stuffing;
	unsigned char random_access;
	unsigned char pcr;
} ts_header;


/* PES header */
typedef struct pes_header {
	unsigned int sync_byte;
	unsigned char stream_id;
	unsigned short pes_pkt_len;
	unsigned char ptsdtsFlags;
	unsigned __int64 pts;
	unsigned __int64 dts;
} pes_header;


/* PAT table */
typedef struct psi {

    unsigned char tabID;
	unsigned char section_syntax_indicator;

	unsigned short section_length;
	unsigned short stream_id;

	unsigned char version;
	unsigned char current_next_indicator;
	unsigned char section_number;
	unsigned char section_last_number;

	unsigned int nb_PID;
	unsigned int n_PMT_PID;
	unsigned int pmtPID[100];
	unsigned int n_NIT_PID;
	unsigned int nitPID[100];

} psi;

/* PMT table */
typedef struct pmt {

	unsigned char tabID;
	unsigned char section_syntax_indicator;
	unsigned short section_length;	
	unsigned short program_number;

	unsigned char version;
	unsigned char current_next_indicator;
	unsigned char section_number;
	unsigned char section_last_number;
	unsigned short PCR_PID;
	unsigned short program_info_length;

	struct stream {
	       unsigned char stream_type;
	       unsigned int elementrery_PID;
	       unsigned int ES_info_length;
	} str[10];

	unsigned int nb_stream;

} pmt;


extern int media[];

void init(globalInfo *gi, const char *pcap);
int rtp_nbkt(const char *pcap, globalInfo gi);
void ts_nbkt(const char *pcap, globalInfo* gi);

int search1(psi, unsigned int);
int search2(pmt, unsigned int);
unsigned __int64 combine (unsigned lo, unsigned hi);

// udp and rtp headers analysis
udp_info udp_header_decode(unsigned char *);
rtp_info rtp_header_decode(unsigned char *);
void udp_display(udp_info);
void rtp_diplay(rtp_info);
double arrival(unsigned int sec, unsigned int usec);

// TS header analysis
ts_header ts_header_decode(unsigned char ts_raw_entete[4]);
void ts_header_display (ts_header ts_en);

// PES header analysis
pes_header pes_decode(unsigned char *pes, int n); 
void pes_header_display (pes_header pes_en);

// Decode PSI tables
psi pat_decode(unsigned char *tpat, int n); 
pmt pmt_decode(unsigned char *tpmt, int n); 
void pat_display(psi clt);
void pmt_display(pmt map);

// TS stream analysis
void read_tstream(const char *pcap, globalInfo* gi, pmt *map);

void nb_pes(globalInfo gi);


#endif