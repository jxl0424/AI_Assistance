"""
Base Agent Class - Foundation for all specialized agents
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from src.core.logger_config import get_logger

logger = get_logger(__name__)


class AgentMessage:
    """Message format for agent-to-agent communication"""
    
    def __init__(self, 
                 from_agent: str,
                 to_agent: str,
                 content: Dict[str, Any],
                 msg_type: str = "request",
                 priority: str = "normal",
                 task_id: Optional[str] = None):
        self.task_id = task_id or str(uuid.uuid4())
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.msg_type = msg_type  # request, response, query, error
        self.content = content
        self.priority = priority  # high, normal, low
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "task_id": self.task_id,
            "from": self.from_agent,
            "to": self.to_agent,
            "type": self.msg_type,
            "content": self.content,
            "priority": self.priority,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Create message from dictionary"""
        return cls(
            from_agent=data["from"],
            to_agent=data["to"],
            content=data["content"],
            msg_type=data.get("type", "request"),
            priority=data.get("priority", "normal"),
            task_id=data.get("task_id")
        )


class AgentCapability:
    """Describes what an agent can do"""
    
    def __init__(self, name: str, description: str, parameters: List[str]):
        self.name = name
        self.description = description
        self.parameters = parameters
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the multi-agent system
    
    Each agent should:
    1. Have a unique name and role
    2. Define its capabilities
    3. Process messages from other agents
    4. Maintain its own state
    """
    
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.capabilities: List[AgentCapability] = []
        self.state: Dict[str, Any] = {}
        self.message_history: List[AgentMessage] = []
        self.logger = get_logger(f"agent.{name}")
        
        # Performance metrics
        self.metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "average_response_time": 0.0
        }
        
        self.logger.info(f"Agent '{name}' initialized with role: {role}")
    
    @abstractmethod
    def get_capabilities(self) -> List[AgentCapability]:
        """
        Define what this agent can do
        
        Returns:
            List of capabilities this agent provides
        """
        pass
    
    @abstractmethod
    def process_message(self, message: AgentMessage) -> AgentMessage:
        """
        Process a message from another agent
        
        Args:
            message: Incoming message
            
        Returns:
            Response message
        """
        pass
    
    @abstractmethod
    def can_handle(self, task: Dict[str, Any]) -> float:
        """
        Determine if this agent can handle a task
        
        Args:
            task: Task description
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        pass
    
    def register_capability(self, name: str, description: str, parameters: List[str]):
        """Register a new capability for this agent"""
        capability = AgentCapability(name, description, parameters)
        self.capabilities.append(capability)
        self.logger.info(f"Registered capability: {name}")
    
    def send_message(self, to_agent: str, content: Dict[str, Any], 
                     msg_type: str = "request") -> AgentMessage:
        """
        Create a message to send to another agent
        
        Args:
            to_agent: Target agent name
            content: Message content
            msg_type: Type of message
            
        Returns:
            Created message
        """
        message = AgentMessage(
            from_agent=self.name,
            to_agent=to_agent,
            content=content,
            msg_type=msg_type
        )
        self.message_history.append(message)
        return message
    
    def update_metrics(self, success: bool, response_time: float):
        """Update agent performance metrics"""
        if success:
            self.metrics["tasks_completed"] += 1
        else:
            self.metrics["tasks_failed"] += 1
        
        # Update average response time
        total_tasks = self.metrics["tasks_completed"] + self.metrics["tasks_failed"]
        current_avg = self.metrics["average_response_time"]
        self.metrics["average_response_time"] = (
            (current_avg * (total_tasks - 1) + response_time) / total_tasks
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "name": self.name,
            "role": self.role,
            "state": self.state,
            "capabilities": [cap.to_dict() for cap in self.capabilities],
            "metrics": self.metrics
        }
    
    def reset_state(self):
        """Reset agent state"""
        self.state = {}
        self.logger.info(f"Agent '{self.name}' state reset")
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.name}', role='{self.role}')>"
