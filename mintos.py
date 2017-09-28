import sys
import time
import os
import requests
import codecs
from bs4 import BeautifulSoup
from contextlib import closing
from selenium import webdriver
from seleniumrequests import Chrome # pip install selenium
#from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
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
        payload = {"_csrf_token": "7TOfAlMdEOAA2IvxkUJBd12Dy_vt7zLdI1HAXl5Hre0", "_username": self.user, "_password": self.passwd}
#        session = requests.Session()
#        r = session.post(self.host + "/login/check", data = payload) # send auth form
#        if r.status_code != 200:
#            self.ts_exit("Unable to open login page")
#        r = session.get(self.host + "/available-loans/primary-market") # get loan list
#        if r.status_code != 200:
#            self.ts_exit("Unable to get loan list")
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
#        with closing(Chrome(chrome_options=options)) as browser:
#            browser.request('POST', self.host + "/login/check", data = payload)
#            browser.get(self.host + "/available-loans/primary-market")
            # store it to string variable
        page_source = codecs.open("./tmp/dump.html", 'r', 'utf-8').read()
            #page_source = browser.page_source
        #codecs.open("./tmp/dump.html", 'w', 'utf-8').write(page_source)
        soup = BeautifulSoup(page_source, "html.parser") # response parsing
        # find primary market table
        rows = soup.find('table', {'id': 'primary-market-table'}).find('tbody').find_all('tr')
        numlist = []
        for row in rows:
            cols = row.find_all('td')
            numlist.append(cols[0].get_text())
            #print(cols[1].get_text())
#            button = browser.find_element_by_name('button')
#            button.click()
# wait for the page to load
#            WebDriverWait(browser, timeout=10).until(
#                lambda x: x.find_element_by_id('primary-market-table'))
        return numlist
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
