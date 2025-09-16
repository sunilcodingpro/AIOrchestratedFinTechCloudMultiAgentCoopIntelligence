"""
Fraud Detection Agent for the FinTech multi-agent system.
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta

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


class FraudDetectionAgent(BaseAgent):
    """Agent responsible for detecting fraudulent transactions."""
    
    def __init__(self):
        super().__init__("fraud_detector")
        self.transaction_history: List[Dict[str, Any]] = []
        self.fraud_patterns = {
            "high_amount_threshold": 10000.0,
            "rapid_transaction_threshold": 5,  # transactions within time window
            "rapid_transaction_window": 300,   # 5 minutes in seconds
            "suspicious_amount_patterns": [999.99, 1234.56, 5000.00]
        }
        
        system_logger.info("Fraud Detection Agent initialized", self.agent_id)
    
    def analyze_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a transaction for fraud indicators."""
        amount = transaction_data.get("amount", 0)
        sender_account = transaction_data.get("sender_account", "")
        recipient_account = transaction_data.get("recipient_account", "")
        
        fraud_indicators = []
        risk_score = 0.0
        
        # Check for high amount transactions
        if amount > self.fraud_patterns["high_amount_threshold"]:
            fraud_indicators.append("high_amount")
            risk_score += 0.3
        
        # Check for suspicious amount patterns
        if amount in self.fraud_patterns["suspicious_amount_patterns"]:
            fraud_indicators.append("suspicious_amount_pattern")
            risk_score += 0.2
        
        # Check for rapid transactions from same account
        recent_transactions = self._get_recent_transactions_by_account(sender_account)
        if len(recent_transactions) >= self.fraud_patterns["rapid_transaction_threshold"]:
            fraud_indicators.append("rapid_transactions")
            risk_score += 0.4
        
        # Check for round-trip transactions (A->B->A pattern)
        if self._check_round_trip_pattern(sender_account, recipient_account):
            fraud_indicators.append("round_trip_pattern")
            risk_score += 0.5
        
        # Simple rule: if risk score > 0.5, consider fraudulent
        is_fraudulent = risk_score > 0.5
        
        # Record this transaction analysis
        self.transaction_history.append({
            "timestamp": datetime.now(),
            "sender_account": sender_account,
            "recipient_account": recipient_account,
            "amount": amount,
            "risk_score": risk_score,
            "fraud_indicators": fraud_indicators,
            "is_fraudulent": is_fraudulent
        })
        
        return {
            "is_fraudulent": is_fraudulent,
            "risk_score": risk_score,
            "fraud_indicators": fraud_indicators,
            "reason": f"Risk score: {risk_score:.2f}, Indicators: {', '.join(fraud_indicators)}" if fraud_indicators else "No fraud indicators detected"
        }
    
    def _get_recent_transactions_by_account(self, account: str) -> List[Dict[str, Any]]:
        """Get recent transactions for a specific account."""
        cutoff_time = datetime.now() - timedelta(seconds=self.fraud_patterns["rapid_transaction_window"])
        return [
            tx for tx in self.transaction_history
            if tx["sender_account"] == account and tx["timestamp"] > cutoff_time
        ]
    
    def _check_round_trip_pattern(self, sender: str, recipient: str) -> bool:
        """Check for round-trip transaction patterns."""
        # Look for recent transactions where current recipient was sender to current sender
        recent_cutoff = datetime.now() - timedelta(hours=1)  # Check last hour
        for tx in self.transaction_history:
            if (tx["timestamp"] > recent_cutoff and 
                tx["sender_account"] == recipient and 
                tx["recipient_account"] == sender):
                return True
        return False
    
    def process_message(self, message: Message):
        """Process fraud check requests."""
        if message.message_type == "fraud_check_request":
            transaction_id = message.payload.get("transaction_id")
            transaction_data = message.payload.get("transaction_data", {})
            
            system_logger.info(f"Analyzing transaction {transaction_id} for fraud", self.agent_id)
            
            # Perform fraud analysis
            analysis_result = self.analyze_transaction(transaction_data)
            
            # Send response back to transaction processor
            self.send_message(
                message.sender,
                "fraud_check_response",
                {
                    "transaction_id": transaction_id,
                    **analysis_result
                },
                correlation_id=message.correlation_id
            )
            
            if analysis_result["is_fraudulent"]:
                system_logger.warning(
                    f"FRAUD DETECTED in transaction {transaction_id}: {analysis_result['reason']}", 
                    self.agent_id
                )
                
                # Notify threat detection agent
                self.send_message(
                    "threat_detector",
                    "fraud_alert",
                    {
                        "transaction_id": transaction_id,
                        "sender_account": transaction_data.get("sender_account"),
                        "threat_type": "fraud",
                        "risk_score": analysis_result["risk_score"],
                        "indicators": analysis_result["fraud_indicators"]
                    }
                )
            else:
                system_logger.info(f"Transaction {transaction_id} cleared fraud check", self.agent_id)
    
    def get_fraud_statistics(self) -> Dict[str, Any]:
        """Get fraud detection statistics."""
        total_transactions = len(self.transaction_history)
        fraudulent_transactions = sum(1 for tx in self.transaction_history if tx["is_fraudulent"])
        
        if total_transactions == 0:
            return {
                "total_transactions": 0,
                "fraudulent_transactions": 0,
                "fraud_rate": 0.0,
                "average_risk_score": 0.0
            }
        
        average_risk_score = sum(tx["risk_score"] for tx in self.transaction_history) / total_transactions
        
        return {
            "total_transactions": total_transactions,
            "fraudulent_transactions": fraudulent_transactions,
            "fraud_rate": fraudulent_transactions / total_transactions,
            "average_risk_score": average_risk_score,
            "most_common_indicators": self._get_most_common_indicators()
        }
    
    def _get_most_common_indicators(self) -> Dict[str, int]:
        """Get the most common fraud indicators."""
        indicator_counts = {}
        for tx in self.transaction_history:
            for indicator in tx["fraud_indicators"]:
                indicator_counts[indicator] = indicator_counts.get(indicator, 0) + 1
        return indicator_counts