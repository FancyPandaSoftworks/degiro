import degiroapi
from datetime import datetime, timedelta
import pandas as pd
import pandasql as ps
import matplotlib.pyplot as plt
import stdiomask
import mpld3
import webbrowser
import fnmatch
import os
pd.options.mode.chained_assignment = None
degiro = degiroapi.DeGiro()


def login_degiro():
    one_time_password = None
    username = input('enter your username: ')
    password = stdiomask.getpass(mask='*')
    one_time = input('Do you have a one time password? y/n ')
    if one_time == 'y':
        one_time_password = input('please fill in your one_time_password: ')
    degiro.login(username, password, one_time_password)
    print('ok zoomer, lets see what we got here')


login_degiro()

# ---------------------------------------------------------
"""
Get information about stocks and portfolio from degiro and store it
"""
# ---------------------------------------------------------


# Get current information of your portfolio
# Portfolio_df
portfolio = degiro.getdata(degiroapi.Data.Type.PORTFOLIO, True)
portfolio_df = pd.DataFrame(portfolio, columns=['id', 'positionType', 'size', 'price', 'value', 'breakEvenPrice'])

# ---
# Processing transaction data
# ---

# Get all the transactions to this date
# Transaction_df
transactions = degiro.transactions(datetime(2019, 1, 1), datetime.now())
transactions_df = pd.DataFrame(transactions, columns=['id', 'productId', 'buysell', 'quantity',
                                                      'totalPlusFeeInBaseCurrency'])

# Split the transaction_df into buy and sell
buy_transaction_df = transactions_df[transactions_df['buysell'] == 'B']
buy_transaction_df.loc[:, 'totalPlusFeeInBaseCurrency'] = buy_transaction_df.loc[:, 'totalPlusFeeInBaseCurrency'] * -1

# Get the average buy of the stock
grouped_buy_transaction_query = 'select productId, ROUND(SUM(totalPlusFeeInBaseCurrency)/SUM(quantity), 2) as buy_average ' \
                                'from buy_transaction_df GROUP BY productId'
grouped_buy_df = ps.sqldf(grouped_buy_transaction_query, locals())

# Split into sell only transactions
sell_transaction_df = transactions_df[transactions_df['buysell'] == 'S']
sell_transaction_df.loc[:, 'quantity'] = sell_transaction_df.loc[:, 'quantity'] * -1
# Get the average sell of the stock
grouped_sell_transaction_query = 'select productId, ROUND(SUM(totalPlusFeeInBaseCurrency)/SUM(quantity), 2) as sell_average, quantity ' \
                                 'from sell_transaction_df GROUP BY productId'
grouped_sell_df = ps.sqldf(grouped_sell_transaction_query, locals())

# ---
# Get single stock information
# ---

# Input: Transactions_df
# Output: Product_df, containing id name currency and closeprice
product_df = pd.DataFrame(columns=['id', 'name', 'currency', 'closePrice'])
for product_id in transactions_df.productId.unique():
    info = degiro.product_info(product_id)
    product_info = list([info["id"], info["name"], info["currency"], info["closePrice"]])
    product_info = pd.Series(product_info, index=product_df.columns)
    product_df = product_df.append(product_info, ignore_index=True)


# Input: product_df
# Output: Product_df
def get_type(name):
    if 'ETF' in name:
        return 'ETF'
    else:
        return 'stonks'


product_df['type'] = product_df['name'].apply(get_type)

# ---------------------------------------------------------
"""
Get profit using transaction data and product_df data
"""
# ---------------------------------------------------------

# Get average sold and bought of the stock
profit_query = 'select grouped_buy_df.productId, grouped_buy_df.buy_average, grouped_sell_df.sell_average, grouped_sell_df.quantity FROM ' \
               'grouped_buy_df INNER JOIN grouped_sell_df ON grouped_sell_df.productId = grouped_buy_df.productId'
profit_df = ps.sqldf(profit_query, locals())

# Get the name of the stocks
name_profit_query = 'select product_df.name, profit_df.buy_average, profit_df.sell_average, profit_df.quantity from profit_df INNER JOIN product_df ON ' \
                    'product_df.id = profit_df.productId'

average_price_df = ps.sqldf(name_profit_query, locals())

# Get the profit per stock
average_price_df['profit'] = round((average_price_df.sell_average - average_price_df.buy_average) *
                                   average_price_df.quantity, 2)
final_profit = sum(average_price_df.profit)
final_row = ['final profit', int(0), int(0), 0, final_profit]
average_price_df.loc[len(average_price_df)] = final_row
average_price_html = average_price_df.to_html()

# write html to file
text_file = open("stonks_profit.html", "w")
text_file.write(average_price_html)
text_file.close()

file_name = fnmatch.filter(os.listdir('.'), 'stonks_profit.html')
webbrowser.open('file://' + os.path.realpath(file_name[0]))


# ---------------------------------------------------------
"""
Get the joined table to get information like pie charts and the distribution of the type of stocks
"""
# ---------------------------------------------------------


# ---
# Get current portfolio value distribution per stock
# ---

query = 'select product_df.name, product_df.type, portfolio_df.value from portfolio_df INNER JOIN product_df ON ' \
        'product_df.id = portfolio_df.id '
stock_info_df = ps.sqldf(query, locals())
# stock_info_df.set_index('name', inplace = True)

sizes = stock_info_df['value']

"""
def absolute_value(val):
    a = np.round(val / 100. * sizes.sum(), 0)
    return a
"""

# plot chart
ax1 = plt.subplot(121, aspect='equal')
stock_info_df.plot(figsize=(20, 10), ax=ax1, kind='pie', y='value', autopct='%1.1f%%',
                   startangle=90, shadow=False, labels=stock_info_df['name'], legend=False, fontsize=13)
plt.tight_layout()

# ---
# Get the ratio based on stock type
# ---

type_query = 'select type, sum(value) as type_value from stock_info_df GROUP BY type'
stock_type_grouped_df = ps.sqldf(type_query, locals())

# plot chart
ax2 = plt.subplot(122, aspect='equal')
stock_type_grouped_df.plot(figsize=(20, 10), ax=ax2, kind='pie', y='type_value', autopct='%1.1f%%',
                           startangle=90, shadow=False, labels=stock_type_grouped_df['type'], legend=False, fontsize=13)

plt.tight_layout()
print('PRESS THE BUTTON BOTTTOM LEFT TO MOVE THE PIE CHARTS')
mpld3.show()
