"""
Blockchain Agent for the FinTech multi-agent system.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
import hashlib
import uuid

from ..protocols.inter_agent_comm import BaseAgent, Message
from ..utils.logging import system_logger


@dataclass
class Block:
    """Blockchain block data structure."""
    index: int
    timestamp: datetime
    transactions: List[Dict[str, Any]]
    previous_hash: str
    hash: str
    nonce: int = 0


@dataclass
class BlockchainTransaction:
    """Blockchain transaction structure."""
    id: str
    transaction_id: str  # Reference to original transaction
    amount: float
    sender: str
    recipient: str
    timestamp: datetime
    status: str = "pending"
    block_index: Optional[int] = None


class BlockchainAgent(BaseAgent):
    """Agent responsible for blockchain transaction handling."""
    
    def __init__(self):
        super().__init__("blockchain_agent")
        self.chain: List[Block] = []
        self.pending_transactions: List[BlockchainTransaction] = []
        self.confirmed_transactions: Dict[str, BlockchainTransaction] = {}
        self.difficulty = 4  # Simple proof-of-work difficulty
        
        # Create genesis block
        self._create_genesis_block()
        
        system_logger.info("Blockchain Agent initialized", self.agent_id)
    
    def _create_genesis_block(self):
        """Create the first block in the blockchain."""
        genesis_block = Block(
            index=0,
            timestamp=datetime.now(),
            transactions=[],
            previous_hash="0",
            hash="",
            nonce=0
        )
        genesis_block.hash = self._calculate_hash(genesis_block)
        self.chain.append(genesis_block)
        
        system_logger.info("Genesis block created", self.agent_id)
    
    def _calculate_hash(self, block: Block) -> str:
        """Calculate hash for a block."""
        block_string = f"{block.index}{block.timestamp}{block.transactions}{block.previous_hash}{block.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def _mine_block(self, block: Block) -> Block:
        """Simple proof-of-work mining."""
        target = "0" * self.difficulty
        
        while not block.hash.startswith(target):
            block.nonce += 1
            block.hash = self._calculate_hash(block)
        
        return block
    
    def create_blockchain_transaction(self, transaction_data: Dict[str, Any]) -> BlockchainTransaction:
        """Create a new blockchain transaction."""
        blockchain_tx = BlockchainTransaction(
            id=str(uuid.uuid4()),
            transaction_id=transaction_data.get("transaction_id", ""),
            amount=transaction_data.get("amount", 0.0),
            sender=transaction_data.get("sender_account", ""),
            recipient=transaction_data.get("recipient_account", ""),
            timestamp=datetime.now()
        )
        
        self.pending_transactions.append(blockchain_tx)
        
        system_logger.info(
            f"Blockchain transaction {blockchain_tx.id} created for transaction {blockchain_tx.transaction_id}",
            self.agent_id
        )
        
        return blockchain_tx
    
    def mine_pending_transactions(self) -> Optional[Block]:
        """Mine pending transactions into a new block."""
        if not self.pending_transactions:
            system_logger.info("No pending transactions to mine", self.agent_id)
            return None
        
        # Take up to 10 transactions for this block
        transactions_to_mine = self.pending_transactions[:10]
        
        # Convert transactions to dict format for block
        transaction_data = []
        for tx in transactions_to_mine:
            transaction_data.append({
                "id": tx.id,
                "transaction_id": tx.transaction_id,
                "amount": tx.amount,
                "sender": tx.sender,
                "recipient": tx.recipient,
                "timestamp": tx.timestamp.isoformat()
            })
        
        # Create new block
        new_block = Block(
            index=len(self.chain),
            timestamp=datetime.now(),
            transactions=transaction_data,
            previous_hash=self.chain[-1].hash,
            hash=""
        )
        
        system_logger.info(f"Mining new block {new_block.index} with {len(transaction_data)} transactions", self.agent_id)
        
        # Mine the block (simple proof-of-work)
        mined_block = self._mine_block(new_block)
        
        # Add block to chain
        self.chain.append(mined_block)
        
        # Update transaction statuses
        for tx in transactions_to_mine:
            tx.status = "confirmed"
            tx.block_index = mined_block.index
            self.confirmed_transactions[tx.id] = tx
        
        # Remove mined transactions from pending
        self.pending_transactions = self.pending_transactions[10:]
        
        system_logger.info(
            f"Block {mined_block.index} mined successfully with hash {mined_block.hash[:16]}...",
            self.agent_id
        )
        
        return mined_block
    
    def verify_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Verify a transaction on the blockchain."""
        # Check confirmed transactions
        for blockchain_tx in self.confirmed_transactions.values():
            if blockchain_tx.transaction_id == transaction_id:
                block = self.chain[blockchain_tx.block_index]
                
                return {
                    "verified": True,
                    "status": "confirmed",
                    "block_index": blockchain_tx.block_index,
                    "block_hash": block.hash,
                    "confirmations": len(self.chain) - blockchain_tx.block_index,
                    "blockchain_tx_id": blockchain_tx.id
                }
        
        # Check pending transactions
        for blockchain_tx in self.pending_transactions:
            if blockchain_tx.transaction_id == transaction_id:
                return {
                    "verified": True,
                    "status": "pending",
                    "blockchain_tx_id": blockchain_tx.id,
                    "position_in_queue": self.pending_transactions.index(blockchain_tx) + 1
                }
        
        return {
            "verified": False,
            "status": "not_found",
            "message": "Transaction not found on blockchain"
        }
    
    def validate_chain(self) -> bool:
        """Validate the entire blockchain."""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Check if current block's hash is valid
            if current_block.hash != self._calculate_hash(current_block):
                system_logger.error(f"Invalid hash at block {i}", self.agent_id)
                return False
            
            # Check if current block points to previous block
            if current_block.previous_hash != previous_block.hash:
                system_logger.error(f"Invalid previous hash at block {i}", self.agent_id)
                return False
        
        return True
    
    def process_message(self, message: Message):
        """Process blockchain-related messages."""
        if message.message_type == "blockchain_record_request":
            # Request to record a transaction on blockchain
            transaction_data = message.payload.get("transaction_data", {})
            
            system_logger.info(
                f"Recording transaction {transaction_data.get('transaction_id')} on blockchain",
                self.agent_id
            )
            
            # Create blockchain transaction
            blockchain_tx = self.create_blockchain_transaction(transaction_data)
            
            # Send response
            self.send_message(
                message.sender,
                "blockchain_record_response",
                {
                    "transaction_id": transaction_data.get("transaction_id"),
                    "blockchain_tx_id": blockchain_tx.id,
                    "status": "pending",
                    "message": "Transaction queued for blockchain recording"
                },
                correlation_id=message.correlation_id
            )
            
            # Auto-mine if we have enough pending transactions
            if len(self.pending_transactions) >= 5:
                self.mine_pending_transactions()
        
        elif message.message_type == "blockchain_verify_request":
            # Request to verify a transaction
            transaction_id = message.payload.get("transaction_id")
            
            verification_result = self.verify_transaction(transaction_id)
            
            self.send_message(
                message.sender,
                "blockchain_verify_response",
                {
                    "transaction_id": transaction_id,
                    **verification_result
                },
                correlation_id=message.correlation_id
            )
        
        elif message.message_type == "mine_block_request":
            # Manual request to mine pending transactions
            mined_block = self.mine_pending_transactions()
            
            if mined_block:
                self.send_message(
                    message.sender,
                    "block_mined",
                    {
                        "block_index": mined_block.index,
                        "block_hash": mined_block.hash,
                        "transactions_count": len(mined_block.transactions)
                    }
                )
    
    def get_blockchain_status(self) -> Dict[str, Any]:
        """Get current blockchain status."""
        total_transactions = sum(len(block.transactions) for block in self.chain)
        
        return {
            "chain_length": len(self.chain),
            "total_transactions": total_transactions,
            "pending_transactions": len(self.pending_transactions),
            "confirmed_transactions": len(self.confirmed_transactions),
            "latest_block_hash": self.chain[-1].hash if self.chain else None,
            "is_valid": self.validate_chain(),
            "difficulty": self.difficulty
        }
    
    def get_block_info(self, block_index: int) -> Optional[Dict[str, Any]]:
        """Get information about a specific block."""
        if 0 <= block_index < len(self.chain):
            block = self.chain[block_index]
            return {
                "index": block.index,
                "timestamp": block.timestamp.isoformat(),
                "transactions_count": len(block.transactions),
                "transactions": block.transactions,
                "previous_hash": block.previous_hash,
                "hash": block.hash,
                "nonce": block.nonce
            }
        return None