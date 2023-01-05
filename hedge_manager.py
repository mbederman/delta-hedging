# Overall manager class to adjust portfolio weights for delta hedging
import robin_stocks.robinhood as rs
import pyotp
import matplotlib.pyplot as plt
import numpy as np
from config import *
from time import sleep
from datetime import datetime
import os

class Hedge_Manager:
    def __init__(self):
        # Starting with initial call to hedge
        self.call_weight = 1

        # Initializing other weights to 0
        self.stock_weight = 0
        self.risk_free_weight = 0

        # Initializing portfolio value
        self.portfolio_value = 0

        # Forces algorithm to start at current value of 0
        self.first = True

        # Logging in to robinhood
        totp = pyotp.TOTP(os.getenv("RB_OTP")).now()
        login = rs.login(os.getenv("RB_USERNAME"), os.getenv("RB_PASSWORD"), mfa_code=totp)

        # Keeping track of data
        self.stock_prices = []
        self.option_prices = []
        self.portfolio_values = []

        # Keep track of start time
        self.start_time = datetime.now()

        with open("log.txt", "w") as file:
            file.write(f"Delta Hedging {TICKER} starting at {datetime.now()}:\n\n")

        self.create_plot()

    def run(self):
        for epoch in range(EPOCHS):
            stock_price = self.get_stock_price()
            try:
                (option_price, delta) = self.get_option_data()
            except TypeError:
                print("Option with inputed parameters doesn't exist\n")
                return 

            self.adjust_weights(stock_price, option_price, delta)
            self.update_plot(epoch)
            sleep(T_INT)
        
        self.hold_plot()
        self.summarize()

    def get_stock_price(self):
        stock_price = float(rs.stocks.get_latest_price(TICKER)[0])
        self.stock_prices.append(round(stock_price, 2))
        return stock_price

    def adjust_weights(self, stock_price, option_price, delta):
        if self.first:
            current_value = 0
            self.first = False
        else:
            current_value = option_price * self.call_weight + self.stock_weight * stock_price + self.risk_free_weight

        new_stock_weight = -1 * self.call_weight * delta
        new_risk_free_weight = current_value - (option_price + (new_stock_weight * stock_price))

        self.log_trades(new_stock_weight, new_risk_free_weight, stock_price)

        self.stock_weight = new_stock_weight
        self.risk_free_weight = new_risk_free_weight

        self.portfolio_value = (self.stock_weight * stock_price) + self.risk_free_weight + (self.call_weight * option_price)
        self.portfolio_values.append(round(self.portfolio_value, 2))

        self.log_portfolio()
            
    def log_portfolio(self):
        with open("log.txt", "a") as file:
                file.write(f"({datetime.now()}) Current Portfolio: {self.stock_weight} shares of {TICKER}, {self.risk_free_weight} risk free assets, {self.call_weight} of call option\n")
                file.write(f"Total Portfolio Value: {self.portfolio_value}\n")

    def get_option_data(self):
        data = rs.options.get_option_market_data(TICKER, EXP_DATE, STRIKE, optionType="call")[0][0]
        option_price = float(data["adjusted_mark_price"]) * 100
        delta = float(data["delta"])

        self.option_prices.append(round(option_price, 2))

        return (option_price, delta)

    def log_trades(self, new_stock_weight, new_risk_free_rate, stock_price):
        current_time = datetime.now()
        with open("log.txt", "a") as file:
            if not new_stock_weight == self.stock_weight:
                if new_stock_weight > self.stock_weight:
                    action = "Buying"
                else:
                    action = "Selling"

                file.write(f"({current_time}) {action} {new_stock_weight - self.stock_weight} share of {TICKER} at {stock_price}\n")

            if not new_risk_free_rate == self.risk_free_weight:
                if new_risk_free_rate > self.risk_free_weight:
                    action = "Buying"
                else:
                    action = "Selling"

                file.write(f"({current_time}) {action} {new_risk_free_rate - self.risk_free_weight} risk free assets\n")

    def create_plot(self):
        plt.ion()
        fig, self.axes = plt.subplots(1, 3, figsize=(20, 5))
        plt.suptitle("Delta Hedging")
        self.axes[0].set_xlabel("Epoch")
        self.axes[0].set_ylabel("Stock Price")
        self.axes[1].set_xlabel("Epoch")
        self.axes[1].set_ylabel("Option Price")
        self.axes[2].set_xlabel("Epoch")
        self.axes[2].set_ylabel("Portfolio Value")


    def update_plot(self, epoch):
        time = range(epoch + 1)
        self.axes[0].plot(time, self.stock_prices, linestyle="--", marker="o", color="r")
        self.axes[1].plot(time, self.option_prices, linestyle="--", marker="o", color="g")
        self.axes[2].plot(time, self.portfolio_values, linestyle="--", marker="o", color="b")
        plt.pause(.00001)

    def hold_plot(self):
        plt.ioff()
        plt.show()

    def summarize(self):
        end_time = datetime.now()
        elapsed_time = end_time - self.start_time

        with open("log.txt", "a") as file:
            file.write(f"\n*** Hedging Summary: ***\n")
            file.write(f"Final portfolo value of {self.portfolio_value}\n")
            file.write(f"Finished at {end_time} with elapsed time of {elapsed_time}\n")
        