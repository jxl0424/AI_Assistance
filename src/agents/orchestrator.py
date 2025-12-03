"""
Agent Orchestrator - Coordinates all specialized agents
"""

from typing import Dict, Any, List, Optional
from src.agents.base_agent import BaseAgent, AgentMessage
from src.core.logger_config import get_logger
from openai import OpenAI
import json
import time

logger = get_logger(__name__)


class AgentOrchestrator:
    """
    Central coordinator for multi-agent system
    
    Responsibilities:
    - Route tasks to appropriate agents
    - Coordinate multi-agent collaboration
    - Synthesize responses from multiple agents
    - Manage shared context
    """
    
    def __init__(self, memory_manager=None):
        self.agents: Dict[str, BaseAgent] = {}
        self.memory_manager = memory_manager
        self.shared_context: Dict[str, Any] = {}
        self.task_history: List[Dict[str, Any]] = []
        
        # LLM for orchestration decisions
        self.client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama"
        )
        self.model = "llama3.2"
        
        logger.info("Agent Orchestrator initialized")
    
    def register_agent(self, agent: BaseAgent):
        """
        Register a new agent with the orchestrator
        
        Args:
            agent: Agent instance to register
        """
        self.agents[agent.name] = agent
        logger.info(f"Registered agent: {agent.name} ({agent.role})")
        
        # Log capabilities
        for cap in agent.get_capabilities():
            logger.info(f"  - {cap.name}: {cap.description}")
    
    def unregister_agent(self, agent_name: str):
        """Remove an agent from the orchestrator"""
        if agent_name in self.agents:
            del self.agents[agent_name]
            logger.info(f"Unregistered agent: {agent_name}")
    
    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """Get agent by name"""
        return self.agents.get(agent_name)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents and their capabilities"""
        return [
            {
                "name": agent.name,
                "role": agent.role,
                "capabilities": [cap.to_dict() for cap in agent.get_capabilities()],
                "metrics": agent.metrics
            }
            for agent in self.agents.values()
        ]
    
    def route_task(self, user_input: str) -> Dict[str, Any]:
        """
        Route user input to appropriate agent(s)
        
        Args:
            user_input: User's natural language request
            
        Returns:
            Response from agent(s)
        """
        start_time = time.time()
        
        try:
            # Step 1: Use LLM to understand intent and identify required agents
            routing_decision = self._decide_routing(user_input)
            
            logger.info(f"Routing decision: {routing_decision}")
            
            # Step 2: Execute task with selected agent(s)
            if routing_decision["type"] == "single":
                result = self._execute_single_agent(routing_decision, user_input)
            elif routing_decision["type"] == "multi":
                result = self._execute_multi_agent(routing_decision, user_input)
            else:
                result = self._handle_chat(user_input)
            
            # Step 3: Record task
            self.task_history.append({
                "input": user_input,
                "routing": routing_decision,
                "result": result,
                "duration": time.time() - start_time,
                "timestamp": time.time()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error routing task: {e}")
            return {
                "success": False,
                "response": "I encountered an error processing your request.",
                "error": str(e)
            }
    
    def _decide_routing(self, user_input: str) -> Dict[str, Any]:
        """
        Use LLM to decide which agent(s) should handle the task
        
        Returns:
            Routing decision with agent names and actions
        """
        # Build agent capabilities description
        agent_descriptions = []
        for agent in self.agents.values():
            caps = ", ".join([cap.name for cap in agent.get_capabilities()])
            agent_descriptions.append(
                f"- {agent.name} ({agent.role}): {caps}"
            )
        
        agents_text = "\n".join(agent_descriptions)
        
        prompt = f"""
You are an orchestrator deciding which agent(s) should handle a user request.

AVAILABLE AGENTS:
{agents_text}

USER REQUEST: "{user_input}"

Decide which agent(s) to use and what action(s) to take.

RESPONSE FORMAT (JSON only):
{{
    "type": "single|multi|chat",
    "agents": [
        {{
            "name": "agent_name",
            "action": "capability_name",
            "params": {{}},
            "reason": "why this agent"
        }}
    ],
    "response_template": "How to respond to user"
}}

If it's just conversation (no action needed), use type="chat".
If multiple agents needed, use type="multi".
"""
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            response = completion.choices[0].message.content
            return json.loads(response)
            
        except Exception as e:
            logger.error(f"Error in routing decision: {e}")
            return {"type": "chat", "agents": []}
    
    def _execute_single_agent(self, routing: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """Execute task with a single agent"""
        if not routing.get("agents"):
            return {"success": False, "response": "No agent selected"}
        
        agent_info = routing["agents"][0]
        agent_name = agent_info["name"]
        agent = self.get_agent(agent_name)
        
        if not agent:
            return {"success": False, "response": f"Agent {agent_name} not found"}
        
        # Create message for agent
        message = AgentMessage(
            from_agent="orchestrator",
            to_agent=agent_name,
            content={
                "action": agent_info["action"],
                "params": agent_info.get("params", {}),
                "context": user_input
            }
        )
        
        # Send to agent and get response
        response = agent.process_message(message)
        
        return {
            "success": response.content.get("success", False),
            "response": response.content.get("message", ""),
            "data": response.content.get("data"),
            "agent": agent_name
        }
    
    def _execute_multi_agent(self, routing: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """Execute task with multiple agents (sequential for now)"""
        results = []
        
        for agent_info in routing.get("agents", []):
            agent_name = agent_info["name"]
            agent = self.get_agent(agent_name)
            
            if not agent:
                logger.warning(f"Agent {agent_name} not found, skipping")
                continue
            
            # Create message
            message = AgentMessage(
                from_agent="orchestrator",
                to_agent=agent_name,
                content={
                    "action": agent_info["action"],
                    "params": agent_info.get("params", {}),
                    "context": user_input
                }
            )
            
            # Execute
            response = agent.process_message(message)
            results.append({
                "agent": agent_name,
                "result": response.content
            })
        
        # Synthesize results
        synthesized = self._synthesize_responses(results, user_input)
        
        return {
            "success": True,
            "response": synthesized,
            "agents": [r["agent"] for r in results],
            "individual_results": results
        }
    
    def _synthesize_responses(self, results: List[Dict[str, Any]], user_input: str) -> str:
        """Combine multiple agent responses into coherent answer"""
        if not results:
            return "No results from agents"
        
        if len(results) == 1:
            return results[0]["result"].get("message", "")
        
        # Use LLM to synthesize multiple responses
        results_text = "\n".join([
            f"- {r['agent']}: {r['result'].get('message', '')}"
            for r in results
        ])
        
        prompt = f"""
User asked: "{user_input}"

Agent responses:
{results_text}

Synthesize these into a single, coherent response to the user.
Be natural and conversational.
"""
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return completion.choices[0].message.content
        except:
            # Fallback: just concatenate
            return " ".join([r["result"].get("message", "") for r in results])
    
    def _handle_chat(self, user_input: str) -> Dict[str, Any]:
        """Handle general conversation (no agent needed)"""
        # Use LLM for chat response
        try:
            memories = ""
            if self.memory_manager:
                memories = self.memory_manager.get_memory_string()
            
            prompt = f"""
You are JARVIS, a helpful AI assistant.

USER MEMORY:
{memories}

USER: {user_input}

Respond naturally and helpfully.
"""
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            response = completion.choices[0].message.content
            
            return {
                "success": True,
                "response": response,
                "type": "chat"
            }
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return {
                "success": False,
                "response": "I'm having trouble responding right now."
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of entire multi-agent system"""
        return {
            "agents": self.list_agents(),
            "shared_context": self.shared_context,
            "total_tasks": len(self.task_history),
            "recent_tasks": self.task_history[-5:] if self.task_history else []
        }


if __name__ == "__main__":
    # Test orchestrator
    print("Testing Agent Orchestrator\n")
    
    from src.agents.finance_agent import FinanceAgent
    
    # Create orchestrator
    orchestrator = AgentOrchestrator()
    
    # Register agents
    finance_agent = FinanceAgent()
    orchestrator.register_agent(finance_agent)
    
    # List agents
    print("Registered Agents:")
    for agent_info in orchestrator.list_agents():
        print(f"- {agent_info['name']}: {agent_info['role']}")
    
    print("\nTesting task routing...")
    result = orchestrator.route_task("I spent $50 on lunch")
    print(f"Result: {result}")
