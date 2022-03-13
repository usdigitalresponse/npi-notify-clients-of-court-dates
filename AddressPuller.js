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
    doTransform(sourceData) {
        let ret = []
        return ret
    }
    loadTable(resultData) {
//        this.clearTable()

    }
    transform() {
        let sourceData = theData // new AddressPuller(theHostName, thePath).pull()
        let resultData = this.doTransform(sourceData)
        this.loadTable(resultData)
    }
}
new TransformerToAirtable().transform()
