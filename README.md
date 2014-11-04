snmp2graphite
=============

Poll SNMP devices (routers/switches) and send data to Graphite


Note:  I am NOT a programmer.  I'm a network engineer - so my code makes sense from a network standpoint, but the code probably sucks.

The goal here is to make a really simple program that dumps switch and router interface counter data into graphite, instead of relying on archaic networking tools like cacti or custom RRD solutions (not that they're bad, but they don't coexist with shiny new programmery things).


