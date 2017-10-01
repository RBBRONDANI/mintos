import sys
import time
import os
import requests
import codecs
import re
from bs4 import BeautifulSoup as bs
from contextlib import closing
from selenium import webdriver
from seleniumrequests import Chrome
#from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from pdb import set_trace as bp

class MI:
    def __init__(self):
        self.host = "https://www.mintos.com/en"
        self.user = os.environ['MINTOS_USER'] # export MINTOS_USER=mintosuser
        self.passwd = os.environ['MINTOS_PASS'] # export MINTOS_PASS=secret
        self.new_loans = []
        self.loan_last = 0
    def ts_exit(self, msg):
        sys.exit(time.strftime("%Y-%m-%d %H:%M:%S ") + str(msg))
    def getNewLoans(self):
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
#        with closing(Chrome(chrome_options=options)) as browser:
#            browser.get(self.host + "/")
#            token = bs(browser.page_source, "html.parser").find('input', {'name': '_csrf_token'})['value']
#            payload = {"_csrf_token": token, "_username": self.user, "_password": self.passwd}
#            browser.request('POST', self.host + "/login/check", data = payload)
#            browser.get(self.host + "/available-loans/primary-market/?sort_field=id&sort_order=DESC&max_results=100&page=1")
#            page_source = browser.page_source # store it to string variable
# debug
#        codecs.open('tmp/dump.html', 'w', encoding='utf-8').write(page_source)
        page_source = codecs.open('tmp/dump.html', 'r', encoding='utf-8').read()
        soup = bs(page_source, "html.parser") # response parsing
        # find primary market table
        rows = soup.find('table', {'id': 'primary-market-table'})
        if rows is not None:
            rows = rows.find('tbody').find_all('tr')
        self.new_loans = []
        pattern = {   'id': [
                                "(\d+)",
                                'loan-id-col m-loan-id',
                            ],
                   'issue': [
                                "(\d{2}\.\d{2}\.\d{4})",
                                'm-loan-issued m-labeled-col',
                            ],
                    'type': [
                                "(Personal Loan|Car Loan|Mortgage Loan|Business Loan|Invoice Financing|Short-Term Loan)",
                                'm-loan-type',
                            ],
                    'rate': [
                                "(\d*\.\d+|\d+)\%",
                                'global-align-right m-loan-interest m-labeled-col',
                            ],
                  }
        pattern = {field: [
                              pattern[field][0],
                              pattern[field][1],
                              re.compile(pattern[field][0]),
                          ] 
                   for field in pattern}
        if rows is not None:
            for row in rows:
                cols = {field: row.find('td', {'class': pattern[field][1]}) for field in pattern}
                loan = {field: pattern[field][2].search(cols[field].get_text()).group(1) for field in pattern}
                loan['id'] = int(loan['id'])
                print(loan)
                if loan['id'] > self.loan_last:
                    self.new_loans.append(loan['id'])
        if len(self.new_loans) > 0:
            self.loan_last = self.new_loans[0]

        return self.new_loans

#            button = browser.find_element_by_name('button')
#            button.click()
# wait for the page to load
#            WebDriverWait(browser, timeout=10).until(
#                lambda x: x.find_element_by_id('primary-market-table'))
