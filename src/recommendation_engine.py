import json
import sys
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).parent.parent

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "ebs-volume-knowledge.json"
)


# ============================================================
# IMPORT PROJECT MODULES
# ============================================================

sys.path.insert(
    0,
    str(Path(__file__).parent)
)


from cost_model import calculate_cost

from benchmark_evidence import (
    get_benchmark_evidence
)

from decision_engine import (
    rank_candidates,
    explain_decision
)

from instance_config import (
    get_instance_profile
)


# ============================================================
# LOAD KNOWLEDGE BASE
# ============================================================

def load_knowledge_base():

    with open(DATA_FILE, "r") as file:

        return json.load(file)


# ============================================================
# WORKLOAD MATCHING
# ============================================================

def workload_matches(
    volume,
    workload
):

    workload_classes = volume.get(
        "workload_classes",
        []
    )

    access_patterns = volume.get(
        "access_patterns",
        []
    )


    if workload == "random":

        return (
            "random_io" in workload_classes
            or
            "high_iops" in workload_classes
            or
            "random" in access_patterns
        )


    elif workload == "sequential":

        return (
            "sequential"
            in access_patterns
        )


    elif workload == "mixed":

        return (
            "mixed_io" in workload_classes
            or
            "mixed" in access_patterns
        )


    elif workload == "general":

        return (
            "general_purpose"
            in workload_classes
        )


    return False


# ============================================================
# CAPACITY MATCHING
# ============================================================

def capacity_matches(
    volume,
    capacity_gib
):

    min_size = volume.get(
        "min_size_gib",
        0
    )

    max_size = volume.get(
        "max_size_gib",
        float("inf")
    )

    return (
        min_size
        <= capacity_gib
        <= max_size
    )


# ============================================================
# PROVISIONING
# ============================================================

def calculate_provisioning(
    volume_name,
    volume,
    required_iops,
    required_throughput,
    capacity_gib
):

    result = {

        "required_iops":
            required_iops,

        "required_throughput_mib_s":
            required_throughput,

        "provisioned_iops":
            None,

        "provisioned_throughput_mib_s":
            None
    }


    # --------------------------------------------------------
    # GP2
    # --------------------------------------------------------

    if volume_name == "gp2":

        baseline_iops = max(
            100,
            min(
                3 * capacity_gib,
                16000
            )
        )

        result[
            "provisioned_iops"
        ] = baseline_iops

        result[
            "provisioned_throughput_mib_s"
        ] = volume.get(
            "max_throughput_mib_s",
            250
        )

        return result


    # --------------------------------------------------------
    # GP3
    # --------------------------------------------------------

    if volume_name == "gp3":

        baseline_iops = volume.get(
            "baseline_iops",
            3000
        )

        baseline_throughput = volume.get(
            "baseline_throughput_mib_s",
            125
        )

        result[
            "provisioned_iops"
        ] = max(
            baseline_iops,
            required_iops
        )

        result[
            "provisioned_throughput_mib_s"
        ] = max(
            baseline_throughput,
            required_throughput
        )

        return result


    # --------------------------------------------------------
    # IO2
    # --------------------------------------------------------

    if volume_name == "io2":

        min_iops = volume.get(
            "min_iops",
            100
        )

        result[
            "provisioned_iops"
        ] = max(
            min_iops,
            required_iops
        )

        result[
            "provisioned_throughput_mib_s"
        ] = required_throughput

        return result


    # --------------------------------------------------------
    # ST1
    # --------------------------------------------------------

    if volume_name == "st1":

        result[
            "provisioned_iops"
        ] = required_iops

        result[
            "provisioned_throughput_mib_s"
        ] = required_throughput

        return result


    # --------------------------------------------------------
    # SC1
    # --------------------------------------------------------

    if volume_name == "sc1":

        result[
            "provisioned_iops"
        ] = required_iops

        result[
            "provisioned_throughput_mib_s"
        ] = required_throughput

        return result


    return result


# ============================================================
# SUPPORTED IOPS
# ============================================================

def get_supported_iops(
    volume_name,
    volume,
    capacity_gib
):

    if volume_name == "gp2":

        return max(
            100,
            min(
                3 * capacity_gib,
                16000
            )
        )


    elif volume_name == "gp3":

        return volume.get(
            "max_iops",
            80000
        )


    elif volume_name == "io2":

        return volume.get(
            "max_iops",
            256000
        )


    elif volume_name in [
        "st1",
        "sc1"
    ]:

        return float("inf")


    return volume.get(
        "max_iops",
        0
    )


# ============================================================
# IOPS MATCHING
# ============================================================

def iops_matches(
    volume_name,
    volume,
    required_iops,
    capacity_gib
):

    supported_iops = get_supported_iops(
        volume_name,
        volume,
        capacity_gib
    )

    return (
        required_iops
        <= supported_iops
    )


# ============================================================
# THROUGHPUT MATCHING
# ============================================================

def throughput_matches(
    volume,
    required_throughput
):

    max_throughput = volume.get(
        "max_throughput_mib_s"
    )


    if max_throughput is None:

        return True


    return (
        required_throughput
        <= max_throughput
    )


# ============================================================
# LATENCY MATCHING
# ============================================================

def latency_matches(
    volume,
    latency_sensitivity
):

    latency_class = volume.get(
        "latency_class",
        "unknown"
    )


    if latency_sensitivity == "very_high":

        return (
            latency_class
            == "very_low"
        )


    elif latency_sensitivity == "high":

        return latency_class in [
            "very_low",
            "low"
        ]


    elif latency_sensitivity == "medium":

        return latency_class in [
            "very_low",
            "low",
            "higher"
        ]


    elif latency_sensitivity == "low":

        return True


    return True


# ============================================================
# BENCHMARK WORKLOAD MAPPING
# ============================================================

def get_benchmark_workload(
    workload
):

    mapping = {

        "random":
            "random_read",

        "sequential":
            "sequential_read",

        "mixed":
            "mixed",

        "general":
            "random_read"
    }


    return mapping.get(
        workload
    )


# ============================================================
# EXPLANATION
# ============================================================

def generate_explanation(
    selected,
    workload,
    required_iops,
    required_throughput,
    latency_sensitivity,
    capacity_gib,
    provisioning,
    cost
):

    explanations = []


    if workload == "random":

        explanations.append(
            "The workload contains small random I/O."
        )


    elif workload == "sequential":

        explanations.append(
            "The workload is sequential and throughput-oriented."
        )


    elif workload == "mixed":

        explanations.append(
            "The workload contains both read and write operations."
        )


    elif workload == "general":

        explanations.append(
            "The workload is a general-purpose workload."
        )


    explanations.append(
        f"Required IOPS: {required_iops}."
    )

    explanations.append(
        f"Required throughput: "
        f"{required_throughput} MiB/s."
    )

    explanations.append(
        f"Required capacity: "
        f"{capacity_gib} GiB."
    )

    explanations.append(
        f"Latency sensitivity: "
        f"{latency_sensitivity}."
    )

    explanations.append(
        f"Provisioned IOPS: "
        f"{provisioning['provisioned_iops']}."
    )

    explanations.append(
        f"Provisioned throughput: "
        f"{provisioning['provisioned_throughput_mib_s']} "
        f"MiB/s."
    )


    if cost is not None:

        explanations.append(
            f"Estimated monthly cost: "
            f"${cost['total_monthly_cost_usd']}."
        )


    explanations.append(
        f"{selected} satisfies "
        f"the supplied technical constraints."
    )


    return explanations


# ============================================================
# MAIN RECOMMENDATION ENGINE
# ============================================================

def recommend(
    workload,
    required_iops,
    required_throughput,
    latency_sensitivity,
    capacity_gib
):

    data = load_knowledge_base()

    volumes = data[
        "volume_types"
    ]


    candidates = []

    rejected = {}

    provisioning = {}

    costs = {}


    # ========================================================
    # EC2 INSTANCE PROFILE
    # ========================================================

    instance_profile = (
        get_instance_profile()
    )

    instance_max_iops = (
        instance_profile.get(
            "max_ebs_iops"
        )
    )

    instance_max_throughput = (
        instance_profile.get(
            "max_ebs_throughput_mib_s"
        )
    )


    # ========================================================
    # TECHNICAL FILTER
    # ========================================================

    for name, volume in volumes.items():

        reasons = []


        # ----------------------------------------------------
        # Workload
        # ----------------------------------------------------

        if not workload_matches(
            volume,
            workload
        ):

            reasons.append(
                "Workload type is not a suitable match."
            )


        # ----------------------------------------------------
        # Capacity
        # ----------------------------------------------------

        if not capacity_matches(
            volume,
            capacity_gib
        ):

            reasons.append(
                "Required capacity is outside "
                "the supported volume range."
            )


        # ----------------------------------------------------
        # Volume IOPS
        # ----------------------------------------------------

        if not iops_matches(
            name,
            volume,
            required_iops,
            capacity_gib
        ):

            supported = get_supported_iops(
                name,
                volume,
                capacity_gib
            )

            reasons.append(
                f"Required IOPS ({required_iops}) "
                f"exceeds the estimated supported "
                f"IOPS ({supported})."
            )


        # ----------------------------------------------------
        # EC2 INSTANCE IOPS
        # ----------------------------------------------------

        if (
            instance_max_iops is not None
            and
            required_iops > instance_max_iops
        ):

            reasons.append(
                f"Required IOPS ({required_iops}) "
                f"exceeds the EC2 instance EBS "
                f"limit ({instance_max_iops})."
            )


        # ----------------------------------------------------
        # Volume Throughput
        # ----------------------------------------------------

        if not throughput_matches(
            volume,
            required_throughput
        ):

            max_throughput = volume.get(
                "max_throughput_mib_s"
            )

            reasons.append(
                f"Required throughput "
                f"({required_throughput} MiB/s) "
                f"exceeds the volume capability "
                f"({max_throughput} MiB/s)."
            )


        # ----------------------------------------------------
        # EC2 INSTANCE THROUGHPUT
        # ----------------------------------------------------

        if (
            instance_max_throughput is not None
            and
            required_throughput
            > instance_max_throughput
        ):

            reasons.append(
                f"Required throughput "
                f"({required_throughput} MiB/s) "
                f"exceeds the EC2 instance EBS "
                f"limit ({instance_max_throughput} MiB/s)."
            )


        # ----------------------------------------------------
        # Latency
        # ----------------------------------------------------

        if not latency_matches(
            volume,
            latency_sensitivity
        ):

            reasons.append(
                "Latency class does not satisfy "
                "the requested sensitivity."
            )


        # ----------------------------------------------------
        # Provisioning
        # ----------------------------------------------------

        volume_provisioning = (
            calculate_provisioning(
                name,
                volume,
                required_iops,
                required_throughput,
                capacity_gib
            )
        )


        # ----------------------------------------------------
        # Candidate
        # ----------------------------------------------------

        if not reasons:

            candidates.append(
                name
            )


            provisioning[name] = (
                volume_provisioning
            )


            # ------------------------------------------------
            # Cost
            # ------------------------------------------------

            try:

                costs[name] = calculate_cost(

                    name,

                    capacity_gib,

                    volume_provisioning[
                        "provisioned_iops"
                    ],

                    volume_provisioning[
                        "provisioned_throughput_mib_s"
                    ]
                )


            except Exception:

                costs[name] = None


        else:

            rejected[name] = reasons


    # ========================================================
    # NO CANDIDATE
    # ========================================================

    if not candidates:

        return {

            "recommendation":
                None,

            "candidates":
                [],

            "instance_profile":
                instance_profile,

            "requirements": {

                "workload":
                    workload,

                "required_iops":
                    required_iops,

                "required_throughput_mib_s":
                    required_throughput,

                "latency_sensitivity":
                    latency_sensitivity,

                "capacity_gib":
                    capacity_gib
            },

            "provisioning":
                {},

            "selected_provisioning":
                None,

            "costs":
                {},

            "selected_cost":
                None,

            "benchmark_evidence":
                {},

            "decision_analysis":
                {},

            "selected_decision":
                None,

            "candidate_analysis":
                [],

            "why_selected":
                [],

            "rejected":
                rejected,

            "message":
                "No volume type satisfies "
                "all supplied requirements "
                "within the selected EC2 instance limits."
        }


    # ========================================================
    # BENCHMARK EVIDENCE
    # ========================================================

    benchmark_workload = (
        get_benchmark_workload(
            workload
        )
    )


    benchmark_evidence = {}


    if benchmark_workload:

        for candidate in candidates:

            benchmark_evidence[
                candidate
            ] = get_benchmark_evidence(

                candidate,

                benchmark_workload
            )


    # ========================================================
    # DECISION ANALYSIS
    # ========================================================

    rankings = rank_candidates(

        candidates,

        workload,

        latency_sensitivity,

        costs
    )


    decision_analysis = (
        explain_decision(
            rankings
        )
    )


    # ========================================================
    # SELECT TOP-RANKED CANDIDATE
    # ========================================================

    selected = (
        rankings[0]["volume"]
    )


    selected_provisioning = (
        provisioning.get(
            selected,
            {}
        )
    )


    selected_cost = (
        costs.get(
            selected
        )
    )


    selected_decision = (
        rankings[0]["score"]
    )


    # ========================================================
    # CANDIDATE ANALYSIS
    # ========================================================

    candidate_analysis = []


    for name in volumes.keys():

        if name in candidates:

            analysis_status = (
                "selected"
                if name == selected
                else "eligible_not_selected"
            )

            matching_score = None

            for item in decision_analysis:

                if item["volume"] == name:

                    matching_score = (
                        item["final_score"]
                    )

                    break


            candidate_analysis.append({

                "volume":
                    name,

                "technical_status":
                    "eligible",

                "decision":
                    analysis_status,

                "decision_score":
                    matching_score,

                "estimated_cost":
                    costs.get(name),

                "reasons":
                    []
            })


        else:

            candidate_analysis.append({

                "volume":
                    name,

                "technical_status":
                    "ineligible",

                "decision":
                    None,

                "decision_score":
                    None,

                "estimated_cost":
                    None,

                "reasons":
                    rejected.get(
                        name,
                        []
                    )
            })


    # ========================================================
    # FINAL RESULT
    # ========================================================

    return {

        "recommendation":
            selected,

        "candidates":
            candidates,

        "benchmark_environment": {

            "instance_type":
                instance_profile.get(
                    "instance_type"
                ),

            "region":
                instance_profile.get(
                    "region"
                ),

            "benchmark_environment":
                instance_profile.get(
                    "benchmark_environment"
                ),

            "max_ebs_iops":
                instance_profile.get(
                    "max_ebs_iops"
                ),

            "max_ebs_throughput_mib_s":
                instance_profile.get(
                    "max_ebs_throughput_mib_s"
                ),

            "note":
                instance_profile.get(
                    "note"
                )
        },

        "instance_profile":
            instance_profile,


        "requirements": {

            "workload":
                workload,

            "required_iops":
                required_iops,

            "required_throughput_mib_s":
                required_throughput,

            "latency_sensitivity":
                latency_sensitivity,

            "capacity_gib":
                capacity_gib
        },


        "provisioning":
            provisioning,


        "selected_provisioning":
            selected_provisioning,


        "costs":
            costs,


        "selected_cost":
            selected_cost,


        "benchmark_evidence":
            benchmark_evidence,


        "decision_analysis":
            decision_analysis,


        "selected_decision":
            selected_decision,


        "candidate_analysis":
            candidate_analysis,


        "why_selected":
            generate_explanation(

                selected,

                workload,

                required_iops,

                required_throughput,

                latency_sensitivity,

                capacity_gib,

                selected_provisioning,

                selected_cost
            ),


        "rejected":
            rejected,


        "message":
            f"{selected} received the highest "
            f"decision score among the technically "
            f"valid candidates."
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    result = recommend(

        workload="random",

        required_iops=10000,

        required_throughput=200,

        latency_sensitivity="high",

        capacity_gib=100
    )


    print(
        json.dumps(
            result,
            indent=4
        )
    )
