from business_opportunity_finder import find_opportunities
from stock_list import load_stock_list
from ask_ai import ask_gpt_for_opportunity


def main():
    tickers = load_stock_list()[:50]
    opportunities = find_opportunities(tickers, show_progress=True)
    if not opportunities:
        print("No opportunities found.")
        return

    for op in opportunities:
        rec = ask_gpt_for_opportunity(op)
        print(f"{op.get('ticker')}: {rec}\n")


if __name__ == "__main__":
    main()

