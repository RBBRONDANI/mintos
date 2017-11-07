#!/bin/env python3.6
import sys
import time
import json
import codecs
import psutil
from mintos import MI
from pdb import set_trace as bp

H = './' # home dir

class Runner(MI):
    def __init__(self, h):
        super().__init__()
        self.h = h
        self.data = dict()
        for var in ['status', 'loandef']:
            self.data.update({var: {'file': 'dat/{}.dat'.format(var), 'value': ''}})
            self.data_load(var)
        self.lock()
        self.loan_last = self.data["status"]["value"]["last"]
        if len(sys.argv) > 1 and sys.argv[1] == '-d':
            self.debug = True
        else:
            self.debug = False
        self.logging(time.strftime("%Y-%m-%d %H:%M:%S"), "init")

    def data_sync(self, varname):
        j = json.dumps(self.data[varname]["value"], sort_keys=True, indent=4)#separators=(',',':')
        open(self.h + self.data[varname]["file"], 'w').write(j)

    def data_load(self, varname):
        self.data[varname]["value"] = json.loads(open(self.h + self.data[varname]["file"]).read())

    def lock(self):
        if self.data["status"]["value"]["lock"] == 1:
            self.ts_exit("system is locked")
        else:
            self.data["status"]["value"]["lock"] = 1
            self.data_sync("status")

    def ulock(self):
        self.data["status"]["value"]["lock"] = 0
        self.data_sync("status")

r = Runner(H)
try:
    r.logIn()
    r.getNewLoans()
    r.runScoring()
    if len(r.new_loans) > 0:
        fail = 99
        accepted = 10
        i = 0
        for k, loan in enumerate(r.new_loans):
            if loan['score'] != fail:
                i += 1
                if i > r.data['loandef']['value']['acceptcnt']:
                    break
                r.acceptLoans(loan['id'])
                r.new_loans[k].update(score = accepted, message = 'accepted')
            r.logging(loan['id'], loan['cur'], loan['amount'], loan['available'], loan['term'], loan['score'], loan['message'])
        success = len([loan['id'] for loan in r.new_loans if loan['score'] != fail])
        basket = len([loan['id'] for loan in r.new_loans if loan['score'] == accepted])
        checkout = ['', '']
        if basket > 0:
            checkout = r.checkOut()
            r.logging(checkout)
        print(time.strftime("%Y-%m-%d %H:%M:%S"), '{} / success {} / {}: {}'.format(
            r.new_loans[0]['id'] - r.loan_last, success, checkout[0], checkout[1]))
        r.loan_last = r.new_loans[0]['id']
    r.data["status"]["value"]["last"] = r.loan_last
    r.data_sync("status")
finally:
    r.Quit()
    r.ulock()
