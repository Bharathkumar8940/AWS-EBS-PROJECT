from flask import Flask, render_template, request
import sys

sys.path.append("/home/ec2-user/ebs-project/src")

from recommendation_engine import recommend
from benchmark_dashboard import load_benchmark_data


app = Flask(__name__)


# ============================================================
# MAIN RECOMMENDATION PAGE
# ============================================================

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    dashboard_url = None

    if request.method == "POST":
        workload = request.form["workload"]
        iops = int(request.form["iops"])
        throughput = float(request.form["throughput"])
        latency = request.form["latency"]
        capacity = float(request.form["capacity"])

        result = recommend(
            workload=workload,
            required_iops=iops,
            required_throughput=throughput,
            latency_sensitivity=latency,
            capacity_gib=capacity
        )

        dashboard_url = (
            "/dashboard?"
            f"workload={workload}"
            f"&iops={iops}"
            f"&throughput={throughput}"
            f"&latency={latency}"
            f"&capacity={capacity}"
        )

    return render_template(
        "index.html",
        result=result,
        dashboard_url=dashboard_url
    )

# ============================================================
# BENCHMARK DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():
    benchmark_data = load_benchmark_data()

    workload = request.args.get("workload")

    workload_groups = {
        "random": [
            "random_read",
            "random_write"
        ],
        "sequential": [
            "sequential_read",
            "sequential_write"
        ],
        "mixed": [
            "mixed_70_30"
        ]
    }

    selected_workloads = workload_groups.get(workload, [])

    selected_benchmark_data = {
        key: benchmark_data[key]
        for key in selected_workloads
        if key in benchmark_data
    }

    return render_template(
        "dashboard.html",
        benchmark_data=benchmark_data,
        selected_benchmark_data=selected_benchmark_data,
        workload=workload,
        required_iops=request.args.get("iops"),
        required_throughput=request.args.get("throughput"),
        latency_sensitivity=request.args.get("latency"),
        capacity_gib=request.args.get("capacity")
    )

# ============================================================
# APPLICATION START
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
