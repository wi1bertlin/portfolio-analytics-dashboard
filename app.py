# BLOCK 0 - IMPORTS
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf


# BLOCK 1 - CONFIGURATION
BENCHMARK_TICKER = "SPY"
RISK_FREE_RATE = 0.02
ANALYSIS_PERIOD = "3y"
TRADING_DAYS = 252
REQUIRED_COLUMNS = ["Ticker", "Shares", "Purchase Price"]


st.set_page_config(
    page_title="Portfolio Analytics Dashboard",
    layout="wide",
)


def format_currency(value):
    return f"${value:,.2f}"


def format_percent(value):
    return f"{value:.2%}"


def format_score(value):
    return f"{value:.1f}/10"


def max_drawdown(cumulative_returns):
    running_max = cumulative_returns.cummax()
    drawdown = cumulative_returns / running_max - 1
    return drawdown.min(), drawdown


def score_diversification(allocation_df):
    largest_weight = allocation_df["Weight"].max()
    number_of_holdings = len(allocation_df)

    if largest_weight <= 0.25:
        score = 9
    elif largest_weight <= 0.40:
        score = 7
    elif largest_weight <= 0.60:
        score = 4
    else:
        score = 2

    if number_of_holdings >= 5:
        score += 1

    return min(score, 10)


def score_risk(risk_summary):
    volatility = risk_summary["Volatility"]
    max_drawdown_value = abs(risk_summary["Maximum Drawdown"])

    if volatility <= 0.15:
        volatility_score = 9
    elif volatility <= 0.25:
        volatility_score = 7
    elif volatility <= 0.35:
        volatility_score = 5
    else:
        volatility_score = 3

    if max_drawdown_value <= 0.15:
        drawdown_score = 9
    elif max_drawdown_value <= 0.25:
        drawdown_score = 7
    elif max_drawdown_value <= 0.40:
        drawdown_score = 5
    else:
        drawdown_score = 3

    return (volatility_score + drawdown_score) / 2


def score_return(risk_summary, benchmark_summary):
    sharpe_ratio = risk_summary["Sharpe Ratio"]
    relative_performance = benchmark_summary["Relative Performance"]
    portfolio_return = benchmark_summary["Portfolio Return"]

    if pd.isna(sharpe_ratio):
        sharpe_ratio = 0

    if relative_performance > 0 and sharpe_ratio >= 1:
        score = 9
    elif relative_performance > 0 or sharpe_ratio >= 0.75:
        score = 7
    elif portfolio_return > 0:
        score = 5
    else:
        score = 3

    return score


def calculate_health_score(allocation_df, risk_summary, benchmark_summary):
    diversification_score = score_diversification(allocation_df)
    risk_score = score_risk(risk_summary)
    return_score = score_return(risk_summary, benchmark_summary)
    overall_score = (diversification_score + risk_score + return_score) / 3

    return {
        "Diversification": diversification_score,
        "Risk": risk_score,
        "Return": return_score,
        "Overall": overall_score,
    }


# BLOCK 2 - FILE UPLOAD
def load_portfolio(uploaded_file):
    if uploaded_file is None:
        return None

    portfolio_df = pd.read_csv(uploaded_file)
    portfolio_df.columns = portfolio_df.columns.str.strip()
    return portfolio_df


# BLOCK 3 - DATA VALIDATION
def validate_portfolio(portfolio_df):
    if portfolio_df is None:
        return None, ["Please upload a portfolio CSV file."]

    errors = []
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in portfolio_df.columns]

    if missing_columns:
        errors.append(f"Missing required columns: {', '.join(missing_columns)}")
        return None, errors

    clean_df = portfolio_df[REQUIRED_COLUMNS].copy()
    clean_df["Ticker"] = clean_df["Ticker"].astype(str).str.upper().str.strip()
    clean_df["Shares"] = pd.to_numeric(clean_df["Shares"], errors="coerce")
    clean_df["Purchase Price"] = pd.to_numeric(clean_df["Purchase Price"], errors="coerce")

    if clean_df.isna().any().any():
        errors.append("The file contains blank or invalid values.")

    if (clean_df["Ticker"] == "").any():
        errors.append("Ticker values cannot be blank.")

    if (clean_df["Shares"] <= 0).any():
        errors.append("Shares must be greater than zero.")

    if (clean_df["Purchase Price"] <= 0).any():
        errors.append("Purchase Price must be greater than zero.")

    if errors:
        return None, errors

    clean_df["Cost Basis"] = clean_df["Shares"] * clean_df["Purchase Price"]
    clean_df = clean_df.groupby("Ticker", as_index=False).agg(
        {"Shares": "sum", "Cost Basis": "sum"}
    )
    clean_df["Purchase Price"] = clean_df["Cost Basis"] / clean_df["Shares"]
    clean_df = clean_df[["Ticker", "Shares", "Purchase Price"]]

    return clean_df, []


# BLOCK 4 - MARKET DATA FETCHING
@st.cache_data(ttl=900)
def fetch_market_data(tickers, benchmark_ticker, analysis_period):
    all_tickers = tickers + [benchmark_ticker]

    historical_data = yf.download(
        all_tickers,
        period=analysis_period,
        auto_adjust=True,
        progress=False,
    )

    if historical_data.empty:
        raise ValueError("No market data was returned. Please check your tickers.")

    historical_prices = historical_data["Close"]

    if isinstance(historical_prices, pd.Series):
        historical_prices = historical_prices.to_frame(name=all_tickers[0])

    historical_prices = historical_prices.ffill().dropna(how="all")
    current_prices = historical_prices[tickers].iloc[-1]

    missing_prices = current_prices[current_prices.isna()].index.tolist()
    if missing_prices:
        raise ValueError(f"No current price found for: {', '.join(missing_prices)}")

    benchmark_prices = historical_prices[benchmark_ticker].dropna()

    return current_prices, historical_prices[tickers].dropna(), benchmark_prices


# BLOCK 5 - PORTFOLIO CALCULATIONS
def calculate_portfolio_summary(portfolio_df, current_prices):
    portfolio_summary = portfolio_df.copy()
    portfolio_summary["Current Price"] = portfolio_summary["Ticker"].map(current_prices)
    portfolio_summary["Current Value"] = (
        portfolio_summary["Shares"] * portfolio_summary["Current Price"]
    )
    portfolio_summary["Cost Basis"] = (
        portfolio_summary["Shares"] * portfolio_summary["Purchase Price"]
    )
    portfolio_summary["Profit/Loss"] = (
        portfolio_summary["Current Value"] - portfolio_summary["Cost Basis"]
    )
    portfolio_summary["Return %"] = (
        portfolio_summary["Profit/Loss"] / portfolio_summary["Cost Basis"]
    )
    return portfolio_summary


# BLOCK 6 - PORTFOLIO ALLOCATION
def calculate_allocation(portfolio_summary):
    allocation_df = portfolio_summary[["Ticker", "Current Value"]].copy()
    total_value = allocation_df["Current Value"].sum()

    if total_value <= 0:
        raise ValueError("Portfolio value must be greater than zero.")

    allocation_df["Weight"] = allocation_df["Current Value"] / total_value
    allocation_df = allocation_df.sort_values("Weight", ascending=False)

    largest_holding = allocation_df.iloc[0]
    concentration_risk = "High" if largest_holding["Weight"] > 0.40 else "Moderate"
    concentration_risk = "Low" if largest_holding["Weight"] <= 0.25 else concentration_risk

    return allocation_df, largest_holding, concentration_risk


# BLOCK 7 - RISK METRICS
def calculate_risk_metrics(historical_prices, allocation_df):
    daily_returns = historical_prices.pct_change().dropna()
    weights = allocation_df.set_index("Ticker").loc[historical_prices.columns, "Weight"]
    portfolio_daily_returns = daily_returns.dot(weights)
    cumulative_returns = (1 + portfolio_daily_returns).cumprod()

    annual_return = (1 + portfolio_daily_returns.mean()) ** TRADING_DAYS - 1
    volatility = portfolio_daily_returns.std() * np.sqrt(TRADING_DAYS)
    sharpe_ratio = (
        (annual_return - RISK_FREE_RATE) / volatility if volatility != 0 else np.nan
    )
    maximum_drawdown, drawdown = max_drawdown(cumulative_returns)

    risk_summary = {
        "Daily Returns": portfolio_daily_returns,
        "Annual Return": annual_return,
        "Volatility": volatility,
        "Sharpe Ratio": sharpe_ratio,
        "Maximum Drawdown": maximum_drawdown,
        "Cumulative Returns": cumulative_returns,
        "Drawdown": drawdown,
    }
    return risk_summary


# BLOCK 8 - BENCHMARK COMPARISON
def calculate_benchmark_summary(risk_summary, benchmark_prices):
    benchmark_returns = benchmark_prices.pct_change().dropna()
    portfolio_returns = risk_summary["Daily Returns"]

    aligned = pd.concat(
        [portfolio_returns.rename("Portfolio"), benchmark_returns.rename("Benchmark")],
        axis=1,
    ).dropna()

    portfolio_return = (1 + aligned["Portfolio"].mean()) ** TRADING_DAYS - 1
    benchmark_return = (1 + aligned["Benchmark"].mean()) ** TRADING_DAYS - 1
    portfolio_volatility = aligned["Portfolio"].std() * np.sqrt(TRADING_DAYS)
    benchmark_volatility = aligned["Benchmark"].std() * np.sqrt(TRADING_DAYS)
    relative_performance = portfolio_return - benchmark_return

    benchmark_summary = {
        "Portfolio Return": portfolio_return,
        "Benchmark Return": benchmark_return,
        "Relative Performance": relative_performance,
        "Portfolio Volatility": portfolio_volatility,
        "Benchmark Volatility": benchmark_volatility,
        "Outperformed": portfolio_return > benchmark_return,
        "Took More Risk": portfolio_volatility > benchmark_volatility,
        "Benchmark Cumulative Returns": (1 + aligned["Benchmark"]).cumprod(),
        "Comparison Data": aligned,
    }
    return benchmark_summary


# BLOCK 9 - VISUALIZATIONS
def plot_portfolio_growth(risk_summary):
    fig, ax = plt.subplots(figsize=(10, 4))
    risk_summary["Cumulative Returns"].plot(ax=ax, linewidth=2)
    ax.set_title("Portfolio Growth")
    ax.set_ylabel("Growth of $1")
    ax.set_xlabel("")
    return fig


def plot_allocation(allocation_df):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(
        allocation_df["Weight"],
        labels=allocation_df["Ticker"],
        autopct="%1.1f%%",
        startangle=90,
    )
    ax.set_title("Portfolio Allocation")
    return fig


def plot_drawdown(risk_summary):
    fig, ax = plt.subplots(figsize=(10, 4))
    drawdown = risk_summary["Drawdown"]
    drawdown.plot(ax=ax, color="#C43E3E", linewidth=2)
    ax.fill_between(drawdown.index, drawdown, 0, color="#C43E3E", alpha=0.2)
    ax.set_title("Portfolio Drawdown")
    ax.set_ylabel("Drawdown")
    ax.set_xlabel("")
    return fig


def plot_portfolio_vs_benchmark(risk_summary, benchmark_summary):
    fig, ax = plt.subplots(figsize=(10, 4))
    risk_summary["Cumulative Returns"].plot(ax=ax, label="Portfolio", linewidth=2)
    benchmark_summary["Benchmark Cumulative Returns"].plot(
        ax=ax, label=BENCHMARK_TICKER, linewidth=2
    )
    ax.set_title(f"Portfolio vs {BENCHMARK_TICKER}")
    ax.set_ylabel("Growth of $1")
    ax.set_xlabel("")
    ax.legend()
    return fig


# BLOCK 10 - DASHBOARD DISPLAY
st.title("Portfolio Analytics Dashboard")
st.caption("Upload a CSV portfolio and receive risk, allocation, and benchmark analytics.")

with st.sidebar:
    st.header("Upload Portfolio")
    st.write("Required columns: Ticker, Shares, Purchase Price")
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

    st.divider()
    st.subheader("Settings")
    st.write(f"Benchmark: {BENCHMARK_TICKER}")
    st.write(f"Risk-free rate: {RISK_FREE_RATE:.2%}")
    st.write(f"Analysis period: {ANALYSIS_PERIOD}")

portfolio_df = load_portfolio(uploaded_file)
clean_portfolio_df, validation_errors = validate_portfolio(portfolio_df)

if validation_errors:
    st.info("Upload a CSV to begin. Example:")
    st.code("Ticker,Shares,Purchase Price\nAAPL,10,180\nMSFT,5,420\nNVDA,3,120")
    for error in validation_errors:
        if error != "Please upload a portfolio CSV file.":
            st.error(error)
    st.stop()

try:
    tickers = clean_portfolio_df["Ticker"].tolist()
    current_prices, historical_prices, benchmark_prices = fetch_market_data(
        tickers, BENCHMARK_TICKER, ANALYSIS_PERIOD
    )
    portfolio_summary = calculate_portfolio_summary(clean_portfolio_df, current_prices)
    allocation_df, largest_holding, concentration_risk = calculate_allocation(
        portfolio_summary
    )
    risk_summary = calculate_risk_metrics(historical_prices, allocation_df)
    benchmark_summary = calculate_benchmark_summary(risk_summary, benchmark_prices)
    health_score = calculate_health_score(allocation_df, risk_summary, benchmark_summary)
except Exception as error:
    st.error(f"Analysis could not be completed: {error}")
    st.stop()

total_value = portfolio_summary["Current Value"].sum()
total_cost = portfolio_summary["Cost Basis"].sum()
total_profit_loss = portfolio_summary["Profit/Loss"].sum()
total_return = total_profit_loss / total_cost

st.subheader("1. Portfolio Summary")
summary_cols = st.columns(4)
summary_cols[0].metric("Current Value", format_currency(total_value))
summary_cols[1].metric("Cost Basis", format_currency(total_cost))
summary_cols[2].metric("Profit/Loss", format_currency(total_profit_loss))
summary_cols[3].metric("Return", format_percent(total_return))

st.subheader("2. Holdings Table")
display_summary = portfolio_summary.copy()
for column in ["Purchase Price", "Current Price", "Current Value", "Cost Basis", "Profit/Loss"]:
    display_summary[column] = display_summary[column].map(format_currency)
display_summary["Return %"] = display_summary["Return %"].map(format_percent)
st.dataframe(display_summary, use_container_width=True, hide_index=True)

st.subheader("3. Allocation Analysis")
allocation_cols = st.columns([1, 1, 2])
allocation_cols[0].metric("Largest Holding", largest_holding["Ticker"])
allocation_cols[1].metric("Largest Weight", format_percent(largest_holding["Weight"]))
allocation_cols[2].metric("Concentration Risk", concentration_risk)

display_allocation = allocation_df.copy()
display_allocation["Current Value"] = display_allocation["Current Value"].map(format_currency)
display_allocation["Weight"] = display_allocation["Weight"].map(format_percent)
st.dataframe(display_allocation, use_container_width=True, hide_index=True)

st.subheader("4. Risk Metrics")
risk_cols = st.columns(4)
risk_cols[0].metric("Annual Return", format_percent(risk_summary["Annual Return"]))
risk_cols[1].metric("Volatility", format_percent(risk_summary["Volatility"]))
risk_cols[2].metric("Sharpe Ratio", f"{risk_summary['Sharpe Ratio']:.2f}")
risk_cols[3].metric("Max Drawdown", format_percent(risk_summary["Maximum Drawdown"]))

st.subheader("5. Portfolio Health Score")
health_cols = st.columns(4)
health_cols[0].metric("Diversification", format_score(health_score["Diversification"]))
health_cols[1].metric("Risk", format_score(health_score["Risk"]))
health_cols[2].metric("Return", format_score(health_score["Return"]))
health_cols[3].metric("Overall Score", format_score(health_score["Overall"]))
st.progress(min(max(health_score["Overall"] / 10, 0), 1))

st.subheader("6. Benchmark Comparison")
benchmark_cols = st.columns(5)
benchmark_cols[0].metric(
    "Portfolio Return", format_percent(benchmark_summary["Portfolio Return"])
)
benchmark_cols[1].metric(
    f"{BENCHMARK_TICKER} Return", format_percent(benchmark_summary["Benchmark Return"])
)
benchmark_cols[2].metric(
    "Relative Performance",
    format_percent(benchmark_summary["Relative Performance"]),
)
benchmark_cols[3].metric(
    "Outperformed?", "Yes" if benchmark_summary["Outperformed"] else "No"
)
benchmark_cols[4].metric(
    "More Risk?", "Yes" if benchmark_summary["Took More Risk"] else "No"
)

st.subheader("7. Charts")
chart_tabs = st.tabs(
    [
        "Portfolio Growth",
        "Allocation Pie Chart",
        "Drawdown Chart",
        "Portfolio vs Benchmark",
    ]
)

with chart_tabs[0]:
    st.pyplot(plot_portfolio_growth(risk_summary), clear_figure=True)

with chart_tabs[1]:
    st.pyplot(plot_allocation(allocation_df), clear_figure=True)

with chart_tabs[2]:
    st.pyplot(plot_drawdown(risk_summary), clear_figure=True)

with chart_tabs[3]:
    st.pyplot(plot_portfolio_vs_benchmark(risk_summary, benchmark_summary), clear_figure=True)
