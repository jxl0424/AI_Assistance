"""
Couples Finance Manager - Enhanced SQLite-based Finance Manager for Two Users
Supports dual-user tracking, shared expenses, budgets, and settlement
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import sqlite3
from datetime import datetime

try:
    from src.core.logger_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)


class CouplesFinanceManager:
    """
    Finance manager for couples with:
    - Dual-user support (you + partner)
    - Shared expense tracking
    - Split calculations
    - Settlement system
    - Budgets (personal + shared)
    - Savings goals
    """
    
    def __init__(self, db_file="data/finance/couples_finance.db"):
        """
        Initialize couples finance manager
        
        Args:
            db_file: Path to SQLite database file
        """
        # Ensure directory exists
        Path(db_file).parent.mkdir(parents=True, exist_ok=True)
        
        self.db_file = db_file
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_database()
        logger.info(f"[CouplesFinance] Database initialized: {db_file}")
    
    def _init_database(self):
        """Create enhanced database schema for couples"""
        
        # Users table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                role TEXT DEFAULT 'partner',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Enhanced transactions table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                currency TEXT DEFAULT '$',
                category TEXT NOT NULL,
                description TEXT,
                type TEXT DEFAULT 'personal',  -- 'personal', 'shared', 'reimbursement'
                split_ratio REAL DEFAULT 0.5,  -- 0.5 = 50/50, 0.6 = 60/40, etc.
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Budgets table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                period TEXT DEFAULT 'monthly',  -- 'weekly', 'monthly', 'yearly'
                budget_type TEXT DEFAULT 'shared',  -- 'personal', 'shared'
                user_id INTEGER,  -- NULL if shared budget
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Savings goals table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS savings_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                target_amount REAL NOT NULL CHECK(target_amount > 0),
                current_amount REAL DEFAULT 0,
                deadline DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Goal contributions table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS goal_contributions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (goal_id) REFERENCES savings_goals(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Settlements table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS settlements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER NOT NULL,
                to_user_id INTEGER NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                note TEXT,
                FOREIGN KEY (from_user_id) REFERENCES users(id),
                FOREIGN KEY (to_user_id) REFERENCES users(id)
            )
        ''')
        
        # Income/Salary table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS income (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                currency TEXT DEFAULT '$',
                source TEXT NOT NULL,  -- 'salary', 'bonus', 'freelance', 'investment', 'other'
                frequency TEXT DEFAULT 'monthly',  -- 'one-time', 'weekly', 'monthly', 'yearly'
                date TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Budget alerts table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS budget_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                budget_id INTEGER NOT NULL,
                alert_type TEXT NOT NULL,  -- 'warning', 'exceeded', 'approaching'
                percentage REAL NOT NULL,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                acknowledged BOOLEAN DEFAULT 0,
                FOREIGN KEY (budget_id) REFERENCES budgets(id)
            )
        ''')
        
        # Financial recommendations table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recommendation_type TEXT NOT NULL,  -- 'savings', 'investment', 'budget', 'warning'
                category TEXT,
                message TEXT NOT NULL,
                priority INTEGER DEFAULT 1,  -- 1=low, 2=medium, 3=high
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                acknowledged BOOLEAN DEFAULT 0
            )
        ''')
        
        # Create indexes
        self.conn.execute('CREATE INDEX IF NOT EXISTS idx_trans_user ON transactions(user_id)')
        self.conn.execute('CREATE INDEX IF NOT EXISTS idx_trans_date ON transactions(date)')
        self.conn.execute('CREATE INDEX IF NOT EXISTS idx_trans_category ON transactions(category)')
        self.conn.execute('CREATE INDEX IF NOT EXISTS idx_trans_type ON transactions(type)')
        self.conn.execute('CREATE INDEX IF NOT EXISTS idx_income_user ON income(user_id)')
        self.conn.execute('CREATE INDEX IF NOT EXISTS idx_income_date ON income(date)')
        
        self.conn.commit()
    
    # ==================== USER MANAGEMENT ====================
    
    def create_user(self, name, role='partner'):
        """
        Create a new user
        
        Args:
            name: User's name
            role: 'primary' or 'partner'
            
        Returns:
            dict: User info with ID
        """
        try:
            cursor = self.conn.execute(
                'INSERT INTO users (name, role) VALUES (?, ?)',
                (name, role)
            )
            self.conn.commit()
            
            user_id = cursor.lastrowid
            logger.info(f"[CouplesFinance] Created user: {name} (ID: {user_id})")
            
            return {
                'success': True,
                'user_id': user_id,
                'name': name,
                'role': role
            }
        except sqlite3.IntegrityError:
            return {
                'success': False,
                'message': f"User '{name}' already exists"
            }
    
    def get_user(self, name):
        """Get user by name"""
        result = self.conn.execute(
            'SELECT * FROM users WHERE name = ?',
            (name,)
        ).fetchone()
        
        if result:
            return {
                'id': result['id'],
                'name': result['name'],
                'role': result['role']
            }
        return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        result = self.conn.execute(
            'SELECT * FROM users WHERE id = ?',
            (user_id,)
        ).fetchone()
        
        if result:
            return {
                'id': result['id'],
                'name': result['name'],
                'role': result['role']
            }
        return None
    
    def list_users(self):
        """List all users"""
        results = self.conn.execute('SELECT * FROM users').fetchall()
        return [{'id': r['id'], 'name': r['name'], 'role': r['role']} for r in results]
    
    # ==================== TRANSACTION MANAGEMENT ====================
    
    def log_transaction(self, user_name, amount, currency, category, description, 
                       transaction_type='personal', split_ratio=0.5):
        """
        Log a transaction for a user
        
        Args:
            user_name: Name of user logging transaction
            amount: Transaction amount
            currency: Currency symbol
            category: Expense category
            description: Transaction description
            transaction_type: 'personal', 'shared', or 'reimbursement'
            split_ratio: For shared expenses (0.5 = 50/50)
            
        Returns:
            dict: Success status and message
        """
        try:
            # Get user
            user = self.get_user(user_name)
            if not user:
                return {
                    'success': False,
                    'message': f"User '{user_name}' not found. Create user first."
                }
            
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
                INSERT INTO transactions 
                (user_id, date, time, amount, currency, category, description, type, split_ratio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user['id'], date_str, time_str, amount, currency, category, 
                  description, transaction_type, split_ratio))
            
            self.conn.commit()
            
            # Build response message
            if transaction_type == 'shared':
                other_user_share = amount * split_ratio
                message = f"Logged {currency}{amount} shared expense for {description}. "
                message += f"Split: {user_name} paid, partner owes {currency}{other_user_share:.2f}"
            else:
                message = f"Logged {currency}{amount} personal expense for {description}"
            
            return {
                'success': True,
                'message': message
            }
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"[CouplesFinance] Error logging transaction: {e}")
            return {
                'success': False,
                'message': f"Error logging: {e}"
            }
    
    def analyze_spending(self, user_name=None, category=None, timeframe='month', 
                        include_shared=True):
        """
        Analyze spending for user(s)
        
        Args:
            user_name: Specific user (None = combined)
            category: Filter by category
            timeframe: 'today', 'month', 'all'
            include_shared: Include shared expenses
            
        Returns:
            str: Formatted spending analysis
        """
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        current_month = now.strftime("%Y-%m")
        
        # Build query
        query = "SELECT SUM(amount) as total, COUNT(*) as count FROM transactions WHERE 1=1"
        params = []
        
        # User filter
        if user_name:
            user = self.get_user(user_name)
            if user:
                query += " AND user_id = ?"
                params.append(user['id'])
        
        # Category filter
        if category:
            query += " AND LOWER(category) LIKE ?"
            params.append(f"%{category.lower()}%")
        
        # Timeframe filter
        if timeframe == "today":
            query += " AND date = ?"
            params.append(today_str)
        elif timeframe == "month":
            query += " AND date LIKE ?"
            params.append(f"{current_month}%")
        
        # Type filter
        if include_shared:
            query += " AND type IN ('personal', 'shared')"
        else:
            query += " AND type = 'personal'"
        
        result = self.conn.execute(query, params).fetchone()
        total = result['total'] or 0.0
        count = result['count'] or 0
        
        # Format response
        user_text = f"{user_name}'s" if user_name else "Combined"
        time_text = "today" if timeframe == "today" else "this month" if timeframe == "month" else "total"
        cat_text = f" on {category}" if category else ""
        
        if count == 0:
            return f"No spending found{cat_text} {time_text}."
        
        return f"{user_text} spending{cat_text} {time_text}: ${total:.2f} across {count} transactions."
    
    # ==================== SETTLEMENT SYSTEM ====================
    
    def calculate_balance(self):
        """
        Calculate who owes who based on shared expenses
        
        Returns:
            dict: Balance information
        """
        users = self.list_users()
        if len(users) < 2:
            return {
                'success': False,
                'message': "Need at least 2 users for settlement"
            }
        
        user1, user2 = users[0], users[1]
        
        # Get all shared expenses
        query = '''
            SELECT user_id, SUM(amount) as total_paid, SUM(amount * split_ratio) as total_owed
            FROM transactions
            WHERE type = 'shared'
            GROUP BY user_id
        '''
        
        results = self.conn.execute(query).fetchall()
        
        balances = {user1['id']: {'paid': 0, 'owed': 0}, 
                   user2['id']: {'paid': 0, 'owed': 0}}
        
        for row in results:
            user_id = row['user_id']
            if user_id in balances:
                balances[user_id]['paid'] = row['total_paid'] or 0
                balances[user_id]['owed'] = row['total_owed'] or 0
        
        # Calculate net balance
        user1_paid = balances[user1['id']]['paid']
        user2_paid = balances[user2['id']]['paid']
        total_shared = user1_paid + user2_paid
        fair_share = total_shared / 2
        
        user1_net = user1_paid - fair_share
        user2_net = user2_paid - fair_share
        
        if user1_net > 0:
            owes_who = f"{user2['name']} owes {user1['name']}"
            amount = user1_net
        elif user2_net > 0:
            owes_who = f"{user1['name']} owes {user2['name']}"
            amount = user2_net
        else:
            owes_who = "All settled up!"
            amount = 0
        
        return {
            'success': True,
            'user1': user1['name'],
            'user1_paid': user1_paid,
            'user2': user2['name'],
            'user2_paid': user2_paid,
            'total_shared': total_shared,
            'fair_share': fair_share,
            'balance': owes_who,
            'amount': abs(amount)
        }
    
    def settle_up(self, note=""):
        """
        Mark current balance as settled
        
        Returns:
            dict: Settlement confirmation
        """
        balance = self.calculate_balance()
        if not balance['success']:
            return balance
        
        if balance['amount'] == 0:
            return {
                'success': True,
                'message': "Already settled up!"
            }
        
        users = self.list_users()
        user1, user2 = users[0], users[1]
        
        # Determine who pays who
        if balance['user1_paid'] > balance['user2_paid']:
            from_user = user2['id']
            to_user = user1['id']
        else:
            from_user = user1['id']
            to_user = user2['id']
        
        # Record settlement
        self.conn.execute('''
            INSERT INTO settlements (from_user_id, to_user_id, amount, note)
            VALUES (?, ?, ?, ?)
        ''', (from_user, to_user, balance['amount'], note))
        
        # Mark shared expenses as settled (change type to 'reimbursement')
        self.conn.execute('''
            UPDATE transactions
            SET type = 'reimbursement'
            WHERE type = 'shared'
        ''')
        
        self.conn.commit()
        
        return {
            'success': True,
            'message': f"Settled! {balance['balance']} ${balance['amount']:.2f}"
        }
    
    # ==================== BUDGET MANAGEMENT ====================
    
    def set_budget(self, category, amount, period='monthly', budget_type='shared', user_name=None):
        """
        Set a budget for a category
        
        Args:
            category: Budget category
            amount: Budget amount
            period: 'weekly', 'monthly', 'yearly'
            budget_type: 'personal' or 'shared'
            user_name: Required if budget_type='personal'
        """
        try:
            user_id = None
            if budget_type == 'personal':
                if not user_name:
                    return {'success': False, 'message': "user_name required for personal budget"}
                user = self.get_user(user_name)
                if not user:
                    return {'success': False, 'message': f"User '{user_name}' not found"}
                user_id = user['id']
            
            # Check if budget exists
            query = 'SELECT id FROM budgets WHERE category = ? AND budget_type = ?'
            params = [category, budget_type]
            if user_id:
                query += ' AND user_id = ?'
                params.append(user_id)
            
            existing = self.conn.execute(query, params).fetchone()
            
            if existing:
                # Update existing budget
                self.conn.execute('''
                    UPDATE budgets SET amount = ?, period = ?
                    WHERE id = ?
                ''', (amount, period, existing['id']))
            else:
                # Create new budget
                self.conn.execute('''
                    INSERT INTO budgets (category, amount, period, budget_type, user_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (category, amount, period, budget_type, user_id))
            
            self.conn.commit()
            
            budget_owner = f"{user_name}'s" if user_name else "Shared"
            return {
                'success': True,
                'message': f"Set {budget_owner} {period} budget for {category}: ${amount}"
            }
        except Exception as e:
            self.conn.rollback()
            return {'success': False, 'message': f"Error setting budget: {e}"}
    
    def check_budget_status(self, category=None):
        """
        Check budget status for category or all categories
        
        Returns:
            str: Budget status report
        """
        query = 'SELECT * FROM budgets'
        params = []
        
        if category:
            query += ' WHERE category = ?'
            params.append(category)
        
        budgets = self.conn.execute(query, params).fetchall()
        
        if not budgets:
            return "No budgets set."
        
        now = datetime.now()
        current_month = now.strftime("%Y-%m")
        
        report = "Budget Status:\n"
        
        for budget in budgets:
            # Calculate spending for this budget
            spent_query = '''
                SELECT SUM(amount) as total
                FROM transactions
                WHERE category = ? AND date LIKE ?
            '''
            spent_params = [budget['category'], f"{current_month}%"]
            
            if budget['user_id']:
                spent_query += ' AND user_id = ?'
                spent_params.append(budget['user_id'])
            
            result = self.conn.execute(spent_query, spent_params).fetchone()
            spent = result['total'] or 0
            
            percentage = (spent / budget['amount'] * 100) if budget['amount'] > 0 else 0
            status = "✅" if percentage < 80 else "⚠️" if percentage < 100 else "❌"
            
            budget_owner = ""
            if budget['user_id']:
                user = self.get_user_by_id(budget['user_id'])
                budget_owner = f"{user['name']}'s "
            
            report += f"{status} {budget_owner}{budget['category']}: ${spent:.2f}/${budget['amount']} ({percentage:.0f}%)\n"
        
        return report.strip()
    
    # ==================== INCOME/SALARY MANAGEMENT ====================
    
    def log_income(self, user_name, amount, currency, source, frequency='monthly', description=''):
        """
        Log income/salary for a user
        
        Args:
            user_name: Name of user
            amount: Income amount
            currency: Currency symbol
            source: 'salary', 'bonus', 'freelance', 'investment', 'other'
            frequency: 'one-time', 'weekly', 'monthly', 'yearly'
            description: Optional description
            
        Returns:
            dict: Success status and message
        """
        try:
            user = self.get_user(user_name)
            if not user:
                return {
                    'success': False,
                    'message': f"User '{user_name}' not found"
                }
            
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            
            self.conn.execute('''
                INSERT INTO income (user_id, amount, currency, source, frequency, date, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user['id'], amount, currency, source, frequency, date_str, description))
            
            self.conn.commit()
            
            return {
                'success': True,
                'message': f"Logged {currency}{amount} {source} income for {user_name}"
            }
        except Exception as e:
            self.conn.rollback()
            return {
                'success': False,
                'message': f"Error logging income: {e}"
            }
    
    def get_monthly_income(self, user_name=None):
        """
        Get total monthly income for user(s)
        
        Args:
            user_name: Specific user (None = combined)
            
        Returns:
            float: Total monthly income
        """
        now = datetime.now()
        current_month = now.strftime("%Y-%m")
        
        query = "SELECT SUM(amount) as total FROM income WHERE date LIKE ?"
        params = [f"{current_month}%"]
        
        if user_name:
            user = self.get_user(user_name)
            if user:
                query += " AND user_id = ?"
                params.append(user['id'])
        
        result = self.conn.execute(query, params).fetchone()
        return result['total'] or 0.0
    
    # ==================== PROACTIVE BUDGET WARNINGS ====================
    
    def check_budget_warnings(self):
        """
        Check all budgets and generate warnings if approaching limits
        
        Returns:
            list: List of budget warnings
        """
        now = datetime.now()
        current_month = now.strftime("%Y-%m")
        
        budgets = self.conn.execute('SELECT * FROM budgets').fetchall()
        warnings = []
        
        for budget in budgets:
            # Calculate spending
            spent_query = '''
                SELECT SUM(amount) as total
                FROM transactions
                WHERE category = ? AND date LIKE ?
            '''
            spent_params = [budget['category'], f"{current_month}%"]
            
            if budget['user_id']:
                spent_query += ' AND user_id = ?'
                spent_params.append(budget['user_id'])
            
            result = self.conn.execute(spent_query, spent_params).fetchone()
            spent = result['total'] or 0
            
            percentage = (spent / budget['amount'] * 100) if budget['amount'] > 0 else 0
            
            budget_owner = ""
            if budget['user_id']:
                user = self.get_user_by_id(budget['user_id'])
                budget_owner = f"{user['name']}'s "
            
            # Generate warnings
            if percentage >= 100:
                warnings.append({
                    'type': 'exceeded',
                    'priority': 3,
                    'category': budget['category'],
                    'message': f"⛔ {budget_owner}{budget['category']} budget EXCEEDED! ${spent:.2f}/${budget['amount']} ({percentage:.0f}%)",
                    'spent': spent,
                    'budget': budget['amount'],
                    'percentage': percentage
                })
            elif percentage >= 90:
                warnings.append({
                    'type': 'critical',
                    'priority': 3,
                    'category': budget['category'],
                    'message': f"🚨 {budget_owner}{budget['category']} budget at {percentage:.0f}%! Only ${budget['amount'] - spent:.2f} left",
                    'spent': spent,
                    'budget': budget['amount'],
                    'percentage': percentage
                })
            elif percentage >= 75:
                warnings.append({
                    'type': 'warning',
                    'priority': 2,
                    'category': budget['category'],
                    'message': f"⚠️  {budget_owner}{budget['category']} budget at {percentage:.0f}%. ${budget['amount'] - spent:.2f} remaining",
                    'spent': spent,
                    'budget': budget['amount'],
                    'percentage': percentage
                })
        
        return warnings
    
    def will_exceed_budget(self, category, amount, user_name=None):
        """
        Check if a new expense would exceed budget
        
        Args:
            category: Expense category
            amount: Proposed expense amount
            user_name: User making the expense
            
        Returns:
            dict: Warning information
        """
        now = datetime.now()
        current_month = now.strftime("%Y-%m")
        
        # Find relevant budget
        query = 'SELECT * FROM budgets WHERE category = ?'
        params = [category]
        
        if user_name:
            user = self.get_user(user_name)
            if user:
                query += ' AND (budget_type = "shared" OR user_id = ?)'
                params.append(user['id'])
        
        budget = self.conn.execute(query, params).fetchone()
        
        if not budget:
            return {
                'will_exceed': False,
                'message': f"No budget set for {category}"
            }
        
        # Calculate current spending
        spent_query = '''
            SELECT SUM(amount) as total
            FROM transactions
            WHERE category = ? AND date LIKE ?
        '''
        spent_params = [category, f"{current_month}%"]
        
        if budget['user_id']:
            spent_query += ' AND user_id = ?'
            spent_params.append(budget['user_id'])
        
        result = self.conn.execute(spent_query, spent_params).fetchone()
        current_spent = result['total'] or 0
        
        # Check if new expense would exceed
        new_total = current_spent + amount
        percentage = (new_total / budget['amount'] * 100) if budget['amount'] > 0 else 0
        
        if percentage > 100:
            return {
                'will_exceed': True,
                'priority': 3,
                'message': f"⛔ This ${amount} expense would EXCEED your {category} budget! (${new_total:.2f}/${budget['amount']})",
                'current_spent': current_spent,
                'new_total': new_total,
                'budget': budget['amount'],
                'percentage': percentage,
                'overage': new_total - budget['amount']
            }
        elif percentage > 90:
            return {
                'will_exceed': False,
                'warning': True,
                'priority': 2,
                'message': f"⚠️  This ${amount} expense would put you at {percentage:.0f}% of {category} budget",
                'current_spent': current_spent,
                'new_total': new_total,
                'budget': budget['amount'],
                'percentage': percentage
            }
        else:
            return {
                'will_exceed': False,
                'warning': False,
                'message': f"✅ Within budget. {category}: ${new_total:.2f}/${budget['amount']} ({percentage:.0f}%)",
                'current_spent': current_spent,
                'new_total': new_total,
                'budget': budget['amount'],
                'percentage': percentage
            }
    
    # ==================== FINANCIAL RECOMMENDATIONS ====================
    
    def generate_recommendations(self):
        """
        Generate AI-powered financial recommendations
        
        Returns:
            list: List of recommendations
        """
        recommendations = []
        now = datetime.now()
        current_month = now.strftime("%Y-%m")
        
        # Get income and spending
        total_income = self.get_monthly_income()
        
        # Get total spending
        result = self.conn.execute('''
            SELECT SUM(amount) as total
            FROM transactions
            WHERE date LIKE ?
        ''', (f"{current_month}%",)).fetchone()
        total_spending = result['total'] or 0
        
        # 1. Savings Rate Recommendation
        if total_income > 0:
            savings = total_income - total_spending
            savings_rate = (savings / total_income * 100)
            
            if savings_rate < 10:
                recommendations.append({
                    'type': 'savings',
                    'priority': 3,
                    'message': f"🚨 LOW SAVINGS RATE: You're only saving {savings_rate:.1f}% of income. Aim for at least 20%!",
                    'action': f"Try to save ${total_income * 0.2 - savings:.2f} more this month"
                })
            elif savings_rate < 20:
                recommendations.append({
                    'type': 'savings',
                    'priority': 2,
                    'message': f"💰 Good start! Saving {savings_rate:.1f}% of income. Try to reach 20%",
                    'action': f"Save ${total_income * 0.2 - savings:.2f} more to hit 20% target"
                })
            else:
                recommendations.append({
                    'type': 'savings',
                    'priority': 1,
                    'message': f"✅ EXCELLENT! Saving {savings_rate:.1f}% of income. Keep it up!",
                    'action': f"Consider investing ${savings:.2f} for long-term growth"
                })
        
        # 2. Category-specific recommendations
        category_spending = {}
        results = self.conn.execute('''
            SELECT category, SUM(amount) as total
            FROM transactions
            WHERE date LIKE ?
            GROUP BY category
        ''', (f"{current_month}%",)).fetchall()
        
        for row in results:
            category_spending[row['category']] = row['total']
        
        # Food/Dining recommendations
        food_total = category_spending.get('Food', 0) + category_spending.get('Groceries', 0)
        if total_income > 0 and food_total / total_income > 0.15:
            recommendations.append({
                'type': 'budget',
                'category': 'Food',
                'priority': 2,
                'message': f"🍔 Food spending is {food_total/total_income*100:.1f}% of income (${food_total:.2f})",
                'action': "Consider meal prepping to save $100-200/month"
            })
        
        # Entertainment recommendations
        entertainment = category_spending.get('Entertainment', 0)
        if total_income > 0 and entertainment / total_income > 0.10:
            recommendations.append({
                'type': 'budget',
                'category': 'Entertainment',
                'priority': 2,
                'message': f"🎬 Entertainment is {entertainment/total_income*100:.1f}% of income (${entertainment:.2f})",
                'action': "Look for free/low-cost alternatives to save money"
            })
        
        # 3. Investment recommendations
        if total_income > 0:
            savings = total_income - total_spending
            if savings > 500:
                recommendations.append({
                    'type': 'investment',
                    'priority': 2,
                    'message': f"💹 You have ${savings:.2f} in savings this month",
                    'action': "Consider investing in index funds (S&P 500) for long-term growth"
                })
        
        # 4. Emergency fund recommendation
        # Check if they have 3-6 months of expenses saved
        avg_monthly_spending = total_spending  # Simplified
        emergency_fund_target = avg_monthly_spending * 6
        
        recommendations.append({
            'type': 'savings',
            'priority': 3,
            'message': f"🏦 Emergency Fund Target: ${emergency_fund_target:.2f} (6 months expenses)",
            'action': "Build emergency fund before investing"
        })
        
        # 5. Debt recommendations (if applicable)
        # This would check for high-interest debt
        
        return sorted(recommendations, key=lambda x: x['priority'], reverse=True)
    
    def get_financial_health_score(self):
        """
        Calculate overall financial health score (0-100)
        
        Returns:
            dict: Health score and breakdown
        """
        score = 0
        breakdown = {}
        now = datetime.now()
        current_month = now.strftime("%Y-%m")
        
        # 1. Savings Rate (30 points)
        total_income = self.get_monthly_income()
        result = self.conn.execute('''
            SELECT SUM(amount) as total
            FROM transactions
            WHERE date LIKE ?
        ''', (f"{current_month}%",)).fetchone()
        total_spending = result['total'] or 0
        
        if total_income > 0:
            savings_rate = ((total_income - total_spending) / total_income * 100)
            savings_score = min(30, savings_rate * 1.5)  # 20% savings = 30 points
            score += savings_score
            breakdown['savings_rate'] = {
                'score': savings_score,
                'max': 30,
                'percentage': savings_rate
            }
        
        # 2. Budget Adherence (40 points)
        budgets = self.conn.execute('SELECT * FROM budgets').fetchall()
        if budgets:
            budget_scores = []
            for budget in budgets:
                spent_query = '''
                    SELECT SUM(amount) as total
                    FROM transactions
                    WHERE category = ? AND date LIKE ?
                '''
                result = self.conn.execute(spent_query, (budget['category'], f"{current_month}%")).fetchone()
                spent = result['total'] or 0
                
                percentage = (spent / budget['amount'] * 100) if budget['amount'] > 0 else 0
                
                if percentage <= 80:
                    budget_scores.append(10)
                elif percentage <= 100:
                    budget_scores.append(5)
                else:
                    budget_scores.append(0)
            
            budget_score = sum(budget_scores) / len(budget_scores) * 4  # Max 40 points
            score += budget_score
            breakdown['budget_adherence'] = {
                'score': budget_score,
                'max': 40
            }
        
        # 3. Income Stability (15 points)
        # Check if income is logged regularly
        income_count = self.conn.execute('''
            SELECT COUNT(*) as count
            FROM income
            WHERE date LIKE ?
        ''', (f"{current_month}%",)).fetchone()['count']
        
        income_score = min(15, income_count * 7.5)  # 2 income entries = 15 points
        score += income_score
        breakdown['income_stability'] = {
            'score': income_score,
            'max': 15
        }
        
        # 4. Financial Awareness (15 points)
        # Based on transaction logging frequency
        transaction_count = self.conn.execute('''
            SELECT COUNT(*) as count
            FROM transactions
            WHERE date LIKE ?
        ''', (f"{current_month}%",)).fetchone()['count']
        
        awareness_score = min(15, transaction_count * 0.5)  # 30 transactions = 15 points
        score += awareness_score
        breakdown['financial_awareness'] = {
            'score': awareness_score,
            'max': 15
        }
        
        # Overall grade
        if score >= 90:
            grade = "A+ Excellent"
        elif score >= 80:
            grade = "A Good"
        elif score >= 70:
            grade = "B Fair"
        elif score >= 60:
            grade = "C Needs Improvement"
        else:
            grade = "D Poor"
        
        return {
            'score': round(score, 1),
            'grade': grade,
            'breakdown': breakdown,
            'total_income': total_income,
            'total_spending': total_spending,
            'savings': total_income - total_spending
        }
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()


if __name__ == "__main__":
    # Test the couples finance manager
    print("="*70)
    print("  Couples Finance Manager - Test")
    print("="*70)
    
    # Initialize
    fm = CouplesFinanceManager("test_couples_finance.db")
    
    # Create users
    print("\n[1] Creating users...")
    fm.create_user("Brendan", "primary")
    fm.create_user("Partner", "partner")
    print("Users created:", fm.list_users())
    
    # Log some transactions
    print("\n[2] Logging transactions...")
    fm.log_transaction("Brendan", 50, "$", "Food", "Lunch")
    fm.log_transaction("Partner", 30, "$", "Coffee", "Morning coffee")
    fm.log_transaction("Brendan", 100, "$", "Groceries", "Weekly shopping", "shared")
    fm.log_transaction("Partner", 80, "$", "Utilities", "Electric bill", "shared")
    
    # Analyze spending
    print("\n[3] Analyzing spending...")
    print(fm.analyze_spending("Brendan"))
    print(fm.analyze_spending("Partner"))
    print(fm.analyze_spending())  # Combined
    
    # Check balance
    print("\n[4] Checking balance...")
    balance = fm.calculate_balance()
    print(f"{balance['balance']}: ${balance['amount']:.2f}")
    
    # Set budgets
    print("\n[5] Setting budgets...")
    fm.set_budget("Food", 500, "monthly", "shared")
    fm.set_budget("Coffee", 100, "monthly", "personal", "Partner")
    print(fm.check_budget_status())
    
    # Cleanup
    import os
    fm.close()
    os.remove("test_couples_finance.db")
    
    print("\n" + "="*70)
    print("Test complete!")
    print("="*70)
