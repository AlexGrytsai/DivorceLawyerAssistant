import json
import logging
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

from src.utils.performance_monitoring import redis_client_monitoring

logger = logging.getLogger(__name__)


def load_usage_data_from_redis(key_prefix: str):
    try:
        if redis_client_monitoring:
            redis_keys = redis_client_monitoring.keys(f"{key_prefix}*")
            return {
                key: [
                    json.loads(value)
                    for value in redis_client_monitoring.lrange(  # type: ignore # noqa
                        key, 0, -1
                    )
                ]
                for key in redis_keys  # type: ignore
            }
    except Exception as exc:
        # sourcery skip: raise-specific-error
        raise Exception(
            f"Failed to load RAM usage data from Redis: {exc}"
        ) from exc


def determine_limit_on_axis_y(
    resource_data: Dict[str, List[Tuple[List[float], float]]],
    y_limit: float,
    is_cpu: bool = False,
) -> float:
    return (
        y_limit
        if y_limit != 0
        else (
            100
            if is_cpu
            else 1.1
            * max(
                max(max(run[0], default=0) for run in data) if data else 0
                for data in resource_data.values()
            )
        )
    )


def determine_min_on_axis_y(
    resource_data: Dict[str, List[Tuple[List[float], float]]],
    is_cpu: bool = False,
) -> float:
    return (
        0
        if is_cpu
        else 0.9
        * min(
            min(min(run[0], default=0) for run in data) if data else 0
            for data in resource_data.values()
        )
    )


def preparation_of_graphs(
    func_name: str,
    runs: List[Tuple[List[float], float]],
    is_cpu: bool,
) -> list[Line2D] | None:
    all_resource_usages = [run[0] for run in runs]
    exec_times = [run[1] for run in runs]

    max_length = max(map(len, all_resource_usages), default=0)
    if max_length == 0:
        return None

    avg_resource_usage = []
    avg_resource_usage.extend(
        np.average([data[i] for data in all_resource_usages if i < len(data)])
        for i in range(max_length)
    )
    avg_exec_time = np.mean(exec_times)
    x_values = np.linspace(0, np.mean(exec_times), len(avg_resource_usage))

    median_resource = np.median(
        [np.median(run) for run in all_resource_usages]
    )
    max_resource = np.max(avg_resource_usage) if avg_resource_usage else 0
    min_resource = np.min(avg_resource_usage) if avg_resource_usage else 0

    if is_cpu:
        percentile_99 = np.percentile(
            [value for run in all_resource_usages for value in run], 99
        )
        label = (
            f"{func_name} (Exec Time: {avg_exec_time:.2f}s, "
            f"Median: {median_resource:.2f}%, P99: {percentile_99:.2f}%, "
            f"Peak: {max_resource:.2f}%)"
        )
    else:
        label = (
            f"{func_name} (Min: {min_resource:.2f} MB, "
            f"Max: {max_resource:.2f} MB, "
            f"Delta: {max_resource - min_resource:.2f} MB"
        )

    return plt.plot(
        x_values,
        avg_resource_usage,
        label=label,
    )


def plot_resource_usage(
    resource_data: Dict[str, List[Tuple[List[float], float]]],
    title: str,
    y_label: str,
    y_limit: float,
    detailing: int = 10,
    is_cpu: bool = False,
) -> None:
    plt.figure(figsize=(10, 6))

    y_limit = determine_limit_on_axis_y(resource_data, y_limit, is_cpu)

    min_y = determine_min_on_axis_y(resource_data, is_cpu)

    for func_name, runs in resource_data.items():
        if not runs:
            continue

        preparation_of_graphs(func_name=func_name, runs=runs, is_cpu=is_cpu)

    plt.title(title)
    plt.xlabel("Time (seconds)")
    plt.ylabel(y_label)
    plt.ylim(min_y, y_limit)
    plt.yticks(np.linspace(min_y, y_limit, detailing))
    plt.grid(True)
    plt.legend(loc="center", bbox_to_anchor=(0.5, -0.3))
    plt.subplots_adjust(bottom=0.3)
    plt.draw()
    plt.show()


def plot_combined_ram_graph(
    ram_data: Dict[str, List[Tuple[List[float], float]]],
    y_limit: float = 0,
    detailing: int = 10,
) -> None:
    plot_resource_usage(
        ram_data,
        title="RAM Usage Comparison",
        y_label="RAM Usage (MB)",
        y_limit=y_limit,
        detailing=detailing,
        is_cpu=False,
    )


def plot_combined_graph_for_cpu(
    cpu_data: Dict[str, List[Tuple[List[float], float]]],
) -> None:
    plot_resource_usage(
        cpu_data,
        title="CPU Usage Comparison",
        y_label="CPU Usage (%)",
        y_limit=100,
        detailing=20,
        is_cpu=True,
    )


def show_graphs():
    data_for_ram_graph = load_usage_data_from_redis(key_prefix="ram_usage_")
    data_for_cpu_graph = load_usage_data_from_redis(key_prefix="cpu_usage_")

    try:
        plot_combined_ram_graph(ram_data=data_for_ram_graph)
    except Exception as exc:
        logger.warning(f"Failed to plot RAM usage graph: {exc}")

    try:
        plot_combined_graph_for_cpu(cpu_data=data_for_cpu_graph)
    except Exception as exc:
        logger.warning(f"Failed to plot CPU usage graph: {exc}")


if __name__ == "__main__":
    show_graphs()
