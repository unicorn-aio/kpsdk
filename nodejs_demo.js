const fs = require("fs")
const axios = require("axios")
const needle = require('needle');
const querystring = require('querystring');
const FormData = require('form-data');
const {gzip, ungzip} = require('node-gzip');


class UnicornSDK {
    constructor(token) {
        this.baseURL = "https://us.unicorn-bot.com"
        // this.baseURL = "http://127.0.0.1:8000"
        this.token = token
        this.CLIENT = axios.create({
            baseURL: this.baseURL,
            headers: {
                "Authorization": this.getAuthorization()
            },
            proxy: this.getProxyForSDK(),
        })
        this.XSESSIONDATA = null
    }

    getToken() {
        return this.token
    }

    getAuthorization() {
        return "Bearer " + this.getToken()
    }

    getProxyForSDK() {
        return {
            host: "127.0.0.1",
            port: 8888,
        }
    }

    getProxyForSDKSimple() {
        return "http://127.0.0.1:8888"
    }

    find_cookie(cookies, name) {
        for (let idx in cookies) {
            let cookie = cookies[idx]
            let kv = cookie.split(";")[0]
            let m = kv.match(/(\w+)\=(\S+)/)
            if (m) {
                let k = m[1]
                let v = m[2]
                if (k === name) {
                    return v
                }
            }
        }
    }

    async init_session(sessionid, platform = "ANDROID") {
        let resp = await needle(
            "post",
            this.baseURL + "/api/session/init/",
            {
                "sessionid": sessionid,
                "platform": platform,
            },
            {
                headers: {
                    "Authorization": this.getAuthorization()
                },
                proxy: this.getProxyForSDKSimple(),
                json: true,
                follow_set_cookies: true
            }
        )
        if (resp.statusCode != 200) {
            throw Error(`init_session --> ${resp.statusCode} --> ${JSON.stringify(resp.body)}`)
        }

        this.XSESSIONDATA = resp.cookies["XSESSIONDATA"]
        console.debug("XSESSIONDATA:", this.XSESSIONDATA)
        return resp.body
    }

    async init_session_axios(sessionid, platform = "ANDROID") {
        try {
            let resp = await this.CLIENT.post(
                "/api/session/init/",
                {
                    "sessionid": sessionid,
                    "platform": platform,
                },
            )

            this.XSESSIONDATA = this.find_cookie(resp.headers["set-cookie"], "XSESSIONDATA")
            console.debug("XSESSIONDATA:", this.XSESSIONDATA)
            return resp.data
        } catch (e) {
            let resp = e.response
            throw Error(`init_session --> ${resp.status}: ${resp.statusText}`)
        }
    }

    async parse_ips(host, ipsjs) {
        let params = {
            "kpver": "v20210513",
            "host": host,
            "site": "VEVE",
            "compress_method": "GZIP",
        }
        var form = {
            ips_js: {
                buffer: ipsjs,
                filename: 'ips_js',
                content_type: 'application/octet-stream'
            }
        }
        let resp = await needle(
            "post",
            this.baseURL + "/api/kpsdk/ips/" + "?" + querystring.stringify(params),
            form,
            {
                headers: {
                    "Authorization": this.getAuthorization()
                },
                'cookies': {
                    XSESSIONDATA: this.XSESSIONDATA,
                },
                multipart: true,
                proxy: this.getProxyForSDKSimple(),
            }
        )
    }

    async parse_ips_axios(host, ipsjs) {
        try {
            var formData = new FormData();
            formData.append("ips_js", ipsjs, {filename:"ips_js"})
            let headers = formData.getHeaders()
            headers["Cookie"] = `XSESSIONDATA=${this.XSESSIONDATA}`
            let resp = await this.CLIENT.post(
                "/api/kpsdk/ips/",
                formData,
                {
                    headers: headers,
                    params: {
                        "kpver": "v20210513",
                        "host": host,
                        "site": "VEVE",
                        "compress_method": "GZIP",
                    }
                }
            )
        } catch (e) {
            console.error(JSON.stringify(e))
            let resp = e.response
            throw Error(`init_session --> ${resp.status}: ${resp.statusText}, ${resp.data}`)
        }

    }
}


console.log("hello world!")

const startDemo = async () => {
    const my_token = "TOKEN_FROM_LOGIN"
    let sdk = new UnicornSDK(my_token)

    resp = await sdk.init_session("testid")
    console.log(resp)

    let ua = resp["user_agent"]

    var ipsjs = fs.readFileSync('./tests/ips.js', 'utf8')
    const gzipd_ipsjs = await gzip(ipsjs)

    kpparam = await sdk.parse_ips("https://mobile.api.prod.veve.me", gzipd_ipsjs)
}

startDemo().then(res => {
    console.log("Yes!")
}).catch(err => {
    console.error(err)
})
