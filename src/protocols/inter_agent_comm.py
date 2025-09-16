"""
Simple message passing protocol between agents in the FinTech system.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid


@dataclass
class Message:
    """Message structure for inter-agent communication."""
    id: str
    sender: str
    recipient: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None


class MessageBus:
    """Simple message bus for agent communication."""
    
    def __init__(self):
        self.message_history: List[Message] = []
        self.agents: Dict[str, 'BaseAgent'] = {}
    
    def register_agent(self, agent_id: str, agent: 'BaseAgent'):
        """Register an agent with the message bus."""
        self.agents[agent_id] = agent
    
    def send_message(self, sender: str, recipient: str, message_type: str, 
                    payload: Dict[str, Any], correlation_id: Optional[str] = None) -> Message:
        """Send a message from one agent to another."""
        message = Message(
            id=str(uuid.uuid4()),
            sender=sender,
            recipient=recipient,
            message_type=message_type,
            payload=payload,
            timestamp=datetime.now(),
            correlation_id=correlation_id
        )
        
        self.message_history.append(message)
        
        # Deliver message to recipient if registered
        if recipient in self.agents:
            self.agents[recipient].receive_message(message)
        
        return message
    
    def broadcast_message(self, sender: str, message_type: str, 
                         payload: Dict[str, Any], correlation_id: Optional[str] = None) -> List[Message]:
        """Broadcast a message to all registered agents except sender."""
        messages = []
        for agent_id in self.agents:
            if agent_id != sender:
                message = self.send_message(sender, agent_id, message_type, payload, correlation_id)
                messages.append(message)
        return messages
    
    def get_message_history(self, agent_id: Optional[str] = None) -> List[Message]:
        """Get message history, optionally filtered by agent."""
        if agent_id:
            return [msg for msg in self.message_history 
                   if msg.sender == agent_id or msg.recipient == agent_id]
        return self.message_history.copy()


# Global message bus instance
message_bus = MessageBus()


class BaseAgent:
    """Base class for all agents in the system."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.message_queue: List[Message] = []
        message_bus.register_agent(agent_id, self)
    
    def receive_message(self, message: Message):
        """Receive a message from another agent."""
        self.message_queue.append(message)
        self.process_message(message)
    
    def process_message(self, message: Message):
        """Process an incoming message. Override in subclasses."""
        pass
    
    def send_message(self, recipient: str, message_type: str, 
                    payload: Dict[str, Any], correlation_id: Optional[str] = None) -> Message:
        """Send a message to another agent."""
        return message_bus.send_message(self.agent_id, recipient, message_type, payload, correlation_id)
    
    def broadcast_message(self, message_type: str, payload: Dict[str, Any], 
                         correlation_id: Optional[str] = None) -> List[Message]:
        """Broadcast a message to all other agents."""
        return message_bus.broadcast_message(self.agent_id, message_type, payload, correlation_id)