"""
Resource Allocation Agent for the FinTech multi-agent system.
"""
from typing import Dict, Any, List
from datetime import datetime
from dataclasses import dataclass

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
class ResourceRequest:
    """Resource allocation request."""
    transaction_id: str
    priority: str
    complexity: str
    timestamp: datetime
    allocated: bool = False
    cpu_units: int = 0
    memory_mb: int = 0
    network_bandwidth: int = 0


class ResourceAllocationAgent(BaseAgent):
    """Agent responsible for allocating computational resources."""
    
    def __init__(self):
        super().__init__("resource_allocator")
        self.total_resources = {
            "cpu_units": 1000,
            "memory_mb": 8192,
            "network_bandwidth": 1000  # Mbps
        }
        self.allocated_resources = {
            "cpu_units": 0,
            "memory_mb": 0,
            "network_bandwidth": 0
        }
        self.resource_requests: List[ResourceRequest] = []
        
        # Resource allocation rules
        self.allocation_rules = {
            "high": {"cpu": 20, "memory": 512, "bandwidth": 50},
            "normal": {"cpu": 10, "memory": 256, "bandwidth": 25},
            "low": {"cpu": 5, "memory": 128, "bandwidth": 10}
        }
        
        system_logger.info("Resource Allocation Agent initialized", self.agent_id)
    
    def allocate_resources(self, transaction_id: str, priority: str = "normal", 
                          complexity: str = "low") -> Dict[str, Any]:
        """Allocate resources for a transaction."""
        
        # Determine resource requirements based on priority and complexity
        base_allocation = self.allocation_rules.get(priority, self.allocation_rules["normal"])
        
        # Adjust based on complexity
        complexity_multiplier = {
            "low": 1.0,
            "medium": 1.5,
            "high": 2.0
        }.get(complexity, 1.0)
        
        required_cpu = int(base_allocation["cpu"] * complexity_multiplier)
        required_memory = int(base_allocation["memory"] * complexity_multiplier)
        required_bandwidth = int(base_allocation["bandwidth"] * complexity_multiplier)
        
        # Check if resources are available
        available_cpu = self.total_resources["cpu_units"] - self.allocated_resources["cpu_units"]
        available_memory = self.total_resources["memory_mb"] - self.allocated_resources["memory_mb"]
        available_bandwidth = self.total_resources["network_bandwidth"] - self.allocated_resources["network_bandwidth"]
        
        if (required_cpu <= available_cpu and 
            required_memory <= available_memory and 
            required_bandwidth <= available_bandwidth):
            
            # Allocate resources
            self.allocated_resources["cpu_units"] += required_cpu
            self.allocated_resources["memory_mb"] += required_memory
            self.allocated_resources["network_bandwidth"] += required_bandwidth
            
            # Create resource request record
            request = ResourceRequest(
                transaction_id=transaction_id,
                priority=priority,
                complexity=complexity,
                timestamp=datetime.now(),
                allocated=True,
                cpu_units=required_cpu,
                memory_mb=required_memory,
                network_bandwidth=required_bandwidth
            )
            self.resource_requests.append(request)
            
            system_logger.info(
                f"Resources allocated for transaction {transaction_id}: "
                f"CPU={required_cpu}, Memory={required_memory}MB, Bandwidth={required_bandwidth}Mbps",
                self.agent_id
            )
            
            return {
                "allocated": True,
                "cpu_units": required_cpu,
                "memory_mb": required_memory,
                "network_bandwidth": required_bandwidth,
                "allocation_id": len(self.resource_requests) - 1
            }
        else:
            # Resources not available
            request = ResourceRequest(
                transaction_id=transaction_id,
                priority=priority,
                complexity=complexity,
                timestamp=datetime.now(),
                allocated=False
            )
            self.resource_requests.append(request)
            
            system_logger.warning(
                f"Insufficient resources for transaction {transaction_id}. "
                f"Required: CPU={required_cpu}, Memory={required_memory}MB, Bandwidth={required_bandwidth}Mbps. "
                f"Available: CPU={available_cpu}, Memory={available_memory}MB, Bandwidth={available_bandwidth}Mbps",
                self.agent_id
            )
            
            return {
                "allocated": False,
                "reason": "Insufficient resources available",
                "required": {
                    "cpu_units": required_cpu,
                    "memory_mb": required_memory,
                    "network_bandwidth": required_bandwidth
                },
                "available": {
                    "cpu_units": available_cpu,
                    "memory_mb": available_memory,
                    "network_bandwidth": available_bandwidth
                }
            }
    
    def release_resources(self, transaction_id: str) -> bool:
        """Release resources allocated to a transaction."""
        for request in self.resource_requests:
            if request.transaction_id == transaction_id and request.allocated:
                # Release the resources
                self.allocated_resources["cpu_units"] -= request.cpu_units
                self.allocated_resources["memory_mb"] -= request.memory_mb
                self.allocated_resources["network_bandwidth"] -= request.network_bandwidth
                
                # Mark as released (could add a released flag to the dataclass)
                request.allocated = False
                
                system_logger.info(
                    f"Resources released for transaction {transaction_id}: "
                    f"CPU={request.cpu_units}, Memory={request.memory_mb}MB, Bandwidth={request.network_bandwidth}Mbps",
                    self.agent_id
                )
                return True
        
        system_logger.warning(f"No allocated resources found for transaction {transaction_id}", self.agent_id)
        return False
    
    def process_message(self, message: Message):
        """Process resource allocation requests."""
        if message.message_type == "resource_request":
            transaction_id = message.payload.get("transaction_id")
            priority = message.payload.get("processing_priority", "normal")
            complexity = message.payload.get("estimated_complexity", "low")
            
            system_logger.info(
                f"Processing resource request for transaction {transaction_id} "
                f"(priority: {priority}, complexity: {complexity})",
                self.agent_id
            )
            
            # Allocate resources
            allocation_result = self.allocate_resources(transaction_id, priority, complexity)
            
            if allocation_result["allocated"]:
                # Send success response
                self.send_message(
                    message.sender,
                    "resource_allocated",
                    {
                        "transaction_id": transaction_id,
                        **allocation_result
                    },
                    correlation_id=message.correlation_id
                )
            else:
                # Send failure response
                self.send_message(
                    message.sender,
                    "resource_allocation_failed",
                    {
                        "transaction_id": transaction_id,
                        **allocation_result
                    },
                    correlation_id=message.correlation_id
                )
                
                # Notify system of resource shortage
                self.send_message(
                    "audit_agent",
                    "resource_shortage",
                    {
                        "transaction_id": transaction_id,
                        "timestamp": datetime.now().isoformat(),
                        "resource_status": self.get_resource_status()
                    }
                )
        
        elif message.message_type == "release_resources":
            transaction_id = message.payload.get("transaction_id")
            self.release_resources(transaction_id)
    
    def get_resource_status(self) -> Dict[str, Any]:
        """Get current resource utilization status."""
        utilization = {}
        for resource, total in self.total_resources.items():
            allocated = self.allocated_resources[resource]
            utilization[resource] = {
                "total": total,
                "allocated": allocated,
                "available": total - allocated,
                "utilization_percent": (allocated / total) * 100 if total > 0 else 0
            }
        
        return {
            "resources": utilization,
            "total_requests": len(self.resource_requests),
            "successful_allocations": sum(1 for r in self.resource_requests if r.allocated),
            "failed_allocations": sum(1 for r in self.resource_requests if not r.allocated)
        }
    
    def optimize_resources(self):
        """Perform resource optimization (stub implementation)."""
        system_logger.info("Performing resource optimization", self.agent_id)
        
        # Simple optimization: release resources from old completed transactions
        # In a real system, this would be more sophisticated
        current_time = datetime.now()
        old_requests = [
            r for r in self.resource_requests 
            if r.allocated and (current_time - r.timestamp).seconds > 300  # 5 minutes old
        ]
        
        for request in old_requests:
            self.release_resources(request.transaction_id)
        
        if old_requests:
            system_logger.info(f"Released resources from {len(old_requests)} old transactions", self.agent_id)