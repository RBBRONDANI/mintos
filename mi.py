import sys
import time
import os
import requests
from bs4 import BeautifulSoup
from sign.signdef import *
from pdb import set_trace as bp

class MI:
    def __init__(self):
        self.host = "https://www.mintos.com/en"
        self.user = os.environ['MINTOS_USER'] # export MINTOS_USER=mintosuser
        self.passwd = os.environ['MINTOS_PASS'] # export MINTOS_PASS=secret
    def ts_exit(self, msg):
        sys.exit(time.strftime("%Y-%m-%d %H:%M:%S ") + str(msg))
    def getNewLoans(self):
        payload = {"_csrf_token": "4GCwzO2PT5tLH7hNChaO6S2dA0N4kq6ySb_CgHtyKTA", "_username": self.user, "_password": self.passwd}
        session = requests.Session()
        r = session.post(self.host + "/login/check", data = payload) # send auth form
        if r.status_code != 200:
            self.ts_exit("Unable to open login page")
        r = session.get(self.host + "/available-loans/primary-market") # get loan list
        if r.status_code != 200:
            self.ts_exit("Unable to get loan list")
        soup = BeautifulSoup(r.text, "html.parser") # response parsing
        table = soup.find('table', {'id': 'primary-market-table'}) # Find users table
        bp()
        return {}
"""
table_body = table.find('tbody') # Skip head, take body
rows = table_body.find_all('tr') # All rows from table
point = datetime.now() # Fix point of time
recipients = []
for row in rows:
    cols = row.find_all('td') # All columns from iterating row
    user = cols[2].get_text() # User email
    recipients.append(user) # Add email to list of recipients
    if datetime.strptime(cols[8].get_text(), "%Y-%m-%d %H:%M:%S") < point - timedelta(days=DELTA): # Break if expired
        break



"""
"""
    def sign(self, ss):
        try:
            return str(subprocess.check_output([self.wmsigner, "-s", ss]), 'ascii')
        except subprocess.CalledProcessError as e:
            self.ts_exit(e.output)
    def getPortfolio(self, tid):
        path = "/ZTenders.ashx"
        t = str(int(time.time())) + '000'
        ss = self.sign(mWMID + ';' + tid + ';' + t)
        params = "WMID="+mWMID+"&TID="+tid+"&t="+t+"&VR=1&SS="+ss
        return self.httpReq('https', path, params, 'get')
#        return [t, str(self.sign(t))]
    def httpReq(self, proto, path, params, reqtype):
        session = requests.Session()
        if reqtype == 'get':
            r = session.get(proto + '://' + self.host + path + '?' + params)
        elif reqtype == 'post':
            payload = params
            r = session.post(proto + '://' + self.host + path, data = payload)
        else:
            self.ts_exit("httpReq: illegal reqtype")
        if r.status_code != 200:
            self.ts_exit("httpReq: http_code = " + str(r.status_code))
        else:
            return r.text
"""
