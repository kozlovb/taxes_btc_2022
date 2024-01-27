#!/usr/bin/env python3
# Register accounts for all bought BTC in Euro. So it looks like this.
# ? ? ?
# amount, date, price
from datetime import datetime
from datetime import timedelta

def read_register():
    file3 = open("/Users/bkozlov/T2022/BTC/register.txt", 'r')
    register_lines = file3.readlines()
    register_info = []
    for r in register_lines:
        register_fields = r.split(",")
            #qty time price
        register_info.append([float(register_fields[0]), datetime.fromtimestamp(float(register_fields[1])), float(register_fields[2])])

    amount_to_sell(register_info, datetime(2022, 7, 13, 0, 0, 0))
    return register_info

def save_new_register(register_info):
    with open("/Users/bkozlov/T2022/BTC/new_register.txt", "w") as f:
        old_timestamp = register_info[0][1].timestamp()
        for r in register_info:
            new_timestamp = r[1].timestamp()
            if new_timestamp < old_timestamp:
                print("ERROR in register timestamp")
                exit()
            f.write(str(r[0]) + "," + str(r[1].timestamp()) + "," + str(r[2])+ "\n")

def amount_to_sell(register_info, date_to_sell):
    amount_to_sell = 0
    for r in register_info:
        if date_to_sell > r[1] + timedelta(days = 366):
            amount_to_sell += r[0]
    print("Amount_to_sell", amount_to_sell)

def update_register(register, fee, t):
    # if sell or buyhyh
    taxable_delta = 0
    if t[0] == "buy":
        register = update_register_buy(register, t)
    elif t[0] == "sell":
        register , taxable_delta = update_register_sell(register, t)
    else:
        print("Unexpected trade nor buy or sell")
        exit()
    return register, fee + t[3], taxable_delta

def update_register_buy(register, t):
    qty = t[4]
    time_since_ep = t[1]
    price = t[2]
    register.append([qty, time_since_ep, price])
    return register

def update_register_sell(register, t):
    register_bfore_line_sub = sum_register(register)
    print(register_bfore_line_sub)
    new_register = []
    qty = t[4]
    time_since_ep = t[1]
    price = t[2]
    taxable_delta = 0
    for r in register:
        if qty == 0:
            new_register.append([r[0], r[1], r[2]])
        if qty > 0 and qty >= r[0]:
            qty = qty - r[0]
            if r[1] + timedelta(days = 365) > time_since_ep:
                taxable_delta += r[0]*(price - r[2])
        elif qty > 0 and qty < r[0]:
            new_register.append([r[0] - qty, r[1], r[2]])
            if r[1] + timedelta(days = 366) > time_since_ep:
                taxable_delta += qty*(price - r[2])
            qty = 0
    register_after_line_sub = sum_register(new_register)
    print(register_after_line_sub)
    return new_register, taxable_delta

#Parse to datetime kraken time
#2022-07-17 17:28:32.3624
def parse_to_date(line):
    x = line.split()
    year_month_day = x[0].split("-")
    hour_min_sec = x[1].split(":")
# datetime(year, month, day, hour, minute, second, microsecond)
    return datetime(int(year_month_day[0]), int(year_month_day[1]), int(year_month_day[2]), int(hour_min_sec[0]), int(hour_min_sec[1]), int(float(hour_min_sec[2])))

def read_kraken_trades():
    file = open("/Users/bkozlov/T2022/BTC/kraken_trades.txt", "r")
    trade_lines = file.readlines()
    trade_info = []
    for t in trade_lines[1:]:
        trade_fields = t.split(",")
        #   0        1         2     3       4        5         6      7      8    9      10       11      12
        #"txid","ordertxid","pair","time","type","ordertype","price","cost","fee","vol","margin","misc","ledgers"

        if str(trade_fields[2]) == 'XXBTZEUR':
            # 0 type buy or sell, 1 date ,2 price in euros, 3 fee in euros, 4 qty -vol in btc.
            trade_info.append([str(trade_fields[4]), parse_to_date(str(trade_fields[3])),float(trade_fields[6]), float(trade_fields[8]), float(trade_fields[9])])
    return trade_info
def read_kraken_ledger():
    trade_info = []
    with open("/Users/bkozlov/T2022/BTC/ledgers2021.txt", "r") as f:
        ledger_lines = f.readlines()

        #read lines by two in a loop
        for i in range(1, len(ledger_lines), 2):
            #   0      1       2     3       4        5         6      7        8    9          
            #"txid","refid","time","type","subtype","aclass","asset","amount","fee","balance"
            ledger_fields1 = ledger_lines[i].split(",")
            ledger_fields2 = ledger_lines[i+1].split(",")
            # each field in ledger has "" around it strip them
            for j in range(len(ledger_fields1)):
                ledger_fields1[j] = ledger_fields1[j].replace('"', '')
            #same for second line
            for j in range(len(ledger_fields2)):
                ledger_fields2[j] = ledger_fields2[j].replace('"', '')            
            # first compare refid if not equal exit
            if ledger_fields1[1] != ledger_fields2[1]:
                print("ERROR in ledger")
                exit()
            if ledger_fields1[3] == "trade":
                # 0 type buy or sell, 1 date ,2 price in euros, 3 fee in euros, 4 qty -vol in btc.
                buy_or_sell = ""
                euro_fields = []
                btc_fields = []
                if ledger_fields1[6]=="XXBT" and ledger_fields2[6]=="ZEUR":
                    buy_or_sell = "sell"
                    btc_fields = ledger_fields1
                    euro_fields = ledger_fields2
                elif ledger_fields1[6]=="ZEUR" and ledger_fields2[6]=="XXBT":
                    buy_or_sell = "buy"
                    btc_fields = ledger_fields2
                    euro_fields = ledger_fields1
                if buy_or_sell != "":
                    # seems btc fee is always 0 if not exit:
                    if float(btc_fields[8]) != 0:
                        print("ERROR in ledger, btc fee is not 0")
                        exit()

                    #TODO: look later into fees as sometimes they are in btc and sometimes in eur
                     # 0 type buy or sell,             1 date ,                       2 price in euros,                          3 fee in euros,       4 qty -vol in btc.
                    trade_info.append([buy_or_sell, parse_to_date(str(btc_fields[2])),abs(float(euro_fields[7])/float(btc_fields[7])), float(euro_fields[8]), abs(float(btc_fields[7]))])
            if ledger_fields1[3] == "spend":
                # 0 type buy or sell, 1 date ,2 price in euros, 3 fee in euros, 4 qty -vol in btc.
                buy_or_sell = ""
                euro_fields = []
                btc_fields = []
                if ledger_fields1[6]=="ZEUR" and ledger_fields2[6]=="XXBT":
                    buy_or_sell = "buy"
                    euro_fields = ledger_fields1
                    btc_fields = ledger_fields2
                    #TODO: look later into fees as sometimes they are in btc and sometimes in eur
                    # 0 type buy or sell,             1 date ,                       2 price in euros,                          3 fee in euros,       4 qty -vol in btc.
                    trade_info.append([buy_or_sell, parse_to_date(str(btc_fields[2])),abs(float(euro_fields[7])/float(btc_fields[7])), float(euro_fields[8]), abs(float(btc_fields[7]))])
                if ledger_fields1[6]=="XXBT" and ledger_fields2[6]=="USDT":
                    # there was one trade btc to usdt:
                    buy_or_sell = "sell"
                    btc_fields = ledger_fields1
                    usdt_fields = ledger_fields2
                    usdt_to_euro_at_trade_time = 0.901
                    trade_info.append([buy_or_sell, parse_to_date(str(btc_fields[2])),usdt_to_euro_at_trade_time * abs(float(usdt_fields[7])/float(usdt_fields[7])), usdt_to_euro_at_trade_time*float(usdt_fields[8]), abs(float(btc_fields[7]))])
    return trade_info                
                
            #print(ledger_lines[i])
            #print(ledger_lines[i+1])
            #print("-------------")
            #print("-------------")
            #print("-------------    
 
def sum_register(register):
    sum = 0
    for r in register:
        sum += r[0]
    return sum

def sum_trades(trades):
    sum = 0
    for t in trades:
        if t[0] == "buy":
            sum += t[4]
        else:
            sum -= t[4]
    return sum

def process():
    fee = 0
    taxable = 0
    register = read_register()
    #trades = read_kraken_trades()
    trades = read_kraken_ledger()

    f_sum = sum_register(register)
    print("before trades sum {}".format(f_sum))
    t_sum = sum_trades(trades)
    print("trade accounts to {}".format(t_sum))

    for t in trades:
        register, fee, taxable_delta = update_register(register, fee, t)
        taxable = taxable + taxable_delta

    print("total fee {}".format(fee))
    print("taxable {}", taxable)
    save_new_register(register)
    f_sum_after_trades = sum_register(register)
    print("sum after trades {}".format(f_sum_after_trades))
    print("descrapancy in the beggining {}".format(f_sum - 4.6127189200))
    print("descrapancy at the end {}".format(f_sum_after_trades - 3.5852546400))
process()
