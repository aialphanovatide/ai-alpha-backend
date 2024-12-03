import json
from functools import wraps
from flask import request, Response, jsonify
import redis
import os

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

redis_client_args = {
    'host': REDIS_HOST,
    'port': REDIS_PORT,
    'db': REDIS_DB,
    'decode_responses': True
}

if REDIS_PASSWORD:
    redis_client_args['password'] = REDIS_PASSWORD

redis_client = redis.Redis(**redis_client_args)
redis_client.ping()
print("---- Redis client connected ----")


def reset_redis_cache():
   """
   Cleans the entire Redis cache by deleting all keys in the current database.
   
   Returns:
       tuple: A tuple containing a message and HTTP status code.
       
   Usage:
       result = reset_redis_cache()
       # Returns ({'message': 'Redis cache cleared successfully'}, 200)
   """
   try:
       redis_client.flushdb()
       return {'message': 'Redis cache cleared successfully'}, 200
   except Exception as e:
       return {'error': f'Failed to clear Redis cache: {str(e)}'}, 500


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


def update_cache_with_redis(related_get_endpoints=[]):
    """
    A decorator that clears the cache for related GET endpoints after a successful request.

    This decorator is designed to be used with functions that modify data that is cached using Redis.
    It clears the cache for all related GET endpoints after a successful request (2xx status code).

    Args:
        related_get_endpoints (list): A list of related GET endpoints to clear the cache for.
                                     For example: ['/api/data', '/api/users'].

    Returns:
        function: A decorated function that implements cache clearing behavior.

    Usage:
        @app.route('/api/update_data', methods=['POST'])
        @update_cache_with_redis(related_get_endpoints=['/api/data'])
        def update_data():
            # Your data update logic here
            return {'message': 'Data updated successfully'}, 200
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # Check if the request was successful
                if isinstance(result, tuple):
                    status_code = result[1]
                elif isinstance(result, Response):
                    status_code = result.status_code
                else:
                    status_code = 200  # Assume success if no status code is provided
                
                # Only clear cache if the request was successful (2xx status codes)
                if 200 <= status_code < 300:
                    for endpoint in related_get_endpoints:
                        cache_pattern = f"{endpoint}:*"
                        for key in redis_client.scan_iter(match=cache_pattern):
                            redis_client.delete(key)
                
                return result
            
            except Exception as e:
                # If an exception occurs, don't clear the cache
                # You might want to log the error here
                return jsonify({'error': str(e)}), 500
        
        return wrapper
    return decorator