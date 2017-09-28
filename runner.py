#!/bin/env python3.6
import sys
import time
import json
from mintos import MI
from pdb import set_trace as bp

H = './' # home dir

class Runner(MI):
    def __init__(self, h):
        super().__init__()
        self.h = h
        self.data = {"status": {"file": "dat/numtdr.dat", "value": ""}}
        self.data_load("status")
        self.lock()
    def data_sync(self, varname):
        j = json.dumps(self.data[varname]["value"], sort_keys=True, indent=4)#separators=(',',':')
        open(self.h + self.data[varname]["file"], 'w').write(j)
    def data_load(self, varname):
        self.data[varname]["value"] = json.loads(open(self.h + self.data[varname]["file"]).read())
    def lock(self):
        if self.data["status"]["value"][2] == 1:
            self.ts_exit("System is locked")
        else:
            self.data["status"]["value"][2] = 1
            self.data_sync("status")
    def ulock(self):
        self.data["status"]["value"][2] = 0
        self.data_sync("status")

class Mintos(Runner):
    def __init__(self, h):
        super().__init__(h)
        self.numlist = {}

m = Mintos(H)
try:
    print("Main part\n")
    m.numlist = m.getNewLoans()
#    bp()
    open("dump.dat", 'w').write(m.numlist)
#    time.sleep(5)
finally:
    m.ulock()
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