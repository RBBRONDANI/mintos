#!/bin/env python3.6
import sys
import time
import json
import codecs
import os
from mintos import MI
from pdb import set_trace as bp

H = './' # home dir

class Runner(MI):
    def __init__(self, h):
        super().__init__()
        self.h = h
        self.data = {"status": {"file": "dat/status.dat", "value": ""}}
        self.data_load("status")
        self.lock()
        self.loan_last = self.data["status"]["value"]["last"]
    def data_sync(self, varname):
        j = json.dumps(self.data[varname]["value"], sort_keys=True, indent=4)#separators=(',',':')
        open(self.h + self.data[varname]["file"], 'w').write(j)
    def data_load(self, varname):
        self.data[varname]["value"] = json.loads(open(self.h + self.data[varname]["file"]).read())
    def lock(self):
        if self.data["status"]["value"]["lock"] == 1:
            self.ts_exit("System is locked")
        else:
            self.data["status"]["value"]["lock"] = 1
            self.data_sync("status")
    def ulock(self):
        self.data["status"]["value"]["lock"] = 0
        self.data_sync("status")

r = Runner(H)
if os.name != 'nt':
    os.setpgrp() # create new process group, become its leader
try:
    r.getNewLoans()
    print(time.strftime("%Y-%m-%d %H:%M:%S"), len(r.new_loans), [loan['id'] for loan in r.new_loans])
    r.data["status"]["value"]["last"] = r.loan_last
    r.data_sync("status")
finally:
    if os.name != 'nt':
        os.killpg(0, signal.SIGKILL) # kill all processes in my group
    r.ulock()
