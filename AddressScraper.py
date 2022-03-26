# Rough code to figure out performance characteristics of Memphis county court web site.

from scrapers.court import case_id
import time
from datetime import datetime
from typing import List

class AddressScraper:
    def __init__(self):
        self.theDate = "2021-05-10"
    def log(self, message):
        timeTag = datetime.now()
        print('"' + str(timeTag) + '",' + message)
    def sendQuery(self, theDate, theLastInitial, hashByCaseNumber) -> List[int]:
        start = time.time()
        cases = case_id.CaseIdScraper().get(date = theDate, last_initial = theLastInitial)
        end = time.time()
        numCases = len(cases)
        for c in cases:
            # self.log(c['Eviction Case Number'] + ',"' + c['Case Title'] + '"')
            hashByCaseNumber[c['Eviction Case Number']] = c['Case Title']
        return [numCases, round(end - start)]
    def getByAlpha(self, startLetter, endLetter, hashByCaseNumber):
        total = 0
        # totalstart = time.time()
        for i in range(ord(startLetter), ord(endLetter) + 1):
            letter = chr(i)
            retVals = self.sendQuery(self.theDate, letter, hashByCaseNumber)
            # self.log(letter + "," + self.theDate + "," + str(retVals[0]) + "," + str(retVals[1]))
            total += retVals[0]
        # totalEnd = time.time()
        # self.log(startLetter + "-" + endLetter + "," + self.theDate + "," +
        #        str(round(totalEnd - totalstart)) + "," + str(total))
    def getByWildCard(self):
        wildcard_cases = {}
        retVals = self.sendQuery(self.theDate, "*", wildcard_cases)
        self.log("*," + self.theDate + "," + str(retVals[0]) + "," + str(retVals[1]))
        return wildcard_cases
    def run(self):
        a_z_cases = {}
        self.getByAlpha("a", "z", a_z_cases)
        wildcard_cases = self.getByWildCard()
        for key in list(wildcard_cases):
            msg = ''
            if key not in a_z_cases:
                msg = 'NOT'
            else:
                msg = '___'
            print(msg + "," + key + "," + wildcard_cases[key])


if __name__ == "__main__":
    AddressScraper().run()