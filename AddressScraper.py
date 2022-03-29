# Rough code to figure out performance characteristics of Memphis county court web site.

from scrapers.court import case_id, case
import time
from datetime import datetime
from datetime import timedelta
from typing import List
import sys
import re
import json
import csv

class AddressScraper:
    def __init__(self):
        self.caseScraper = case.CaseScraper()
        self.errors = []
        self.MAX_DAYS = 260
        self.startLetter = 'a'
        self.endLetter = 'z'
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
        self.logProgress(totalStart, startLetter, endLetter, len(hashByCaseNumber))
    def findSettlements(self, case):
        for entry in case['docket_entries']:
            if entry['description'] == 'POSSESSION $___& COST FED':
                settledDate = entry['date']
                filedDate = case['description']['filing_date']
                delta = settledDate - filedDate
                self.log(case['description']['case_num'] + "," + str(settledDate) + ','
                        + str(filedDate) + ',' + str(delta.days))
    def createParty(self, party) :
        if not party['address']:
            self.errors.append('No address for: ' + party['name'])
            return None
        names = party['name'].split(', ')
        addresses = party['address'].split('\n')
        address1 = ''
        cityStateZip = ''
        theRe = re.compile('^(\w+?) (\w\w) \d\d\d\d\d')
        for i in range(len(addresses)):
            if theRe.match(addresses[i]):
                cityStateZip = addresses[i]
                break;
            address1 = address1 + ',' + addresses[i]
        if cityStateZip:
            [city, state, theZip] = cityStateZip.split(' ')
        else:
            self.errors.append('Unable to split city/state/zip for: ' + party['name'] +
                                ', ' + party['address'])
            return None
        return {
                'FIRST NAME' : names[1] if len(names) > 1 else names[0],
                'LAST NAME' : names[0] if len(names) > 1 else '',
                'ADDRESS 1' : address1,
                'ADDRESS 2' : '',
                'CITY' : city,
                'STATE' : state,
                'ZIP CODE' : party['zip']
        }
    def writeCSV(self, a_z_cases, tenants, landlords):
        for caseNumber in list(a_z_cases):
            case = a_z_cases[caseNumber]
            for party in case['parties']:
                caseURL = r'https://gscivildata.shelbycountytn.gov/pls/gnweb/ck\_public\_qry\_doct.cp\_dktrpt\_frames?case_id=' + str(caseNumber)
                if party['type'] == 'DEFENDANT':
                    theP = self.createParty(party)
                    if theP:
                        tenants[caseNumber] = theP
                    else:
                        self.errors.append('Unable to get tenant address for case: ' + caseURL)
                elif party['type'] in ['PRO SE LITIGANT', 'PLAINTIFF', 'ATTORNEY FOR PLAINTIFF']:
                    landlordURL = r'https://gscivildata.shelbycountytn.gov/pls/gnweb/ck_public_qry_cpty.cp_personcase_details_idx?id_code=' + str(party['eid'])
                    theP = self.createParty(party)
                    if theP:
                        landlords[party['eid']] = theP
                    else:
                        self.errors.append('Unable to get landlord address for landlord: ' + landlordURL + ', case: ' + caseURL)
    def run(self):
        self.log('Started: ' + self.toJSON())
        tenants = {}
        landlords = {}
        for i in range(self.numDays):
            a_z_cases = {}
            self.getByAlpha(self.startLetter, self.endLetter, a_z_cases)
            self.writeCSV(a_z_cases, tenants, landlords)
            currentDate = datetime.strptime(self.theDate, self.DATE_FORMAT)
            currentDate = currentDate - timedelta(days = 1)
            self.theDate = currentDate.strftime(self.DATE_FORMAT)
        theFieldNames = ['FIRST NAME', 'LAST NAME', 'ADDRESS 1', 'ADDRESS 2', 'CITY', 'STATE', 'ZIP CODE']
        with open('tenants.csv', 'w', newline='') as tenant_file:
            csvwriter = csv.DictWriter(tenant_file, fieldnames = theFieldNames)
            csvwriter.writeheader()
            for t in list(tenants):
                csvwriter.writerow(tenants[t])
        with open('landlords.csv', 'w', newline='') as landlord_file:
            csvwriter = csv.DictWriter(landlord_file, fieldnames = theFieldNames)
            csvwriter.writeheader()
            for id in list(landlords):
                csvwriter.writerow(landlords[id])
        self.log('Ended')
        for s in self.errors:
            self.log(s)
    def test(self):
        self.theDate = '2021-05-10'
        self.numDays = 1
        self.startLetter = 'b'
        self.endLetter = 'b'
        self.run()

if __name__ == "__main__":
    AddressScraper().run()