import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

sys.path.insert(0, str(Path(__file__).parent))

from benchmark_analyzer import normalize_result


def get_benchmark_evidence(volume_type, workload):
    """
    Return measured benchmark evidence for a volume/workload.
    """

    result = normalize_result(
        volume_type,
        workload
    )

    if not result.get("available", False):
        return {
            "available": False,
            "volume": volume_type,
            "workload": workload,
            "message": "No measured benchmark data is available."
        }

    evidence = {
        "available": True,
        "volume": volume_type,
        "workload": workload,
        "source": "Controlled AWS fio benchmark",
        "environment": {
            "instance": "t3.micro",
            "region": "ap-south-1",
            "availability_zone": "ap-south-1b",
            "volume_size_gib": 20
        }
    }

    # --------------------------------------------------------
    # Normal workloads
    # --------------------------------------------------------

    if "iops" in result:

        evidence["metrics"] = {
            "iops": result["iops"],
            "throughput_mib_s": result["throughput_mib_s"],
            "avg_latency_ms": result["avg_latency_ms"],
            "p95_ms": result["p95_ms"],
            "p99_ms": result["p99_ms"]
        }

    # --------------------------------------------------------
    # Mixed workload
    # --------------------------------------------------------

    elif "total_iops" in result:

        evidence["metrics"] = {
            "read_iops": result["read_iops"],
            "write_iops": result["write_iops"],
            "total_iops": result["total_iops"],
            "read_throughput_mib_s": result[
                "read_throughput_mib_s"
            ],
            "write_throughput_mib_s": result[
                "write_throughput_mib_s"
            ],
            "read_avg_latency_ms": result[
                "read_avg_latency_ms"
            ],
            "write_avg_latency_ms": result[
                "write_avg_latency_ms"
            ]
        }

    return evidence


def compare_measured_performance(
    workload,
    volume_a="gp2",
    volume_b="gp3"
):
    """
    Compare measured performance between two tested volumes.
    """

    a = get_benchmark_evidence(
        volume_a,
        workload
    )

    b = get_benchmark_evidence(
        volume_b,
        workload
    )

    result = {
        "workload": workload,
        volume_a: a,
        volume_b: b,
        "observed_difference": {}
    }

    if not a["available"] or not b["available"]:
        return result

    metrics_a = a["metrics"]
    metrics_b = b["metrics"]

    # --------------------------------------------------------
    # Normal workload
    # --------------------------------------------------------

    if "iops" in metrics_a and "iops" in metrics_b:

        result["observed_difference"] = {

            "iops": (
                metrics_b["iops"]
                - metrics_a["iops"]
            ),

            "throughput_mib_s": round(
                metrics_b["throughput_mib_s"]
                - metrics_a["throughput_mib_s"],
                2
            ),

            "avg_latency_ms": round(
                metrics_b["avg_latency_ms"]
                - metrics_a["avg_latency_ms"],
                3
            ),

            "p95_ms": round(
                metrics_b["p95_ms"]
                - metrics_a["p95_ms"],
                3
            ),

            "p99_ms": round(
                metrics_b["p99_ms"]
                - metrics_a["p99_ms"],
                3
            )
        }

    # --------------------------------------------------------
    # Mixed workload
    # --------------------------------------------------------

    elif "total_iops" in metrics_a:

        result["observed_difference"] = {

            "total_iops": (
                metrics_b["total_iops"]
                - metrics_a["total_iops"]
            ),

            "read_iops": (
                metrics_b["read_iops"]
                - metrics_a["read_iops"]
            ),

            "write_iops": (
                metrics_b["write_iops"]
                - metrics_a["write_iops"]
            ),

            "read_latency_ms": round(
                metrics_b["read_avg_latency_ms"]
                - metrics_a["read_avg_latency_ms"],
                3
            ),

            "write_latency_ms": round(
                metrics_b["write_avg_latency_ms"]
                - metrics_a["write_avg_latency_ms"],
                3
            )
        }

    return result


def evidence_summary(
    workload,
    volume_type
):
    """
    Generate a human-readable benchmark summary.
    """

    evidence = get_benchmark_evidence(
        volume_type,
        workload
    )

    if not evidence["available"]:
        return (
            f"No measured benchmark evidence is available "
            f"for {volume_type}."
        )

    metrics = evidence["metrics"]

    if "iops" in metrics:

        return (
            f"{volume_type} measured "
            f"{metrics['iops']} IOPS, "
            f"{metrics['throughput_mib_s']} MiB/s throughput, "
            f"{metrics['avg_latency_ms']} ms average latency, "
            f"{metrics['p95_ms']} ms P95, and "
            f"{metrics['p99_ms']} ms P99."
        )

    return (
        f"{volume_type} measured "
        f"{metrics['total_iops']} total IOPS "
        f"for the mixed workload, with "
        f"{metrics['read_iops']} read IOPS and "
        f"{metrics['write_iops']} write IOPS."
    )


if __name__ == "__main__":

    workloads = [
        "random_read",
        "random_write",
        "sequential_read",
        "sequential_write",
        "mixed"
    ]

    for workload in workloads:

        print("\n========================================")
        print(f"BENCHMARK EVIDENCE: {workload}")
        print("========================================")

        print(
            evidence_summary(
                workload,
                "gp2"
            )
        )

        print(
            evidence_summary(
                workload,
                "gp3"
            )
        )

        comparison = compare_measured_performance(
            workload
        )

        print("\nObserved difference (gp3 - gp2):")

        for key, value in comparison[
            "observed_difference"
        ].items():

            print(
                f"  {key}: {value}"
            )
