"""
Configuration management for the Autonomous Trading Evolution Engine.
Centralizes all configuration with validation and type safety.
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
import yaml
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class FirebaseConfig:
    """Firebase configuration with validation"""
    credentials_path: str
    project_id: str
    
    def validate(self) -> bool:
        """Validate Firebase configuration"""
        if not os.path.exists(self.credentials_path):
            logger.error(f"Firebase credentials not found at {self.credentials_path}")
            return False
        if not self.project_id:
            logger.error("Firebase project ID not configured")
            return False
        return True

@dataclass
class TelegramConfig:
    """Telegram bot configuration"""
    bot_token: str
    chat_id: str
    
    def validate(self) -> bool:
        """Validate Telegram configuration"""
        if not self.bot_token or self.bot_token == "your_bot_token_here":
            logger.warning("Telegram bot token not configured")
            return False
        if not self.chat_id or self.chat_id == "your_chat_id_here":
            logger.warning("Telegram chat ID not configured")
            return False
        return True

@dataclass
class ResearchConfig:
    """Research engine configuration"""
    max_hypotheses_per_cycle: int = 5
    backtest_days: int = 365
    min_win_rate: float = 0.55
    max_drawdown: float = 0.2
    data_cache_hours: int = 1
    confidence_threshold: float = 0.7
    
    def validate(self) -> bool:
        """Validate research configuration"""
        if self.max_hypotheses_per_cycle <= 0:
            logger.error("max_hypotheses_per_cycle must be positive")
            return False
        if self.backtest_days < 30:
            logger.warning("backtest_days less than 30 may lead to unreliable results")
        return True

class ConfigManager:
    """Singleton configuration manager with validation and error handling"""
    
    _instance: Optional['ConfigManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Load configurations
        self.firebase = FirebaseConfig(
            credentials_path=os.getenv('FIREBASE_CREDENTIALS_PATH', './firebase-credentials.json'),
            project_id=os.getenv('FIREBASE_PROJECT_ID', '')
        )
        
        self.telegram = TelegramConfig(
            bot_token=os.getenv('TELEGRAM_BOT_TOKEN', ''),
            chat_id=os.getenv('TELEGRAM_CHAT_ID', '')
        )
        
        self.research = ResearchConfig(
            max_hypotheses_per_cycle=int(os.getenv('MAX_HYPOTHESES_PER_CYCLE', 5)),
            backtest_days=int(os.getenv('BACKTEST_DAYS', 365)),
            min_win_rate=float(os.getenv('MIN_WIN_RATE', 0.55)),
            max_drawdown=float(os.getenv('MAX_DRAWDOWN', 0.2))
        )
        
        # Exchange configurations
        self.exchanges = {
            'binance': {
                'api_key': os.getenv('BINANCE_API_KEY', ''),
                'api_secret': os.getenv('BINANCE_API_SECRET', '')
            },
            'coinbase': {
                'api_key': os.getenv('COINBASE_API_KEY', ''),
                'api_secret': os.getenv('COINBASE_API_SECRET', '')
            }
        }
        
        # Load YAML config if exists
        self._load_yaml_config()
        
        # Validate configurations
        self.validate()
        
        self._initialized = True
    
    def _load_yaml_config(self) -> None:
        """Load additional configuration from YAML file if exists"""
        yaml_path = './config.yaml'
        if os.path.exists(yaml_path):
            try:
                with open(yaml_path, 'r') as f:
                    yaml_config = yaml.safe_load(f)
                    # Merge with existing configs
                    if 'research' in yaml_config:
                        for key, value in yaml_config['research'].items():
                            if hasattr(self.research, key):
                                setattr(self.research, key, value)
            except Exception as e:
                logger.error(f"