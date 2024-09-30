from tronpy import Tron
from tronpy.keys import PrivateKey
from tronpy.exceptions import TransactionError
from decimal import Decimal
import trontxsize
import requests
from tronpy.providers import HTTPProvider



# ایجاد یک اتصال به شبکه ترون
# tron = Tron(HTTPProvider(api_key="2ed30a45-fe41-4421-b2c0-bb415a45d2f4")) # یا می‌توانید از شبکه اصلی استفاده کنید: Tron()

tron = Tron(network="nile")


# آدرس مقصد برای انتقال TRX
# recipient_address = 'TVqaEdGkZb4R6UCMxham9jSBhpUH1ZhLA7'
recipient_address = input('please enter your recipient adderss :')

# درخواست نام فایل ولت‌ها
wallet_file = input("Enter the wallet file name (For example wallets1.txt): ")

# خواندن ولت‌ها از فایل
def read_wallets(file_path):
    wallets = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for i in range(0, len(lines), 3):  # هر ولت شامل 3 خط است
            address = lines[i].strip().replace('Address: ', '')
            private_key = lines[i+1].strip().replace('Private Key: ', '')
            wallets.append({
                'address': address,
                'private_key': private_key
            })
    return wallets

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

# تابع برای ارسال TRX از ولت به مقصد
def send_trx_from_wallet(wallet, recipient_address):
    private_key = PrivateKey(bytes.fromhex(wallet["private_key"]))
    sender_address = wallet["address"]

    try:
        balance = Decimal(tron.get_account_balance(sender_address))
        print(f"Current balance of {sender_address}: {balance} TRX")

        available_balance = balance
        estimated_fees = []

        if balance > 0:
             # ساخت تراکنش برای شبیه‌سازی و تخمین کارمزد
            txn = tron.trx.transfer(
               sender_address,
                recipient_address,
                int(balance)
            ).memo("Fee estimation").build()

            # محاسبه هزینه تراکنش
            estimated_fee = calculate_transaction_fee(txn) * 10
            estimated_fees.append(estimated_fee)
            print(f"Estimated fee for transaction to {wallet['address']}: {estimated_fee} TRX")

            total_estimated_fee = sum(estimated_fees)
            print(f"Total estimated fees: {total_estimated_fee} TRX")

            # مرحله ۲: محاسبه موجودی قابل ارسال پس از کسر هزینه‌ها
            if available_balance <= total_estimated_fee:
                print("Not enough balance to cover all transaction fees.")

            # موجودی نهایی قابل ارسال به ولت‌ها
            available_balance -= total_estimated_fee

            # ساخت تراکنش برای ارسال تمام موجودی ولت به آدرس مقصد
            txn = (
                tron.trx.transfer(
                    sender_address,
                    recipient_address,
                    int((available_balance) * 1_000_000)  # ارسال کل موجودی به جز 1 TRX برای هزینه تراکنش
                )
                .memo("TRX distribution")
                .build()
                .sign(private_key)
            )

            txn_result = txn.broadcast().wait()
            print(f"Transaction result: {txn_result}")

            # بررسی وجود txid در نتیجه تراکنش
            if 'txid' in txn_result:
                print(f"Sent {balance} TRX from {sender_address} to {recipient_address}: {txn_result['txid']}")
            else:
                print(f"Transaction did not include 'txid'. Full result: {txn_result}")

        else:
            print(f"Insufficient balance in wallet {sender_address}.")

    except TransactionError as e:
        print(f"Transaction error while transferring from {sender_address} to {recipient_address}: {e}")
    except Exception as e:
        print(f"Error occurred while transferring from {sender_address} to {recipient_address}: {e}")

# خواندن ولت‌ها از فایل و ارسال TRX
wallets = read_wallets(wallet_file)

for wallet in wallets:
    send_trx_from_wallet(wallet, recipient_address)