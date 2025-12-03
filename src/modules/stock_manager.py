"""
Stock Price Manager for JARVIS
Fetches and displays real-time stock prices
"""

import yfinance as yf
from datetime import datetime
from src.core.logger_config import get_logger

logger = get_logger(__name__)


class StockManager:
    def __init__(self):
        """Initialize stock manager"""
        self.watchlist = []
        logger.info("[Stocks] Stock manager initialized")
    
    def get_stock_price(self, symbol):
        """
        Get current stock price
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
            
        Returns:
            dict with stock info or None if error
        """
        try:
            stock = yf.Ticker(symbol.upper())
            info = stock.info
            
            # Get current price
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            if not current_price:
                logger.warning(f"[Stocks] Could not get price for {symbol}")
                return None
            
            # Get other info
            previous_close = info.get('previousClose', 0)
            change = current_price - previous_close if previous_close else 0
            change_percent = (change / previous_close * 100) if previous_close else 0
            
            result = {
                'symbol': symbol.upper(),
                'name': info.get('shortName', symbol),
                'price': current_price,
                'change': change,
                'change_percent': change_percent,
                'previous_close': previous_close,
                'open': info.get('open', 0),
                'high': info.get('dayHigh', 0),
                'low': info.get('dayLow', 0),
                'volume': info.get('volume', 0),
                'market_cap': info.get('marketCap', 0),
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            logger.info(f"[Stocks] {symbol}: ${current_price:.2f} ({change_percent:+.2f}%)")
            return result
            
        except Exception as e:
            logger.error(f"[Stocks] Error fetching {symbol}: {e}")
            return None
    
    def get_multiple_stocks(self, symbols):
        """
        Get prices for multiple stocks
        
        Args:
            symbols: List of ticker symbols
            
        Returns:
            dict of symbol -> stock info
        """
        results = {}
        
        for symbol in symbols:
            stock_info = self.get_stock_price(symbol)
            if stock_info:
                results[symbol.upper()] = stock_info
        
        return results
    
    def add_to_watchlist(self, symbol):
        """Add stock to watchlist"""
        symbol = symbol.upper()
        if symbol not in self.watchlist:
            self.watchlist.append(symbol)
            logger.info(f"[Stocks] Added {symbol} to watchlist")
            return True
        return False
    
    def remove_from_watchlist(self, symbol):
        """Remove stock from watchlist"""
        symbol = symbol.upper()
        if symbol in self.watchlist:
            self.watchlist.remove(symbol)
            logger.info(f"[Stocks] Removed {symbol} from watchlist")
            return True
        return False
    
    def get_watchlist_prices(self):
        """Get prices for all stocks in watchlist"""
        if not self.watchlist:
            return {}
        
        return self.get_multiple_stocks(self.watchlist)
    
    def search_stock(self, query):
        """
        Search for stock by name or symbol
        
        Args:
            query: Search term
            
        Returns:
            Stock info if found
        """
        try:
            # Try as ticker symbol first
            result = self.get_stock_price(query)
            if result:
                return result
            
            # Could add more sophisticated search here
            return None
            
        except Exception as e:
            logger.error(f"[Stocks] Search error: {e}")
            return None
    
    def get_stock_history(self, symbol, period="1mo"):
        """
        Get historical stock data
        
        Args:
            symbol: Stock ticker
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            
        Returns:
            DataFrame with historical data
        """
        try:
            stock = yf.Ticker(symbol.upper())
            history = stock.history(period=period)
            
            logger.info(f"[Stocks] Retrieved {len(history)} days of history for {symbol}")
            return history
            
        except Exception as e:
            logger.error(f"[Stocks] Error getting history for {symbol}: {e}")
            return None
    
    def format_price_message(self, stock_info):
        """
        Format stock info as readable message
        
        Args:
            stock_info: Stock info dict
            
        Returns:
            Formatted string
        """
        if not stock_info:
            return "Stock not found"
        
        symbol = stock_info['symbol']
        name = stock_info['name']
        price = stock_info['price']
        change = stock_info['change']
        change_percent = stock_info['change_percent']
        
        direction = "up" if change >= 0 else "down"
        arrow = "↑" if change >= 0 else "↓"
        
        message = f"{name} ({symbol}): ${price:.2f} {arrow} {abs(change):.2f} ({change_percent:+.2f}%)"
        
        return message


# Example usage
if __name__ == "__main__":
    manager = StockManager()
    
    print("Stock Manager Test\n")
    
    # Test single stock
    print("Fetching Apple stock...")
    aapl = manager.get_stock_price("AAPL")
    if aapl:
        print(manager.format_price_message(aapl))
        print(f"  Open: ${aapl['open']:.2f}")
        print(f"  High: ${aapl['high']:.2f}")
        print(f"  Low: ${aapl['low']:.2f}")
        print(f"  Volume: {aapl['volume']:,}")
    
    # Test watchlist
    print("\nTesting watchlist...")
    manager.add_to_watchlist("AAPL")
    manager.add_to_watchlist("GOOGL")
    manager.add_to_watchlist("MSFT")
    
    watchlist = manager.get_watchlist_prices()
    print(f"\nWatchlist ({len(watchlist)} stocks):")
    for symbol, info in watchlist.items():
        print(f"  {manager.format_price_message(info)}")
    
    # Test history
    print("\nFetching 5-day history for AAPL...")
    history = manager.get_stock_history("AAPL", "5d")
    if history is not None:
        print(f"  Retrieved {len(history)} days")
        print(f"  Latest close: ${history['Close'].iloc[-1]:.2f}")
