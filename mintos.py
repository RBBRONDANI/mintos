import sys
import time
import os
import codecs
import re
from bs4 import BeautifulSoup as bs
from contextlib import closing
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
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
        ld = self.data['loandef']['value']
        with closing(webdriver.Chrome(chrome_options = options)) as browser:
            browser.get(self.host + "/")
            wait = WebDriverWait(browser, timeout = 10) # seconds
            account = wait.until(EC.presence_of_element_located((By.NAME, 'MyAccountButton')))
            account.click()
            time.sleep(1) # workaround: javascript needs to be loaded
            username = wait.until(EC.presence_of_element_located((By.NAME, '_username')))
            username.send_keys(self.user)
            password = browser.find_element_by_name('_password')
            password.send_keys(self.passwd)
            form = browser.find_element_by_id('login-form')
            form.submit()
            wait.until(EC.presence_of_element_located((By.ID, 'header-username')))
            browser.get(self.host + "/available-loans/primary-market/?min_interest={}&max_interest={}&currencies[]=978&sort_field=id&sort_order=DESC&max_results=100&page=1"
                .format(ld['ratemin'] * 100, ld['ratemin'] * 100))
            wait.until(EC.presence_of_element_located((By.ID, 'primary-market-table')))
            page_source = browser.page_source # store it to string variable
# debug
#        codecs.open('tmp/dump', 'w', encoding='utf-8').write(page_source)
#        page_source = codecs.open('tmp/dump.html', 'r', encoding='utf-8').read()
        soup = bs(page_source, "html.parser") # response parsing
        # find primary market table
        rows = soup.find('table', {'id': 'primary-market-table'})
        if rows is not None:
            rows = rows.find('tbody').find_all('tr')
        self.new_loans = []
        pattern = {   'id': [
                                r'(\d+)',
                                'loan-id-col m-loan-id',
                            ],
                   'issue': [
                                r'(\d{2}\.\d{2}\.\d{4})',
                                'm-loan-issued m-labeled-col',
                            ],
                    'type': [
                                r'(Personal Loan|Car Loan|Mortgage Loan|Business Loan|Invoice Financing|Short-Term Loan)',
                                'm-loan-type',
                            ],
                  'amount': [
                                r'(\d+\.\d+|\d+)',
                                'global-align-right m-loan-amount m-labeled-col',
                            ],
                    'rate': [
                                r'(\d*\.\d+|\d+)\%',
                                'global-align-right m-loan-interest m-labeled-col',
                            ],
                    'term': [
                                r'(\d+) d\.',
                                'global-align-right m-loan-term m-labeled-col',
                            ],
                  'term_m': [
                                r'(\d+) m\.',
                                'global-align-right m-loan-term m-labeled-col',
                            ],
               'available': [
                                r'(\d+\.\d+|\d+)',
                                'global-align-right m-labeled-col mod-highlighted',
                            ],
                     'cur': [
                                r'(.) \d+',
                                'global-align-right m-labeled-col mod-highlighted',
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
                cols =  {
                            field: row.find('td', {'class': pattern[field][1]})
                                for field in pattern
                        }
                loan =  {
                            field: pattern[field][2].search(cols[field].get_text())
                                for field in pattern
                        }
                loan =  {
                            field: loan[field].group(1)
                                for field in pattern
                                if loan[field] is not None
                        }
                loan['id']      = int(loan['id'])
                loan['issue']   = time.strptime(loan['issue'], '%d.%m.%Y')
                loan['amount']  = float(loan['amount'])
                loan['rate']    = float(loan['rate'])
                loan['term']    = int(loan['term'])
                if loan.get('term_m'):
                    loan['term_m'] = int(loan['term_m'])
                    loan['term'] = loan['term'] + loan['term_m'] * 30 # rounded, acceptable for scoring purposes only
                    del loan['term_m']
                loan['available'] = float(loan['available'])
                if loan['cur'] == '\u20AC':
                    loan['cur'] = 'EUR'
                else:
                    loan['cur'] = None
#                elif loan['cur'] == '\u10DA': # other ccy not for now...
#                    loan['cur'] = 'GEL'
                if loan['id'] > self.loan_last:
                    self.new_loans.append(loan)
        if len(self.new_loans) > 0:
            self.loan_last = self.new_loans[0]['id']
        return self.new_loans

    def runScoring(self):
        ld = self.data['loandef']['value']
        fail = 99
        for i, loan in enumerate(self.new_loans):
            if loan['amount'] > ld['amountmax']:
                self.new_loans[i].update(score = fail, message = 'amount ({}) > amountmax'.format(loan['amount']))
            elif loan['amount'] < ld['amountmin']:
                self.new_loans[i].update(score = fail, message = 'amount ({}) < amountmin'.format(loan['amount']))
            elif loan['term'] > ld['termmax']:
                self.new_loans[i].update(score = fail, message = 'term ({}) > termmax'.format(loan['term']))
            else:
                rate = loan['rate'] / 100
                if rate > ld['ratemax']:
                    self.new_loans[i].update(score = fail, message = 'rate ({}) > ratemax'.format(rate))
                elif rate < ld['ratemin']:
                    self.new_loans[i].update(score = fail, message = 'rate ({}) < ratemin'.format(rate))
                else:
                    self.new_loans[i].update(score = 0, message = 'Ok')

    def acceptLoans(self, loan):
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        ld = self.data['loandef']['value']
        with closing(webdriver.Chrome(chrome_options = options)) as browser:
            browser.get(self.host + "/")
            wait = WebDriverWait(browser, timeout = 10) # seconds
            account = wait.until(EC.presence_of_element_located((By.NAME, 'MyAccountButton')))
            account.click()
            time.sleep(1) # workaround: javascript needs to be loaded
            username = wait.until(EC.presence_of_element_located((By.NAME, '_username')))
            username.send_keys(self.user)
            password = browser.find_element_by_name('_password')
            password.send_keys(self.passwd)
            form = browser.find_element_by_id('login-form')
            form.submit()
            wait.until(EC.presence_of_element_located((By.ID, 'header-username')))
            browser.get("{}/{}-01".format(self.host, loan))
            investment = wait.until(EC.presence_of_element_located((By.ID, 'investment-tab')))
            investment.click()
            table = wait.until(EC.presence_of_element_located((By.ID, 'investment-group-table')))
            row2 = table.find_element_by_xpath('./tbody/tr[2]')
            row3 = table.find_element_by_xpath('./tbody/tr[3]')
            percent = re.compile('(-*\d+\.\d+)%')
            imin = 0
            pmin = 100
            for i in range(2, 4):
#                print(i)
                row = table.find_element_by_xpath('./tbody/tr[{}]'.format(i))
                td5 = row.find_element_by_xpath('./td[5]').text
#                print(td5, len(td5))
                if len(td5) > 0:
                    p = float(percent.search(td5).group(1))
                    if p < pmin:
                        pmin = p
                        imin = i
            print(imin, pmin, table.find_element_by_xpath('./tbody/tr[{}]/td[7]/div'.format(imin)).get_attribute('data-hash'));
#            print(table.find_element_by_xpath('./tbody/tr[{}]/td[7]/div'.format(imin)).get_attribute('innerHTML'))
#            row1 = wait.until(EC.presence_of_element_located((By.XPATH, '//table[@id="investment-group-table"]/tbody/tr[2]/td[5]')))
#            row2 = wait.until(EC.presence_of_element_located((By.XPATH, '//table[@id="investment-group-table"]/tbody/tr[2]/td[5]')))
#            codecs.open('tmp/dump_accept', 'w', encoding='utf-8').write(row2.get_attribute('innerHTML'))
#            browser.get(self.host + "/available-loans/primary-market/?min_interest={}&max_interest={}&currencies[]=978&sort_field=id&sort_order=DESC&max_results=100&page=1"
#                .format(ld['ratemin'] * 100, ld['ratemin'] * 100))
#            wait.until(EC.presence_of_element_located((By.ID, 'primary-market-table')))
#            page_source = browser.page_source # store it to string variable
# debug
#        codecs.open('tmp/dump_accept', 'w', encoding='utf-8').write(page_source)
#        page_source = codecs.open('tmp/dump.html', 'r', encoding='utf-8').read()
        return True
