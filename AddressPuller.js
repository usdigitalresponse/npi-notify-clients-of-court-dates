'use strict';
const fs = require('fs');
const https = require('https')

class Getter {
    Getter() {
        this.ret = 'empty result'
    }
    get(hostname, path) {
        const options = {
            hostname: hostname,
            port: 443,
            path: path,
            method: 'GET'
        }
        const req = https.request(options, res => {
            console.log(`res: ${res}`)
            console.log(`statusCode: ${res.statusCode}`)
            
            res.on('data', d => {
                process.stdout.write(d)
            })
        })          
        req.on('error', error => {
            console.error(error)
        })          
        req.end()
        return this.ret
    }    
}
class AddressPuller {
    constructor(host, path) {
        this.HOST = host
        this.PATH = path
    }
    pull() {
        let g = new Getter()
        let res = g.get(this.HOST, this.PATH)
        console.log('pulled: ' + res.substring(0, 128))
    }
}
class TransformerToAirtable {
    constructor() {}

    // for viewing possible field values
    displayValues(sourceData) {
        const parties = new Set()
        const docket_descriptions = new Set()
        for (const evictionCase of sourceData) {
            for (const party of evictionCase.parties) {
                parties.add(party.type)
            }
            for (const docket_entry of evictionCase.docket_entries) {
                docket_descriptions.add(docket_entry.description)
            }
        }
        console.log('Total cases: ' + sourceData.length)
        let i = 0
        for (const p of parties) {
            console.log(i + ' ' + p)
            i++
        }
        i = 0
        for (const d of docket_descriptions) {
            console.log(i + ' ' + d)
            i++
        }
    }
    extractFields(party, partyType) {
        if (!party) {
            return new Object()
        }
        let ret = new Object()
        let names = party.name.split(', ')
        if (names.length > 1) {
            ret[ partyType + 'FirstName' ] = names[1]
        }
        ret[ partyType + 'LastName' ] = names[0]
        let addressParts = party.address.split('\n')
        ret[ partyType + 'Address' ] = addressParts[0]
        addressParts = addressParts[1].split(' ') 
        ret[ partyType + 'City' ] = addressParts[0]
        ret[ partyType + 'State' ] = addressParts[1]
        ret[ partyType + 'Zip' ] = addressParts[2]
        return ret
    }
    createRow(evictionCase) {
        let topLevelCaseData = new Object()
        topLevelCaseData.evictionCaseNumber = evictionCase.case_num
        topLevelCaseData.dateFiled = evictionCase.filing_date
        topLevelCaseData.caseTitle = evictionCase.title
        let defendant = null
        let plaintiff = null
        let attorney = null
        let proSe = null
        for (const party of evictionCase.parties) {
            switch (party.type) {
                case "DEFENDANT" : defendant = party; break
                case "PLAINTIFF" : plaintiff = party; topLevelCaseData.plaintiffType = party.type; break
                case "ATTORNEY FOR PLAINTIFF" : attorney = party;  topLevelCaseData.plaintiffType = party.type; break
                case "PRO SE LITIGANT" : proSe = party;  topLevelCaseData.plaintiffType = party.type; break
            }
        }
        let landlord
        if (plaintiff) {
            landlord = plaintiff
        } else if (attorney) {
            landlord = attorney
        } else if (proSe) {
            landlord = proSe
        }
        topLevelCaseData.settlementDate = null
        for (const docket_entry of evictionCase.docket_entries) {
            if (docket_entry.description === 'POST JUDGMENT ORDER') {
                topLevelCaseData.settlementDate = docket_entry.date
            }
        }
        let defendantObj = this.extractFields(defendant, 'app')
        let landlordObj = this.extractFields(landlord, 'landlord')
        return {
            ...topLevelCaseData,
            ...defendantObj,
            ...landlordObj
        }
    }
    doTransform(sourceData) {
        let ret = []
        for (const evictionCase of sourceData) {
            let r = this.createRow(evictionCase)
            ret.push(r)
        }
        console.log('Processed ' + ret.length + ' records.')
        console.log('First record: ' + JSON.stringify(ret[0]))
        console.log('Last record: ' + JSON.stringify(ret[ret.length - 1]))
        return ret
    }
    loadTable(resultData) {
        // Lookup, call update if record exists, insert if it doesn't.
    }
    transform() {
        let sourceData = JSON.parse(fs.readFileSync('private.json')) // new AddressPuller(theHostName, thePath).pull()
        let resultData = this.doTransform(sourceData)
        this.loadTable(resultData)
    }
}
new TransformerToAirtable().transform()
