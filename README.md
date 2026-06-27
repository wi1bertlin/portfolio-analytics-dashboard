# Portfolio Risk and Benchmark Dashboard

## Overview
This project is a Python-based portfolio analysis tool that evaluates a stock portfolio using real market data. It calculates portfolio value, risk metrics, allocation, and compares performance against the S&P 500 using SPY.

The goal is to understand both portfolio return and portfolio risk.

---

## Features
- Input portfolio holdings
- Download historical stock data using yfinance
- Calculate current portfolio value
- Calculate profit/loss and return %
- Analyze portfolio allocation
- Calculate volatility, Sharpe Ratio, and maximum drawdown
- Compare performance against SPY
- Visualize portfolio growth, allocation, drawdown, and benchmark comparison

---

## How It Works
The notebook:
1. Creates a portfolio with tickers, shares, and purchase prices
2. Downloads historical price data
3. Calculates current value and return for each holding
4. Calculates portfolio allocation
5. Measures portfolio risk
6. Compares portfolio performance against SPY
7. Displays charts for analysis

---

## Example Output
Current Value: $5,600.35

Cost Basis: $4,260.00

Profit/Loss: $1,340.35

Annual Return: 23.34%

Volatility: 21.97%

Sharpe Ratio: 0.97

Maximum Drawdown: -27.66%

---

## Technologies Used
- Python
- Jupyter Notebook
- yfinance
- pandas
- numpy
- matplotlib

---

## How to Run

1. Install required libraries:

    pip install yfinance pandas numpy matplotlib

2. Run the notebook:

    portfolio_risk_benchmark_dashboard.ipynb

3. Edit the portfolio tickers, shares, and purchase prices if needed

---

## Key Learning
This project shows how to evaluate a portfolio using both return and risk.

It also demonstrates that a portfolio should not only be judged by profit, but also by volatility, drawdown, diversification, and performance compared with the market.

---

## Author
Ping-Hsiang (Wilbert) Lin
