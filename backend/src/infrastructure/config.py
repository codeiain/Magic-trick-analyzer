"""
Configuration management for the Magic Trick Analyzer.
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str = "sqlite:///data/magic_tricks.db"
    echo: bool = False


@dataclass
class AIConfig:
    """AI model configuration."""
    sentence_transformer_model: str = "all-MiniLM-L6-v2"
    spacy_model: str = "en_core_web_sm"
    confidence_threshold: float = 0.6
    similarity_threshold: float = 0.7


@dataclass
class PDFConfig:
    """PDF processing configuration."""
    enable_ocr: bool = True
    watch_directories: List[str] = None
    upload_directory: str = "/app/uploads"
    
    def __post_init__(self):
        if self.watch_directories is None:
            self.watch_directories = ["/app/uploads"]


@dataclass
class APIConfig:
    """API configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    log_level: str = "info"
    cors_origins: List[str] = None
    
    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["*"]


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = "/app/logs/magic_analyzer.log"


class Config:
    """Main configuration class."""
    
    def __init__(self, config_file: Optional[str] = None):
        # Default configuration file path
        if config_file is None:
            config_file = os.getenv("CONFIG_FILE", "/app/config/config.yaml")
        
        self.config_file = config_file
        self._config_data = {}
        
        # Load configuration
        self._load_config()
        
        # Initialize configuration sections
        self.database = DatabaseConfig(**self._get_section("database", {}))
        self.ai = AIConfig(**self._get_section("ai", {}))
        self.pdf = PDFConfig(**self._get_section("pdf", {}))
        self.api = APIConfig(**self._get_section("api", {}))
        self.logging = LoggingConfig(**self._get_section("logging", {}))
    
    def _load_config(self):
        """Load configuration from file and environment variables."""
        # Start with defaults
        self._config_data = {}
        
        # Load from YAML file if it exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    file_config = yaml.safe_load(f) or {}
                    self._config_data.update(file_config)
            except Exception as e:
                print(f"Warning: Could not load config file {self.config_file}: {e}")
        
        # Override with environment variables
        self._load_env_overrides()
    
    def _load_env_overrides(self):
        """Load environment variable overrides."""
        env_mappings = {
            # Database
            "DATABASE_URL": ("database", "url"),
            "DATABASE_ECHO": ("database", "echo"),
            
            # AI
            "AI_MODEL": ("ai", "sentence_transformer_model"),
            "SPACY_MODEL": ("ai", "spacy_model"),
            "CONFIDENCE_THRESHOLD": ("ai", "confidence_threshold"),
            "SIMILARITY_THRESHOLD": ("ai", "similarity_threshold"),
            
            # PDF
            "ENABLE_OCR": ("pdf", "enable_ocr"),
            "WATCH_DIRECTORIES": ("pdf", "watch_directories"),
            "UPLOAD_DIRECTORY": ("pdf", "upload_directory"),
            
            # API
            "API_HOST": ("api", "host"),
            "API_PORT": ("api", "port"),
            "API_WORKERS": ("api", "workers"),
            "API_RELOAD": ("api", "reload"),
            "LOG_LEVEL": ("api", "log_level"),
            
            # Logging
            "LOG_FILE": ("logging", "file"),
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert types
                if key in ["echo", "enable_ocr", "reload"]:
                    value = value.lower() in ("true", "1", "yes", "on")
                elif key in ["port", "workers"]:
                    value = int(value)
                elif key in ["confidence_threshold", "similarity_threshold"]:
                    value = float(value)
                elif key == "watch_directories":
                    value = [d.strip() for d in value.split(",")]
                
                # Set in config
                if section not in self._config_data:
                    self._config_data[section] = {}
                self._config_data[section][key] = value
    
    def _get_section(self, section_name: str, default: Dict[str, Any]) -> Dict[str, Any]:
        """Get a configuration section with defaults."""
        section = self._config_data.get(section_name, {})
        return {**default, **section}
    
    def setup_logging(self):
        """Setup logging based on configuration."""
        # Create logs directory if it doesn't exist
        if self.logging.file:
            log_path = Path(self.logging.file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, self.logging.level.upper()),
            format=self.logging.format,
            handlers=[
                logging.StreamHandler(),  # Console output
                logging.FileHandler(self.logging.file) if self.logging.file else logging.NullHandler()
            ]
        )
    
    def get_database_url(self) -> str:
        """Get database URL with proper path handling."""
        if self.database.url.startswith("sqlite:///"):
            # Ensure data directory exists
            db_path = self.database.url.replace("sqlite:///", "")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        return self.database.url
    
    def validate(self) -> List[str]:
        """Validate configuration and return any issues."""
        issues = []
        
        # Validate AI configuration
        if self.ai.confidence_threshold < 0 or self.ai.confidence_threshold > 1:
            issues.append("AI confidence_threshold must be between 0 and 1")
        
        if self.ai.similarity_threshold < 0 or self.ai.similarity_threshold > 1:
            issues.append("AI similarity_threshold must be between 0 and 1")
        
        # Validate API configuration
        if self.api.port < 1 or self.api.port > 65535:
            issues.append("API port must be between 1 and 65535")
        
        if self.api.workers < 1:
            issues.append("API workers must be at least 1")
        
        # Validate directories exist or can be created
        for directory in self.pdf.watch_directories:
            try:
                Path(directory).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"Cannot access watch directory {directory}: {e}")
        
        return issues


# Global config instance
_config_instance = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def init_config(config_file: Optional[str] = None):
    """Initialize the global configuration."""
    global _config_instance
    _config_instance = Config(config_file)
    return _config_instance
