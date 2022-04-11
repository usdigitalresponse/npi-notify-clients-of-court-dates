import time
from datetime import datetime
from datetime import timedelta
import sys
import re
import json
import csv
import requests
import os

class PostcardAddressCreator:
    """Read court case data from AWS webservice.
    Create three CSV files containing addresses for landlord and tenants for:
    - tenant filings
    - landlord filings
    - tenant judgments
    """
    def __init__(self):
        self.errors = []
        """Save up errors to display when we're finished.
        """

        self.MAX_DAYS = 260
        """ Look back this many days for judgments. """
        
        self.DATE_FORMAT = '%Y-%m-%d'
        self.theDate = datetime.now().strftime(self.DATE_FORMAT)
        self.numDays = 7
        """ Date range is defined by self.theDate
        going backwards self.numDays number of days.
        """

        self.dateRange = self.theDate
        self.endDate = self.theDate
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
        """If there are multiple plaintiff parties,
        use this to determine which to use for 'landlord'.
        3 is highest priority.
        """

        self.plaintiffPriorities = {}
        """Keep track of priorities while iterating over list of parties.
        """
        self.addDiagnostics = False
        """Add more columns to CSVs to help diagnose issues.
        """
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
        """Utility for dumping object containing fields that don't automatically support str()
        """
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True)
    def log(self, message):
        timeTag = datetime.now()
        print('"' + str(timeTag) + '",' + message)
    def hasJudgment(self, case):
        """ If one of the specified docket entry types is within date range,
        a judgment has been made against tenant.
        """
        today = datetime.now()
        minDay = today - timedelta(days = self.numDays)
        for entry in case['docket_entries']:
            if entry['description'] in ['POSSESSION $___& COST FED', 'POSSESSION ONLY FED']:
                if ' ' in entry['date']:
                    splitter = ' '
                else:
                    splitter = 'T'   
                settledDate = datetime.strptime(entry['date'].split(splitter)[0], self.DATE_FORMAT)
                if (settledDate <= today) and (settledDate >= minDay):
                    return True
        return False
    def getElapsedStr(self, start):
        """Utility for displaying elapsed MM:SS.
        """
        theEnd = time.time()
        totalSeconds = int(round(theEnd - start))
        minutes = round(totalSeconds / 60)
        seconds = round(totalSeconds % 60)
        return '{0:0>2}:{1:0>2}'.format(minutes, seconds)
    def generateNames(self, rawName):
        """Given raw name from court website, attempt to find first and last names.
        """
        names = rawName.split(',')
        for name in names:
            if re.match('\W*LLC\W*', name):
                """Don't split a company name.
                """
                return [rawName, '']
        if (len(names) == 1):
            return [names[0], '']
        if (len(names) > 2):
            """Join all except last name into first name.
            """
            firstName = ','.join(names[1 : len(names) - 1])
        else:
            firstName = names[1]
        lastName = names[0]
        return [firstName.strip(), lastName.strip()]
    def createParty(self, party):
        """Given party data from the website, attempt to extract the names and address.
        """
        if not party['address'] or party['address'] == 'unavailable':
            return None
        [firstName, lastName] = self.generateNames(party['name'])
        addresses = party['address'].split('\n')
        address1 = ''
        cityStateZip = ''
        theZip = party['zip']
        theRe = re.compile('^([\w ]+?) (\w\w) (\d\d\d\d\d)')
        for i in range(len(addresses)):
            if theRe.match(addresses[i]):
                cityStateZip = addresses[i]
                break;
            address1 = addresses[i] if i == 0 else (address1 + ', ' + addresses[i])
        if cityStateZip:
            theMatch = theRe.match(cityStateZip)
            city = theMatch.group(1)
            state = theMatch.group(2)
            if not re.match('\d\d\d\d\d', theZip):
                """If zip code field not filled in, attempt to get from address.
                """
                theZip = theMatch.group(3)
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
                'ZIP CODE' : theZip
        }
    def addPlaintiff(self, landlords, party, caseURL):
        """Add plaintiff (e.g., 'landlord') address to landlords map,
        which is keyed by eid from website (e.g., '@nnnnnnn').
        """
        theP = self.createParty(party)
        landlordURL = r'https://gscivildata.shelbycountytn.gov/pls/gnweb/ck_public_qry_cpty.cp_personcase_details_idx?id_code=' + str(party['eid'])
        if theP:
            if self.addDiagnostics:
                theP['URL'] = landlordURL
            landlords[party['eid']] = theP
            self.plaintiffPriorities[party['eid']] = self.PLAINTIFF_PRIORITY[party['type']]
        elif party['address'] != 'unavailable':
            self.errors.append('Unable to get landlord address for landlord: ' + landlordURL + ', case: ' + caseURL)
    def createTenantFromParty(self, party, tenantMap, caseNumber):
        """Add tenant address to appropriate map,
        which is keyed by case number + tenant id,
        since there can be multiple tenants at different addresses per case.
        """
        caseURL = r'https://gscivildata.shelbycountytn.gov/pls/gnweb/ck_public_qry_doct.cp_dktrpt_frames?case_id=' + str(caseNumber)
        theP = self.createParty(party)
        if theP:
            if self.addDiagnostics:
                theP['URL'] = caseURL
            tenantMap[str(caseNumber) + party['eid']] = theP
        elif party['address'] != 'unavailable':
            self.errors.append('Unable to get tenant address for case: ' + caseURL)
    def createTenant(self, case, tenantMap, caseNumber):
        for party in case['parties']:
            if party['type'] == 'DEFENDANT':
                self.createTenantFromParty(party, tenantMap, caseNumber)
    def loadMaps(self, a_z_cases, tenants, landlords, judgments):
        """Iterate through cases to build three maps,
        which will be used to create CSVs.
        """
        for caseNumber in list(a_z_cases):
            case = a_z_cases[caseNumber]
            if self.hasJudgment(case):
                self.createTenant(case, judgments, caseNumber)
            else:
                for party in case['parties']:
                    if party['type'] == 'DEFENDANT':
                        self.createTenantFromParty(party, tenants, caseNumber)
                    elif party['type'] in ['PRO SE LITIGANT', 'PLAINTIFF', 'ATTORNEY FOR PLAINTIFF']:
                        if not party['eid'] in self.plaintiffPriorities or (self.plaintiffPriorities[party['eid']] < self.PLAINTIFF_PRIORITY[party['type']]):
                            caseURL = r'https://gscivildata.shelbycountytn.gov/pls/gnweb/ck_public_qry_doct.cp_dktrpt_frames?case_id=' + str(caseNumber)
                            self.addPlaintiff(landlords, party, caseURL)
    def writeOneCSV(self, fileName, caseMap):
        """Write one CSV file, sorted by first name + last name.
        The sorting is just to make reading and comparing files easier.
        It isn't needed by the mailing house.
        """
        sortedMap = dict(sorted(caseMap.items(), key=lambda item:
                            item[1]['FIRST NAME'] + ',' + item[1]['LAST NAME']+ ',' + item[1]['ADDRESS 1']))
        theFieldNames = ['FIRST NAME', 'LAST NAME', 'ADDRESS 1', 'ADDRESS 2', 'CITY', 'STATE', 'ZIP CODE']
        if self.addDiagnostics:
            theFieldNames.append('URL')
        with open(fileName, 'w', newline='') as csv_file:
            csvwriter = csv.DictWriter(csv_file, fieldnames = theFieldNames)
            csvwriter.writeheader()
            for t in list(sortedMap):
                csvwriter.writerow(sortedMap[t])
    def writeCSVs(self, tenants, landlords, judgments):
        startDate = datetime.now() - timedelta(days = self.numDays)
        self.dateRange = startDate.strftime(self.DATE_FORMAT) + '_' + self.endDate
        self.writeOneCSV('Tenant_Filings_' + self.dateRange + '.csv', tenants)
        self.writeOneCSV('Landlord_Filings_' + self.dateRange + '.csv', landlords)
        self.writeOneCSV('Tenant_Judgments_' + self.dateRange + '.csv', judgments)
    def filterCases(self, target_cases, source_cases):
        for caseNumber in list(source_cases):
            if self.hasJudgment(source_cases[caseNumber]):
                target_cases[caseNumber] = source_cases[caseNumber]
    def readFromAPI(self, apiKey):
        """Read a week's worth of data at a time.
        Load map with appropriate cases.
        """
        a_z_cases = {}
        first = True
        theHeaders = {'Authorization' : 'Api-Key ' + apiKey}
        host = 'http://npi-server-prod-1276539913.us-east-1.elb.amazonaws.com/api/cases/'
        for i in range(int(self.MAX_DAYS / 7)):
            endDate = datetime.strptime(self.theDate, self.DATE_FORMAT)
            startDate = endDate - timedelta(days = 7)
            url = host + '?start=' + startDate.strftime(self.DATE_FORMAT) + '&end=' + self.theDate
            response = requests.get(url, headers = theHeaders)
            api_cases = json.loads(response.text)
            source_cases = {}
            for case in api_cases:
                source_cases[int(case['case_num'])] = case
            if first:
                for caseNumber in list(source_cases):
                    a_z_cases[caseNumber] = source_cases[caseNumber]
                first = False
            else:
                self.filterCases(a_z_cases, source_cases)
            newEndDate = datetime.strptime(self.theDate, self.DATE_FORMAT) - timedelta(days = 8)
            self.theDate = newEndDate.strftime(self.DATE_FORMAT)
        return a_z_cases
    def run(self):
        self.log('Started: ' + self.toJSON())
        try:
            apiKey = os.environ['CASES_API_KEY']
        except:
            self.log('No CASES_API_KEY system environment variable')
            return
        started = time.time()
        a_z_cases = self.readFromAPI(apiKey)
        tenants = {}
        landlords = {}
        judgments = {}
        self.loadMaps(a_z_cases, tenants, landlords, judgments)
        self.writeCSVs(tenants, landlords, judgments)
        for s in self.errors:
            self.log(s)
        self.log('Ended: ' + self.getElapsedStr(started))

if __name__ == "__main__":
    PostcardAddressCreator().run()