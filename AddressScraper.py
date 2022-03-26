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
        totalstart = time.time()
        for i in range(ord(startLetter), ord(endLetter) + 1):
            letter = chr(i)
            self.sendQuery(self.theDate, letter, hashByCaseNumber)
        totalEnd = time.time()
        totalSeconds = int(round(totalEnd - totalstart))
        minutes = round(totalSeconds / 60)
        seconds = round(totalSeconds % 60)
        elapsedTime = '{0:0>2}:{1:0>2}'.format(minutes, seconds)
        self.log(startLetter + "-" + endLetter + "," + self.theDate + "," +
                elapsedTime)
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
    def run(self):
        a_z_cases = {}
        self.getByAlpha("a", "z", a_z_cases)

if __name__ == "__main__":
    AddressScraper().run()