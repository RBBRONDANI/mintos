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
from selenium.common.exceptions import NoSuchElementException
from urllib.parse import urlencode
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

    def logIn(self):
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        self.browser = webdriver.Chrome(chrome_options = options)
        self.browser.get(self.host + "/")
        self.wait = WebDriverWait(self.browser, timeout = 10) # seconds
        account = self.wait.until(EC.presence_of_element_located((By.NAME, 'MyAccountButton')))
        account.click()
        time.sleep(1) # workaround: javascript needs to be loaded
        username = self.wait.until(EC.presence_of_element_located((By.NAME, '_username')))
        username.send_keys(self.user)
        password = self.browser.find_element_by_name('_password')
        password.send_keys(self.passwd)
        form = self.browser.find_element_by_id('login-form')
        form.submit()
        header = self.wait.until(EC.presence_of_element_located((By.ID, 'header-username')))
        return header.text

    def getNewLoans(self):
        ld = self.data['loandef']['value']
        query = {
            'min_interest':   ld['ratemin'] * 100,
            'max_interest':   ld['ratemax'] * 100,
            'min_term':       0,
            'max_term':       ld['termmax'],
            'currencies[]':   978,
            'sort_field':     'id',
            'sort_order':     'DESC',
            'max_results':    100,
            'page':           1
        }
        self.browser.get(self.host + "/available-loans/primary-market/?" + urlencode(query))
        self.wait.until(EC.presence_of_element_located((By.ID, 'primary-market-table')))
# debug
#        codecs.open('tmp/dump', 'w', encoding='utf-8').write(self.browser.page_source)
        soup = bs(self.browser.page_source, "html.parser") # response parsing
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
                                r'. (\d+\s*\d*\.*\d*)',
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
                                r'. (\d+\s*\d*\.*\d*)',
                                'global-align-right m-labeled-col mod-highlighted',
                            ],
                     'cur': [
                                r'(.) \d+\s*\d*',
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
                loan['amount']  = float(loan['amount'].replace(' ', ''))
                loan['rate']    = float(loan['rate'])
                loan['term']    = int(loan['term'])
                if loan.get('term_m'):
                    loan['term_m'] = int(loan['term_m'])
                    loan['term'] = loan['term'] + loan['term_m'] * 30 # rounded, acceptable for scoring purposes only
                    del loan['term_m']
                loan['available'] = float(loan['available'].replace(' ', ''))
                if loan['cur'] == '\u20AC':
                    loan['cur'] = 'EUR'
                else:
                    loan['cur'] = None
#                elif loan['cur'] == '\u10DA': # other ccy not for now...
#                    loan['cur'] = 'GEL'
                if loan['id'] > self.loan_last:
                    if (loan['id'] - self.loan_last) % ld['acceptskip'] == 0:
                        self.new_loans.append(loan)
                else:
                    break
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
        ld = self.data['loandef']['value']
        self.browser.get("{}/{}-01".format(self.host, loan))
        investment = self.wait.until(EC.presence_of_element_located((By.ID, 'investment-tab')))
        investment.click()
        table = self.wait.until(EC.presence_of_element_located((By.ID, 'investment-group-table')))
        percent = re.compile('(-*\d+\.\d+)%')
        imin = 0
        pmin = 100
        cnt = len(table.find_elements_by_xpath('./tbody/tr'))
        if cnt >= 3:
            cnt = 3
        for i in range(2, cnt + 1):
            row = table.find_element_by_xpath('./tbody/tr[{}]'.format(i))
            discount = row.find_element_by_xpath('./td[5]').text
            if len(discount) > 0 and self.isElementExist(row, './td[7]/div'):
                p = float(percent.search(discount).group(1))
                if p < pmin:
                    pmin = p
                    imin = i
        if imin == 0:
            print('Cannot find invest line')
        else:
            div = table.find_element_by_xpath('./tbody/tr[{}]/td[7]/div'.format(imin))
            self.logging(imin, pmin, loan, 'data-hash:', div.get_attribute('data-hash'))
            button = div.find_element_by_xpath('./button')
            fillin = div.find_element_by_xpath('./input')
            case = div.find_element_by_xpath('./a[@class="btn btn-primary trigger-submit"]')
            button.send_keys(Keys.SPACE)
            amount = re.compile('\u20AC (\d+\.\d+)') # euro only
            value = float(amount.search(fillin.get_attribute('value')).group(1))
            if value > ld['acceptmax']:
                fillin.send_keys(ld['acceptmax'])
            fillin.send_keys(Keys.TAB)
            case.click()
            time.sleep(1) # workaround: javascript needs to be loaded
        return True

    def isElementExist(self, parent, locator):
        try:
            parent.find_element_by_xpath(locator)
        except NoSuchElementException:
            self.logging('No such thing: {}'.format(locator))
            return False
        return True

    def checkOut(self):
        self.browser.get("{}/review-investments/".format(self.host))
        confirm = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'form-horizontal')))
        confirm.submit()
        time.sleep(1) # workaround: javascript needs to be loaded
        if self.debug:
            codecs.open('tmp/dump_checkout', 'w', encoding='utf-8').write(self.browser.page_source)
        if self.isElementExist(self.browser, '//div[@id="investment-review"]'):
            message = self.browser.find_element_by_xpath('//div[@id="investment-review"]/h1').text
            if message == "Thank you! Your investments have been approved.":
                return ['approved', message]
        if self.isElementExist(self.browser, '//div[@class="common-error pull-right"]'):
            message = self.browser.find_element_by_xpath('//div[@class="common-error pull-right"]').text
            return ['error', message]
        return ['error', 'unable to parse result']

    def Quit(self):
        self.browser.quit()

    def logging(self, *args):
        if self.debug:
            print(args)
