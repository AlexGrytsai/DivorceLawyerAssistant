import functools
import json
import threading
import time
from typing import Callable, List, Tuple, Optional, Dict

import psutil
from redis import Redis

from src.core.config import settings, redis_client_monitoring

# from src.utils.performance_monitoring import redis_client_monitoring

monitoring = False
ram_usage = []
ram_usage_results: Dict[str, List[Tuple[List[float], float]]] = {}


def save_data_to_usage_results(
    func_name: str,
    ram_data: Tuple[List[float], float],
    r_client: Optional[Redis] = None,
) -> None:
    if r_client:
        try:
            r_client.rpush(f"ram_usage_{func_name}", json.dumps(ram_data))
        except Exception as exc:
            # sourcery skip: raise-specific-error
            raise Exception(
                f"Failed to save RAM usage data to Redis: {exc}"
            ) from exc
    else:
        if func_name not in ram_usage_results:
            ram_usage_results[func_name] = []
        ram_usage_results[func_name].append(ram_data)


def monitor_ram_usage(interval: float = 0.1) -> None:
    local_ram_usage = []
    process = psutil.Process()
    while monitoring:
        local_ram_usage.append(process.memory_info().rss / 1024 / 1024)
        time.sleep(interval)
    ram_usage.extend(local_ram_usage)


def ram_monitor_decorator(
    r_client: Optional[Redis] = redis_client_monitoring,
    save_data: Optional[bool] = True,
    is_enabled: Optional[bool] = settings.DEBUG,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if not is_enabled:
                result = await func(*args, **kwargs)
                return result

            global monitoring, ram_usage

            ram_usage = []
            monitoring = True

            thread = threading.Thread(target=monitor_ram_usage, daemon=True)
            thread.start()

            try:
                start_time = time.perf_counter()
                result = await func(*args, **kwargs)
                end_time = time.perf_counter()
            finally:
                monitoring = False
                thread.join()
            if save_data:
                save_data_to_usage_results(
                    func_name=kwargs.get("func_name", func.__name__),
                    ram_data=(ram_usage, end_time - start_time),
                    r_client=r_client,
                )

            return result

        return wrapper

    return decorator
