# Stock-market app

Harvard's CS50x Problem 9 - Stock market app. It's written using Flask framework, API data provided by IEX (https://iexcloud.io/) and Python language.

Full specification: https://cs50.harvard.edu/x/2022/psets/9/finance/

## Video Demo

https://youtu.be/QB-f8lMKd0I

## Setup

Clone this repository and change directory to CS50-Flask: 

```bash
git clone https://github.com/Looterro/CS50-Flask.git
cd CS50-Flask-master
```

Install dependencies:
```bash
python3 -m pip install requirements.txt
```

## Specification:

**Register, login, logout** 
- User is able to register and login through flask sessions and use of sqlite 3 database.
- If not logged in, a user will be redirected to login page, where they can register if they do not have the account yet.

**Index** 
- The main page, accessed through clicking on the main logo, shows in a table the amount of all the current holdings, their current price(updated through the IEX API) and total value(shares*current price).
- Additionally, user can see their current cash amount (By default $10000 for new users) and their grand total(all shares value + available cash)

**Buy and Sell** 
- User can use buy and sell links in navigation bar to buy or sell stocks.
- On each page a user is provided with two inputs, where they can specify which stocks they want to buy by providing a symbol, and the number of shares.
- The server will render an error template if user does not hold any shares of given stock and tries to sell them or will try to sell more then they currently have. The server also protects against buying non-existent stocks and buying more then a user can afford.
- With each purchase and sell the server uses IEX (https://iexcloud.io/) API to get the current price of the stock.
- In order to keep track of the orders, the server uses orders table created in sqlite 3, with information about the time of processing of the order, whether the action was "buy" or "sell" as well as username of the user and the change in the amount of holdings.

**Quote** 
- User can access quote tab to search the stocks before purchasing them
- The page asks user for a symbol of a stock and returns a template with information about given stock using IEX API (https://iexcloud.io/).

**History** 
- All changes recorded in orders table in database are displayed in the history section, which can also be accessed through nav bar.
