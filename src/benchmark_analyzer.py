import json
from pathlib import Path


# ============================================================
# PATH
# ============================================================

DATA_FILE = (
    Path(__file__).parent.parent
    / "data"
    / "ebs-volume-knowledge.json"
)


# ============================================================
# LOAD DATA
# ============================================================

def load_knowledge_base():

    with open(DATA_FILE, "r") as file:
        return json.load(file)


# ============================================================
# WORKLOAD NAME
# ============================================================

def workload_key(workload):

    mapping = {

        "random_read":
            "random_read",

        "random_write":
            "random_write",

        "sequential_read":
            "sequential_read",

        "sequential_write":
            "sequential_write",

        "mixed":
            "mixed_70_30"
    }

    if workload not in mapping:

        raise ValueError(
            f"Unsupported workload: {workload}"
        )

    return mapping[workload]


# ============================================================
# GET BENCHMARK
# ============================================================

def get_benchmark(
    volume_type,
    workload
):

    data = load_knowledge_base()

    volumes = data["volume_types"]

    if volume_type not in volumes:

        raise ValueError(
            f"Unknown volume type: {volume_type}"
        )

    benchmark = volumes[
        volume_type
    ].get(
        "benchmark"
    )

    if not benchmark:

        return None


    key = workload_key(workload)

    return benchmark.get(key)


# ============================================================
# NORMALIZE RESULTS
# ============================================================

def normalize_result(
    volume_type,
    workload
):

    result = get_benchmark(
        volume_type,
        workload
    )


    if result is None:

        return {

            "volume":
                volume_type,

            "workload":
                workload,

            "available":
                False
        }


    normalized = {

        "volume":
            volume_type,

        "workload":
            workload,

        "available":
            True
    }


    # --------------------------------------------------------
    # Random / Sequential
    # --------------------------------------------------------

    if "iops" in result:

        normalized["iops"] = (
            result["iops"]
        )

        normalized["throughput_mib_s"] = (
            result["throughput_mib_s"]
        )

        normalized["avg_latency_ms"] = (
            result["avg_latency_ms"]
        )

        normalized["p95_ms"] = (
            result["p95_ms"]
        )

        normalized["p99_ms"] = (
            result["p99_ms"]
        )


    # --------------------------------------------------------
    # Mixed workload
    # --------------------------------------------------------

    elif "total_iops" in result:

        normalized["read_iops"] = (
            result["read_iops"]
        )

        normalized["write_iops"] = (
            result["write_iops"]
        )

        normalized["total_iops"] = (
            result["total_iops"]
        )

        normalized["read_throughput_mib_s"] = (
            result["read_throughput_mib_s"]
        )

        normalized["write_throughput_mib_s"] = (
            result["write_throughput_mib_s"]
        )

        normalized["read_avg_latency_ms"] = (
            result["read_avg_latency_ms"]
        )

        normalized["write_avg_latency_ms"] = (
            result["write_avg_latency_ms"]
        )


    return normalized


# ============================================================
# COMPARE GP2 AND GP3
# ============================================================

def compare_gp2_gp3(
    workload
):

    gp2 = normalize_result(
        "gp2",
        workload
    )

    gp3 = normalize_result(
        "gp3",
        workload
    )


    result = {

        "workload":
            workload,

        "gp2":
            gp2,

        "gp3":
            gp3,

        "comparison":
            {}
    }


    if not (
        gp2["available"]
        and gp3["available"]
    ):

        return result


    # --------------------------------------------------------
    # Normal workloads
    # --------------------------------------------------------

    if "iops" in gp2:

        result["comparison"]["iops_difference"] = (
            gp3["iops"]
            - gp2["iops"]
        )


        result["comparison"][
            "iops_difference_percent"
        ] = round(

            (
                (
                    gp3["iops"]
                    - gp2["iops"]
                )
                / gp2["iops"]
            )
            * 100,

            2
        )


        result["comparison"][
            "throughput_difference_mib_s"
        ] = round(

            gp3["throughput_mib_s"]
            - gp2["throughput_mib_s"],

            2
        )


        result["comparison"][
            "avg_latency_difference_ms"
        ] = round(

            gp3["avg_latency_ms"]
            - gp2["avg_latency_ms"],

            3
        )


        result["comparison"][
            "p95_difference_ms"
        ] = round(

            gp3["p95_ms"]
            - gp2["p95_ms"],

            3
        )


        result["comparison"][
            "p99_difference_ms"
        ] = round(

            gp3["p99_ms"]
            - gp2["p99_ms"],

            3
        )


    # --------------------------------------------------------
    # Mixed workload
    # --------------------------------------------------------

    elif "total_iops" in gp2:

        result["comparison"][
            "total_iops_difference"
        ] = (
            gp3["total_iops"]
            - gp2["total_iops"]
        )


        result["comparison"][
            "read_iops_difference"
        ] = (
            gp3["read_iops"]
            - gp2["read_iops"]
        )


        result["comparison"][
            "write_iops_difference"
        ] = (
            gp3["write_iops"]
            - gp2["write_iops"]
        )


        result["comparison"][
            "read_latency_difference_ms"
        ] = round(

            gp3["read_avg_latency_ms"]
            - gp2["read_avg_latency_ms"],

            3
        )


        result["comparison"][
            "write_latency_difference_ms"
        ] = round(

            gp3["write_avg_latency_ms"]
            - gp2["write_avg_latency_ms"],

            3
        )


    return result


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    workloads = [

        "random_read",
        "random_write",
        "sequential_read",
        "sequential_write",
        "mixed"
    ]


    for workload in workloads:

        print(
            "\n========================================"
        )

        print(
            f"WORKLOAD: {workload}"
        )

        print(
            "========================================"
        )


        result = compare_gp2_gp3(
            workload
        )


        print(
            json.dumps(
                result,
                indent=4
            )
        )
