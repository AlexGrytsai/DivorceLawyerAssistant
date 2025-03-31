import functools
import json
import threading
import time
from typing import Callable, List, Tuple, Optional, Dict

import psutil
from redis import Redis

from src.core.config import settings, redis_client_monitoring

# from src.utils.performance_monitoring import redis_client_monitoring

running = False
cpu_usage_data = []
cpu_usage_results: Dict[str, List[Tuple[List[float], float]]] = {}


def monitor_cpu_usage(interval: float = 0.1):
    global running, cpu_usage_data
    local_cpu_usage = []

    psutil.cpu_percent(interval=None)
    while running:
        local_cpu_usage.append(psutil.cpu_percent(interval=interval))

    cpu_usage_data.extend(local_cpu_usage)


def save_data_to_usage_results(
    func_name: str,
    cpu_data: Tuple[List[float], float],
    r_client: Optional[Redis] = None,
) -> None:
    if r_client:
        try:
            r_client.rpush(f"cpu_usage_{func_name}", json.dumps(cpu_data))
        except Exception as exc:
            # sourcery skip: raise-specific-error
            raise Exception(
                f"Failed to save CPU usage data to Redis: {exc}"
            ) from exc
    else:
        if func_name not in cpu_usage_results:
            cpu_usage_results[func_name] = []
        cpu_usage_results[func_name].append(cpu_data)


def cpu_monitor_decorator(
    save_data: bool = True,
    is_enabled: bool = settings.DEBUG,
    r_client: Optional[Redis] = redis_client_monitoring,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if not is_enabled:
                result = await func(*args, **kwargs)
                return result

            global running, cpu_usage_data

            cpu_usage_data = []
            running = True
            cpu_thread = threading.Thread(
                target=monitor_cpu_usage, daemon=True
            )
            cpu_thread.start()

            start_time = time.perf_counter()
            result = await func(*args, **kwargs)
            end_time = time.perf_counter()

            running = False

            cpu_thread.join()

            if save_data:
                save_data_to_usage_results(
                    func_name=kwargs.get("func_name", func.__name__),
                    cpu_data=(cpu_usage_data, end_time - start_time),
                    r_client=r_client,
                )

            return result

        return wrapper

    return decorator
