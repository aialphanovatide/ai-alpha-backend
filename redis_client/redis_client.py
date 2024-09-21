import json
from functools import wraps
from flask import request, Response, jsonify
import redis
import os

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True
)

try:
    if redis_client.ping():
        print('Successfully connected to Redis')
    else:
        print('Failed to connect to Redis')
except Exception as e:
    raise Exception(f'Error connecting to redis client: {str(e)}')


def cache_with_redis(expiration=300):
    """
    A decorator that caches the result of a function using Redis.

    This decorator is designed to be used with Flask route handlers. It caches the
    result of the decorated function based on the function name, request path, and
    query string. If cached data exists and hasn't expired, it's returned instead
    of calling the function. Otherwise, the function is called, and its result is
    cached before being returned.

    Args:
        expiration (int): The number of seconds the cached data should remain valid.
                          Defaults to 300 seconds (5 minutes).

    Returns:
        function: A decorated function that implements caching behavior.

    Usage:
        @app.route('/api/data')
        @cache_with_redis(expiration=600)
        def get_data():
            # Your data retrieval logic here
            return {'data': 'Some data'}
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{request.path}:{request.query_string.decode()}"
            
            # Try to get data from cache
            cached_data = redis_client.get(cache_key)
            if cached_data:
                cached_response = json.loads(cached_data)
                return jsonify(cached_response['data']), cached_response['status']
            
            # If not in cache, call the original function
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                # Handle the exception and return an error response
                return jsonify({'error': str(e)}), 500
            
            
            # Prepare the result for caching
            if isinstance(result, tuple) and len(result) == 2:
                response_data, status_code = result
                if isinstance(response_data, Response):
                    response_data = json.loads(response_data.get_data(as_text=True))
            elif isinstance(result, Response):
                response_data = json.loads(result.get_data(as_text=True))
                status_code = result.status_code
            else:
                response_data = result
                status_code = 200
            
            cache_data = json.dumps({
                'data': response_data,
                'status': status_code
            })
            
            # Cache the result
            redis_client.setex(cache_key, expiration, cache_data)
            
            return jsonify(response_data), status_code
        return wrapper
    return decorator


def cache_with_redis_raw_data(expiration=300):
    """
    A decorator that caches the result of a function using Redis.

    This decorator is designed to be used with Flask route handlers. It caches the
    result of the decorated function based on the function name, request path, and
    query string. If cached data exists and hasn't expired, it's returned instead
    of calling the function. Otherwise, the function is called, and its result is
    cached before being returned.

    Args:
        expiration (int): The number of seconds the cached data should remain valid.
                          Defaults to 300 seconds (5 minutes).

    Returns:
        function: A decorated function that implements caching behavior.

    Usage:
        @app.route('/api/data')
        @cache_with_redis(expiration=600)
        def get_data():
            # Your data retrieval logic here
            return {'data': 'Some data'}
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{request.path}:{request.query_string.decode()}"
            
            # Try to get data from cache
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            
            # If not in cache, call the original function
            result = func(*args, **kwargs)
            
            # Cache the result
            redis_client.setex(cache_key, expiration, json.dumps(result))
            
            return result
        return wrapper
    return decorator