"""
Audit Agent for the FinTech multi-agent system.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
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
class AuditRecord:
    """Audit record data structure."""
    id: str
    timestamp: datetime
    event_type: str
    source: str
    details: Dict[str, Any]
    severity: str = "info"
    reviewed: bool = False


class AuditAgent(BaseAgent):
    """Agent responsible for auditing and logging system events."""
    
    def __init__(self):
        super().__init__("audit_agent")
        self.audit_records: List[AuditRecord] = []
        self.audit_summary: Dict[str, Any] = {
            "total_transactions": 0,
            "successful_transactions": 0,
            "failed_transactions": 0,
            "fraud_incidents": 0,
            "compliance_violations": 0,
            "threat_alerts": 0,
            "resource_shortages": 0
        }
        
        system_logger.info("Audit Agent initialized", self.agent_id)
    
    def create_audit_record(self, event_type: str, source: str, details: Dict[str, Any], 
                          severity: str = "info") -> AuditRecord:
        """Create a new audit record."""
        record = AuditRecord(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            event_type=event_type,
            source=source,
            details=details,
            severity=severity
        )
        
        self.audit_records.append(record)
        
        system_logger.info(
            f"Audit record created: {event_type} from {source} (ID: {record.id})",
            self.agent_id
        )
        
        return record
    
    def process_message(self, message: Message):
        """Process audit-related messages from other agents."""
        
        if message.message_type == "transaction_completed":
            # Log successful transaction
            self.audit_summary["total_transactions"] += 1
            self.audit_summary["successful_transactions"] += 1
            
            self.create_audit_record(
                "transaction_completed",
                message.sender,
                {
                    "transaction_id": message.payload.get("transaction_id"),
                    "amount": message.payload.get("amount"),
                    "timestamp": message.payload.get("timestamp")
                },
                "info"
            )
        
        elif message.message_type == "transaction_failed":
            # Log failed transaction
            self.audit_summary["total_transactions"] += 1
            self.audit_summary["failed_transactions"] += 1
            
            self.create_audit_record(
                "transaction_failed",
                message.sender,
                {
                    "transaction_id": message.payload.get("transaction_id"),
                    "reason": message.payload.get("reason"),
                    "timestamp": message.payload.get("timestamp")
                },
                "warning"
            )
        
        elif message.message_type == "compliance_violation":
            # Log compliance violation
            self.audit_summary["compliance_violations"] += 1
            
            self.create_audit_record(
                "compliance_violation",
                message.sender,
                {
                    "transaction_id": message.payload.get("transaction_id"),
                    "violations": message.payload.get("violations", []),
                    "sender_account": message.payload.get("sender_account"),
                    "amount": message.payload.get("amount"),
                    "timestamp": message.payload.get("timestamp")
                },
                "error"
            )
        
        elif message.message_type == "threat_alert":
            # Log threat alert
            self.audit_summary["threat_alerts"] += 1
            
            self.create_audit_record(
                "threat_alert",
                message.sender,
                {
                    "alert_id": message.payload.get("alert_id"),
                    "threat_type": message.payload.get("threat_type"),
                    "severity": message.payload.get("severity"),
                    "description": message.payload.get("description"),
                    "mitigation_actions": message.payload.get("mitigation_actions", []),
                    "timestamp": message.payload.get("timestamp")
                },
                "critical" if message.payload.get("severity") == "high" else "warning"
            )
        
        elif message.message_type == "resource_shortage":
            # Log resource shortage
            self.audit_summary["resource_shortages"] += 1
            
            self.create_audit_record(
                "resource_shortage",
                message.sender,
                {
                    "transaction_id": message.payload.get("transaction_id"),
                    "resource_status": message.payload.get("resource_status"),
                    "timestamp": message.payload.get("timestamp")
                },
                "warning"
            )
        
        elif message.message_type == "audit_query":
            # Handle audit queries
            self._handle_audit_query(message)
        
        else:
            # Log any other system events
            self.create_audit_record(
                "system_event",
                message.sender,
                {
                    "message_type": message.message_type,
                    "payload": message.payload
                },
                "info"
            )
    
    def _handle_audit_query(self, message: Message):
        """Handle audit query requests."""
        query_type = message.payload.get("query_type")
        
        if query_type == "summary":
            response_data = self.get_audit_summary()
        elif query_type == "records":
            filters = message.payload.get("filters", {})
            response_data = self.query_audit_records(filters)
        elif query_type == "compliance_report":
            response_data = self.generate_compliance_report()
        elif query_type == "security_report":
            response_data = self.generate_security_report()
        else:
            response_data = {"error": f"Unknown query type: {query_type}"}
        
        self.send_message(
            message.sender,
            "audit_query_response",
            response_data,
            correlation_id=message.correlation_id
        )
    
    def query_audit_records(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query audit records with filters."""
        results = []
        
        for record in self.audit_records:
            # Apply filters
            if filters.get("event_type") and record.event_type != filters["event_type"]:
                continue
            
            if filters.get("source") and record.source != filters["source"]:
                continue
            
            if filters.get("severity") and record.severity != filters["severity"]:
                continue
            
            if filters.get("start_date"):
                start_date = datetime.fromisoformat(filters["start_date"])
                if record.timestamp < start_date:
                    continue
            
            if filters.get("end_date"):
                end_date = datetime.fromisoformat(filters["end_date"])
                if record.timestamp > end_date:
                    continue
            
            # Include this record
            results.append({
                "id": record.id,
                "timestamp": record.timestamp.isoformat(),
                "event_type": record.event_type,
                "source": record.source,
                "details": record.details,
                "severity": record.severity,
                "reviewed": record.reviewed
            })
        
        return results
    
    def get_audit_summary(self) -> Dict[str, Any]:
        """Get audit summary with statistics."""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate today's statistics
        today_records = [r for r in self.audit_records if r.timestamp >= today_start]
        
        severity_counts = {}
        event_type_counts = {}
        
        for record in self.audit_records:
            # Count by severity
            severity_counts[record.severity] = severity_counts.get(record.severity, 0) + 1
            
            # Count by event type
            event_type_counts[record.event_type] = event_type_counts.get(record.event_type, 0) + 1
        
        return {
            "summary": self.audit_summary,
            "total_audit_records": len(self.audit_records),
            "records_today": len(today_records),
            "severity_distribution": severity_counts,
            "event_type_distribution": event_type_counts,
            "unreviewed_records": sum(1 for r in self.audit_records if not r.reviewed),
            "last_updated": now.isoformat()
        }
    
    def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate a compliance report."""
        compliance_records = [
            r for r in self.audit_records 
            if r.event_type in ["compliance_violation", "transaction_completed", "transaction_failed"]
        ]
        
        violations = [r for r in compliance_records if r.event_type == "compliance_violation"]
        
        # Calculate compliance rate
        total_transactions = self.audit_summary["total_transactions"]
        violation_count = len(violations)
        compliance_rate = (total_transactions - violation_count) / total_transactions if total_transactions > 0 else 1.0
        
        # Analyze violation types
        violation_types = {}
        for record in violations:
            for violation in record.details.get("violations", []):
                rule = violation.get("rule", "unknown")
                violation_types[rule] = violation_types.get(rule, 0) + 1
        
        return {
            "report_type": "compliance",
            "generated_at": datetime.now().isoformat(),
            "compliance_rate": compliance_rate,
            "total_transactions": total_transactions,
            "violation_count": violation_count,
            "violation_types": violation_types,
            "recommendations": self._get_compliance_recommendations(violation_types)
        }
    
    def generate_security_report(self) -> Dict[str, Any]:
        """Generate a security report."""
        security_records = [
            r for r in self.audit_records 
            if r.event_type in ["threat_alert", "transaction_failed"]
        ]
        
        threat_alerts = [r for r in security_records if r.event_type == "threat_alert"]
        
        # Analyze threat types
        threat_types = {}
        severity_distribution = {}
        
        for record in threat_alerts:
            threat_type = record.details.get("threat_type", "unknown")
            severity = record.details.get("severity", "unknown")
            
            threat_types[threat_type] = threat_types.get(threat_type, 0) + 1
            severity_distribution[severity] = severity_distribution.get(severity, 0) + 1
        
        return {
            "report_type": "security",
            "generated_at": datetime.now().isoformat(),
            "total_threat_alerts": len(threat_alerts),
            "threat_types": threat_types,
            "severity_distribution": severity_distribution,
            "fraud_incidents": self.audit_summary["fraud_incidents"],
            "recommendations": self._get_security_recommendations(threat_types, severity_distribution)
        }
    
    def _get_compliance_recommendations(self, violation_types: Dict[str, int]) -> List[str]:
        """Get compliance recommendations based on violation patterns."""
        recommendations = []
        
        if violation_types.get("max_single_transaction", 0) > 0:
            recommendations.append("Review single transaction limits and consider dynamic limits based on account history")
        
        if violation_types.get("max_daily_amount", 0) > 0:
            recommendations.append("Implement real-time daily limit monitoring and early warnings")
        
        if violation_types.get("kyc_required", 0) > 0:
            recommendations.append("Enhance KYC verification processes and automated checks")
        
        if violation_types.get("prohibited_country", 0) > 0:
            recommendations.append("Update prohibited country lists and improve geolocation verification")
        
        return recommendations
    
    def _get_security_recommendations(self, threat_types: Dict[str, int], 
                                    severity_distribution: Dict[str, int]) -> List[str]:
        """Get security recommendations based on threat patterns."""
        recommendations = []
        
        if threat_types.get("financial_fraud", 0) > 0:
            recommendations.append("Enhance fraud detection algorithms and implement machine learning models")
        
        if threat_types.get("ddos_attack", 0) > 0:
            recommendations.append("Implement advanced DDoS protection and rate limiting")
        
        if threat_types.get("brute_force_attack", 0) > 0:
            recommendations.append("Strengthen authentication mechanisms and account lockout policies")
        
        if severity_distribution.get("high", 0) > 0:
            recommendations.append("Establish 24/7 security monitoring and incident response team")
        
        return recommendations
    
    def mark_record_reviewed(self, record_id: str) -> bool:
        """Mark an audit record as reviewed."""
        for record in self.audit_records:
            if record.id == record_id:
                record.reviewed = True
                system_logger.info(f"Audit record {record_id} marked as reviewed", self.agent_id)
                return True
        
        system_logger.warning(f"Audit record {record_id} not found", self.agent_id)
        return False
    
    def export_audit_records(self, filters: Optional[Dict[str, Any]] = None) -> str:
        """Export audit records to a formatted string (CSV-like format)."""
        records = self.query_audit_records(filters or {})
        
        lines = ["ID,Timestamp,Event Type,Source,Severity,Reviewed,Details"]
        
        for record in records:
            details_str = str(record["details"]).replace(",", ";")  # Avoid CSV conflicts
            line = f"{record['id']},{record['timestamp']},{record['event_type']},{record['source']},{record['severity']},{record['reviewed']},\"{details_str}\""
            lines.append(line)
        
        return "\n".join(lines)