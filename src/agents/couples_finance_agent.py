"""
Couples Finance Agent - Specialized agent for couples financial tracking
Extends base Finance Agent with multi-user support
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Dict, Any, List
from src.agents.base_agent import BaseAgent, AgentMessage, AgentCapability
from src.modules.couples_finance_manager import CouplesFinanceManager
import time


class CouplesFinanceAgent(BaseAgent):
    """
    Specialized agent for couples financial operations
    
    Capabilities:
    - Track expenses for two users
    - Shared expense management
    - Settlement calculations
    - Budget management (personal + shared)
    - Savings goals
    """
    
    def __init__(self):
        super().__init__(name="couples_finance_agent", role="Couples Financial Advisor")
        
        # Initialize couples finance tools
        self.finance_manager = CouplesFinanceManager()
        
        # Register capabilities
        self._register_capabilities()
        
        self.logger.info("Couples Finance Agent ready")
    
    def _register_capabilities(self):
        """Register all financial capabilities"""
        self.register_capability(
            name="track_expense",
            description="Log an expense for a user (personal or shared)",
            parameters=["user_name", "amount", "currency", "category", "description", "type", "split_ratio"]
        )
        
        self.register_capability(
            name="analyze_spending",
            description="Analyze spending for user(s)",
            parameters=["user_name", "category", "timeframe"]
        )
        
        self.register_capability(
            name="calculate_balance",
            description="Calculate who owes who",
            parameters=[]
        )
        
        self.register_capability(
            name="settle_up",
            description="Mark current balance as settled",
            parameters=["note"]
        )
        
        self.register_capability(
            name="set_budget",
            description="Set a budget (personal or shared)",
            parameters=["category", "amount", "period", "budget_type", "user_name"]
        )
        
        self.register_capability(
            name="check_budget_status",
            description="Check budget status",
            parameters=["category"]
        )
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Return list of capabilities"""
        return self.capabilities
    
    def can_handle(self, task: Dict[str, Any]) -> float:
        """
        Determine if this agent can handle a task
        
        Returns confidence score (0.0 to 1.0)
        """
        action = task.get("action", "").lower()
        
        # High confidence for explicit finance actions
        finance_keywords = [
            "expense", "spending", "budget", "money", "cost", 
            "price", "finance", "track", "analyze", "spent",
            "owe", "owes", "settle", "split", "shared"
        ]
        
        if any(keyword in action for keyword in finance_keywords):
            return 0.95
        
        # Check content for finance-related terms
        content = str(task.get("content", "")).lower()
        if any(keyword in content for keyword in finance_keywords):
            return 0.75
        
        return 0.0
    
    def process_message(self, message: AgentMessage) -> AgentMessage:
        """
        Process incoming message and execute financial task
        
        Args:
            message: Incoming message from orchestrator or other agent
            
        Returns:
            Response message with results
        """
        start_time = time.time()
        
        try:
            content = message.content
            action = content.get("action")
            params = content.get("params", {})
            
            self.logger.info(f"Processing action: {action}")
            
            # Route to appropriate handler
            if action == "track_expense":
                result = self._track_expense(params)
            elif action == "analyze_spending":
                result = self._analyze_spending(params)
            elif action == "calculate_balance":
                result = self._calculate_balance(params)
            elif action == "settle_up":
                result = self._settle_up(params)
            elif action == "set_budget":
                result = self._set_budget(params)
            elif action == "check_budget_status":
                result = self._check_budget_status(params)
            else:
                result = {
                    "success": False,
                    "message": f"Unknown action: {action}"
                }
            
            # Update metrics
            response_time = time.time() - start_time
            self.update_metrics(success=result.get("success", False), 
                              response_time=response_time)
            
            # Create response message
            response = self.send_message(
                to_agent=message.from_agent,
                content=result,
                msg_type="response"
            )
            response.task_id = message.task_id
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            response_time = time.time() - start_time
            self.update_metrics(success=False, response_time=response_time)
            
            return self.send_message(
                to_agent=message.from_agent,
                content={
                    "success": False,
                    "message": f"Error: {str(e)}"
                },
                msg_type="error"
            )
    
    def _track_expense(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Track an expense"""
        try:
            result = self.finance_manager.log_transaction(
                user_name=params.get("user_name", "User1"),
                amount=params.get("amount"),
                currency=params.get("currency", "$"),
                category=params.get("category"),
                description=params.get("description", ""),
                transaction_type=params.get("type", "personal"),
                split_ratio=params.get("split_ratio", 0.5)
            )
            return result
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to track expense: {str(e)}"
            }
    
    def _analyze_spending(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze spending patterns"""
        try:
            analysis = self.finance_manager.analyze_spending(
                user_name=params.get("user_name"),
                category=params.get("category"),
                timeframe=params.get("timeframe", "month")
            )
            return {
                "success": True,
                "message": analysis,
                "data": analysis
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to analyze spending: {str(e)}"
            }
    
    def _calculate_balance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate who owes who"""
        try:
            balance = self.finance_manager.calculate_balance()
            if balance['success']:
                message = f"{balance['balance']}: ${balance['amount']:.2f}"
                return {
                    "success": True,
                    "message": message,
                    "data": balance
                }
            return balance
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to calculate balance: {str(e)}"
            }
    
    def _settle_up(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Settle up current balance"""
        try:
            result = self.finance_manager.settle_up(
                note=params.get("note", "")
            )
            return result
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to settle up: {str(e)}"
            }
    
    def _set_budget(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set a budget"""
        try:
            result = self.finance_manager.set_budget(
                category=params.get("category"),
                amount=params.get("amount"),
                period=params.get("period", "monthly"),
                budget_type=params.get("budget_type", "shared"),
                user_name=params.get("user_name")
            )
            return result
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to set budget: {str(e)}"
            }
    
    def _check_budget_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check budget status"""
        try:
            status = self.finance_manager.check_budget_status(
                category=params.get("category")
            )
            return {
                "success": True,
                "message": status,
                "data": status
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to check budget: {str(e)}"
            }


if __name__ == "__main__":
    # Test the Couples Finance Agent
    print("Testing Couples Finance Agent\n")
    
    agent = CouplesFinanceAgent()
    
    # First, create users in the database
    agent.finance_manager.create_user("Brendan", "primary")
    agent.finance_manager.create_user("Partner", "partner")
    
    # Test 1: Track personal expense
    print("Test 1: Track personal expense")
    message = AgentMessage(
        from_agent="orchestrator",
        to_agent="couples_finance_agent",
        content={
            "action": "track_expense",
            "params": {
                "user_name": "Brendan",
                "amount": 50,
                "currency": "$",
                "category": "food",
                "description": "lunch",
                "type": "personal"
            }
        }
    )
    response = agent.process_message(message)
    print(f"Response: {response.content}\n")
    
    # Test 2: Track shared expense
    print("Test 2: Track shared expense")
    message = AgentMessage(
        from_agent="orchestrator",
        to_agent="couples_finance_agent",
        content={
            "action": "track_expense",
            "params": {
                "user_name": "Partner",
                "amount": 100,
                "currency": "$",
                "category": "groceries",
                "description": "weekly shopping",
                "type": "shared",
                "split_ratio": 0.5
            }
        }
    )
    response = agent.process_message(message)
    print(f"Response: {response.content}\n")
    
    # Test 3: Calculate balance
    print("Test 3: Calculate balance")
    message = AgentMessage(
        from_agent="orchestrator",
        to_agent="couples_finance_agent",
        content={
            "action": "calculate_balance",
            "params": {}
        }
    )
    response = agent.process_message(message)
    print(f"Response: {response.content}\n")
    
    # Test 4: Set budget
    print("Test 4: Set shared budget")
    message = AgentMessage(
        from_agent="orchestrator",
        to_agent="couples_finance_agent",
        content={
            "action": "set_budget",
            "params": {
                "category": "food",
                "amount": 500,
                "period": "monthly",
                "budget_type": "shared"
            }
        }
    )
    response = agent.process_message(message)
    print(f"Response: {response.content}\n")
    
    # Test 5: Check budget status
    print("Test 5: Check budget status")
    message = AgentMessage(
        from_agent="orchestrator",
        to_agent="couples_finance_agent",
        content={
            "action": "check_budget_status",
            "params": {}
        }
    )
    response = agent.process_message(message)
    print(f"Response: {response.content}\n")
    
    # Check agent status
    status = agent.get_status()
    print(f"Agent Status:")
    print(f"  Tasks Completed: {status['metrics']['tasks_completed']}")
    print(f"  Tasks Failed: {status['metrics']['tasks_failed']}")
    print(f"  Avg Response Time: {status['metrics']['average_response_time']:.3f}s")
