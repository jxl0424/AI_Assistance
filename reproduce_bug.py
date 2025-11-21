
from command_executor import CommandExecutor

def test_ask_finance_bug():
    executor = CommandExecutor()
    
    intent = {
        "success": True,
        "action": "ask_finance",
        "target": None,
        "timeframe": "today"
    }
    
    print(f"Testing intent: {intent}")
    result = executor.execute(intent)
    print(f"Result: {result}")
    
    if result["message"] == "Conversation processed":
        print("BUG CONFIRMED: 'ask_finance' action fell through to default chat handler.")
    else:
        print("'ask_finance' handled correctly (or at least differently).")

if __name__ == "__main__":
    test_ask_finance_bug()
