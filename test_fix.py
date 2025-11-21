from llm_core import LLMCore
from command_executor import CommandExecutor

def test_fix():
    print("--- Testing Transaction Memory Fix ---")
    
    llm = LLMCore()
    executor = CommandExecutor()
    
    # 1. Simulate User: "Spent $100 on groceries"
    print("\n1. User: Spent $100 on groceries")
    user_input = "Spent $100 on groceries"
    decision = llm.process(user_input)
    print(f"Decision: {decision}")
    
    intent = decision.get("intent", {})
    if intent.get("success") and intent.get("action") == "track_expense":
        # Execute
        result = executor.execute(intent)
        print(f"Execution Result: {result}")
        
        # THIS IS THE FIX: Add result to history
        llm.add_entry("system", f"Action executed. Result: {result['message']}")
    
    # 2. Simulate User: "What did I just spend?"
    print("\n2. User: What did I just spend?")
    user_input_2 = "What did I just spend?"
    decision_2 = llm.process(user_input_2)
    print(f"Response: {decision_2.get('response')}")
    
    # Check if response mentions the $100
    response_text = decision_2.get("response", "").lower()
    if "100" in response_text or "groceries" in response_text:
        print("\nSUCCESS: Agent remembered the transaction.")
    else:
        print("\nFAILURE: Agent did not mention the transaction.")

if __name__ == "__main__":
    test_fix()
