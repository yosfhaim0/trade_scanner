from scanner import Scanner


def main():
    # Example watchlist
    tickers = ["AAPL", "MSFT", "GOOGL"]
    scanner = Scanner(tickers)
    scanner.update_data()
    results = scanner.scan()
    for res in results:
        print(
            f"{res['ticker']}: price={res['price']:.2f} RSI14={res['RSI14']:.2f} "
            f"support={res['support']:.2f} resistance={res['resistance']:.2f} "
            f"near_support={res['near_support']} near_resistance={res['near_resistance']}"
        )
    scanner.close()


if __name__ == "__main__":
    main()
