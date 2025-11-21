from finance_manager import FinanceManager

def test_memory():
    fm = FinanceManager()
    print("--- Testing analyze_spending ---")
    
    # Test 1: All spending
    print("\n1. All spending:")
    res = fm.analyze_spending(timeframe="all")
    print(res)
    
    # Test 2: Specific category (groceries)
    print("\n2. Groceries spending:")
    res = fm.analyze_spending(category="groceries", timeframe="all")
    print(res)
    
    # Test 3: Today spending
    print("\n3. Today spending:")
    res = fm.analyze_spending(timeframe="today")
    print(res)

if __name__ == "__main__":
    test_memory()
