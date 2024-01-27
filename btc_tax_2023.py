#!/usr/bin/env python3

# Register accounts for all bought BTC in Euro. So it looks like this.
# ? ? ?
# amount, date, price

from datetime import datetime
from datetime import timedelta

# Number of seconds in a day
SECONDS_IN_DAY = 24 * 60 * 60

# Number of seconds in 365 days
SECONDS_IN_YEAR = 365 * SECONDS_IN_DAY

#Parse to datetime kraken time
#2022-07-17 17:28:32.3624
def date_to_sec_since_epoch(line):
    x = line.split()
    year_month_day = x[0].split("-")
    hour_min_sec = x[1].split(":")
    # datetime(year, month, day, hour, minute, second, microsecond)
    dt = datetime(int(year_month_day[0]), int(year_month_day[1]), int(year_month_day[2]), int(hour_min_sec[0]), int(hour_min_sec[1]), int(float(hour_min_sec[2])))
    return int(dt.timestamp())

def parse_to_date(line):
    x = line.split()
    year_month_day = x[0].split("-")
    hour_min_sec = x[1].split(":")
    # datetime(year, month, day, hour, minute, second, microsecond)
    dt = datetime(int(year_month_day[0]), int(year_month_day[1]), int(year_month_day[2]), int(hour_min_sec[0]), int(hour_min_sec[1]), int(float(hour_min_sec[2])))
    return int(dt.timestamp())

class StateEntry:
    def __init__(self, qty, time_epoch, price):
        self.qty = qty
        self.time_epoch = time_epoch
        self.price = price

class State:
    def __init__(self, state_filename):
        self.state = []
        if state_filename:
            self.read_state(state_filename)
    def read_state(self, state_filename):
        with open(state_filename,"r") as file:
            register_lines = file.readlines()
            for r in register_lines:
                register_fields = r.split(",")
                #qty time price
                self.state.append(StateEntry(float(register_fields[0]), float(register_fields[1]), float(register_fields[2])))

    def process_trades(self, trades):
        taxable_delta = 0
        for t in trades:
            taxable_delta += self.process_trade(t)
        return taxable_delta
    
    def process_trade(self, trade):
        if trade.type == "buy":
            self.process_buy(trade)
            return 0
        elif trade.type == "sell":
            return self.process_sell(trade)
        else:
            print("Unexpected trade type")
            exit()

    def process_buy(self, trade):
        # fee is in euro other wise warning
        if trade.fee_eur != 0:
            print("Warning: fee is not 0")
        self.state.append(StateEntry(trade.qty_btc, trade.date, trade.price_eur))

    def process_sell(self, trade):  
        qty = trade.qty_btc
        time_since_ep = trade.date
        price = trade.price_eur
        taxable_delta = 0
        for state_entry in self.state:
            if qty == 0:
                break
            if qty > 0 and qty >= state_entry.qty:
                #do I need to take in account a loss if it occured for btc that was aquired more than a year ago
                if time_since_ep < state_entry.time_epoch + SECONDS_IN_YEAR:
                    taxable_delta += state_entry.qty*(price - state_entry.price)
                qty = qty - state_entry.qty
                state_entry.qty = 0
            elif qty > 0 and qty < state_entry.qty:
                if time_since_ep < state_entry.time_epoch + SECONDS_IN_YEAR:
                    taxable_delta += state_entry.qty*(price - state_entry.price)
                state_entry.qty = state_entry.qty - qty
                qty = 0
        if qty > 0:
            print("Error in sell trade")
            exit()
        self.state = [state_entry for state_entry in self.state if state_entry.qty > 0]
        return taxable_delta

    def save_new_register(self, filename):
        with open(filename, "w") as f:
            for r in self.state:
                f.write(str(r.qty) + "," + str(r.time_epoch) + "," + str(r.price) + "\n")

    def output_total_qty(self):
        total_qty = 0
        for r in self.state:
            total_qty += r.qty
        print("Total qty: ", total_qty)

    def output_qty_held_more_than_a_year(self):
        total_qty = 0
        for r in self.state:
            if r.time_epoch < datetime.now().timestamp() - SECONDS_IN_YEAR:
                total_qty += r.qty
        print("Total qty held more than a year: ", total_qty)
    
    def entry_price_for_first_x_btc(self, x):
        total_qty = 0
        total_price = 0
        for r in self.state:
            if total_qty < x:
                total_qty += r.qty
                total_price += r.qty * r.price
            else:
                break
        return total_price / total_qty
    
    def entry_price_for_btc_from_x_to_y(self, x, y):
        total_qty = 0
        qty_accounted = 0
        total_price = 0
        for r in self.state:
            if total_qty < x:
                total_qty += r.qty
            elif total_qty >= x and total_qty < y:
                total_qty += r.qty
                total_price += r.qty * r.price
                qty_accounted += r.qty
            else:
                break
        return total_price / qty_accounted
    
class KrakenTrade:
    def __init__(self, type, date, price_eur, fee_eur, qty_btc):
        self.type = type
        self.date = date
        self.price_eur = price_eur
        self.fee_eur = fee_eur
        self.qty_btc = qty_btc
#state_filename = "/Users/bkozlov/T2023/BTC/register.txt"
#"2023-06-11 07:59:50"
def convert_to_sec_since_epoch(date):
    x = date.split()
    year_month_day = x[0].split("-")
    year = int(year_month_day[0].replace('"', ''))
    month = int(year_month_day[1])
    day = int(year_month_day[2])
    hour_min_sec = x[1].split(":")
    hour = int(hour_min_sec[0])
    minute = int(hour_min_sec[1])
    second = int(float(hour_min_sec[2].replace('"', '')))
    dt = datetime(year, month, day, hour, minute, second)
    return int(dt.timestamp())

class KrakenTrades:
    def __init__(self, state_filename):
        self.trades = []
        if state_filename:
            self.read_kraken_trades(state_filename)

    def read_kraken_trades(self,filename):
        file = open(filename, "r")
        trade_lines = file.readlines()
        trade_info = []
        for t in trade_lines[1:]:
            trade_fields = t.split(",")
            #   0        1         2     3       4        5         6      7      8    9      10       11      12
            #"txid","ordertxid","pair","time","type","ordertype","price","cost","fee","vol","margin","misc","ledgers"

            if str(trade_fields[2]) == 'XXBTZEUR':
                # 0 type buy or sell, 1 date ,2 price in euros, 3 fee in euros, 4 qty -vol in btc.
                trade_info.append([str(trade_fields[4]), parse_to_date(str(trade_fields[3])),float(trade_fields[6]), float(trade_fields[8]), float(trade_fields[9])])
                self.trades.append(KrakenTrade(str(trade_fields[4]), parse_to_date(str(trade_fields[3])),float(trade_fields[6]), float(trade_fields[8]), float(trade_fields[9])))


if __name__ == "__main__":
    #Execution
    state = State("register.txt")
    print("Before 2023 trading")
    state.output_total_qty()
    kraken_trades = KrakenTrades("kraken_trades.txt")
    taxable_delta = state.process_trades(kraken_trades.trades)
    state.save_new_register("new_register.txt")
    print("Taxable delta: ", taxable_delta)
    state.output_total_qty()
    state.output_qty_held_more_than_a_year()
    print("Entry price 1st ", state.entry_price_for_btc_from_x_to_y(0, 1))
    print("Entry price from 1 to 2 BTC: ", state.entry_price_for_btc_from_x_to_y(1, 2))
    print("Entry price from 2 to 3 BTC: ", state.entry_price_for_btc_from_x_to_y(2, 3))





