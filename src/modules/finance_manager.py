import csv
import os
from datetime import datetime

class FinanceManager:
    def __init__(self, filename="finance_tracker.csv"):
        self.filename = filename
        self._init_file()

    def _init_file(self):
        """Creates the CSV file with headers if it doesn't exist"""
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Time", "Amount", "Currency", "Category", "Description"])

    def log_transaction(self, amount, currency, category, description):
        """Logs a new expense"""
        try:
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S")
            
            if not category: category = "Uncategorized"
            if not description: description = category
            
            with open(self.filename, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([date_str, time_str, amount, currency, category, description])
            
            return {
                "success": True, 
                "message": f"Logged {currency}{amount} expense for {description}"
            }
        except Exception as e:
            return {"success": False, "message": f"Error logging: {e}"}

    def analyze_spending(self, category=None, timeframe="all"):
        """
        Analyzes spending based on filters
        timeframe: 'today', 'month', 'all'
        """
        if not os.path.exists(self.filename):
            return "No records found."

        total = 0.0
        count = 0
        target_cat = category.lower() if category else None
        
        # Get current date details
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        current_month = now.strftime("%Y-%m")

        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row_date = row["Date"]
                    row_amount = float(row["Amount"])
                    row_cat = row["Category"].lower()

                    # Filter by Category
                    if target_cat and target_cat not in row_cat:
                        continue

                    # Filter by Timeframe
                    if timeframe == "today" and row_date != today_str:
                        continue
                    if timeframe == "month" and not row_date.startswith(current_month):
                        continue

                    total += row_amount
                    count += 1

            # Formulate response
            time_text = f"today" if timeframe == "today" else f"this month" if timeframe == "month" else "total"
            cat_text = f" on {category}" if category else ""
            
            if count == 0:
                return f"No spending found{cat_text} {time_text}."
            
            return f"You have spent ${total:.2f}{cat_text} {time_text} across {count} transactions."

        except Exception as e:
            return f"Error reading records: {e}"