import json
from pathlib import Path


BASE_DIR = Path("/home/ec2-user/ebs-project")
DATA_FILE = BASE_DIR / "data" / "ebs-volume-knowledge.json"


def load_benchmark_data():
    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    volumes = data["volume_types"]

    workloads = {
        "random_read": "Random Read",
        "random_write": "Random Write",
        "sequential_read": "Sequential Read",
        "sequential_write": "Sequential Write",
        "mixed_70_30": "Mixed 70/30"
    }

    dashboard = {}

    for workload_key, workload_name in workloads.items():

        gp2 = volumes["gp2"]["benchmark"][workload_key]
        gp3 = volumes["gp3"]["benchmark"][workload_key]

        if workload_key == "mixed_70_30":

            dashboard[workload_key] = {
                "name": workload_name,
                "type": "mixed",
                "gp2": gp2,
                "gp3": gp3
            }

        else:

            dashboard[workload_key] = {
                "name": workload_name,
                "type": "standard",
                "gp2": gp2,
                "gp3": gp3
            }

    return dashboard


def print_standard_workload(values):

    for volume in ["gp2", "gp3"]:

        result = values[volume]

        print(f"  {volume}:")

        print(
            f"    IOPS: "
            f"{result.get('iops', 'N/A')}"
        )

        print(
            f"    Throughput: "
            f"{result.get('throughput_mib_s', 'N/A')} MiB/s"
        )

        print(
            f"    Average Latency: "
            f"{result.get('avg_latency_ms', 'N/A')} ms"
        )

        print(
            f"    P95: "
            f"{result.get('p95_ms', 'N/A')} ms"
        )

        print(
            f"    P99: "
            f"{result.get('p99_ms', 'N/A')} ms"
        )


def print_mixed_workload(values):

    for volume in ["gp2", "gp3"]:

        result = values[volume]

        print(f"  {volume}:")

        print(
            f"    Read IOPS: "
            f"{result['read_iops']}"
        )

        print(
            f"    Write IOPS: "
            f"{result['write_iops']}"
        )

        print(
            f"    Total IOPS: "
            f"{result['total_iops']}"
        )

        print(
            f"    Read Throughput: "
            f"{result['read_throughput_mib_s']} MiB/s"
        )

        print(
            f"    Write Throughput: "
            f"{result['write_throughput_mib_s']} MiB/s"
        )

        print(
            f"    Read Average Latency: "
            f"{result['read_avg_latency_ms']} ms"
        )

        print(
            f"    Write Average Latency: "
            f"{result['write_avg_latency_ms']} ms"
        )


if __name__ == "__main__":

    data = load_benchmark_data()

    print("========================================")
    print("BENCHMARK DASHBOARD DATA")
    print("========================================")

    for workload, values in data.items():

        print(f"\n{values['name']}")

        if values["type"] == "mixed":
            print_mixed_workload(values)
        else:
            print_standard_workload(values)
