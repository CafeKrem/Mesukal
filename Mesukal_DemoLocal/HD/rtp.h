
#include <pcap.h>

#include <winsock2.h>
#include <windows.h>

#ifndef RTP_H_
#define RTP_H_


/* 4 bytes IP address */
typedef struct ip_address{
    u_char byte1;
    u_char byte2;
    u_char byte3;
    u_char byte4;
}ip_address;


/* IPv4 header */
typedef struct ip_header{
    u_char  ver_ihl;        // Version (4 bits) + Internet header length (4 bits)
    u_char  tos;            // Type of service 
    u_short tlen;           // Total length 
    u_short identification; // Identification
    u_short flags_fo;       // Flags (3 bits) + Fragment offset (13 bits)
    u_char  ttl;            // Time to live
    u_char  proto;          // Protocol
    u_short crc;            // Header checksum
    ip_address  saddr;      // Source address
    ip_address  daddr;      // Destination address
    u_int   op_pad;         // Option + Padding
}ip_header;


/* UDP header*/
typedef struct udp_header{
    u_short sport;          // Source port
    u_short dport;          // Destination port
    u_short len;            // Datagram length
    u_short crc;            // Checksum
}udp_header;


/* RTP header*/
typedef struct rtp_header {
   unsigned int version:2;   /* protocol version */
   unsigned int p:1;         /* padding flag */
   unsigned int x:1;         /* header extension flag */
   unsigned int cc:4;        /* CSRC count */
   unsigned int m:1;         /* marker bit */
   unsigned int pt:7;        /* payload type */
   unsigned short seq;               /* sequence number */
   unsigned int ts;                /* timestamp */
   unsigned int ssrc;              /* synchronization source */
   unsigned int csrc[1];           /* optional CSRC list */
 } rtp_header;


int read_rtp_nb(const char *fpcap, int dport);
unsigned int* read_rtp_ts(const char *fpcap, int dport, int n);
unsigned int* read_rtp_seq(const char *fpcap, int dport, int n);
unsigned int* read_rtp_size(const char *fpcap, int dport, int n);
double * read_rtp_atime(const char *fpcap, int dport, int n);

//unsigned int* read_rtp_marker(const char *fpcap, int dport, int n);

#endif