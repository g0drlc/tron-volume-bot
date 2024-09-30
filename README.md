
# solid trex bot 



1. `python -m venv venv ` 

2. 
- for linux: 
    `source venv/bin/activate`
- for windows:
    `.\venv\Scripts\activate.bat`

3. `pip install -r requirements.txt`

4. `python solid_trex.py`

#### If you want to use this bot on the main grid, you need to get and enter the api key from https://www.trongrid.io/. But there is no need to enter the api key in the testnet network (demo mode).


Inside this folder there is a file called trx_sender.py
Using this file, you can send all the trons in the wallets to the main address, and you just need to give it the name of the created wallet file to send the trons balance of all the wallets in that file to the address you want. If you need to send it, you can use it with the command: python trx_sender.py and at the input it will take the address of the wallet you want to send to, and then it will ask you to enter the name of the file where the wallets are, for example : wallets1.txt and finally sends all the trx in the wallets in the file wallets1.txt to the address you want


***Please enter a minimum delay of 10 seconds, otherwise the bot may give an error***


Please be careful when entering the min_trade_amount and max_trade_amount values ​​so that the robot does not make an error when buying and selling (always consider the minimums in the exchanges and be sure to run it on the testnet network before running this robot on the mainnet)


# Warning: You are responsible for any loss of capital when using the robot.