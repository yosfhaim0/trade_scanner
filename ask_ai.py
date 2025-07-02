import os
from typing import List, Dict, Any

import openai
from tabulate import tabulate

import secret

openai.api_key = secret.secret


def ask_gpt_for_opportunity(opportunity: Dict[str, Any]) -> str:
    """Get a short recommendation for a single trading opportunity."""
    ticker = opportunity.get("ticker")
    if isinstance(ticker, dict):
        ticker = ticker.get("ticker")
    prompt = (
        f"Ticker: {ticker}\n"
        f"Price: {opportunity.get('price'):.2f}\n"
        f"RSI: {opportunity.get('rsi'):.2f}\n"
        f"Stoch %K: {opportunity.get('stoch_k'):.2f}\n"
        f"Stoch %D: {opportunity.get('stoch_d'):.2f}\n"
        f"Support: {opportunity.get('support'):.2f}\n"
        f"Resistance: {opportunity.get('resistance'):.2f}\n\n"
        "Based on these indicators, is this a good trade setup? Please answer in a single short paragraph."
    )

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
    )
    return response["choices"][0]["message"]["content"].strip()


def ask_gpt_about_opportunities(opportunities: List[Dict[str, Any]]) -> str:
    """Uses OpenAI ChatGPT to analyze the opportunity list and return trade suggestions."""
    table_data = []
    for row in opportunities:
        ticker = row.get("ticker")
        if isinstance(ticker, dict):
            ticker = ticker.get("ticker")
        price = row.get("price")
        table_data.append(
            [
                ticker,
                f"{row.get('rsi', 0):.2f}",
                f"{row.get('stoch_k', 0):.2f}",
                f"{row.get('stoch_d', 0):.2f}",
                f"{price:.2f}" if isinstance(price, (int, float)) else "",
                f"{row.get('support', 0):.2f}",
                f"{row.get('resistance', 0):.2f}",
            ]
        )
    headers = ["Ticker", "RSI", "Stoch %K", "Stoch %D", "Price", "Support", "Resistance"]
    table = tabulate(table_data, headers=headers, tablefmt="github")

    prompt = (
        "Given the following technical indicators, which stocks would you recommend trading today? "
        "Please explain why.\n\n" + table
    )

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
    )
    return response["choices"][0]["message"]["content"].strip()


if __name__ == "__main__":
    from business_opportunity_finder import find_opportunities
    from stock_list import load_stock_list

    ops = find_opportunities(load_stock_list()[:20], show_progress=True)
    if not ops:
        print("No opportunities found.")
    else:
        for op in ops:
            rec = ask_gpt_for_opportunity(op)
            print(f"{op.get('ticker')}: {rec}\n")

