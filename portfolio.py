#!/bin/env python3
import sys
import time
import json
from cwm import CWM

H = '/opt/naolcwmdev/' # home dir
#NUMTDR = H + 'dat' + OS + 'numtdr.dat' # status file
#require_once('WMSigner.php');
#include ('k'.OS.'signdef.php');
#include('cwm.php');
#include('loandef.php');
#include('errdesc.php');
#include('/home/srv30502/htdocs/trk/sms/smstraffic/sms.php');

class Runner(CWM):
    def __init__(self, h):
        super().__init__()
        self.h = h
        self.varset = {"status": {"file": "dat/numtdr.dat", "var": ""}}
        self.var_load("status")
        self.lock()
    def sync(self, varname):
        j = json.dumps(self.varset[varname]["var"], sort_keys=True, indent=4)#separators=(',',':')
        open(self.h + self.varset[varname]["file"], 'w').write(j)
    def var_load(self, varname):
        self.varset[varname]["var"] = json.loads(open(self.h + self.varset[varname]["file"]).read())
    def lock(self):
        if self.varset["status"]["var"][2] == 1:
            self.ts_exit("System is locked")
        else:
            self.varset["status"]["var"][2] = 1
            self.sync("status")
    def ulock(self):
        self.varset["status"]["var"][2] = 0
        self.sync("status")

class Portfolio(Runner):
    def __init__(self, h):
        super().__init__(h)
        self.varset["portfolio"] = {"file": "dat/port/port000000.dat", "var": ""}
        self.var_load("portfolio")

p = Portfolio(H)
try:
    print('Main part\n')
    p.varset["portfolio"]["var"] = json.loads(p.getPortfolio('0'))
    p.sync("portfolio")
#    time.sleep(5)
#    open('testfile')
finally:
    p.ulock()
"""
    // RETRIEVE LIST
    file_put_contents('dat\port000000.dat', cwm::getPortfolio('0', $sig));
    $ts = json_decode(file_get_contents('dat'.OS.'port000000.dat'));
    // RETRIEVE TENDERS
    foreach ($ts->ztenders as $t)
	if ($t->State == 3 and !file_exists('dat'.OS.'port'.$t->CTenderID.'.dat')) 
		file_put_contents('dat'.OS.'port'.$t->CTenderID.'.dat', cwm::getTender($t->CTenderID, $sig));
		unset($t);
		// RETRIEVE OPERATIONS
		//!!! Copy numx3.dat, 
		//	histx3op.dat, 
		//	histx3ret.dat first !!!
		//!!!	and back to Site after update !!!
		//!!! Look to histX3ret.dat and observe all ret id's !!!
		cwm::getX3hist(date('Ymd H:i:s',time()), $sig);
		print "Checking ret's ID's...";
		$ret = json_decode(file_get_contents(H.'dat'.OS.'histx3ret.dat'), true);
		foreach ($ret as $idx => $v) 
		    if(preg_match("/^[0-9]{10}$/", $v['org']) == 0)
			    print "\nerror: org=".$v['org']; 
			    unset($v);
			    print "Done\n";
			    exit(0);
"""