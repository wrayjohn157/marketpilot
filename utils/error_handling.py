        from pathlib import Path
        import json
from typing import Any, Callable, Optional, Type, Union
import logging

                        import time
import functools

"""Centralized error handling utilities for Market7."""

logger = logging.getLogger(__name__)

def safe_execute(
    func: Callable,
    *args,
    default_return: Any = None,
    exceptions: tuple = (Exception,),
    log_errors: bool = True,
    **kwargs
) -> Any:
    """Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        *args: Positional arguments for the function
        default_return: Value to return if function fails
        exceptions: Tuple of exception types to catch
        log_errors: Whether to log errors
        **kwargs: Keyword arguments for the function
        
    Returns:
        Function result or default_return if error occurs
    """
    try:
        return func(*args, **kwargs)
    except exceptions as e:
        if log_errors:
            logger.error(f"Error in {func.__name__}: {e}")
        return default_return

def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,),
    backoff_factor: float = 2.0
):
    """Decorator to retry function on failure.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        exceptions: Tuple of exception types to retry on
        backoff_factor: Multiplier for delay between retries
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay:.2f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}: {e}")
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    return decorator

def validate_required_keys(data: dict, required_keys: list, context: str = "") -> bool:
    """Validate that required keys exist in data dictionary.
    
    Args:
        data: Dictionary to validate
        required_keys: List of required keys
        context: Context for error messages
        
    Returns:
        True if all keys present, False otherwise
    """
    missing_keys = [key for key in required_keys if key not in data]
    if missing_keys:
        logger.error(f"Missing required keys in {context}: {missing_keys}")
        return False
    return True

def safe_json_loads(json_string: str, default: Any = None) -> Any:
    """Safely parse JSON string.
    
    Args:
        json_string: JSON string to parse
        default: Default value if parsing fails
        
    Returns:
        Parsed JSON or default value
    """
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse JSON: {e}")
        return default

def safe_file_read(file_path: Union[str, Path], default: str = "") -> str:
    """Safely read file contents.
    
    Args:
        file_path: Path to file to read
        default: Default content if file read fails
        
    Returns:
        File contents or default value
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except (IOError, OSError) as e:
        logger.warning(f"Failed to read file {file_path}: {e}")
        return default

def safe_file_write(file_path: Union[str, Path], content: str) -> bool:
    """Safely write content to file.
    
    Args:
        file_path: Path to file to write
        content: Content to write
        
    Returns:
        True if successful, False otherwise
    """
    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except (IOError, OSError) as e:
        logger.error(f"Failed to write file {file_path}: {e}")
        return False