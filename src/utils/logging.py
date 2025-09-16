"""
Basic logging utility for the FinTech multi-agent system.
"""
import logging
import sys
from datetime import datetime
from typing import Optional


class FinTechLogger:
    """Centralized logging for FinTech multi-agent system."""
    
    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Create console handler if not already exists
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(level)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def info(self, message: str, agent_id: Optional[str] = None):
        """Log info message."""
        prefix = f"[{agent_id}] " if agent_id else ""
        self.logger.info(f"{prefix}{message}")
    
    def warning(self, message: str, agent_id: Optional[str] = None):
        """Log warning message."""
        prefix = f"[{agent_id}] " if agent_id else ""
        self.logger.warning(f"{prefix}{message}")
    
    def error(self, message: str, agent_id: Optional[str] = None):
        """Log error message."""
        prefix = f"[{agent_id}] " if agent_id else ""
        self.logger.error(f"{prefix}{message}")
    
    def debug(self, message: str, agent_id: Optional[str] = None):
        """Log debug message."""
        prefix = f"[{agent_id}] " if agent_id else ""
        self.logger.debug(f"{prefix}{message}")


# Global logger instance
system_logger = FinTechLogger("FinTechSystem")