#!/usr/bin/env python3
"""
Main orchestration entry-point for the FinTech cloud multi-agent system.
Demonstrates agent interaction for sample transactions with logging and compliance checks.
"""
import time
from datetime import datetime
from typing import Dict, Any

from agents.transaction_processing_agent import TransactionProcessingAgent
from agents.fraud_detection_agent import FraudDetectionAgent
from agents.compliance_agent import ComplianceAgent
from agents.resource_allocation_agent import ResourceAllocationAgent
from agents.threat_detection_agent import ThreatDetectionAgent
from agents.blockchain_agent import BlockchainAgent
from agents.audit_agent import AuditAgent
from utils.logging import system_logger


class FinTechOrchestrator:
    """Main orchestrator for the FinTech multi-agent system."""
    
    def __init__(self):
        system_logger.info("Initializing FinTech Multi-Agent System", "orchestrator")
        
        # Initialize all agents
        self.transaction_agent = TransactionProcessingAgent()
        self.fraud_agent = FraudDetectionAgent()
        self.compliance_agent = ComplianceAgent()
        self.resource_agent = ResourceAllocationAgent()
        self.threat_agent = ThreatDetectionAgent()
        self.blockchain_agent = BlockchainAgent()
        self.audit_agent = AuditAgent()
        
        system_logger.info("All agents initialized successfully", "orchestrator")
    
    def run_sample_transaction_flow(self):
        """Demonstrate a complete transaction flow through the multi-agent system."""
        system_logger.info("=" * 60, "orchestrator")
        system_logger.info("STARTING SAMPLE TRANSACTION FLOW", "orchestrator")
        system_logger.info("=" * 60, "orchestrator")
        
        # Sample transaction data
        sample_transactions = [
            {
                "amount": 1500.00,
                "sender_account": "verified_user_001",
                "recipient_account": "merchant_account_123",
                "currency": "USD",
                "metadata": {"description": "Payment for services", "category": "business"}
            },
            {
                "amount": 15000.00,  # High amount - should trigger fraud checks
                "sender_account": "user_002",
                "recipient_account": "vendor_xyz",
                "currency": "USD",
                "metadata": {"description": "Large purchase", "category": "equipment"}
            },
            {
                "amount": 999.99,  # Suspicious amount pattern
                "sender_account": "user_003",
                "recipient_account": "user_004",
                "currency": "USD",
                "metadata": {"description": "Transfer", "category": "personal"}
            },
            {
                "amount": 30000.00,  # Exceeds single transaction limit
                "sender_account": "user_005",
                "recipient_account": "business_account",
                "currency": "USD",
                "metadata": {"description": "Investment", "category": "investment"}
            }
        ]
        
        transactions = []
        
        # Process each sample transaction
        for i, tx_data in enumerate(sample_transactions, 1):
            system_logger.info(f"Processing Sample Transaction {i}/{len(sample_transactions)}", "orchestrator")
            system_logger.info(f"Amount: ${tx_data['amount']}, From: {tx_data['sender_account']}, To: {tx_data['recipient_account']}", "orchestrator")
            
            # Create transaction
            transaction = self.transaction_agent.create_transaction(**tx_data)
            transactions.append(transaction)
            
            # Process transaction through the pipeline
            self.transaction_agent.process_transaction(transaction)
            
            # Allow some time for agent communication
            time.sleep(2)
            
            # Request blockchain recording
            self.blockchain_agent.send_message(
                "blockchain_agent",
                "blockchain_record_request",
                {
                    "transaction_data": {
                        "transaction_id": transaction.id,
                        "amount": transaction.amount,
                        "sender_account": transaction.sender_account,
                        "recipient_account": transaction.recipient_account,
                        "currency": transaction.currency
                    }
                }
            )
            
            system_logger.info(f"Sample Transaction {i} submitted for processing", "orchestrator")
            print("-" * 40)
        
        # Allow time for all processing to complete
        system_logger.info("Waiting for transaction processing to complete...", "orchestrator")
        time.sleep(5)
        
        # Mine blockchain transactions
        system_logger.info("Mining blockchain transactions...", "orchestrator")
        self.blockchain_agent.mine_pending_transactions()
        
        return transactions
    
    def display_system_status(self):
        """Display the current status of all system components."""
        system_logger.info("=" * 60, "orchestrator")
        system_logger.info("SYSTEM STATUS REPORT", "orchestrator")
        system_logger.info("=" * 60, "orchestrator")
        
        # Transaction Processing Status
        pending = len(self.transaction_agent.pending_transactions)
        completed = len(self.transaction_agent.completed_transactions)
        failed = len(self.transaction_agent.failed_transactions)
        
        system_logger.info("TRANSACTION PROCESSING AGENT:", "orchestrator")
        system_logger.info(f"  - Pending: {pending}", "orchestrator")
        system_logger.info(f"  - Completed: {completed}", "orchestrator")
        system_logger.info(f"  - Failed: {failed}", "orchestrator")
        
        # Fraud Detection Status
        fraud_stats = self.fraud_agent.get_fraud_statistics()
        
        system_logger.info("FRAUD DETECTION AGENT:", "orchestrator")
        system_logger.info(f"  - Total Analyzed: {fraud_stats['total_transactions']}", "orchestrator")
        system_logger.info(f"  - Fraudulent: {fraud_stats['fraudulent_transactions']}", "orchestrator")
        system_logger.info(f"  - Fraud Rate: {fraud_stats['fraud_rate']:.2%}", "orchestrator")
        system_logger.info(f"  - Avg Risk Score: {fraud_stats['average_risk_score']:.2f}", "orchestrator")
        
        # Compliance Status
        compliance_stats = self.compliance_agent.get_compliance_statistics()
        
        system_logger.info("COMPLIANCE AGENT:", "orchestrator")
        system_logger.info(f"  - Total Violations: {compliance_stats['total_violations']}", "orchestrator")
        system_logger.info(f"  - Avg Compliance Score: {compliance_stats['average_compliance_score']:.2f}", "orchestrator")
        
        # Resource Allocation Status
        resource_stats = self.resource_agent.get_resource_status()
        
        system_logger.info("RESOURCE ALLOCATION AGENT:", "orchestrator")
        system_logger.info(f"  - CPU Utilization: {resource_stats['resources']['cpu_units']['utilization_percent']:.1f}%", "orchestrator")
        system_logger.info(f"  - Memory Utilization: {resource_stats['resources']['memory_mb']['utilization_percent']:.1f}%", "orchestrator")
        system_logger.info(f"  - Successful Allocations: {resource_stats['successful_allocations']}", "orchestrator")
        
        # Threat Detection Status
        threat_stats = self.threat_agent.get_threat_statistics()
        
        system_logger.info("THREAT DETECTION AGENT:", "orchestrator")
        system_logger.info(f"  - Total Alerts: {threat_stats['total_alerts']}", "orchestrator")
        system_logger.info(f"  - Resolution Rate: {threat_stats['resolution_rate']:.2%}", "orchestrator")
        
        # Blockchain Status
        blockchain_stats = self.blockchain_agent.get_blockchain_status()
        
        system_logger.info("BLOCKCHAIN AGENT:", "orchestrator")
        system_logger.info(f"  - Chain Length: {blockchain_stats['chain_length']} blocks", "orchestrator")
        system_logger.info(f"  - Total Transactions: {blockchain_stats['total_transactions']}", "orchestrator")
        system_logger.info(f"  - Pending: {blockchain_stats['pending_transactions']}", "orchestrator")
        system_logger.info(f"  - Chain Valid: {blockchain_stats['is_valid']}", "orchestrator")
        
        # Audit Status
        audit_stats = self.audit_agent.get_audit_summary()
        
        system_logger.info("AUDIT AGENT:", "orchestrator")
        system_logger.info(f"  - Total Records: {audit_stats['total_audit_records']}", "orchestrator")
        system_logger.info(f"  - Records Today: {audit_stats['records_today']}", "orchestrator")
        system_logger.info(f"  - Unreviewed: {audit_stats['unreviewed_records']}", "orchestrator")
    
    def generate_reports(self):
        """Generate compliance and security reports."""
        system_logger.info("=" * 60, "orchestrator")
        system_logger.info("GENERATING REPORTS", "orchestrator")
        system_logger.info("=" * 60, "orchestrator")
        
        # Request compliance report
        self.audit_agent.send_message(
            "audit_agent",
            "audit_query",
            {"query_type": "compliance_report"}
        )
        
        # Request security report
        self.audit_agent.send_message(
            "audit_agent",  
            "audit_query",
            {"query_type": "security_report"}
        )
        
        time.sleep(1)  # Allow reports to be generated
        
        # Generate compliance report directly
        compliance_report = self.audit_agent.generate_compliance_report()
        system_logger.info("COMPLIANCE REPORT:", "orchestrator")
        system_logger.info(f"  - Compliance Rate: {compliance_report['compliance_rate']:.2%}", "orchestrator")
        system_logger.info(f"  - Total Transactions: {compliance_report['total_transactions']}", "orchestrator")
        system_logger.info(f"  - Violations: {compliance_report['violation_count']}", "orchestrator")
        
        # Generate security report directly
        security_report = self.audit_agent.generate_security_report()
        system_logger.info("SECURITY REPORT:", "orchestrator")
        system_logger.info(f"  - Threat Alerts: {security_report['total_threat_alerts']}", "orchestrator")
        system_logger.info(f"  - Fraud Incidents: {security_report['fraud_incidents']}", "orchestrator")
    
    def run_system_test(self):
        """Run a comprehensive system test."""
        system_logger.info("Starting FinTech Multi-Agent System Test", "orchestrator")
        
        # Run sample transaction flow
        transactions = self.run_sample_transaction_flow()
        
        # Display system status
        self.display_system_status()
        
        # Generate reports
        self.generate_reports()
        
        system_logger.info("=" * 60, "orchestrator")
        system_logger.info("SYSTEM TEST COMPLETED", "orchestrator")
        system_logger.info("=" * 60, "orchestrator")
        
        return {
            "transactions_processed": len(transactions),
            "test_completed": True,
            "timestamp": datetime.now().isoformat()
        }


def main():
    """Main entry point for the FinTech multi-agent system."""
    try:
        # Initialize the orchestrator
        orchestrator = FinTechOrchestrator()
        
        # Run the system test
        result = orchestrator.run_system_test()
        
        system_logger.info(f"System test completed successfully: {result}", "main")
        return 0
        
    except Exception as e:
        system_logger.error(f"System test failed with error: {str(e)}", "main")
        return 1


if __name__ == "__main__":
    exit(main())