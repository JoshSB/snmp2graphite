#!/usr/bin/env python

#  This program runs as a daemon, collects switch/router interface counter data, and sends
#  the metrics to Graphite.  It also serves a simple HTTP service that organizes links for 
#  the interfaces it monitors, as to create a dashboard of graphs without needing to browse
#  and click through the Graphite UI or laboriously create your own dashboards for hundreds
#  of interfaces.

#  User Variables:
#  PER_SECOND           Display value perSecond? Default is per INTERVAL (requires patch or graphite>0.10)
#  SNMP_COMMUNITY	Set this to the SNMPv2 community used to pull stats from your network gear
#  CARBON_SERVER	The hostname/IP used to address your Carbon-Cache
#  CARBON_PORT		The TCP port to which metrics will be sent
#  GRAPHITE_SERVER	The hostname for the Graphite server that will appear in Dashboards
#  GRAPHITE_PREFIX	The Graphite node path under which these metrics will be stored (must end with ".")
#  WEB_SERVER_HOST	The IP address(es) that will serve Dashboard pages
#  WEB_SERVER_PORT	The TCP port that will serve Dashboard pages
#  IFACE_EXCEPT		A list of strings, for which any interface containing these will not be graphed
#  HOST_LIST		Hostnames of routers/switches to poll

import os
import netsnmp
import time
import socket
import threading
import cherrypy
INTERVAL = 60 
SNMP_VERSION = 2

#  /USER VARIABLES/
PER_SECOND = 1
SNMP_COMMUNITY = "my_community"  
CARBON_SERVER = "carbon_server"  
CARBON_PORT = 2003  
GRAPHITE_SERVER = "graphite_server"  
GRAPHITE_PREFIX = "network.switches." 
WEB_SERVER_HOST = "0.0.0.0"  
WEB_SERVER_PORT = 8111  
IFACE_EXCEPT = [ "Vlan", "Null", ".0", "bme", "vcp", "lsi", "dsc", "lo0", "vlan", "tap", "gre", "ipip", "pime", "pimd", "mtun" ]

HOST_LIST = [ "router1", "switch1", "linux-box1" ]  

port_list = {}  #this is dynamic
for hn in HOST_LIST:
    port_list[hn] = []

cherrypy.config.update({'server.socket_host': WEB_SERVER_HOST,
                        'server.socket_port': WEB_SERVER_PORT,
                       })

class BaseCP(object):
    @cherrypy.expose
    def default(self,*args,**kwargs):
        try:
            args[0]
        except:
            html_body = ""
            html_top = "<html><head><title>Switch Graphs</title></head><body>"
            for x in HOST_LIST:
                html_body+="<a href=\"http://" + cherrypy.request.headers['Host'] + "/" + x + "\">" + x + "</a><br>"
            html_end = "</body></html>"
            return html_top + html_body + html_end
        try:
            port_list[args[0]]
        except:
            return "host not found"
        else:
            html_body = ""
            html_top = "<html><head><title>" + args[0] + "</title></head><body>"
            for x in port_list[args[0]]:
                if (PER_SECOND == 0):
                    html_body+="<img src=\"http://" + GRAPHITE_SERVER + "/render?target=nonNegativeDerivative%28" + GRAPHITE_PREFIX + args[0] + ".if." + x + "-*,18446744073709551615%29&from=-60min&height=200&width=600\">"
                if (PER_SECOND == 1):
                    html_body+="<img src=\"http://" + GRAPHITE_SERVER + "/render?target=perSecond%28" + GRAPHITE_PREFIX + args[0] + ".if." + x + "-*%29&from=-60min&height=200&width=600\">"
            html_end = "</body></html>"
            return html_top + html_body + html_end

def schedule_collect(interval, collector, hst, vrs, comm, num_runs = 0):
    if num_runs != 1:
        threading.Timer(interval, schedule_collect, [interval, collector, hst, vrs, comm, 0 if num_runs == 0 else num_runs-1]).start()
        collector(hst, vrs, comm)


def do_collect(hst, vrs, comm):
        port_list[hst] = []
        sock = socket.socket()
        try:
            sock.connect( (CARBON_SERVER,CARBON_PORT) )
        except:
            traceback.print_exc()
        now = int(time.time())
        args = {
            "Version": SNMP_VERSION,
            "DestHost": hst,
            "Community": comm
        }
        sess = netsnmp.Session (**args)
        INDEX_POS = 0
        MIB_ROOT = "ifIndex"
        MIB_CURR = MIB_ROOT
        RESULTS = {}
        while (MIB_ROOT == MIB_CURR):
            vars = netsnmp.VarList(netsnmp.Varbind(MIB_CURR,INDEX_POS))
            vals = sess.getbulk(0,16,vars)
            for i in vars:
                if (i.tag == MIB_CURR):
                    KEY = i.iid
                    RESULTS[KEY] = i
            INDEX_POS = int(vars[-1].iid)
            MIB_CURR = vars[-1].tag
        for idx in RESULTS:
            descr, oper, cin, cout = netsnmp.snmpget(
                netsnmp.Varbind("IF-MIB::ifDescr", idx),
                netsnmp.Varbind("IF-MIB::ifOperStatus", idx),
                netsnmp.Varbind("IF-MIB::ifHCInOctets", idx),
                netsnmp.Varbind("IF-MIB::ifHCOutOctets", idx),
                **args)
            assert(descr is not None and
                   cin is not None and
                   cout is not None) 
            if descr == "lo":
                continue
            if oper != "1":  
                continue
            skip = 0
            for term in IFACE_EXCEPT:
                if term in descr:
                    skip = 1
            if skip == 0:
                descr = descr.replace("/","-")
                descr = descr.replace("SuperBlade Gigabit Switch BMB-GEM-003, Port #","port-")
                port_list[hst].append(descr)
                graphiteMessage = GRAPHITE_PREFIX + "%s.if.%s-%s %s %d\n" % (hst,descr,"in",cin,now)
                sock.sendall(graphiteMessage)
                graphiteMessage = GRAPHITE_PREFIX + "%s.if.%s-%s %s %d\n" % (hst,descr,"out",cout,now)
                sock.sendall(graphiteMessage)
        sock.close()

for myhost in HOST_LIST:
    schedule_collect(INTERVAL, do_collect, myhost, SNMP_VERSION, SNMP_COMMUNITY, 0)

if __name__ == "__main__":
    serverThread = threading.Thread(target = cherrypy.quickstart(BaseCP()))
    serverThread.start()
