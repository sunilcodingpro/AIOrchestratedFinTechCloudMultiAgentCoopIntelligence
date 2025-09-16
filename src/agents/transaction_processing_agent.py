"""
Transaction Processing Agent for the FinTech multi-agent system.
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid

try:
    from ..protocols.inter_agent_comm import BaseAgent, Message
    from ..utils.logging import system_logger
except ImportError:
    # For when imported directly (e.g., in tests)
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from protocols.inter_agent_comm import BaseAgent, Message
    from utils.logging import system_logger


@dataclass
class Transaction:
    """Transaction data structure."""
    id: str
    amount: float
    sender_account: str
    recipient_account: str
    currency: str = "USD"
    timestamp: datetime = None
    status: str = "pending"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class TransactionProcessingAgent(BaseAgent):
    """Agent responsible for processing financial transactions."""
    
    def __init__(self):
        super().__init__("transaction_processor")
        self.pending_transactions: Dict[str, Transaction] = {}
        self.completed_transactions: Dict[str, Transaction] = {}
        self.failed_transactions: Dict[str, Transaction] = {}
        
        system_logger.info("Transaction Processing Agent initialized", self.agent_id)
    
    def create_transaction(self, amount: float, sender_account: str, 
                          recipient_account: str, currency: str = "USD", 
                          metadata: Optional[Dict[str, Any]] = None) -> Transaction:
        """Create a new transaction."""
        transaction = Transaction(
            id=str(uuid.uuid4()),
            amount=amount,
            sender_account=sender_account,
            recipient_account=recipient_account,
            currency=currency,
            metadata=metadata or {}
        )
        
        self.pending_transactions[transaction.id] = transaction
        
        system_logger.info(
            f"Created transaction {transaction.id}: {amount} {currency} "
            f"from {sender_account} to {recipient_account}",
            self.agent_id
        )
        
        return transaction
    
    def process_transaction(self, transaction: Transaction) -> bool:
        """Process a transaction through the multi-agent pipeline."""
        system_logger.info(f"Processing transaction {transaction.id}", self.agent_id)
        
        # Request fraud detection check
        self.send_message(
            "fraud_detector",
            "fraud_check_request",
            {
                "transaction_id": transaction.id,
                "transaction_data": {
                    "amount": transaction.amount,
                    "sender_account": transaction.sender_account,
                    "recipient_account": transaction.recipient_account,
                    "currency": transaction.currency
                }
            },
            correlation_id=transaction.id
        )
        
        # Request compliance check
        self.send_message(
            "compliance_agent",
            "compliance_check_request",
            {
                "transaction_id": transaction.id,
                "transaction_data": {
                    "amount": transaction.amount,
                    "sender_account": transaction.sender_account,
                    "recipient_account": transaction.recipient_account,
                    "currency": transaction.currency
                }
            },
            correlation_id=transaction.id
        )
        
        # Request resource allocation
        self.send_message(
            "resource_allocator",
            "resource_request",
            {
                "transaction_id": transaction.id,
                "processing_priority": "normal",
                "estimated_complexity": "low"
            },
            correlation_id=transaction.id
        )
        
        return True
    
    def complete_transaction(self, transaction_id: str) -> bool:
        """Mark a transaction as completed."""
        if transaction_id in self.pending_transactions:
            transaction = self.pending_transactions.pop(transaction_id)
            transaction.status = "completed"
            self.completed_transactions[transaction_id] = transaction
            
            system_logger.info(f"Transaction {transaction_id} completed successfully", self.agent_id)
            
            # Notify audit agent
            self.send_message(
                "audit_agent",
                "transaction_completed",
                {
                    "transaction_id": transaction_id,
                    "amount": transaction.amount,
                    "timestamp": transaction.timestamp.isoformat()
                }
            )
            
            return True
        return False
    
    def fail_transaction(self, transaction_id: str, reason: str) -> bool:
        """Mark a transaction as failed."""
        if transaction_id in self.pending_transactions:
            transaction = self.pending_transactions.pop(transaction_id)
            transaction.status = "failed"
            transaction.metadata["failure_reason"] = reason
            self.failed_transactions[transaction_id] = transaction
            
            system_logger.error(f"Transaction {transaction_id} failed: {reason}", self.agent_id)
            
            # Notify audit agent
            self.send_message(
                "audit_agent",
                "transaction_failed",
                {
                    "transaction_id": transaction_id,
                    "reason": reason,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            return True
        return False
    
    def process_message(self, message: Message):
        """Process incoming messages from other agents."""
        if message.message_type == "fraud_check_response":
            self._handle_fraud_response(message)
        elif message.message_type == "compliance_check_response":
            self._handle_compliance_response(message)
        elif message.message_type == "resource_allocated":
            self._handle_resource_allocation(message)
        else:
            system_logger.debug(f"Received unknown message type: {message.message_type}", self.agent_id)
    
    def _handle_fraud_response(self, message: Message):
        """Handle fraud detection response."""
        transaction_id = message.payload.get("transaction_id")
        is_fraudulent = message.payload.get("is_fraudulent", False)
        
        if is_fraudulent:
            reason = message.payload.get("reason", "Fraudulent transaction detected")
            self.fail_transaction(transaction_id, f"Fraud detected: {reason}")
        else:
            system_logger.info(f"Transaction {transaction_id} passed fraud check", self.agent_id)
    
    def _handle_compliance_response(self, message: Message):
        """Handle compliance check response."""
        transaction_id = message.payload.get("transaction_id")
        is_compliant = message.payload.get("is_compliant", True)
        
        if not is_compliant:
            reason = message.payload.get("reason", "Compliance violation detected")
            self.fail_transaction(transaction_id, f"Compliance violation: {reason}")
        else:
            system_logger.info(f"Transaction {transaction_id} passed compliance check", self.agent_id)
    
    def _handle_resource_allocation(self, message: Message):
        """Handle resource allocation confirmation."""
        transaction_id = message.payload.get("transaction_id")
        system_logger.info(f"Resources allocated for transaction {transaction_id}", self.agent_id)
        
        # Check if all validations are complete and proceed with completion
        # In a real system, this would be more sophisticated
        if transaction_id in self.pending_transactions:
            self.complete_transaction(transaction_id)
    
    def get_transaction_status(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a transaction."""
        for transactions in [self.pending_transactions, self.completed_transactions, self.failed_transactions]:
            if transaction_id in transactions:
                transaction = transactions[transaction_id]
                return {
                    "id": transaction.id,
                    "status": transaction.status,
                    "amount": transaction.amount,
                    "sender_account": transaction.sender_account,
                    "recipient_account": transaction.recipient_account,
                    "currency": transaction.currency,
                    "timestamp": transaction.timestamp.isoformat(),
                    "metadata": transaction.metadata
                }
        return None