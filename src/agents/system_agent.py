"""
System Agent - Specialized agent for system control and automation
"""

from typing import Dict, Any, List
from src.agents.base_agent import BaseAgent, AgentMessage, AgentCapability
import subprocess
import webbrowser
import time


class SystemAgent(BaseAgent):
    """
    Specialized agent for system operations
    
    Capabilities:
    - Open/close applications
    - System controls (volume, screenshots, etc.)
    - Web searches
    - File operations
    """
    
    def __init__(self):
        super().__init__(name="system_agent", role="System Controller")
        
        # Track running processes
        self.running_processes = {}
        
        # Register capabilities
        self._register_capabilities()
        
        self.logger.info("System Agent ready")
    
    def _register_capabilities(self):
        """Register all system capabilities"""
        self.register_capability(
            name="open_application",
            description="Open an application",
            parameters=["app_name"]
        )
        
        self.register_capability(
            name="close_application",
            description="Close an application",
            parameters=["app_name"]
        )
        
        self.register_capability(
            name="search_web",
            description="Open browser with search query",
            parameters=["query"]
        )
        
        self.register_capability(
            name="system_control",
            description="Control system functions (volume, screenshot, etc.)",
            parameters=["command"]
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
        
        # High confidence for explicit system actions
        system_keywords = [
            "open", "close", "launch", "start", "stop",
            "volume", "screenshot", "search", "browse"
        ]
        
        if any(keyword in action for keyword in system_keywords):
            return 0.95
        
        # Check content
        content = str(task.get("content", "")).lower()
        if any(keyword in content for keyword in system_keywords):
            return 0.75
        
        return 0.0
    
    def process_message(self, message: AgentMessage) -> AgentMessage:
        """
        Process incoming message and execute system task
        
        Args:
            message: Incoming message from orchestrator
            
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
            if action == "open_application":
                result = self._open_application(params)
            elif action == "close_application":
                result = self._close_application(params)
            elif action == "search_web":
                result = self._search_web(params)
            elif action == "system_control":
                result = self._system_control(params)
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
    
    def _open_application(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Open an application"""
        try:
            from src.utils.apps_config import find_application_path
            
            app_name = params.get("app_name")
            if not app_name:
                return {"success": False, "message": "No app name provided"}
            
            path = find_application_path(app_name)
            if not path:
                return {
                    "success": False,
                    "message": f"Could not find path for {app_name}"
                }
            
            # Start the process
            proc = subprocess.Popen(path)
            self.running_processes[app_name] = proc
            
            return {
                "success": True,
                "message": f"Opened {app_name}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to open application: {str(e)}"
            }
    
    def _close_application(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Close an application"""
        app_name = params.get("app_name")
        
        if app_name in self.running_processes:
            try:
                self.running_processes[app_name].terminate()
                del self.running_processes[app_name]
                return {
                    "success": True,
                    "message": f"Closed {app_name}"
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Failed to close {app_name}: {str(e)}"
                }
        else:
            return {
                "success": False,
                "message": f"{app_name} is not running or was not opened by me"
            }
    
    def _search_web(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Open browser with search query"""
        try:
            query = params.get("query")
            if not query:
                return {"success": False, "message": "No search query provided"}
            
            url = f"https://www.google.com/search?q={query}"
            webbrowser.open(url)
            
            return {
                "success": True,
                "message": f"Searched for: {query}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to search: {str(e)}"
            }
    
    def _system_control(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute system control commands"""
        try:
            import pyautogui
            
            command = params.get("command")
            if not command:
                return {"success": False, "message": "No command provided"}
            
            if command == "volume_up":
                pyautogui.press("volumeup")
                message = "Volume increased"
            elif command == "volume_down":
                pyautogui.press("volumedown")
                message = "Volume decreased"
            elif command == "mute":
                pyautogui.press("volumemute")
                message = "Volume muted"
            elif command == "screenshot":
                pyautogui.screenshot("screenshot.png")
                message = "Screenshot saved"
            else:
                return {
                    "success": False,
                    "message": f"Unknown system command: {command}"
                }
            
            return {
                "success": True,
                "message": message
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"System control failed: {str(e)}"
            }


if __name__ == "__main__":
    # Test the System Agent
    print("Testing System Agent\n")
    
    agent = SystemAgent()
    
    # Test capability check
    task = {"action": "open_application", "content": "open chrome"}
    confidence = agent.can_handle(task)
    print(f"Can handle task: {confidence:.2f}\n")
    
    # Test message processing
    message = AgentMessage(
        from_agent="orchestrator",
        to_agent="system_agent",
        content={
            "action": "search_web",
            "params": {
                "query": "weather today"
            }
        }
    )
    
    response = agent.process_message(message)
    print(f"Response: {response.content}\n")
    
    # Check status
    status = agent.get_status()
    print(f"Agent Status: {status}")
