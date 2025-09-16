"""
Tests for the Transaction Processing Agent.
"""
import pytest
from datetime import datetime
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from agents.transaction_processing_agent import TransactionProcessingAgent, Transaction
from protocols.inter_agent_comm import Message


class TestTransactionProcessingAgent:
    """Test suite for Transaction Processing Agent."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.agent = TransactionProcessingAgent()
    
    def test_agent_initialization(self):
        """Test that the agent initializes correctly."""
        assert self.agent.agent_id == "transaction_processor"
        assert len(self.agent.pending_transactions) == 0
        assert len(self.agent.completed_transactions) == 0
        assert len(self.agent.failed_transactions) == 0
    
    def test_create_transaction(self):
        """Test transaction creation."""
        amount = 1000.0
        sender = "test_sender"
        recipient = "test_recipient"
        currency = "USD"
        
        transaction = self.agent.create_transaction(
            amount=amount,
            sender_account=sender,
            recipient_account=recipient,
            currency=currency
        )
        
        assert isinstance(transaction, Transaction)
        assert transaction.amount == amount
        assert transaction.sender_account == sender
        assert transaction.recipient_account == recipient
        assert transaction.currency == currency
        assert transaction.status == "pending"
        assert isinstance(transaction.timestamp, datetime)
        assert transaction.id in self.agent.pending_transactions
    
    def test_create_transaction_with_metadata(self):
        """Test transaction creation with metadata."""
        metadata = {"description": "Test payment", "category": "business"}
        
        transaction = self.agent.create_transaction(
            amount=500.0,
            sender_account="sender",
            recipient_account="recipient",
            metadata=metadata
        )
        
        assert transaction.metadata == metadata
    
    def test_complete_transaction(self):
        """Test transaction completion."""
        transaction = self.agent.create_transaction(
            amount=100.0,
            sender_account="sender",
            recipient_account="recipient"
        )
        
        transaction_id = transaction.id
        
        # Complete the transaction
        result = self.agent.complete_transaction(transaction_id)
        
        assert result is True
        assert transaction_id not in self.agent.pending_transactions
        assert transaction_id in self.agent.completed_transactions
        assert self.agent.completed_transactions[transaction_id].status == "completed"
    
    def test_fail_transaction(self):
        """Test transaction failure."""
        transaction = self.agent.create_transaction(
            amount=100.0,
            sender_account="sender",
            recipient_account="recipient"
        )
        
        transaction_id = transaction.id
        failure_reason = "Insufficient funds"
        
        # Fail the transaction
        result = self.agent.fail_transaction(transaction_id, failure_reason)
        
        assert result is True
        assert transaction_id not in self.agent.pending_transactions
        assert transaction_id in self.agent.failed_transactions
        assert self.agent.failed_transactions[transaction_id].status == "failed"
        assert self.agent.failed_transactions[transaction_id].metadata["failure_reason"] == failure_reason
    
    def test_get_transaction_status_pending(self):
        """Test getting status of a pending transaction."""
        transaction = self.agent.create_transaction(
            amount=200.0,
            sender_account="sender",
            recipient_account="recipient"
        )
        
        status = self.agent.get_transaction_status(transaction.id)
        
        assert status is not None
        assert status["id"] == transaction.id
        assert status["status"] == "pending"
        assert status["amount"] == 200.0
        assert status["sender_account"] == "sender"
        assert status["recipient_account"] == "recipient"
    
    def test_get_transaction_status_completed(self):
        """Test getting status of a completed transaction."""
        transaction = self.agent.create_transaction(
            amount=300.0,
            sender_account="sender",
            recipient_account="recipient"
        )
        
        self.agent.complete_transaction(transaction.id)
        status = self.agent.get_transaction_status(transaction.id)
        
        assert status is not None
        assert status["status"] == "completed"
    
    def test_get_transaction_status_not_found(self):
        """Test getting status of a non-existent transaction."""
        status = self.agent.get_transaction_status("non_existent_id")
        assert status is None
    
    def test_process_fraud_check_response_clean(self):
        """Test processing a clean fraud check response."""
        transaction = self.agent.create_transaction(
            amount=100.0,
            sender_account="sender",
            recipient_account="recipient"
        )
        
        # Create a fraud check response message
        message = Message(
            id="msg_001",
            sender="fraud_detector",
            recipient="transaction_processor",
            message_type="fraud_check_response",
            payload={
                "transaction_id": transaction.id,
                "is_fraudulent": False,
                "risk_score": 0.1
            },
            timestamp=datetime.now()
        )
        
        # Process the message
        self.agent.process_message(message)
        
        # Transaction should still be pending (waiting for other checks)
        assert transaction.id in self.agent.pending_transactions
    
    def test_process_fraud_check_response_fraudulent(self):
        """Test processing a fraudulent transaction response."""
        transaction = self.agent.create_transaction(
            amount=100.0,
            sender_account="sender",
            recipient_account="recipient"
        )
        
        # Create a fraud check response message indicating fraud
        message = Message(
            id="msg_002",
            sender="fraud_detector",
            recipient="transaction_processor",
            message_type="fraud_check_response",
            payload={
                "transaction_id": transaction.id,
                "is_fraudulent": True,
                "risk_score": 0.9,
                "reason": "High risk indicators detected"
            },
            timestamp=datetime.now()
        )
        
        # Process the message
        self.agent.process_message(message)
        
        # Transaction should be failed
        assert transaction.id not in self.agent.pending_transactions
        assert transaction.id in self.agent.failed_transactions
        assert "Fraud detected" in self.agent.failed_transactions[transaction.id].metadata["failure_reason"]
    
    def test_process_compliance_check_response_compliant(self):
        """Test processing a compliant transaction response."""
        transaction = self.agent.create_transaction(
            amount=100.0,
            sender_account="sender",
            recipient_account="recipient"
        )
        
        # Create a compliance check response message
        message = Message(
            id="msg_003",
            sender="compliance_agent",
            recipient="transaction_processor",
            message_type="compliance_check_response",
            payload={
                "transaction_id": transaction.id,
                "is_compliant": True,
                "compliance_score": 1.0
            },
            timestamp=datetime.now()
        )
        
        # Process the message
        self.agent.process_message(message)
        
        # Transaction should still be pending (waiting for other checks)
        assert transaction.id in self.agent.pending_transactions
    
    def test_process_compliance_check_response_violation(self):
        """Test processing a non-compliant transaction response."""
        transaction = self.agent.create_transaction(
            amount=100.0,
            sender_account="sender",
            recipient_account="recipient"
        )
        
        # Create a compliance check response message indicating violation
        message = Message(
            id="msg_004",
            sender="compliance_agent",
            recipient="transaction_processor",
            message_type="compliance_check_response",
            payload={
                "transaction_id": transaction.id,
                "is_compliant": False,
                "compliance_score": 0.3,
                "reason": "Exceeds daily limit"
            },
            timestamp=datetime.now()
        )
        
        # Process the message
        self.agent.process_message(message)
        
        # Transaction should be failed
        assert transaction.id not in self.agent.pending_transactions
        assert transaction.id in self.agent.failed_transactions
        assert "Compliance violation" in self.agent.failed_transactions[transaction.id].metadata["failure_reason"]
    
    def test_process_resource_allocation_response(self):
        """Test processing resource allocation response."""
        transaction = self.agent.create_transaction(
            amount=100.0,
            sender_account="sender",
            recipient_account="recipient"
        )
        
        # Create a resource allocation response
        message = Message(
            id="msg_005",
            sender="resource_allocator",
            recipient="transaction_processor",
            message_type="resource_allocated",
            payload={
                "transaction_id": transaction.id,
                "allocated": True,
                "cpu_units": 10,
                "memory_mb": 256
            },
            timestamp=datetime.now()
        )
        
        # Process the message
        self.agent.process_message(message)
        
        # In the simplified implementation, this should complete the transaction
        # (in reality, it would wait for all checks to complete)
        assert transaction.id in self.agent.completed_transactions
    
    def test_process_unknown_message_type(self):
        """Test processing an unknown message type."""
        message = Message(
            id="msg_006",
            sender="unknown_agent",
            recipient="transaction_processor",
            message_type="unknown_message",
            payload={"data": "test"},
            timestamp=datetime.now()
        )
        
        # This should not raise an exception
        self.agent.process_message(message)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])