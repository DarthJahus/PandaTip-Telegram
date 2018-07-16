## PandaTip - Pandacoin tipbot for Telegram
 
### Dependencies 

* `apt-get install python3`
* `apt-get install python3-pip`
* `pip3 install beautifulsoup4`
* `pip3 install python-telegram-bot --upgrade`


In order to run the tip-bot a Pandacoin-Core client is needed (pandacoind). 

### Configuration file

JSON file

Template:

    {
    	"telegram-token": "such:sicret-token",
    	"telegram-botname": "PandaTip",
    	"rpc-uri": "http://127.0.0.1:22444",
    	"rpc-user": "panda",
    	"rpc-psw": "suchpassword"
    }

---

Forked from https://github.com/samgos/reddbot-telegram
