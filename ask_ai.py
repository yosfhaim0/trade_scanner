import os
from typing import List, Dict, Any

import openai
from tabulate import tabulate

openai.api_key = os.getenv("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")


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

    ops = find_opportunities(load_stock_list())
    if not ops:
        print("No opportunities found.")
    else:
        answer = ask_gpt_about_opportunities(ops)
        print(answer)

