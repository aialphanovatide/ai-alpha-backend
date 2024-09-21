from functools import wraps
import time

def measure_execution_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        print(f"\n-- Endpoint '{func.__name__}' took {execution_time:.4f} seconds to execute --")
        return result
    return wrapper