#!/usr/bin/python

import os

servers = open('servers.txt','r').readlines()
#servers = open('server_inuse.txt','r').readlines()

for server in servers:
	server = server.strip()
	print '====================\n' + server
	command = "ssh -oStrictHostKeyChecking=no umd_rental@" + server + " 'bash -s' < ssh_script.sh"
	os.system(command)
