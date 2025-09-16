"""
Threat Detection Agent for the FinTech multi-agent system.
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..protocols.inter_agent_comm import BaseAgent, Message
from ..utils.logging import system_logger


@dataclass
class ThreatAlert:
    """Threat alert data structure."""
    id: str
    threat_type: str
    severity: str
    source: str
    target: str
    timestamp: datetime
    description: str
    mitigation_actions: List[str]
    resolved: bool = False


class ThreatDetectionAgent(BaseAgent):
    """Agent responsible for detecting and responding to security threats."""
    
    def __init__(self):
        super().__init__("threat_detector")
        self.threat_alerts: List[ThreatAlert] = []
        self.threat_patterns = {
            "ddos_threshold": 100,  # requests per minute
            "brute_force_threshold": 10,  # failed attempts per account
            "suspicious_ips": ["192.168.1.100", "10.0.0.50"],  # Mock suspicious IPs
            "threat_keywords": ["attack", "exploit", "breach", "malware"]
        }
        self.request_counts: Dict[str, List[datetime]] = {}
        self.failed_attempts: Dict[str, int] = {}
        
        system_logger.info("Threat Detection Agent initialized", self.agent_id)
    
    def analyze_threat(self, threat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze potential security threats."""
        threat_type = threat_data.get("threat_type", "unknown")
        source_ip = threat_data.get("source_ip", "")
        target = threat_data.get("target", "")
        
        threats_detected = []
        severity = "low"
        
        if threat_type == "fraud":
            # Handle fraud alerts from fraud detection agent
            threats_detected.append("financial_fraud")
            severity = self._calculate_fraud_severity(threat_data)
        
        elif threat_type == "suspicious_activity":
            # Analyze suspicious patterns
            if self._check_ddos_pattern(source_ip):
                threats_detected.append("ddos_attack")
                severity = "high"
            
            if self._check_brute_force_pattern(target):
                threats_detected.append("brute_force_attack")
                severity = "medium"
        
        elif threat_type == "network_anomaly":
            # Analyze network anomalies
            if source_ip in self.threat_patterns["suspicious_ips"]:
                threats_detected.append("suspicious_ip_activity")
                severity = "medium"
        
        # Check for threat keywords in data
        data_text = str(threat_data).lower()
        for keyword in self.threat_patterns["threat_keywords"]:
            if keyword in data_text:
                threats_detected.append(f"keyword_threat_{keyword}")
                severity = max(severity, "medium", key=lambda x: ["low", "medium", "high"].index(x))
        
        return {
            "threats_detected": threats_detected,
            "severity": severity,
            "requires_immediate_action": severity == "high",
            "recommended_actions": self._get_mitigation_actions(threats_detected, severity)
        }
    
    def _calculate_fraud_severity(self, fraud_data: Dict[str, Any]) -> str:
        """Calculate severity based on fraud indicators."""
        risk_score = fraud_data.get("risk_score", 0.0)
        if risk_score >= 0.8:
            return "high"
        elif risk_score >= 0.5:
            return "medium"
        else:
            return "low"
    
    def _check_ddos_pattern(self, source_ip: str) -> bool:
        """Check for DDoS attack patterns."""
        current_time = datetime.now()
        minute_ago = current_time - timedelta(minutes=1)
        
        # Track requests from this IP
        if source_ip not in self.request_counts:
            self.request_counts[source_ip] = []
        
        # Clean old requests
        self.request_counts[source_ip] = [
            req_time for req_time in self.request_counts[source_ip] 
            if req_time > minute_ago
        ]
        
        # Add current request
        self.request_counts[source_ip].append(current_time)
        
        # Check if threshold exceeded
        return len(self.request_counts[source_ip]) > self.threat_patterns["ddos_threshold"]
    
    def _check_brute_force_pattern(self, target_account: str) -> bool:
        """Check for brute force attack patterns."""
        failed_count = self.failed_attempts.get(target_account, 0)
        return failed_count > self.threat_patterns["brute_force_threshold"]
    
    def _get_mitigation_actions(self, threats: List[str], severity: str) -> List[str]:
        """Get recommended mitigation actions based on detected threats."""
        actions = []
        
        if "financial_fraud" in threats:
            actions.extend([
                "block_transaction",
                "flag_account",
                "notify_compliance",
                "initiate_investigation"
            ])
        
        if "ddos_attack" in threats:
            actions.extend([
                "rate_limit_ip",
                "activate_ddos_protection",
                "alert_network_team"
            ])
        
        if "brute_force_attack" in threats:
            actions.extend([
                "lock_account_temporarily",
                "require_additional_authentication",
                "alert_security_team"
            ])
        
        if "suspicious_ip_activity" in threats:
            actions.extend([
                "block_ip_address",
                "review_ip_reputation",
                "notify_threat_intelligence"
            ])
        
        if severity == "high":
            actions.append("escalate_to_security_team")
            actions.append("activate_incident_response")
        
        return list(set(actions))  # Remove duplicates
    
    def create_threat_alert(self, threat_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> ThreatAlert:
        """Create a threat alert."""
        import uuid
        
        alert = ThreatAlert(
            id=str(uuid.uuid4()),
            threat_type=", ".join(analysis_result["threats_detected"]),
            severity=analysis_result["severity"],
            source=threat_data.get("source", "unknown"),
            target=threat_data.get("target", "unknown"),
            timestamp=datetime.now(),
            description=f"Detected threats: {', '.join(analysis_result['threats_detected'])}",
            mitigation_actions=analysis_result["recommended_actions"]
        )
        
        self.threat_alerts.append(alert)
        return alert
    
    def process_message(self, message: Message):
        """Process threat detection requests and alerts."""
        if message.message_type == "fraud_alert":
            # Handle fraud alerts from fraud detection agent
            threat_data = {
                "threat_type": "fraud",
                "transaction_id": message.payload.get("transaction_id"),
                "sender_account": message.payload.get("sender_account"),
                "risk_score": message.payload.get("risk_score", 0.0),
                "indicators": message.payload.get("indicators", [])
            }
            
            system_logger.warning(
                f"Fraud alert received for transaction {threat_data['transaction_id']}", 
                self.agent_id
            )
            
            # Analyze the threat
            analysis_result = self.analyze_threat(threat_data)
            
            # Create threat alert
            alert = self.create_threat_alert(threat_data, analysis_result)
            
            system_logger.warning(
                f"Threat alert {alert.id} created: {alert.description} (Severity: {alert.severity})",
                self.agent_id
            )
            
            # Notify audit agent
            self.send_message(
                "audit_agent",
                "threat_alert",
                {
                    "alert_id": alert.id,
                    "threat_type": alert.threat_type,
                    "severity": alert.severity,
                    "timestamp": alert.timestamp.isoformat(),
                    "description": alert.description,
                    "mitigation_actions": alert.mitigation_actions
                }
            )
            
            # If high severity, take immediate action
            if analysis_result["requires_immediate_action"]:
                self._execute_mitigation_actions(alert.mitigation_actions, threat_data)
        
        elif message.message_type == "security_incident":
            # Handle general security incidents
            system_logger.warning("Security incident reported", self.agent_id)
            
            threat_data = message.payload
            analysis_result = self.analyze_threat(threat_data)
            alert = self.create_threat_alert(threat_data, analysis_result)
            
            system_logger.warning(
                f"Security incident alert {alert.id} created: {alert.description}",
                self.agent_id
            )
    
    def _execute_mitigation_actions(self, actions: List[str], threat_data: Dict[str, Any]):
        """Execute mitigation actions for high-severity threats."""
        system_logger.warning(f"Executing mitigation actions: {', '.join(actions)}", self.agent_id)
        
        for action in actions:
            if action == "block_transaction":
                # In a real system, would interface with transaction processing
                system_logger.warning(f"BLOCKING transaction {threat_data.get('transaction_id')}", self.agent_id)
            
            elif action == "flag_account":
                account = threat_data.get("sender_account")
                system_logger.warning(f"FLAGGING account {account} for review", self.agent_id)
            
            elif action == "escalate_to_security_team":
                system_logger.warning("ESCALATING to security team for immediate response", self.agent_id)
            
            # Add more mitigation actions as needed
    
    def get_threat_statistics(self) -> Dict[str, Any]:
        """Get threat detection statistics."""
        total_alerts = len(self.threat_alerts)
        
        if total_alerts == 0:
            return {
                "total_alerts": 0,
                "alerts_by_severity": {},
                "alerts_by_type": {},
                "resolved_alerts": 0
            }
        
        # Count by severity
        alerts_by_severity = {}
        alerts_by_type = {}
        resolved_count = 0
        
        for alert in self.threat_alerts:
            # Count by severity
            alerts_by_severity[alert.severity] = alerts_by_severity.get(alert.severity, 0) + 1
            
            # Count by type
            alerts_by_type[alert.threat_type] = alerts_by_type.get(alert.threat_type, 0) + 1
            
            # Count resolved
            if alert.resolved:
                resolved_count += 1
        
        return {
            "total_alerts": total_alerts,
            "alerts_by_severity": alerts_by_severity,
            "alerts_by_type": alerts_by_type,
            "resolved_alerts": resolved_count,
            "resolution_rate": resolved_count / total_alerts if total_alerts > 0 else 0
        }
    
    def resolve_threat_alert(self, alert_id: str) -> bool:
        """Mark a threat alert as resolved."""
        for alert in self.threat_alerts:
            if alert.id == alert_id:
                alert.resolved = True
                system_logger.info(f"Threat alert {alert_id} marked as resolved", self.agent_id)
                return True
        
        system_logger.warning(f"Threat alert {alert_id} not found", self.agent_id)
        return False