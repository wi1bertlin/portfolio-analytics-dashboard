# Portfolio Risk and Benchmark Dashboard

## Research Question
How can a portfolio be evaluated beyond its profit or loss, and did it earn enough return for the risk taken relative to the S&P 500?

I built this project after my stock-comparison and moving-average projects because both focused mainly on returns. This project adds portfolio allocation, diversification, volatility, Sharpe ratio, drawdown, benchmark analysis, and a simple portfolio health score.

## Portfolio Input
The Streamlit application accepts a CSV with three columns:

```text
Ticker,Shares,Purchase Price
AAPL,10,180
MSFT,5,420
NVDA,3,120
```

Shares and purchase prices must be greater than zero. If the same ticker appears more than once, the app combines the rows using total shares and total cost basis.

The Jupyter notebook contains the same example portfolio directly in a DataFrame so each calculation can be studied one step at a time.

## Data
- Historical adjusted market prices are downloaded through `yfinance`.
- SPY is used as the S&P 500 benchmark.
- The dashboard uses a three-year analysis period and a 2% annual risk-free rate.
- Holdings, share counts, and purchase prices come from the user.

## Methodology
1. Validate the portfolio tickers, shares, and purchase prices.
2. Combine duplicate tickers using total shares and total cost basis.
3. Calculate current value, cost basis, profit/loss, and holding return.
4. Calculate each holding's weight using current market value.
5. Combine the historical stock returns using those portfolio weights.
6. Annualise portfolio return and volatility.
7. Calculate Sharpe ratio and maximum drawdown.
8. Compare portfolio return and volatility with SPY.
9. Estimate a simple portfolio health score.
10. Display the holdings, allocation, risk metrics, benchmark comparison, health score, and charts in Streamlit.

## Portfolio Health Score
The health score is a simple rule-based score out of 10. It is designed to make the dashboard easier to interpret, not to give investment advice.

The score has three parts:
- Diversification: based on the largest holding and number of holdings
- Risk: based on volatility and maximum drawdown
- Return: based on Sharpe ratio and performance relative to SPY

The overall score is the average of the three parts.

Example output:

```text
Diversification: 7/10
Risk: 6/10
Return: 8/10
Overall Score: 7.0/10
```

## Outputs and Interpretation
The project produces:
- Portfolio value, cost basis, and profit/loss
- Holding-level returns and portfolio weights
- Largest holding and a simple concentration-risk label
- Annual return, volatility, Sharpe ratio, and maximum drawdown
- Portfolio health score
- Portfolio growth and drawdown charts
- Portfolio-versus-SPY return and risk comparison

The results are intentionally dynamic. They depend on the uploaded holdings, purchase prices, analysis date, and market data, so the README does not present fixed performance figures as universal results.

## Limitations
- The health score is a simplified educational score, not a professional investment rating.
- Historical portfolio returns use weights based on current market values rather than a complete transaction history.
- Purchase prices do not include purchase dates, deposits, withdrawals, dividends received, taxes, or fees.
- The portfolio is treated as static and rebalancing is not modelled.
- The risk-free rate and three-year lookback period are simplified assumptions.
- Sharpe ratio and volatility do not capture every form of investment risk.
- Yahoo Finance data is appropriate for education but should not be treated as institutional-quality portfolio accounting data.

## What I Learned
This project taught me that a portfolio cannot be judged by profit alone. Two portfolios can produce similar returns while having very different concentration, volatility, and drawdown. I also learned how individual security returns are combined through portfolio weights and why a benchmark provides necessary context.

Adding the health score helped me practise turning several portfolio metrics into a simple summary that a user can understand quickly.

## How to Run the Streamlit Dashboard
1. Install the dependencies:

```bash
pip install -r requirements.txt
```

2. Start the application:

```bash
streamlit run app.py
```

3. Upload `sample_portfolio.csv` or a CSV using the same column names.

## How to Run the Notebook
Open `portfolio_risk_benchmark_dashboard.ipynb` in Jupyter Notebook and run the cells from top to bottom.

## Author
Ping-Hsiang (Wilbert) Lin
