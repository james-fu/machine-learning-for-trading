"""This module implements a system for devising when to trade stocks based on bollinger bands,
stock price momentum, and volatility. More info can be found in the comments or the writeup for this file in the project description"""

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from utils.util import get_data, plot_data, pairwise
import csv
import os, datetime
from Unit1.analysis import get_portfolio_value, get_portfolio_stats, plot_normalized_data
from datetime import timedelta
from trade_simulator import calculate_portfolio_value


"""Generates an orders .csv file indicating when stocks should be bought or sold based on a strategy described in the project writeup
stocks are assumed to be bought in increments of 100."""
def generate_orders_file(prices_all, dates, stock):
        #calculate the SMA and bollinger bands
    data_to_plot = pd.DataFrame(index=dates)
    data_to_plot[stock] = prices_all[stock]
    data_to_plot.dropna(inplace=True)
    data_to_plot['rolling_mean'] = pd.rolling_mean(prices_all[stock], window=20)
    rolling_std = pd.rolling_std(prices_all[stock], window=20)
    data_to_plot['upper_band'] = data_to_plot['rolling_mean'] + (2 * rolling_std)
    data_to_plot['lower_band'] = data_to_plot['rolling_mean'] - (2 * rolling_std)
    plot_one = data_to_plot.copy()

    #calculate the SMA and bollinger bands for the SPY as well
    data_to_plot['SPY'] = prices_all['SPY']
    data_to_plot['SPY_rolling_mean'] = pd.rolling_mean(prices_all['SPY'], window=20)
    SPY_rolling_std = pd.rolling_std(prices_all['SPY'], window=20)
    data_to_plot['SPY_upper_band'] = data_to_plot['SPY_rolling_mean'] + (2 * rolling_std)
    data_to_plot['SPY_lower_band'] = data_to_plot['SPY_rolling_mean'] - (2 * rolling_std)


    #iterate through the dataframe and find the points where the price crosses over the bollinger bands 
    long_entries = []
    short_entries = []
    exits = []
    currently_holding_long = "uninit"
    currently_holding_short = "uninit"
    f = open('Unit2/orders/orders_mystrategy.csv','w')
    f.write("Date,Symbol,Order,Shares\n")

    for (index1, row1), (index2, row2) in pairwise(data_to_plot.iterrows()):
        bollinger_val = (row2[stock] - row2['rolling_mean'])/(row2['upper_band'] - row2['lower_band'])
        SPY_bollinger_val = (row2['SPY'] - row2['SPY_rolling_mean'])/(row2['SPY_upper_band'] - row2['SPY_lower_band'])

        momentum = 0
        if ((index2-timedelta(days=5)) in data_to_plot.index):
            momentum = (data_to_plot.loc[index2, stock]/data_to_plot.loc[(index2-timedelta(days=5)), stock]) - 1.0

        #if you should buy the stock
        if (((row1[stock] < row1['lower_band'] and row2[stock] > row2['lower_band']) or ((bollinger_val - SPY_bollinger_val) < -0.3) or (momentum > .25)) and (currently_holding_long == "F" or currently_holding_long == "uninit")):
            long_entries.append(str(index2)[:10])
            currently_holding_long = "T"
            f.write("{},{},BUY,100\n".format(str(index2)[:10], stock))

        #if you should sell the stock
        elif(((row1[stock] < row1['rolling_mean'] and row2[stock] > row2['rolling_mean']) or ((bollinger_val - SPY_bollinger_val) > 0.7)) and currently_holding_long == "T"):
            exits.append(str(index2)[:10])
            currently_holding_long = "F"
            f.write("{},{},SELL,100\n".format(str(index2)[:10], stock))

        #if you should start shorting the stock
        elif(((row1[stock] > row1['upper_band'] and row2[stock] < row2['upper_band']) or ((bollinger_val - SPY_bollinger_val) < -0.3) or (momentum < -.25)) and (currently_holding_short == "F" or currently_holding_short == "uninit")):
            short_entries.append(str(index2)[:10])
            currently_holding_short = "T"
            f.write("{},{},SELL,100\n".format(str(index2)[:10], stock))

        #if you should stop shorting the stock
        elif(((row1[stock] > row1['rolling_mean'] and row2[stock] < row2['rolling_mean']) or ((bollinger_val - SPY_bollinger_val) > 0.7)) and currently_holding_short == "T"):
            exits.append(str(index2)[:10])
            currently_holding_short = "F"
            f.write("{},{},BUY,100\n".format(str(index2)[:10], stock))

    f.close()

    #create a plot of the results you've found
    ax = plot_one.plot(fontsize=12)
    ax.set_xlabel("Date")
    ax.set_ylabel("Prices")
    for i, val in enumerate(long_entries):
        ax.axvline(x=val, ymin=0, ymax = 100, linewidth=.5, color='green')
    for i, val in enumerate(short_entries):
        ax.axvline(x=val, ymin=0, ymax = 100, linewidth=.5, color='red')
    for i, val in enumerate(exits):
        ax.axvline(x=val, ymin=0, ymax = 100, linewidth=.5, color='black')
    plt.show()


"""Runs the implementation of the bollinger band based trading strategy. Optional inputs are as follows:
Stock: the ticker symbol of the stock you'd like to calculate a trading strategy for
Start_date: date at which to start determining when to make trades
End_date: date at which to stop making trades"""
def run():
    # Define default parameters
    start_date = '2007-12-31'
    end_date = '2009-12-31'
    stock = 'IBM'

    #check for user input of stocks and date range
    if (len(sys.argv) > 1):
        file_path = "data/" + sys.argv[1] + ".csv"
        # Check if that file exists
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            print 'Data for the stock specified does not exist. Please reference stocks in the data folder, or run with no option provided (will display IBM data by default)'
            return
        stock = sys.argv[1]

    if (len(sys.argv) > 3):
        try:
            pd.date_range(sys.argv[2], sys.argv[3])
        except:
            print "The arguments you input for the start and end dates are not valid dates. Please enter your input in the format like 'YYYY-MM-DD' or omit arguments for default value"
            return
        start_date = sys.argv[2]
        end_date = sys.argv[3]
        #note that this does not check if the dates are actually present in the stock data files. This should be implemented later. 

    dates = pd.date_range(start_date, end_date)
    prices_all = get_data([stock], dates)

    generate_orders_file(prices_all, dates, stock)
    calculate_portfolio_value("Unit2/orders/orders_bollingerstrategy.csv", prices_all, dates, stock)



if __name__ == "__main__":
    run()
