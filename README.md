snmp2graphite
=============

Poll SNMP devices (routers/switches) and send data to Graphite

The goal here is to make a really simple program that dumps switch and router interface counter data into graphite, instead of relying on archaic networking tools like cacti or custom RRD solutions (not that they're bad, but wouldn't it be nice to consolidate?).

--

Updates Dec. 29, 2014:

- Poll devices using bulk-gets, increases "walk" efficiency by about 10x

- Now, the program provides a HTTP server that will spit out URLs for graphs per-switch.  So, not only does it actively record interface utilization stats for in-use interfaces, but it directly provides a dashboard of graphs for those same interfaces.

- Interface MIBs now use the HC mibs (kind of an obvious oversight in the initial version). 

The grahping server is pretty rudimentary, and I'll make it better over time, but for now, what it accomplishes is you can add a new switch to your network, add its hostname to this script, restart it and with NO more configuration, you can access graphs for all of the currently-in-use interfaces on that switch with a single URL.  
