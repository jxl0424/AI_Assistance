"""
Finance Agent - Specialized agent for financial tracking and analysis
"""

from typing import Dict, Any, List
from src.agents.base_agent import BaseAgent, AgentMessage, AgentCapability
from src.modules.finance_manager_sql import FinanceManagerSQL
import time


class FinanceAgent(BaseAgent):
    """
    Specialized agent for financial operations
    
    Capabilities:
    - Track expenses and income
    - Analyze spending patterns
    - Budget management
    - Financial reporting
    """
    
    def __init__(self):
        super().__init__(name="finance_agent", role="Financial Advisor")
        
        # Initialize finance tools
        self.finance_manager = FinanceManagerSQL()
        
        # Register capabilities
        self._register_capabilities()
        
        self.logger.info("Finance Agent ready")
    
    def _register_capabilities(self):
        """Register all financial capabilities"""
        self.register_capability(
            name="track_expense",
            description="Log an expense transaction",
            parameters=["amount", "currency", "category", "description"]
        )
        
        self.register_capability(
            name="analyze_spending",
            description="Analyze spending patterns by category or timeframe",
            parameters=["category", "timeframe"]
        )
        
        self.register_capability(
            name="get_budget_status",
            description="Check budget status for a category",
            parameters=["category"]
        )
        
        self.register_capability(
            name="generate_report",
            description="Generate financial report",
            parameters=["timeframe", "format"]
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
            "price", "finance", "track", "analyze", "spent"
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
            elif action == "get_budget_status":
                result = self._get_budget_status(params)
            elif action == "generate_report":
                result = self._generate_report(params)
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
                amount=params.get("amount"),
                currency=params.get("currency", "$"),
                category=params.get("category"),
                description=params.get("description", "")
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
                category=params.get("category"),
                timeframe=params.get("timeframe", "all")
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
    
    def _get_budget_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get budget status for a category"""
        try:
            category = params.get("category")
            # This would need to be implemented in FinanceManagerSQL
            # For now, return a placeholder
            return {
                "success": True,
                "message": f"Budget status for {category} not yet implemented",
                "data": {}
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to get budget status: {str(e)}"
            }
    
    def _generate_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate financial report"""
        try:
            timeframe = params.get("timeframe", "month")
            # This would generate a comprehensive report
            # For now, return a placeholder
            return {
                "success": True,
                "message": f"Financial report for {timeframe} not yet implemented",
                "data": {}
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to generate report: {str(e)}"
            }


if __name__ == "__main__":
    # Test the Finance Agent
    print("Testing Finance Agent\n")
    
    agent = FinanceAgent()
    
    # Test capability check
    task = {"action": "track_expense", "content": "I spent $50 on food"}
    confidence = agent.can_handle(task)
    print(f"Can handle task: {confidence:.2f}\n")
    
    # Test message processing
    message = AgentMessage(
        from_agent="orchestrator",
        to_agent="finance_agent",
        content={
            "action": "track_expense",
            "params": {
                "amount": 50,
                "currency": "$",
                "category": "food",
                "description": "lunch"
            }
        }
    )
    
    response = agent.process_message(message)
    print(f"Response: {response.content}\n")
    
    # Check status
    status = agent.get_status()
    print(f"Agent Status: {status}")
