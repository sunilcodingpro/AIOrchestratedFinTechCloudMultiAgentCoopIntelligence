"""
Compliance Agent for the FinTech multi-agent system.
"""
from typing import Dict, Any, List
from datetime import datetime

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


class ComplianceAgent(BaseAgent):
    """Agent responsible for ensuring regulatory compliance."""
    
    def __init__(self):
        super().__init__("compliance_agent")
        self.compliance_rules = {
            "max_daily_amount": 50000.0,
            "max_single_transaction": 25000.0,
            "prohibited_countries": ["XX", "YY"],  # Mock prohibited countries
            "kyc_required_threshold": 5000.0,
            "suspicious_keywords": ["ransom", "illegal", "drugs"]
        }
        self.daily_transaction_totals: Dict[str, float] = {}
        self.compliance_violations: List[Dict[str, Any]] = []
        
        system_logger.info("Compliance Agent initialized", self.agent_id)
    
    def check_compliance(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check transaction compliance against regulatory rules."""
        amount = transaction_data.get("amount", 0)
        sender_account = transaction_data.get("sender_account", "")
        recipient_account = transaction_data.get("recipient_account", "")
        currency = transaction_data.get("currency", "USD")
        
        violations = []
        compliance_score = 1.0
        
        # Check single transaction limit
        if amount > self.compliance_rules["max_single_transaction"]:
            violations.append({
                "rule": "max_single_transaction",
                "description": f"Transaction amount {amount} exceeds single transaction limit of {self.compliance_rules['max_single_transaction']}"
            })
            compliance_score -= 0.5
        
        # Check daily limit for sender
        today = datetime.now().strftime("%Y-%m-%d")
        daily_key = f"{sender_account}_{today}"
        current_daily_total = self.daily_transaction_totals.get(daily_key, 0.0)
        
        if current_daily_total + amount > self.compliance_rules["max_daily_amount"]:
            violations.append({
                "rule": "max_daily_amount",
                "description": f"Daily transaction total would exceed limit of {self.compliance_rules['max_daily_amount']}"
            })
            compliance_score -= 0.4
        
        # Check KYC requirements
        if amount >= self.compliance_rules["kyc_required_threshold"]:
            # In a real system, this would check actual KYC status
            kyc_verified = self._check_kyc_status(sender_account)
            if not kyc_verified:
                violations.append({
                    "rule": "kyc_required",
                    "description": f"KYC verification required for transactions >= {self.compliance_rules['kyc_required_threshold']}"
                })
                compliance_score -= 0.6
        
        # Check for prohibited countries (simplified)
        if self._involves_prohibited_country(sender_account, recipient_account):
            violations.append({
                "rule": "prohibited_country",
                "description": "Transaction involves prohibited country"
            })
            compliance_score -= 0.8
        
        # Check for suspicious keywords in metadata
        metadata_text = str(transaction_data.get("metadata", {})).lower()
        for keyword in self.compliance_rules["suspicious_keywords"]:
            if keyword in metadata_text:
                violations.append({
                    "rule": "suspicious_keywords",
                    "description": f"Suspicious keyword '{keyword}' found in transaction metadata"
                })
                compliance_score -= 0.3
                break
        
        is_compliant = len(violations) == 0
        
        # Update daily totals if compliant
        if is_compliant:
            self.daily_transaction_totals[daily_key] = current_daily_total + amount
        
        # Record violation if any
        if violations:
            violation_record = {
                "timestamp": datetime.now(),
                "sender_account": sender_account,
                "recipient_account": recipient_account,
                "amount": amount,
                "violations": violations,
                "compliance_score": compliance_score
            }
            self.compliance_violations.append(violation_record)
        
        return {
            "is_compliant": is_compliant,
            "compliance_score": compliance_score,
            "violations": violations,
            "reason": self._format_violations(violations) if violations else "All compliance checks passed"
        }
    
    def _check_kyc_status(self, account: str) -> bool:
        """Mock KYC status check. In real system, would query KYC database."""
        # Simple stub: assume accounts starting with "verified_" are KYC verified
        return account.startswith("verified_")
    
    def _involves_prohibited_country(self, sender: str, recipient: str) -> bool:
        """Check if transaction involves prohibited countries."""
        # Simple stub: check if account contains prohibited country codes
        all_accounts = [sender, recipient]
        for account in all_accounts:
            for country in self.compliance_rules["prohibited_countries"]:
                if country.lower() in account.lower():
                    return True
        return False
    
    def _format_violations(self, violations: List[Dict[str, Any]]) -> str:
        """Format violations into a readable string."""
        if not violations:
            return "No violations"
        
        violation_descriptions = [v["description"] for v in violations]
        return "; ".join(violation_descriptions)
    
    def process_message(self, message: Message):
        """Process compliance check requests."""
        if message.message_type == "compliance_check_request":
            transaction_id = message.payload.get("transaction_id")
            transaction_data = message.payload.get("transaction_data", {})
            
            system_logger.info(f"Checking compliance for transaction {transaction_id}", self.agent_id)
            
            # Perform compliance check
            compliance_result = self.check_compliance(transaction_data)
            
            # Send response back to transaction processor
            self.send_message(
                message.sender,
                "compliance_check_response",
                {
                    "transaction_id": transaction_id,
                    **compliance_result
                },
                correlation_id=message.correlation_id
            )
            
            if not compliance_result["is_compliant"]:
                system_logger.warning(
                    f"COMPLIANCE VIOLATION in transaction {transaction_id}: {compliance_result['reason']}", 
                    self.agent_id
                )
                
                # Notify audit agent of violation
                self.send_message(
                    "audit_agent",
                    "compliance_violation",
                    {
                        "transaction_id": transaction_id,
                        "violations": compliance_result["violations"],
                        "sender_account": transaction_data.get("sender_account"),
                        "amount": transaction_data.get("amount"),
                        "timestamp": datetime.now().isoformat()
                    }
                )
            else:
                system_logger.info(f"Transaction {transaction_id} passed compliance checks", self.agent_id)
    
    def get_compliance_statistics(self) -> Dict[str, Any]:
        """Get compliance statistics."""
        total_violations = len(self.compliance_violations)
        
        if total_violations == 0:
            return {
                "total_violations": 0,
                "violation_types": {},
                "average_compliance_score": 1.0
            }
        
        # Count violation types
        violation_types = {}
        total_score = 0
        
        for violation in self.compliance_violations:
            total_score += violation["compliance_score"]
            for v in violation["violations"]:
                rule = v["rule"]
                violation_types[rule] = violation_types.get(rule, 0) + 1
        
        average_score = total_score / total_violations
        
        return {
            "total_violations": total_violations,
            "violation_types": violation_types,
            "average_compliance_score": average_score,
            "daily_transaction_totals": dict(self.daily_transaction_totals)
        }
    
    def update_compliance_rules(self, new_rules: Dict[str, Any]):
        """Update compliance rules (for administrative purposes)."""
        self.compliance_rules.update(new_rules)
        system_logger.info(f"Compliance rules updated: {new_rules}", self.agent_id)