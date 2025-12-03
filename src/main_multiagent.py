"""
Multi-Agent JARVIS - Entry point for multi-agent system
"""

import sys
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from src.modules.speech_to_text import SpeechToText
from src.modules.wake_word_detector import WakeWordDetector
from src.modules.continuous_listener import ContinuousListener
from src.modules.feedback_system import FeedbackSystem
from src.modules.tts_engine import TextToSpeech
from src.modules.memory_manager import MemoryManager

# Import multi-agent components
from src.agents.orchestrator import AgentOrchestrator
from src.agents.finance_agent import FinanceAgent
from src.agents.system_agent import SystemAgent

from src.core.logger_config import get_logger

logger = get_logger(__name__)


class MultiAgentJarvis:
    """
    Multi-Agent JARVIS System
    
    Uses specialized agents coordinated by an orchestrator:
    - Finance Agent: Handles all financial operations
    - System Agent: Handles system control and applications
    - More agents can be added easily!
    """
    
    def __init__(self, use_wake_word=True, feedback_system=None):
        self.feedback = feedback_system if feedback_system else FeedbackSystem()
        self.feedback.print_banner("JARVIS - Multi-Agent Mode")
        
        self.feedback.print_status("Initializing Multi-Agent System...", "info")
        
        # Core components
        self.memory_manager = MemoryManager()
        self.stt = SpeechToText()
        self.listener = ContinuousListener()
        self.tts = TextToSpeech()
        
        # Multi-Agent System
        self.orchestrator = AgentOrchestrator(memory_manager=self.memory_manager)
        
        # Register specialized agents
        self._register_agents()
        
        # Wake word detection
        self.use_wake_word = use_wake_word
        self.wake_detector = None
        if use_wake_word:
            try:
                self.wake_detector = WakeWordDetector(wake_words=["jarvis", "hey jarvis"])
            except:
                logger.warning("Wake word model missing. Run setup_resources.py")
                self.use_wake_word = False
        
        self.feedback.print_status("Multi-Agent JARVIS Online", "success")
        self._show_agent_status()
        self.tts.speak("Multi-agent system online, sir.")
    
    def _register_agents(self):
        """Register all specialized agents"""
        self.feedback.print_status("Registering agents...", "info")
        
        # Finance Agent
        finance_agent = FinanceAgent()
        self.orchestrator.register_agent(finance_agent)
        self.feedback.print_status(f"  ✓ {finance_agent.name} ({finance_agent.role})", "success")
        
        # System Agent
        system_agent = SystemAgent()
        self.orchestrator.register_agent(system_agent)
        self.feedback.print_status(f"  ✓ {system_agent.name} ({system_agent.role})", "success")
        
        # TODO: Add more agents here
        # research_agent = ResearchAgent()
        # self.orchestrator.register_agent(research_agent)
        
        logger.info(f"Registered {len(self.orchestrator.agents)} agents")
    
    def _show_agent_status(self):
        """Display status of all agents"""
        print("\n" + "="*60)
        print("ACTIVE AGENTS:")
        print("="*60)
        
        for agent_info in self.orchestrator.list_agents():
            print(f"\n{agent_info['name'].upper()} ({agent_info['role']})")
            print("  Capabilities:")
            for cap in agent_info['capabilities']:
                print(f"    - {cap['name']}: {cap['description']}")
        
        print("\n" + "="*60 + "\n")
    
    def process_command(self, audio_file):
        """Process voice command using multi-agent system"""
        self.feedback.show_thinking()
        
        # Step 1: Speech to Text
        transcription = self.stt.transcribe_simple(audio_file)
        
        if not transcription:
            self.feedback.clear_thinking()
            return
        
        self.feedback.print_command(transcription)
        self.feedback.print_status("Routing to agents...", "info")
        
        # Step 2: Orchestrator routes to appropriate agent(s)
        result = self.orchestrator.route_task(transcription)
        self.feedback.clear_thinking()
        
        # Step 3: Display which agent(s) handled the task
        if "agent" in result:
            self.feedback.print_status(f"Handled by: {result['agent']}", "info")
        elif "agents" in result:
            agents_str = ", ".join(result['agents'])
            self.feedback.print_status(f"Handled by: {agents_str}", "info")
        
        # Step 4: Speak response
        response_text = result.get("response", "")
        if response_text:
            self.tts.speak(response_text)
            self.feedback.print_status(response_text, "success")
        
        # Step 5: Update memory if needed
        if result.get("success"):
            # Memory updates would be handled by a Memory Agent in the future
            pass
    
    def run(self):
        """Run the multi-agent JARVIS system"""
        if self.use_wake_word:
            self.listener.calibrate_vad(duration=1)
            print(f"\nSay 'Jarvis' to activate...\n")
            
            try:
                while True:
                    if self.wake_detector.start_listening():
                        self.feedback.activation_beep()
                        self.feedback.print_status("Listening...", "listening")
                        audio_file = self.listener.record_with_vad(max_duration=60)
                        if audio_file:
                            self.process_command(audio_file)
                        self.feedback.print_status("Waiting...", "wake")
            except KeyboardInterrupt:
                print("\n\nShutting down multi-agent system...")
                self._show_final_stats()
        else:
            print("\nPress Enter to speak, Ctrl+C to exit\n")
            try:
                while True:
                    input("\nPress Enter to speak...")
                    self.feedback.print_status("Listening...", "listening")
                    audio_file = self.listener.record_with_vad(max_duration=60)
                    if audio_file:
                        self.process_command(audio_file)
            except KeyboardInterrupt:
                print("\n\nShutting down multi-agent system...")
                self._show_final_stats()
    
    def _show_final_stats(self):
        """Show statistics before shutdown"""
        print("\n" + "="*60)
        print("AGENT PERFORMANCE SUMMARY")
        print("="*60)
        
        for agent_info in self.orchestrator.list_agents():
            metrics = agent_info['metrics']
            total = metrics['tasks_completed'] + metrics['tasks_failed']
            success_rate = (metrics['tasks_completed'] / total * 100) if total > 0 else 0
            
            print(f"\n{agent_info['name']}:")
            print(f"  Tasks Completed: {metrics['tasks_completed']}")
            print(f"  Tasks Failed: {metrics['tasks_failed']}")
            print(f"  Success Rate: {success_rate:.1f}%")
            print(f"  Avg Response Time: {metrics['average_response_time']:.2f}s")
        
        print("\n" + "="*60)
        print("Goodbye, sir.")


if __name__ == "__main__":
    # Initialize logging
    from src.core.logger_config import init_jarvis_logging
    init_jarvis_logging(debug=False)
    
    # Start multi-agent JARVIS
    jarvis = MultiAgentJarvis(use_wake_word=False)  # Set to True for wake word
    jarvis.run()
