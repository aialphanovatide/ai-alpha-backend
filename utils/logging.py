import logging

def setup_logger(name: str) -> logging.Logger:
    """Set up a logger with a specified name."""
    logger = logging.getLogger(name)
    
    # Configure the logger if it hasn't been configured yet
    if not logger.handlers:
        # Create console handler
        handler = logging.StreamHandler()
        
        # Create a custom formatter
        formatter = logging.Formatter(
            '[%(levelname)s] %(message)s'
        )
        
        # Add formatter to handler
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
        
        # Set level to INFO by default
        logger.setLevel(logging.INFO)
    
    return logger

