from scrapers.court import case_id, case
import time
from datetime import datetime
from datetime import timedelta
from typing import List
import sys
import re
import json
import csv
from os import listdir
from os.path import isfile, join
import requests

class AddressScraper:
    def __init__(self):
        self.caseScraper = case.CaseScraper()
        self.errors = []
        self.MAX_DAYS = 260
        self.startLetter = 'a'
        self.endLetter = 'z'
        self.DATE_FORMAT = '%Y-%m-%d'
        self.theDate = datetime.now().strftime(self.DATE_FORMAT)
        self.dateRange = self.theDate
        self.endDate = self.theDate
        self.numDays = 7
        if len(sys.argv) > 0:
            for i, arg in enumerate(sys.argv):
                if i == 1:
                    self.handleDate(arg)
                    break
                elif i == 2:
                    self.handleDays(arg)
                    break
        self.PLAINTIFF_PRIORITY = {
            'PLAINTIFF' : 3,
            'PRO SE LITIGANT' : 2,
            'ATTORNEY FOR PLAINTIFF' : 1
        }
        self.plaintiffPriorities = {}
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
    def hasJudgment(self, case):
        today = datetime.now()
        minDay = today - timedelta(days = self.numDays)
        for entry in case['docket_entries']:
            if entry['description'] == 'POSSESSION $___& COST FED':
                if ' ' in entry['date']:
                    splitter = ' '
                else:
                    splitter = 'T'   
                settledDate = datetime.strptime(entry['date'].split(splitter)[0], self.DATE_FORMAT)
                if (settledDate <= today) and (settledDate >= minDay):
                    return True
        return False
    def sendQuery(self, theDate, theLastInitial, hashByCaseNumber, judgmentsOnly) -> List[int]:
        start = time.time()
        cases = case_id.CaseIdScraper().get(date = theDate, last_initial = theLastInitial)
        end = time.time()
        numCases = len(cases)
        for c in cases:
            if not judgmentsOnly or self.hasJudgement(c):
                hashByCaseNumber[c['Eviction Case Number']] = self.caseScraper.get(c['Eviction Case Number'])
        return [numCases, round(end - start)]
    def getElapsedStr(self, start):
        theEnd = time.time()
        totalSeconds = int(round(theEnd - start))
        minutes = round(totalSeconds / 60)
        seconds = round(totalSeconds % 60)
        return '{0:0>2}:{1:0>2}'.format(minutes, seconds)
    def logProgress(self, totalStart, startLetter, endLetter, numCases):
        elapsedTime = self.getElapsedStr(totalStart)
        self.log(startLetter + "-" + endLetter + "," + self.theDate + "," +
                str(numCases) + "," + elapsedTime)
    def getByAlpha(self, startLetter, endLetter, hashByCaseNumber, judgmentsOnly):
        # totalStart = time.time()
        for i in range(ord(startLetter), ord(endLetter) + 1):
            letter = chr(i)
            try:
                self.sendQuery(self.theDate, letter, hashByCaseNumber, judgmentsOnly)
            except  Exception as e:
                self.errors.append('Letter: ' + letter + ', date: ' + self.theDate + ', Exception: ' + str(e))
        # self.logProgress(totalStart, startLetter, endLetter, len(hashByCaseNumber))
    def findSettlements(self, case):
        for entry in case['docket_entries']:
            if entry['description'] == 'POSSESSION $___& COST FED':
                settledDate = entry['date']
                filedDate = case['description']['filing_date']
                delta = settledDate - filedDate
                self.log(case['description']['case_num'] + "," + str(settledDate) + ','
                        + str(filedDate) + ',' + str(delta.days))
    def generateNames(self, rawName):
        names = rawName.split(',')
        for name in names:
            if re.match('\W*LLC\W*', name):
                return [rawName, '']
        if (len(names) == 1):
            return [names[0], '']
        if (len(names) > 2):
            firstName = ','.join(names[1 : len(names) - 1])
        else:
            firstName = names[1]
        lastName = names[0]
        return [firstName.strip(), lastName.strip()]
    def createParty(self, party) :
        if not party['address']:
            self.errors.append('No address for: ' + party['name'])
            return None
        [firstName, lastName] = self.generateNames(party['name'])
        addresses = party['address'].split('\n')
        address1 = ''
        cityStateZip = ''
        theRe = re.compile('^(\w+?) (\w\w) \d\d\d\d\d')
        for i in range(len(addresses)):
            if theRe.match(addresses[i]):
                cityStateZip = addresses[i]
                break;
            address1 = addresses[i] if i == 0 else (address1 + ', ' + addresses[i])
        if cityStateZip:
            [city, state, theZip] = cityStateZip.split(' ')
        else:
            self.errors.append('Unable to split city/state/zip for: ' + party['name'] +
                                ', ' + party['address'])
            return None
        return {
                'FIRST NAME' : firstName,
                'LAST NAME' : lastName,
                'ADDRESS 1' : address1,
                'ADDRESS 2' : '',
                'CITY' : city,
                'STATE' : state,
                'ZIP CODE' : party['zip']
        }
    def addPlaintiff(self, landlords, party, caseURL):
        theP = self.createParty(party)
        if theP:
            landlords[party['eid']] = theP
            self.plaintiffPriorities[party['eid']] = self.PLAINTIFF_PRIORITY[party['type']]
        else:
            landlordURL = r'https://gscivildata.shelbycountytn.gov/pls/gnweb/ck_public_qry_cpty.cp_personcase_details_idx?id_code=' + str(party['eid'])
            self.errors.append('Unable to get landlord address for landlord: ' + landlordURL + ', case: ' + caseURL)
    def createTenant(self, case, tenantMap, caseNumber):
        for party in case['parties']:
            caseURL = r'https://gscivildata.shelbycountytn.gov/pls/gnweb/ck_public_qry_doct.cp_dktrpt_frames?case_id=' + str(caseNumber)
            if party['type'] == 'DEFENDANT':
                theP = self.createParty(party)
                if theP:
                    tenantMap[caseNumber] = theP
                else:
                    self.errors.append('Unable to get tenant address for case: ' + caseURL)
    def loadMaps(self, a_z_cases, tenants, landlords, judgments):
        for caseNumber in list(a_z_cases):
            case = a_z_cases[caseNumber]
            if self.hasJudgment(case):
                self.createTenant(case, judgments, caseNumber)
            else:
                for party in case['parties']:
                    caseURL = r'https://gscivildata.shelbycountytn.gov/pls/gnweb/ck_public_qry_doct.cp_dktrpt_frames?case_id=' + str(caseNumber)
                    if party['type'] == 'DEFENDANT':
                        theP = self.createParty(party)
                        if theP:
                            tenants[caseNumber] = theP
                        else:
                            self.errors.append('Unable to get tenant address for case: ' + caseURL)
                    elif party['type'] in ['PRO SE LITIGANT', 'PLAINTIFF', 'ATTORNEY FOR PLAINTIFF']:
                        if not party['eid'] in self.plaintiffPriorities or (self.plaintiffPriorities[party['eid']] < self.PLAINTIFF_PRIORITY[party['type']]):
                            self.addPlaintiff(landlords, party, caseURL)
    def dumpInputData(self, a_z_cases, dateRange):
        with open('inputs_' + dateRange + '.json', 'w') as fp:            
            fp.write(json.dumps(a_z_cases, indent=4, sort_keys=True, default=str))
    def writeOneCSV(self, fileName, caseMap):
        sortedMap = dict(sorted(caseMap.items(), key=lambda item: item[1]['FIRST NAME'] + ',' + item[1]['LAST NAME']))
        theFieldNames = ['FIRST NAME', 'LAST NAME', 'ADDRESS 1', 'ADDRESS 2', 'CITY', 'STATE', 'ZIP CODE']
        with open(fileName, 'w', newline='') as csv_file:
            csvwriter = csv.DictWriter(csv_file, fieldnames = theFieldNames)
            csvwriter.writeheader()
            for t in list(sortedMap):
                csvwriter.writerow(sortedMap[t])
    def writeCSV(self, tenants, landlords, judgments):
        startDate = datetime.now() - timedelta(days = 7)
        self.dateRange = startDate.strftime(self.DATE_FORMAT) + '_' + self.endDate
        self.writeOneCSV('Tenant_Filings_' + self.dateRange + '.csv', tenants)
        self.writeOneCSV('Landlord_Filings_' + self.dateRange + '.csv', landlords)
        self.writeOneCSV('Tenant_Judgments_' + self.dateRange + '.csv', judgments)
    def filterCases(self, target_cases, source_cases):
        for caseNumber in list(source_cases):
            if self.hasJudgment(source_cases[caseNumber]):
                target_cases[caseNumber] = source_cases[caseNumber]
    def readFromLocal(self):
        a_z_cases = {}
        cutOffDate = datetime.now() - timedelta(days = 7)
        mypath = '.'
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        for fileName in onlyfiles:
            theMatch = re.match('.+(\d\d\d\d\-\d\d\-\d\d).(\d\d\d\d\-\d\d\-\d\d)\.json', fileName)
            if theMatch:
                with open(fileName, 'r') as fp:
                    source_cases =  json.loads(fp.read())
                    judgmentsOnly = False
                    if theMatch.group(2):
                        endDate = datetime.strptime(theMatch.group(2), self.DATE_FORMAT)
                        judgmentsOnly = cutOffDate > endDate
                    if judgmentsOnly:
                        self.filterCases(a_z_cases, source_cases)
                    else:
                        for caseNumber in list(source_cases):
                            a_z_cases[caseNumber] = source_cases[caseNumber]
        return a_z_cases
    def readFromAPI(self):
        a_z_cases = {}
        first = True
        theHeaders = {'Authorization' : 'Api-Key API_KEY_GOES_HERE'}
        host = 'http://npi-server-prod-1276539913.us-east-1.elb.amazonaws.com/api/cases/'
        for i in range(int(self.MAX_DAYS / 7)):
            endDate = datetime.strptime(self.theDate, self.DATE_FORMAT)
            startDate = endDate - timedelta(days = 7)
            url = host + '?start=' + startDate.strftime(self.DATE_FORMAT) + '&end=' + self.theDate
            response = requests.get(url, headers = theHeaders)
            api_cases = json.loads(response.text)
            source_cases = {}
            for case in api_cases:
                source_cases[case['case_num']] = case
            if first:
                for caseNumber in list(source_cases):
                    a_z_cases[caseNumber] = source_cases[caseNumber]
                first = False
            else:
                self.filterCases(a_z_cases, source_cases)
            newEndDate = datetime.strptime(self.theDate, self.DATE_FORMAT) - timedelta(days = 7)
            self.theDate = newEndDate.strftime(self.DATE_FORMAT)
        return a_z_cases
    def getAppropriateCases(self):
        return self.readFromAPI()
    def scrape(self):
        a_z_cases = {}
        endDate = self.theDate
        startTime = time.time()
        for i in range(self.MAX_DAYS):
            self.getByAlpha(self.startLetter, self.endLetter, a_z_cases, False)
            doWrite = (i % 7 == 6)
            if doWrite:
                dateRange = self.theDate + '_' + endDate
                self.dumpInputData(a_z_cases, dateRange)
                self.logProgress(startTime, self.startLetter, self.endLetter, len(a_z_cases))
                a_z_cases = {}
            currentDate = datetime.strptime(self.theDate, self.DATE_FORMAT)
            currentDate = currentDate - timedelta(days = 1)
            self.theDate = currentDate.strftime(self.DATE_FORMAT)
            if doWrite:
                endDate = self.theDate
                startTime = time.time()
    def run(self):
        self.log('Started: ' + self.toJSON())
        started = time.time()
        a_z_cases = self.getAppropriateCases()
        tenants = {}
        landlords = {}
        judgments = {}
        self.loadMaps(a_z_cases, tenants, landlords, judgments)
        self.writeCSV(tenants, landlords, judgments)
        for s in self.errors:
            self.log(s)
        self.log('Ended: ' + self.getElapsedStr(started))
    def test(self):
        self.theDate = '2022-04-03'
        self.run()

if __name__ == "__main__":
    AddressScraper().test()