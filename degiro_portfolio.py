import degiroapi
from degiroapi.product import Product
from degiroapi.order import Order
from degiroapi.utils import pretty_json
from datetime import datetime, timedelta
import pandas as pd
import pandasql as ps
degiro = degiroapi.DeGiro()
import matplotlib.pyplot as plt
import stdiomask

username = input('enter your username: ')
password = stdiomask.getpass(mask='*')
print('ok zoomer, lets see what we got here')
degiro.login(username, password)

#---------------------------------------------------------
"""
Get portfolio (All the information of your current stocks)
"""
#---------------------------------------------------------
portfolio = degiro.getdata(degiroapi.Data.Type.PORTFOLIO, True)
portfolio_df = pd.DataFrame(portfolio, columns=['id', 'positionType', 'size', 'price', 'value', 'breakEvenPrice'])
#for data in portfolio:
#    print(data)
#    print(' ')



#---------------------------------------------------------
"""
Get all the transactions from your trading history
"""
#---------------------------------------------------------
transactions = degiro.transactions(datetime(2019, 1, 1), datetime.now())
#print(pretty_json(transactions))

transactions_df = pd.DataFrame(transactions, columns=['id', 'productId', 'date', 'buysell', 'price', 'quantity',
                                                      'total', 'orderTypeId'])




#---------------------------------------------------------
"""
Get the stock information like name of the stock and its current price
"""
#---------------------------------------------------------

product_df = pd.DataFrame(columns=['id', 'name', 'currency', 'closePrice'])
for product_id in transactions_df.productId.unique():
    info = degiro.product_info(product_id)
    product_info = list([info["id"], info["name"], info["currency"], info["closePrice"]])
    product_info = pd.Series(product_info, index=product_df.columns)
    product_df = product_df.append(product_info, ignore_index=True)



#---------------------------------------------------------
#Get the type of the stock, etf or stonks
#---------------------------------------------------------
def get_type(name):
    if 'ETF' in name:
        return 'ETF'
    else:
        return 'stonks'
product_df['type'] = product_df['name'].apply(get_type)

#---------------------------------------------------------
"""
Get the joined table to get information like pie charts and the distribution of the type of stocks
"""
#---------------------------------------------------------


#---------------------------------------------------------
#Get current portfolio value distribution per stock
#---------------------------------------------------------

query = 'select product_df.name, product_df.type, portfolio_df.value from portfolio_df INNER JOIN product_df ON product_df.id = portfolio_df.id'
stock_info_df = ps.sqldf(query, locals())
#stock_info_df.set_index('name', inplace = True)

# plot chart
ax1 = plt.subplot(121, aspect='equal')
stock_info_df.plot(figsize = (30,15), ax=ax1, kind='pie', y = 'value', autopct='%1.1f%%',
 startangle=90, shadow=False, labels=stock_info_df['name'], legend = False, fontsize=11)
plt.tight_layout()

#---------------------------------------------------------
#Get the ratio based on stock type
#---------------------------------------------------------
type_query = 'select type, sum(value) as type_value from stock_info_df GROUP BY type'
stock_type_grouped_df = ps.sqldf(type_query, locals())

# plot chart
ax2 = plt.subplot(122, aspect='equal')
stock_type_grouped_df.plot(figsize = (30,15), ax=ax2, kind='pie', y = 'type_value', autopct='%1.1f%%',
 startangle=90, shadow=False, labels=stock_type_grouped_df['type'], legend = False, fontsize=9)
plt.tight_layout()
plt.show()
