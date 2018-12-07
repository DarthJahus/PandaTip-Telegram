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
    	"rpc-psw": "suchpassword",
    	"admins": [-0, 0],
    	"spam_filter": [5, 60]
    }

* `telegram-token`: Your bot's unique and secret token.
  > Create a new bot by talking with [@BotFather](https://t.me/BotFather) to get one. 
* `rpc-uri`: Address and port for the daemon.
  > We do not advice to expose the port to external network. Please, be cautious.
  > See [next section](#Pandacoin-daemon-configuration) to allow access for network addresses.
* `rpc-user`, `rpc-psw`: Username and password for the daemon.
  > You can set them in the `pandacoin.conf` file ([see next section](#Pandacoin-daemon-configuration)).
* `admins`: An array of administrators' Telegram UserID (as integers).
  > You can send `/user_id` to [@ContremaitreBot](https://t.me/ContremaitreBot) to know your UserID.
* `spam_filter`: An array of two integers. The first value is the number of actions a user can perform in a period of time, the 2nd value defines that period of time in seconds.
  > `"spam_filter": [5, 60]` means that users cannot perform more than 5 actions per minute.


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

- [x] Add service commands like `/pause` (pauses the bot for everyone), and maybe some commands to check the health of the daemon / wallet.
- [x] Populate `strings.json`
- [x] Add spam protection
- [ ] Per-user language
- [ ] ~~Show fiat equivalent for balance~~
- [ ] ~~Add `/price` and `/marketcap` commands~~
