# Rough code to figure out performance characteristics of Memphis county court web site.

from scrapers.court import case_id, case
import time
from datetime import datetime
from datetime import timedelta
from typing import List
import sys
import re
import json

class AddressScraper:
    def __init__(self):
        self.caseScraper = case.CaseScraper()
        self.errors = []
        self.MAX_DAYS = 260
        self.DATE_FORMAT = '%Y-%m-%d'
        self.theDate = datetime.now().strftime(self.DATE_FORMAT)
        self.numDays = 7
        if len(sys.argv) > 0:
            for i, arg in enumerate(sys.argv):
                if i == 1:
                    self.handleDate(arg)
                    break
                elif i == 2:
                    self.handleDays(arg)
                    break
    def handleDate(self, arg):
        if re.match('\d\d\d\d-\d\d-\d\d', arg):
            startDate = datetime.strptime(arg, self.DATE_FORMAT)
            startLimit = datetime.now() - timedelta(days = self.MAX_DAYS)
            endLimit = datetime.strptime(self.theDate, self.DATE_FORMAT)
            if startDate <= endLimit and startDate > startLimit:
                self.theDate = arg
    def handleDays(self, arg):
        if re.match('\d+', arg):
            nDays = int(arg)
            if nDays <= self.MAX_DAYS:
                self.numDays = nDays
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True)
    def log(self, message):
        timeTag = datetime.now()
        print('"' + str(timeTag) + '",' + message)
    def sendQuery(self, theDate, theLastInitial, hashByCaseNumber) -> List[int]:
        start = time.time()
        cases = case_id.CaseIdScraper().get(date = theDate, last_initial = theLastInitial)
        end = time.time()
        numCases = len(cases)
        for c in cases:
            hashByCaseNumber[c['Eviction Case Number']] = self.caseScraper.get(c['Eviction Case Number'])
        # self.log(theLastInitial + ',numCases: ' + str(numCases) + ',len(hashByCaseNumber): ' + str(len(hashByCaseNumber)))
        return [numCases, round(end - start)]
    def logProgress(self, totalStart, startLetter, endLetter, numCases):
        totalEnd = time.time()
        totalSeconds = int(round(totalEnd - totalStart))
        minutes = round(totalSeconds / 60)
        seconds = round(totalSeconds % 60)
        elapsedTime = '{0:0>2}:{1:0>2}'.format(minutes, seconds)
        self.log(startLetter + "-" + endLetter + "," + self.theDate + "," +
                str(numCases) + "," + elapsedTime)
    def getByAlpha(self, startLetter, endLetter, hashByCaseNumber):
        totalStart = time.time()
        for i in range(ord(startLetter), ord(endLetter) + 1):
            letter = chr(i)
            try:
                self.sendQuery(self.theDate, letter, hashByCaseNumber)
            except  Exception as e:
                self.errors.append('Letter: ' + letter + ', date: ' + self.theDate + ', Exception: ' + str(e))
        # self.logProgress(totalStart, startLetter, endLetter, len(hashByCaseNumber))
    def getByWildCard(self):
        wildcard_cases = {}
        retVals = self.sendQuery(self.theDate, "*", wildcard_cases)
        self.log("*," + self.theDate + "," + str(retVals[0]) + "," + str(retVals[1]))
        return wildcard_cases
    def compare_scraping(self, a_z_cases):
        wildcard_cases = self.getByWildCard()
        for key in list(wildcard_cases):
            msg = ''
            if key not in a_z_cases:
                msg = 'NOT'
            else:
                msg = '___'
            print(msg + "," + key + "," + wildcard_cases[key])
    def findSettlements(self, case):
        for entry in case['docket_entries']:
            if entry['description'] == 'POSSESSION $___& COST FED':
                settledDate = entry['date']
                filedDate = case['description']['filing_date']
                delta = settledDate - filedDate
                self.log(case['description']['case_num'] + "," + str(settledDate) + ','
                        + str(filedDate) + ',' + str(delta.days))
    def writeCSV(self, a_z_cases, tenants, landlords):
        for case in a_z_cases:
            pass
    def run(self):
        self.log('Started: ' + self.toJSON())
        tenants = {}
        landlords = {}
        current_time = datetime.now()
        for i in range(self.numDays):
            self.theDate = current_time.strftime(self.DATE_FORMAT)
            a_z_cases = {}
            self.getByAlpha("a", "z", a_z_cases, tenants,landlords)
            self.writeCSV(a_z_cases)
            current_time = current_time - timedelta(days = 1)
        with open('tenants.csv', 'w') as tenant_file:
            tenant_file.write('')
            for t in tenants:
                tenant_file.write(t)
        with open('landlords.csv') as landlord_file:
            landlord_file.write('')
            for ll in landlords:
                landlord_file.write(ll)
        self.log('Ended')
        for s in self.errors:
            self.log(s)

if __name__ == "__main__":
    AddressScraper().run()