

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdint.h>

#include "globalInfo.h"

#ifndef MPEG_H_
#define MPEG_H_


#define WS_H 24
#define WS_FH 16

#define TS_L 188
#define TS_H 4

#define ETH_H 14
#define IP_H 20
#define UDP_H 8

typedef struct ts_header {
	unsigned char sync_byte;
	unsigned char transport_error_indicator;
	unsigned char payload_start_indicator;
	unsigned char transport_priority;
	unsigned int  PID;
	unsigned char transport_scrambling_control;
	unsigned char adaption_field_control;
	unsigned char continuity_counter;
	int paylen;
	int stuffing;
	unsigned char random_access;
	unsigned char pcr;
} ts_header;


typedef struct pts_dts {
     unsigned __int64 pts;
	 unsigned __int64 dts;
} pts_dts;


typedef struct psi {
     int n;
	 unsigned int pmt[100];
	 int m;
	 unsigned int nit[100];
} psi;


typedef struct str{
	 short PID;
	 short type;
} str;

typedef struct tstr{
	 int n;
	 str t[100];
} tstr;


extern int media[];

ts_header ts_header_decode(unsigned char ts_raw_entete[4]);
int find_ts_sync_byte(unsigned char *pkt, long n);
void read_tstream(const char *pcap, GlobalInfo* GI);

psi pat_decode(unsigned char *pat, int n); 
tstr pmt_decode(unsigned char *pmt, int n); 
pts_dts pes_decode(unsigned char *pes, int n); 

int search1(psi, unsigned int);
int search2(tstr, unsigned int);


unsigned __int64 combine (unsigned lo, unsigned hi);


#endif