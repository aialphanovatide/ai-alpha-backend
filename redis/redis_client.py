import json
import os
from typing import Any, Callable, TypeVar, cast
from functools import wraps

import redis
from redis import RedisError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Type variable for the decorated function
F = TypeVar('F', bound=Callable[..., Any])

# Configure Redis client using environment variables
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True
    )
    if redis_client.ping():
        print('Successfully connected to Redis')
    else:
        print('Failed to connect to Redis')
except RedisError as e:
    print(f'Error connecting to Redis: {e}')
    redis_client = None

def redis_cache(expire_time: int = 300):
    """
    Decorator for caching function results in Redis.

    Args:
        expire_time (int): Time in seconds for the cache to expire. Defaults to 300 seconds (5 minutes).

    Returns:
        Callable: Decorated function with caching capability.
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            if redis_client is None:
                return func(*args, **kwargs)

            # Create a unique cache key
            cache_key = f"{func.__module__}:{func.__name__}:{hash(str(args))}{hash(str(kwargs))}"

            try:
                # Try to get the cached result
                cached_result = redis_client.get(cache_key)
                if cached_result:
                    return json.loads(cached_result)

                # If not cached, call the function and cache the result
                result = func(*args, **kwargs)
                redis_client.setex(cache_key, expire_time, json.dumps(result))
                return result
            except (RedisError, json.JSONDecodeError) as e:
                print(f"Error in redis_cache: {e}")
                # If there's an error with Redis or JSON parsing, call the function without caching
                return func(*args, **kwargs)

        return cast(F, decorated_function)
    return decorator

# Example usage
@redis_cache(expire_time=60)
def example_function(param: str) -> dict:
    return {"result": f"Processed {param}"}

if __name__ == "__main__":
    # Test the cached function
    result1 = example_function("test")
    print("First call:", result1)

    result2 = example_function("test")
    print("Second call (should be cached):", result2)
