#!/usr/bin/env python
#import argparse
import netsnmp
import time
import socket
import threading

# You probably don't want to change these
INTERVAL = 60 
VERSION = 2
NUM_ITER = 0
interface_exceptions = [ "Vlan", "Null", ".0", "bme", "vcp", "lsi", "dsc", "lo0", "vlan", "tap", "gre", "ipip", "pime", "pimd", "mtun" ]

# You probably want to change these
COMMUNITY = "mycommunity"
CARBON_SERVER = "myhost.example.com"
host_list = [ "core-switch-1", "core-switch-2", "access-switch-1" ]

# /shrug
CARBON_PORT = 2003

def schedule_collect(interval, collector, hst, vrs, comm, num_runs = 0):
    if num_runs != 1:
        threading.Timer(interval, schedule_collect, [interval, collector, hst, vrs, comm, 0 if num_runs == 0 else num_runs-1]).start()
        collector(hst, vrs, comm)


def do_collect(hst, vrs, comm):
        sock = socket.socket()
        try:
            sock.connect( (CARBON_SERVER,CARBON_PORT) )
        except:
            traceback.print_exc()
        now = int(time.time())
        args = {
            "Version": VERSION,
            "DestHost": hst,
            "Community": comm,
            "Timeout": 3
        }
        for idx in netsnmp.snmpwalk(netsnmp.Varbind("IF-MIB::ifIndex"), **args):
            descr, oper, cin, cout = netsnmp.snmpget(
                netsnmp.Varbind("IF-MIB::ifDescr", idx),
                netsnmp.Varbind("IF-MIB::ifOperStatus", idx),
                netsnmp.Varbind("IF-MIB::ifInOctets", idx),
                netsnmp.Varbind("IF-MIB::ifOutOctets", idx),
                **args)
            assert(descr is not None and
                   cin is not None and
                   cout is not None) 
            if descr == "lo":
                continue
            if oper != "1":  
                continue
            skip = 0
            for term in interface_exceptions:
                if term in descr:
                    skip = 1
            if skip == 0:
                descr = descr.replace("/","-")
                graphiteMessage = "infra.network.%s.if.%s-%s %s %d\n" % (hst,descr,"in",cin,now)
                sock.sendall(graphiteMessage)
                graphiteMessage = "infra.network.%s.if.%s-%s %s %d\n" % (hst,descr,"out",cout,now)
                sock.sendall(graphiteMessage)
        sock.close()

for myhost in host_list:
    schedule_collect(INTERVAL, do_collect, myhost, VERSION, COMMUNITY, 0)
