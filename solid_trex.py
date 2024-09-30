import time
import random
import os
import requests
from tronpy import Tron
from tronpy.keys import PrivateKey
from tronpy.providers import HTTPProvider
from tronpy.exceptions import TransactionError
from decimal import Decimal
import trontxsize
from dataclasses import dataclass
from enum import Enum
import logging
import json
from pyfiglet import figlet_format
import sys
from termcolor import colored
from getpass import getpass
import atexit
from requests.exceptions import ConnectionError
import pyfiglet.fonts


logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


Nikoosen_logo = figlet_format(' Solid Trex ')


def green_logger(text):
    logger.info(colored(text, 'green'))


def yellow_logger(text):
    logger.info(colored(text, 'yellow'))


def red_logger(text):
    logger.info(colored(text, 'red', attrs=['bold']))


def colorize_text(text, start_color, end_color):
    """
    Colorizes the given text with a gradient from start_color to end_color.

    Args:
        text (str): The text to colorize.
        start_color (int): The starting color code.
        end_color (int): The ending color code.
    """

    color_delta = (end_color - start_color) / len(text)
    current_color = start_color

    colored_text = ""
    for char in text:
        colored_text += f"\033[{int(current_color)}m{char}\033[0m"
        current_color += color_delta

    return colored_text

def print_gradient_text(text, start_color, end_color, delay=0.00025):
    """
    Prints the colored text with a gradient effect, optionally with a delay between characters.

    Args:
        text (str): The text to colorize.
        start_color (int): The starting color code.
        end_color (int): The ending color code.
        delay (float): The delay between printing each character (optional).
    """

    colored_text = colorize_text(text, start_color, end_color)
    for char in colored_text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)

start_color = 31 
end_color = 32   
print()
time.sleep(0.5)
print()
print_gradient_text(Nikoosen_logo, start_color, end_color)
print('v1.0')

logger.info(colored('Bot in desinged for trading inclusively. see licence for more info', "green", attrs=['bold']))

# pv = PrivateKey(bytes.fromhex(main_wallet_private_key))

class Wallet:

    def __init__(self, name, address, private_key):
        self.name = name
        self.address = address
        self.pv = PrivateKey(bytes.fromhex(private_key))


@dataclass
class Contract:
    symbol: str
    address: str
    decimals: int = None


class BotSettings:
    num_wallets = 2
    trade_delay  = 2
    trade_min_amount = 100
    trade_max_amount = 200


class KnownWallets:
    owner_wallet = Wallet('owner', 'TM5w4eJzfhnsPBZrCLhaEVRznwVEUS8UCr', '76a868f6fdfac6de37900c89cbaf95e62c04e9612b428de49e6bf772fdac9afa')

    
class KnownContract:
    testnet_wtrx = Contract("NILE WTRX", "TYsbWxNnyTgsZaTFaue9hqpxkU3Fkco94a", 6)
    mainnet_wtrx = Contract("WTRX", "TNUC9Qb1rRpS5CbWLmNMxXBjyFoydXjWFR", 6)
    testnet_sunswap = Contract("NILE SunswapV2Router02", "TAMW6AJKgW9WeFxhCaQ2ZY56jRrJf4CjNv")
    mainnet_sunswap_router = Contract("SunswapV2Router02", "TXF1xDbVGdxFGbovmmmXvBGu8ZiE3Lq4mR")


demo_mode = input(colored("Do you want to enable demo mode on testnet? (yes/no): ", 'yellow', attrs=['bold'])).lower() == "yes"
if not demo_mode:
    api_key = getpass(colored("Please enter your trongrid.io api key: ", 'yellow', attrs=['bold']))
main_wallet_address = input(colored("What is your main wallet address: ", 'yellow', attrs=['bold']))
main_wallet_private_key = getpass(colored("What is your main wallet private key: ", 'yellow', attrs=['bold']))
num_wallets = int(input(colored("How many wallets do you want to create? ", 'yellow', attrs=['bold'])))
trade_delay = float(input(colored("How much delay do you want between your trades (seconds)? ", 'yellow', attrs=['bold'])))
min_trade_amount = float(input(colored('Minimum Amount of your Trade: ', attrs=['bold'])))
max_trade_amount = float(input(colored('Maximum Amount of your Trade: ', attrs=['bold'])))
target_token_address = input(colored('Please enter target token contract address(press enter for default path): ', 'yellow',attrs=['bold']))
tr_token = target_token_address if target_token_address is not None else 'TF17BgPaZYbz8oxbjhriubPDsA7ArKoLX3'
sell_after_purchase = input(colored("Do you want to sell the tokens after purchase? (yes/no): ", 'yellow', attrs=['bold'])).lower() == "yes"
read_pre = input(colored("Do you want to read from wallet file? (yes/no): ", 'yellow', attrs=['bold'])).lower() == "yes"

if demo_mode:
    fee_wallet_address = 'TVqaEdGkZb4R6UCMxham9jSBhpUH1ZhLA7'
else:
    fee_wallet_address = 'TLj3ZWs3kMYQNYLTRRR3EB3YgnNEmLaeAY'

# demo_mode = True
# if not demo_mode:
#     api_key = getpass(colored("Please enter your trongrid.io api key: ", 'yellow', attrs=['bold']))
# main_wallet_address = 'TVqaEdGkZb4R6UCMxham9jSBhpUH1ZhLA7'
# main_wallet_private_key = '1f8cf2d58cd213526d9ed51955d9ce74eb5fd4614d284ace2013b4601dfa07db'
# main_wallet_address = 'TM5w4eJzfhnsPBZrCLhaEVRznwVEUS8UCr'
# main_wallet_private_key = '76a868f6fdfac6de37900c89cbaf95e62c04e9612b428de49e6bf772fdac9afa'
# num_wallets = 3
# trade_delay = 10
# min_trade_amount = 10
# max_trade_amount = 15
# target_token_address = 'TF17BgPaZYbz8oxbjhriubPDsA7ArKoLX3'
# sell_after_purchase = True
# read_pre = False


SUNPUMP_ROUTER_ADDRESS = 'TAMW6AJKgW9WeFxhCaQ2ZY56jRrJf4CjNv'
MAX_SLIPPAGE = 0.1
FEE_LIMIT = 50 * 1_000_000
TOKEN_SELL_PERCENTAGE = None

# wtrx_addr = 'TYsbWxNnyTgsZaTFaue9hqpxkU3Fkco94a'
# target_token_addr = 'TF17BgPaZYbz8oxbjhriubPDsA7ArKoLX3'
path = []

if demo_mode:
    WTRX_CONTRACT_ADDRESS = "TYsbWxNnyTgsZaTFaue9hqpxkU3Fkco94a"
    green_logger('Enabling demo mode, connecting to tron testnet...')
    tron = Tron(network="nile")
    contract = tron.get_contract(KnownContract.testnet_sunswap.address)
    wtrx_address = KnownContract.testnet_wtrx.address
    path.append(wtrx_address)
    path.append(target_token_address)
    SUNSWAP_CON = tron.get_contract(KnownContract.testnet_sunswap.address)

else:
    WTRX_CONTRACT_ADDRESS = "TNUC9Qb1rRpS5CbWLmNMxXBjyFoydXjWFR"
    green_logger('Connecting to Tron Network')
    tron = Tron(HTTPProvider(api_key=api_key))
    contract = tron.get_contract(KnownContract.mainnet_sunswap_router.address)
    wtrx_address = KnownContract.mainnet_wtrx.address
    path.append(wtrx_address)
    path.append(target_token_address)
    SUNSWAP_CON = tron.get_contract(KnownContract.mainnet_sunswap_router.address)


target_token_connectin = tron.get_contract(target_token_address)


main_wallet = {
    "address": main_wallet_address,
    "private_key": main_wallet_private_key
}


def create_wallets(num_wallets):
    wallets = []
    for i in range(num_wallets):
        private_key = PrivateKey.random()
        public_key = private_key.public_key
        address = public_key.to_base58check_address()
        name = f"Wallet{i+1}"
        wallets.append({
            'name': name,
            'address': address,
            'private_key': private_key.hex(),
        })
    return wallets


def get_next_filename(base_name='wallets', extension='txt'):
    i = 1
    while True:
        file_name = f"{base_name}{i}.{extension}"
        if not os.path.exists(file_name):
            return file_name
        i += 1


def save_wallets_to_file(wallets):
    file_path = get_next_filename()
    with open(file_path, 'w') as f:
        for wallet in wallets:
            f.write(f"Address: {wallet['address']}\n")
            f.write(f"Private Key: {wallet['private_key']}\n\n")
    print(f"Wallets saved to {file_path}")


def get_bandwidth_price():
    url = "https://api.trongrid.io/wallet/getchainparameters"
    response = requests.get(url)
    data = response.json()
    bandwidth_price = Decimal(data['chainParameter'][3]['value']) / Decimal(1_000_000)
    return bandwidth_price


def calculate_transaction_fee(transaction):
    bandwidth_price = get_bandwidth_price()
    tx_size = trontxsize.get_tx_size({"raw_data": transaction._raw_data, "signature": transaction._signature})
    bandwidth_points = Decimal(tx_size) * bandwidth_price
    total_fee = bandwidth_points
    return total_fee


def transfer_trx(from_address, to, amount):
    '''
    build a transfer transaction (not signed)
    '''
    txn = tron.trx.transfer(
            from_address,
            to,
            int(amount * 1_000_000)
        ).memo("Fee wallet distribution").build()

    return txn


def distribute_trx(main_wallet, wallets, fee_wallet_address):
    try:
        total_balance = Decimal(tron.get_account_balance(main_wallet["address"]))
        # total_balance = 600 # TODO: revert back
        green_logger(f"Total balance retrieved: {total_balance} TRX")
        print('')
    except Exception as e:
        red_logger(f"Error retrieving balance for main wallet: {e}")
        return []

    priv_key = PrivateKey(bytes.fromhex(main_wallet["private_key"]))
    available_balance = total_balance
    successful_wallets = []
    estimated_fees = []

    fee_amount = total_balance * Decimal('0.05')

    try:
        fee_txn = transfer_trx(
                    main_wallet["address"],
                    fee_wallet_address,
                    int(fee_amount )
                    )

        estimated_fee = calculate_transaction_fee(fee_txn) * 10
        estimated_fees.append(estimated_fee)
        # print(f"Estimated fee for transaction to fee Wallet {fee_wallet_address}: {estimated_fee} TRX")

        fee_txn.sign(priv_key)

        fee_txn.broadcast().wait()
        # green_logger(f"Sent 5% of balance ({fee_amount} TRX) to fee wallet {fee_wallet_address}. Transaction result: {fee_txn_result}")
        available_balance -= fee_amount

    except Exception as e:
        print(f"Error occurred while transferring 5% to fee wallet {fee_wallet_address}: {e}")
        return successful_wallets

    trx_per_wallet = available_balance / Decimal(len(wallets))


    for wallet in wallets:
        
        try:
            txn = transfer_trx(
                KnownWallets.owner_wallet.address, 
                wallet['address'], 
                int(trx_per_wallet)
            )
            estimated_fee = calculate_transaction_fee(txn) * 10
            estimated_fees.append(estimated_fee)
            print(f"Estimated fee for transaction to {wallet['address']}: {estimated_fee} TRX")
        except Exception as e:
            print(f"Error estimating fee for {wallet['address']}: {e}")
            estimated_fees.append(Decimal('0'))

    total_estimated_fee = sum(estimated_fees)
    print(f"Total estimated fees: {total_estimated_fee} TRX")

    if available_balance <= total_estimated_fee:
        print("Not enough balance to cover all transaction fees.")
        return successful_wallets

    available_balance -= total_estimated_fee
    trx_per_wallet = available_balance / Decimal(len(wallets))

    if trx_per_wallet <= 0:
        print("Insufficient balance after accounting for fees.")
        return successful_wallets
    
    if trx_per_wallet > 80:
        for wallet in wallets:
            try:
                txn = (
                    tron.trx.transfer(
                        main_wallet["address"],
                        wallet["address"],
                        int(trx_per_wallet * 1_000_000) 
                    )
                    .memo("TRX distribution")
                    .build()
                    .sign(priv_key)
                )

                txn_result = txn.broadcast().wait()
                print('')
                print(f"Transaction result: {txn_result}")
                green_logger(f"Sent {trx_per_wallet} TRX from main wallet to {wallet['address']}")
            except Exception as e:
                red_logger(f"Error occurred while transferring to {wallet['address']}: {e}")

        return successful_wallets
    else:
        red_logger('Your wallet balance is not enough to cover the purchase costs. The minimum balance of each wallet must be 80 trx (consider this amount for fee_limit when purchasing and this amount must increase as much as the purchase amount, otherwise your purchase will not be completed). Please increase the balance of your main wallet or reduce the number of wallets and calculate so that at least 80 trx will be sent to each wallet in addition to the purchase amount !!')
        exit()



def deadline():
    return int(time.time()) + 300


def balance_of_token(wallet, con):
    balance = con.functions.balanceOf(wallet)
    decimals = con.functions.decimals()
    adjusted = balance / (10 ** decimals)
    return adjusted



def get_token_pair(from_token_address: str, to_token_address: str) -> list:
    token_in = tron.to_hex_address(from_token_address)
    token_out = tron.to_hex_address(to_token_address)
    return [token_in, token_out]


def approve_buy(wallet, pv, amount_in, path): 
        try:
            logger.info(f"Approving {wallet['name']} with address {wallet['address']}")
            factory_address = SUNSWAP_CON.functions.factory.call()
            factory_contact = tron.get_contract(factory_address)
            pair = factory_contact.functions.getPair(path[0], path[1])
            pair_contract = tron.get_contract(pair)

            pair_contract.abi = get_target_token_wtrx_pair_abi()

            txn = pair_contract.functions \
                .approve(wallet['address'], int(amount_in * 1000)) \
                .with_owner(wallet['address']) \
                .build().sign(pv)
            res =  txn.broadcast().wait()
            green_logger(f"Approve for {wallet['name']} with address {wallet['address']} successful")
        
        except ConnectionError as con: 
            yellow_logger('Connection Error. Trying again...')
            approve_buy(wallet, pv, amount_in, path)

        except Exception as e:
            red_logger(e)
            red_logger('Approve Failed.')
            return 1


def approve(token_contract, user_address: str, priv_key: str, tt_amount:int) -> bool:
    try:
        print('inside approve')
        txn = (
            token_contract.functions.approve(
                SUNPUMP_ROUTER_ADDRESS,
                tt_amount
            )
            .with_owner(user_address)
            .fee_limit(15_000_000)
            .build()
            .sign(priv_key)
            .broadcast()
        )
        print('approved')
        return handle_transaction(txn)

    except ConnectionError as con:
        yellow_logger('Connection Error. Trying again...')
        approve(token_contract, user_address, priv_key, tt_amount)

    except Exception as e:
        # print(f"Error performing raapprove: {e}")
        return False


def get_target_token_wtrx_pair_abi():
    with open('pair_contract_abi.json') as file:
        abi = json.load(file)
    return abi


def get_reserves(client, contract, path):
    pair_address = contract.functions.getPair(path[0],path[1])
    pair_contract = client.get_contract(pair_address)
    pair_contract.abi = get_target_token_wtrx_pair_abi()
    reserves = pair_contract.functions.getReserves()

    return reserves


def get_balance(token_address, wallet_address):
    jst_contract = tron.get_contract(token_address)
    balance = jst_contract.functions.balanceOf(wallet_address)
    return balance


def get_decimals(token_address):
    jst_contract = tron.get_contract(token_address)
    decimals = jst_contract.functions.decimals()
    return decimals


def is_approved(token_contract, user_address: str) -> bool:
    try:
        amount_approved = token_contract.functions.allowance(
            user_address, SUNPUMP_ROUTER_ADDRESS)
        if amount_approved > 0:
            logger.info('Already Approved...')
        return amount_approved > 0

    except Exception as e:
        print(f"Error performing approve check: {e}")
        return False


def handle_transaction(transaction_type, txn):
    txn_receipt = txn.wait()
    result = txn_receipt.get('receipt', {}).get('result')
    
    if result == 'SUCCESS':
        green_logger(f"{transaction_type.capitalize()} successful: {txn['txid']}") # green
        return True
    else:
        error_message = txn_receipt.get('resMessage')
        red_logger(f"{transaction_type.capitalize()} failed: {error_message}, txnId: {txn['txid']}") #red
        return False


def sell_token(token_address: str, wallet_dict: dict, private_key: str, sell_all=False) -> bool:
    global TOKEN_SELL_PERCENTAGE
    try:
        if sell_all:
            TOKEN_SELL_PERCENTAGE = 98
        else:
            if not TOKEN_SELL_PERCENTAGE:
                TOKEN_SELL_PERCENTAGE = random.uniform(80, 100)  

        user_address = wallet_dict['address']
        token_contract = tron.get_contract(token_address)
        token_symbol = token_contract.functions.symbol()
        path = get_token_pair(target_token_address, WTRX_CONTRACT_ADDRESS)
        target_token_contract  = tron.get_contract(target_token_address)
        token_balance = target_token_contract.functions.balanceOf(user_address)

        amount_in = int(token_balance * (TOKEN_SELL_PERCENTAGE / 100))

        if not is_approved(token_contract, wallet_dict['address']):
            approve(target_token_contract, user_address, private_key, amount_in)
            approve_buy(wallet_dict, private_key, amount_in, path)
            time.sleep(trade_delay)

            # token_address, user_address, priv_key
        if sell_all:
            logger.info(f'Sell Percentage: {100}%')
        else:
            logger.info(f'Sell Percentage: {TOKEN_SELL_PERCENTAGE}%')

        amounts_out = SUNSWAP_CON.functions.getAmountsOut(amount_in, path)        
        amount_out_min = int(amounts_out[1] * (1 - MAX_SLIPPAGE))
        logger.info(f"Sell {amount_in} {token_symbol} from {wallet_dict['name']} to {target_token_address}")
        txn = (
            SUNSWAP_CON.functions.swapExactTokensForETH(
                amountIn=amount_in,
                amountOutMin=amount_out_min,
                path=path,
                to=user_address,
                deadline=deadline()
            )
            .with_owner(user_address)
            .fee_limit(100_000_000)
            .build()
            .sign(private_key)
            .broadcast()
        )

        return handle_transaction(sell_token.__qualname__, txn)

    except Exception as e:
        logger.exception(e)
        red_logger(e)
        print(f"Error performing trade: {e}")
        return False



def buy_token(buy_amount:int, token_address: str, wallet_dict: dict, private_key_hex: str) -> bool:
    try:
        user_address = wallet_dict['address']
        token_contract = tron.get_contract(token_address)
        priv_key = private_key_hex

        deadline = int(time.time()) + 300

        path = get_token_pair(WTRX_CONTRACT_ADDRESS, target_token_address)

        if not is_approved(token_contract, wallet_dict['address']):
            approve_buy(wallet_dict, priv_key, buy_amount, path)
            # token_address, user_address, priv_key
        amounts_out = contract.functions.getAmountsOut(
            buy_amount, path)
        slippage_tolerance = MAX_SLIPPAGE
        amount_out_min = int(amounts_out[-1] * (1 - slippage_tolerance))
        logger.info(f"Purchase {buy_amount//1_000_000} TRX from {wallet_dict['name']} to {target_token_address}")
        
        txn = (
            contract.functions.swapExactETHForTokens.with_transfer(buy_amount)(
                amountOutMin=amount_out_min,
                path=path,
                to=user_address,
                deadline=deadline
            )
            .with_owner(user_address)
            .fee_limit(50_000_000)
            .build()
            .sign(priv_key)
            .broadcast()
        )

        return handle_transaction(buy_token.__qualname__, txn)

    except Exception as e:
        logger.error(f"Error performing trade: {e}")
        return False


def buy_until_insufficient_balance(wallets, con):
    while True:
        for wallet in wallets:
            try:    
                wal_balance = int(tron.get_account_balance(wallet['address']))
                
                tx_value = random.uniform(min_trade_amount, max_trade_amount)
                available_balance = 80 + tx_value
                if wal_balance < available_balance:
                    yellow_logger(f"Minimum balance of {wallet['name']} with {wallet['address']} is over.")
                    return
                print('Press Ctrl + C to stop the bot and sell all tokens ...')
                print('')  
                yellow_logger(f"Balance of {wallet['name']} with address {wallet['address']}: {wal_balance}")
                wal_private_key = PrivateKey(bytes.fromhex(wallet['private_key']))
                buy_token(int(tx_value * 1_000_000), wtrx_address, wallet, wal_private_key)

                print('')
            except Exception as e:
                red_logger(f"Purchase from {wallet['name']} failed")
                red_logger(f'There was an Error making the Transaction:\n{e}')
            time.sleep(trade_delay)
        print('')
        logger.info('press ctrl + c to stop bot and sell all token ...')


def buy_and_sell_until_insufficient_balance(wallets, router_con, target_token_addr):
    logger.debug('Entering function buy and sell until insufficient amounts')
    tx_value = random.uniform(min_trade_amount, max_trade_amount)

    while True:
        for wallet in wallets:
            try:    
                wal_balance = int(tron.get_account_balance(wallet['address']))
                available_balance = 80 + tx_value

                if wal_balance <= available_balance:
                    yellow_logger(f"Minimum balance of {wallet['name']} with {wallet['address']} is over.")
                    return True
                print('Press Ctrl + C to stop the bot and sell all tokens ...')
                print('')
                yellow_logger(f"TRX Balance of {wallet['name']} with address {wallet['address']}: {wal_balance}")
                tx_value = random.uniform(min_trade_amount, max_trade_amount)
                wal_private_key = PrivateKey(bytes.fromhex(wallet['private_key']))
                buy_token(int(tx_value * 1_000_000), wtrx_address, wallet, wal_private_key)

                print('')
            except Exception as e:
                red_logger(f"Purchase from {wallet['name']} failed")
                red_logger(f'There was an Error making the Transaction:\n{e}')
            time.sleep(trade_delay)

        for wallet in wallets:
            try:
                target_token_symbol = target_token_connectin.functions.symbol() 
                decimals = target_token_connectin.functions.decimals()
                traget_token_balance = target_token_connectin.functions.balanceOf(wallet['address'])
                human_target_token_balance = traget_token_balance // 10 ** decimals 
                print('Press Ctrl + C to stop the bot and sell all tokens ...')
                print('')  
                yellow_logger(f"TRX Balance of {wallet['name']} with address {wallet['address']}: {wal_balance} TRX")
                yellow_logger(f"{target_token_symbol} Balance of {wallet['name']} with address {wallet['address']}: {human_target_token_balance} {target_token_symbol}")

                wal_private_key = PrivateKey(bytes.fromhex(wallet['private_key']))
                sell_token(target_token_address, wallet, wal_private_key)
                print('')
            except Exception as e:
                red_logger(f"Sell from {wallet['name']} failed")
                red_logger(f'There was an Error making the Transaction:\n{e}')
            time.sleep(trade_delay)
        logger.info('press ctrl + c to stop bot and sell all token ...')
        print('')



def sync_liquidity_pool(router_contract, path): 
        try:
            logger.info("Syncing the liquidity pool")
            factory_address = router_contract.functions.factory.call()
            factory_contact = tron.get_contract(factory_address)
            pair = factory_contact.functions.getPair(path[0], path[1])
            pair_contract = tron.get_contract(pair)

            pair_contract.abi = get_target_token_wtrx_pair_abi()

            pair_contract.functions.sync()
              
            # green_logger(f"Approve for wallet {wallet['name']} with address {wallet['address']} successful")
        except Exception as e:
            red_logger(e)
            red_logger('Insufficient amounts of token.')
            return 1


end_flag = False



# Function to stop the bot
def stop_bot(wallets):
    global end_flag
    if end_flag:
        return 
    print("Stopping bot and selling all tokens...")

    def sell():
        wallets_sold = []
        factory_address = SUNSWAP_CON.functions.factory.call()
        factory_contact = tron.get_contract(factory_address)

        for wallet in wallets:
            wallets_sold.append(wallet)

        while True:

            reserves = get_reserves(tron, factory_contact, path)

            reserve_jst = reserves[0] 
            reserve_trx = reserves[1] 
                        
            for wallet in wallets:
                logger.debug(wallets_sold)
                decimals = target_token_connectin.functions.decimals()
                target_token_balance = int(target_token_connectin.functions.balanceOf(wallet['address'])) 
                human_target_token_balance = int(target_token_balance // (10 ** decimals))

                wal_balance = int(tron.get_account_balance(wallet['address']))
                
                
                # For Example JST
                target_token_symbol = target_token_connectin.functions.symbol()
               

                if len(wallets_sold) == 0: 
                    return
                
                if wal_balance < 80: 
                    yellow_logger('Wallet balance not sufficient!')
                    continue
                
                if human_target_token_balance == 0: 
                    wallets_sold.remove(wallet)
                    yellow_logger(f"{target_token_symbol} Balance of {wallet['name']} with address {wallet['address']}: {human_target_token_balance} {target_token_symbol}")
                    
                    yellow_logger('Insufficient amount of input token.')

                    continue
                wal_private_key = PrivateKey(bytes.fromhex(wallet['private_key']))
                try: 
                    target_token_value_trx = SUNSWAP_CON.functions.getAmountOut(int(target_token_balance), reserve_jst, reserve_trx)

                    if target_token_value_trx < 1 * 1_000_000:
                        yellow_logger('Small amount of target token to swap')
                        wallets_sold.remove(wallet)
                        continue

                    if wal_balance > 0 and target_token_balance > 0:   
                        yellow_logger(f"{target_token_symbol} Balance of {wallet['name']} with address {wallet['address']}: {human_target_token_balance} {target_token_symbol}")
                        yellow_logger(f"TRX Balance of {wallet['name']} with address {wallet['address']}: {wal_balance} TRX")

                        res = sell_token(target_token_address, wallet, wal_private_key, sell_all=True)
                        if res: 
                            wallets_sold.remove(wallet)
                        # else: 
                        #     raise RevertTransation('Transaction Reverted')
                        print('')
                    else:
                        yellow_logger(f"{target_token_symbol} Balance of {wallet['name']} with address {wallet['address']}: {human_target_token_balance} {target_token_symbol}")
                        yellow_logger(f"TRX Balance of {wallet['name']} with address {wallet['address']}: {wal_balance} TRX")
                        yellow_logger("Target Token balance insufficient, or not enough Tron...")
                        return 

                except Exception as e:
                    logger.exception(e)
                    red_logger(f"Sell from {wallet['name']} failed")
                    red_logger(f'There was an Error making the Transaction:\n{e}')
                time.sleep(trade_delay + 5 )


    sell()
    recipient_address = input('please enter your main wallet address for send all tron :')
    for wallet in wallets:
            try:
                private_key = PrivateKey(bytes.fromhex(wallet['private_key']))
                balance = Decimal(tron.get_account_balance(wallet['address']))
                print('')
                print(f"Current balance of {wallet['name']}: {balance} TRX")

                available_balance = balance
                estimated_fees = []

                if balance > 0:
                    # ساخت تراکنش برای شبیه‌سازی و تخمین کارمزد
                    txn = tron.trx.transfer(
                    wallet['address'],
                        recipient_address,
                        int(balance)
                    ).memo("Fee estimation").build()

                    estimated_fee = calculate_transaction_fee(txn) * 10
                    estimated_fees.append(estimated_fee)
                    print(f"Estimated fee for transaction to {wallet['address']}: {estimated_fee} TRX")

                    total_estimated_fee = sum(estimated_fees)

                    if available_balance <= total_estimated_fee:
                        logger.info("Not enough balance to cover all transaction fees.")

                    available_balance -= total_estimated_fee

                    txn = (
                        tron.trx.transfer(
                            wallet['address'],
                            recipient_address,
                            int((available_balance) * 1_000_000)
                        )
                        .memo("TRX distribution")
                        .build()
                        .sign(private_key)
                    )

                    txn_result = txn.broadcast().wait()
                    logger.info(f"Transaction result: {txn_result}")
                    green_logger(f"sent {balance} TRX from {wallet['name']} to {recipient_address} successful")
                else:
                    print(f"Insufficient balance in wallet {wallet['address']}.")

            except TransactionError as e:
                red_logger(f"Transaction error while transferring from {wallet['address']} to {recipient_address}: {e}")
            except Exception as e:
                red_logger(f"Error occurred while transferring from {wallet['address']} to {recipient_address}: {e}")


def read_wallets(file_path):
    wallets = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        print(lines)
        for i in range(0, len(lines), 2):  # هر ولت شامل 3 خط است
            # name = lines[i].strip().replace('name: ', '')
            address = lines[i].strip().replace('Address: ', '')
            private_key = lines[i+1].strip().replace('Private Key: ', '')
            wallets.append({
                'name': 'name',
                'address': address,
                'private_key': private_key
            })
            # print(wallets)
    return wallets


if __name__ == "__main__": 
    # target_token_con = tron.get_contract(target_token_address)
    if read_pre:
            # wallet_file = input(colored('enter wallet file path: ', 'yellow'))
        wallet_file = 'wallets10.txt'
        wallets = read_wallets(wallet_file)
    else: 
        wallets = create_wallets(num_wallets)
        save_wallets_to_file(wallets)
        distribute_trx(main_wallet, wallets, fee_wallet_address)
    
    atexit.register(stop_bot, wallets)
    
    try:
        
        # trade_wallets(wallets, sell_after_purchase)
        if sell_after_purchase:
            sell_token_percent = input('Do you want to specify a sell percentage?(yes/no) ').lower() == 'yes'
            if sell_token_percent:
                TOKEN_SELL_PERCENTAGE = float(input('How much of your portfolio would you like to sell?(e.g 80) ')) 

            end_flag = buy_and_sell_until_insufficient_balance(wallets, SUNSWAP_CON, target_token_address)
        else:
            buy_until_insufficient_balance(wallets, SUNSWAP_CON)
        
        yellow_logger('Operation is over successfuly.')
        print("Bot has completely stopped.")
    
    except KeyboardInterrupt as e:
        # stop_bot(wallets=wallets)
        print()
        
    except Exception as e: 
        print(e)

