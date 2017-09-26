import sys
import time
import subprocess
import requests
from sign.signdef import *

class CWM:
    def __init__(self):
        self.wmsigner = "sign/wmsigner"
        self.host = "credit.webmoney.ru"
    def ts_exit(self, msg):
        sys.exit(time.strftime("%Y-%m-%d %H:%M:%S ") + str(msg))
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
