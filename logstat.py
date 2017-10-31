#!/bin/env python3.6
import sys
import time
import re

with open('log/runner.log', 'r') as f:
    total = dict()
    for line in f.read().splitlines():
        elem = line.split(' ')
        if elem[0][:4] == '2017' and elem[3] == '/':
            c = total.get(elem[0], dict(total = 0, success = 0))
            total[elem[0]] = dict(
                                      total   = c['total']   + int(elem[2]),
                                      success = c['success'] + int(elem[5])
                                 )
    for date in total:
        print(date, total[date])
