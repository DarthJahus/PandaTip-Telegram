## PandaTip - Pandacoin tipbot for Telegram
 
### Dependencies 

* `apt-get install python-dev`
* `apt-get install python-pip`
* `pip install python-telegram-bot --upgrade`
* `pip install requests`
* `pip install emoji`


In order to run the tip-bot a Pandacoin-Core client is needed (pandacoind). 

### Configuration file

Create a `config.json` **JSON** file and set up the following parameters:

(sample)
 
    {
    	"telegram-token": "such:sicret-token",
    	"telegram-botname": "PandaTip",
    	"rpc-uri": "http://127.0.0.1:22444",
    	"rpc-user": "panda",
    	"rpc-psw": "suchpassword"
    }

### Pandacoin daemon configuration

A `pandacoin.conf` file is needed in data directory.

(sample)

    server=1
    daemon=1
    staking=0
    rpcuser=muchuser
    rpcpassword=suchsicret
    pid=pandacoind.pid
    rpcallowip=127.0.0.1
    rpcconnect=127.0.0.1

---

### ToDo

- [ ] Per-user language
- [x] Add service commands like `/pause` (pauses the bot for everyone), and maybe some commands to check the health of the daemon / wallet.
- [x] Populate `strings.json`
- [ ] Show fiat equivalent for balance
- [ ] Add `/price` and `/marketcap` commands
- [x] Add spam protection
