from src.core.logger_config import get_logger

logger = get_logger(__name__)
"""
SQLite-based Finance Manager for JARVIS
Upgraded from CSV for better performance, data integrity, and analytics
"""

import sqlite3
from datetime import datetime
from pathlib import Path


class FinanceManagerSQL:
    """
    Finance manager using SQLite database
    
    Benefits over CSV:
    - 100x faster queries on large datasets
    - Data integrity and validation
    - Complex analytics with SQL
    - Safe concurrent access
    - Transaction support (all-or-nothing saves)
    """
    
    def __init__(self, db_file="finance.db"):
        """
        Initialize finance manager with SQLite database
        
        Args:
            db_file: Path to SQLite database file
        """
        self.db_file = db_file
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Access columns by name
        self._init_database()
    
    def _init_database(self):
        """Create database schema if it doesn't exist"""
        
        # Main transactions table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                currency TEXT DEFAULT '$',
                category TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for fast queries
        self.conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_date ON transactions(date)
        ''')
        self.conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_category ON transactions(category)
        ''')
        self.conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_date_category ON transactions(date, category)
        ''')
        
        self.conn.commit()
        logger.info(f"[Finance] Database initialized: {self.db_file}")
    
    def log_transaction(self, amount, currency, category, description):
        """
        Log a new expense transaction
        
        Args:
            amount: Transaction amount (must be positive)
            currency: Currency symbol (default: $)
            category: Expense category
            description: Transaction description
            
        Returns:
            dict: Success status and message
        """
        try:
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S")
            
            # Default values
            if not category:
                category = "Uncategorized"
            if not description:
                description = category
            
            # Insert transaction
            self.conn.execute('''
                INSERT INTO transactions (date, time, amount, currency, category, description)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (date_str, time_str, amount, currency, category, description))
            
            self.conn.commit()
            
            return {
                "success": True,
                "message": f"Logged {currency}{amount} expense for {description}"
            }
            
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            return {
                "success": False,
                "message": f"Invalid data: {e}"
            }
        except Exception as e:
            self.conn.rollback()
            return {
                "success": False,
                "message": f"Error logging: {e}"
            }
    
    def analyze_spending(self, category=None, timeframe="all"):
        """
        Analyze spending based on filters
        
        Args:
            category: Filter by category (optional)
            timeframe: 'today', 'month', or 'all'
            
        Returns:
            str: Formatted spending analysis
        """
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        current_month = now.strftime("%Y-%m")
        
        # Build SQL query
        query = "SELECT SUM(amount) as total, COUNT(*) as count FROM transactions WHERE 1=1"
        params = []
        
        # Add category filter
        if category:
            query += " AND LOWER(category) LIKE ?"
            params.append(f"%{category.lower()}%")
        
        # Add timeframe filter
        if timeframe == "today":
            query += " AND date = ?"
            params.append(today_str)
        elif timeframe == "month":
            query += " AND date LIKE ?"
            params.append(f"{current_month}%")
        
        # Execute query
        result = self.conn.execute(query, params).fetchone()
        total = result['total'] or 0.0
        count = result['count'] or 0
        
        # Format response
        time_text = "today" if timeframe == "today" else "this month" if timeframe == "month" else "total"
        cat_text = f" on {category}" if category else ""
        
        if count == 0:
            return f"No spending found{cat_text} {time_text}."
        
        return f"You have spent ${total:.2f}{cat_text} {time_text} across {count} transactions."
    
    def get_category_breakdown(self, timeframe="month"):
        """
        Get spending breakdown by category
        
        Args:
            timeframe: 'today', 'month', or 'all'
            
        Returns:
            list: List of dicts with category statistics
        """
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        current_month = now.strftime("%Y-%m")
        
        # Build query
        query = '''
            SELECT 
                category,
                SUM(amount) as total,
                COUNT(*) as count,
                AVG(amount) as average,
                MIN(amount) as min_amount,
                MAX(amount) as max_amount
            FROM transactions
            WHERE 1=1
        '''
        params = []
        
        if timeframe == "today":
            query += " AND date = ?"
            params.append(today_str)
        elif timeframe == "month":
            query += " AND date LIKE ?"
            params.append(f"{current_month}%")
        
        query += " GROUP BY category ORDER BY total DESC"
        
        results = self.conn.execute(query, params).fetchall()
        
        breakdown = []
        for row in results:
            breakdown.append({
                'category': row['category'],
                'total': row['total'],
                'count': row['count'],
                'average': row['average'],
                'min': row['min_amount'],
                'max': row['max_amount']
            })
        
        return breakdown
    
    def get_recent_transactions(self, limit=10):
        """
        Get most recent transactions
        
        Args:
            limit: Number of transactions to return
            
        Returns:
            list: List of recent transactions
        """
        query = '''
            SELECT * FROM transactions
            ORDER BY date DESC, time DESC
            LIMIT ?
        '''
        
        results = self.conn.execute(query, (limit,)).fetchall()
        
        transactions = []
        for row in results:
            transactions.append({
                'id': row['id'],
                'date': row['date'],
                'time': row['time'],
                'amount': row['amount'],
                'currency': row['currency'],
                'category': row['category'],
                'description': row['description']
            })
        
        return transactions
    
    def get_spending_trend(self, days=30):
        """
        Get daily spending trend
        
        Args:
            days: Number of days to analyze
            
        Returns:
            list: Daily spending totals
        """
        query = '''
            SELECT 
                date,
                SUM(amount) as daily_total,
                COUNT(*) as transaction_count
            FROM transactions
            WHERE date >= date('now', '-' || ? || ' days')
            GROUP BY date
            ORDER BY date DESC
        '''
        
        results = self.conn.execute(query, (days,)).fetchall()
        
        trend = []
        for row in results:
            trend.append({
                'date': row['date'],
                'total': row['daily_total'],
                'count': row['transaction_count']
            })
        
        return trend
    
    def get_total_spending(self):
        """Get total spending across all time"""
        result = self.conn.execute(
            "SELECT SUM(amount) as total FROM transactions"
        ).fetchone()
        return result['total'] or 0.0
    
    def get_transaction_count(self):
        """Get total number of transactions"""
        result = self.conn.execute(
            "SELECT COUNT(*) as count FROM transactions"
        ).fetchone()
        return result['count']
    
    def delete_transaction(self, transaction_id):
        """
        Delete a transaction by ID
        
        Args:
            transaction_id: ID of transaction to delete
            
        Returns:
            dict: Success status and message
        """
        try:
            cursor = self.conn.execute(
                "DELETE FROM transactions WHERE id = ?",
                (transaction_id,)
            )
            self.conn.commit()
            
            if cursor.rowcount > 0:
                return {
                    "success": True,
                    "message": f"Deleted transaction {transaction_id}"
                }
            else:
                return {
                    "success": False,
                    "message": f"Transaction {transaction_id} not found"
                }
        except Exception as e:
            self.conn.rollback()
            return {
                "success": False,
                "message": f"Error deleting: {e}"
            }
    
    def search_transactions(self, search_term):
        """
        Search transactions by description or category
        
        Args:
            search_term: Term to search for
            
        Returns:
            list: Matching transactions
        """
        query = '''
            SELECT * FROM transactions
            WHERE LOWER(description) LIKE ? OR LOWER(category) LIKE ?
            ORDER BY date DESC, time DESC
            LIMIT 50
        '''
        
        search_pattern = f"%{search_term.lower()}%"
        results = self.conn.execute(query, (search_pattern, search_pattern)).fetchall()
        
        transactions = []
        for row in results:
            transactions.append({
                'id': row['id'],
                'date': row['date'],
                'time': row['time'],
                'amount': row['amount'],
                'currency': row['currency'],
                'category': row['category'],
                'description': row['description']
            })
        
        return transactions
    
    def export_to_csv(self, output_file="finance_export.csv"):
        """
        Export all transactions to CSV
        
        Args:
            output_file: Path to output CSV file
            
        Returns:
            str: Success message
        """
        import csv
        
        try:
            cursor = self.conn.execute('''
                SELECT date, time, amount, currency, category, description
                FROM transactions
                ORDER BY date, time
            ''')
            
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Date', 'Time', 'Amount', 'Currency', 'Category', 'Description'])
                writer.writerows(cursor)
            
            return f"Exported to {output_file}"
        except Exception as e:
            return f"Export failed: {e}"
    
    def get_statistics(self):
        """
        Get comprehensive statistics
        
        Returns:
            dict: Various statistics
        """
        stats = {}
        
        # Total spending
        stats['total_spending'] = self.get_total_spending()
        
        # Transaction count
        stats['transaction_count'] = self.get_transaction_count()
        
        # Average transaction
        result = self.conn.execute(
            "SELECT AVG(amount) as avg FROM transactions"
        ).fetchone()
        stats['average_transaction'] = result['avg'] or 0.0
        
        # Largest transaction
        result = self.conn.execute('''
            SELECT description, amount, date
            FROM transactions
            ORDER BY amount DESC
            LIMIT 1
        ''').fetchone()
        
        if result:
            stats['largest_transaction'] = {
                'description': result['description'],
                'amount': result['amount'],
                'date': result['date']
            }
        
        # Most common category
        result = self.conn.execute('''
            SELECT category, COUNT(*) as count
            FROM transactions
            GROUP BY category
            ORDER BY count DESC
            LIMIT 1
        ''').fetchone()
        
        if result:
            stats['most_common_category'] = {
                'category': result['category'],
                'count': result['count']
            }
        
        return stats
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()


# For backward compatibility, create an alias
FinanceManager = FinanceManagerSQL


if __name__ == "__main__":
    # Test the finance manager
    logger.info("="*70)
    logger.info("  Finance Manager SQL - Test")
    logger.info("="*70)
    
    # Initialize
    fm = FinanceManagerSQL("test_finance.db")
    
    # Add some test transactions
    logger.info("\n[1] Adding test transactions...")
    fm.log_transaction(50.00, "$", "Food", "Lunch at restaurant")
    fm.log_transaction(25.00, "$", "Coffee", "Morning coffee")
    fm.log_transaction(100.00, "$", "Shopping", "Groceries")
    fm.log_transaction(30.00, "$", "Food", "Dinner")
    
    # Analyze spending
    logger.info("\n[2] Analyzing spending...")
    print(fm.analyze_spending())
    print(fm.analyze_spending(category="Food"))
    print(fm.analyze_spending(timeframe="today"))
    
    # Category breakdown
    logger.info("\n[3] Category breakdown...")
    breakdown = fm.get_category_breakdown()
    for cat in breakdown:
        logger.info(f"  {cat['category']}: ${cat['total']:.2f} ({cat['count']} transactions)")
    
    # Recent transactions
    logger.info("\n[4] Recent transactions...")
    recent = fm.get_recent_transactions(5)
    for t in recent:
        logger.info(f"  {t['date']} - {t['description']}: ${t['amount']:.2f}")
    
    # Statistics
    logger.info("\n[5] Statistics...")
    stats = fm.get_statistics()
    logger.info(f"  Total spending: ${stats['total_spending']:.2f}")
    logger.info(f"  Transaction count: {stats['transaction_count']}")
    logger.info(f"  Average transaction: ${stats['average_transaction']:.2f}")
    
    # Cleanup
    import os
    fm.close()
    os.remove("test_finance.db")
    
    logger.info("\n" + "="*70)
    logger.info("Test complete!")
    logger.info("="*70)
