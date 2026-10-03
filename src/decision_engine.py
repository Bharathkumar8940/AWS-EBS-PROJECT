import sys
from pathlib import Path


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).parent.parent


# ============================================================
# IMPORT PROJECT MODULES
# ============================================================

sys.path.insert(
    0,
    str(Path(__file__).parent)
)

from benchmark_evidence import (
    get_benchmark_evidence
)

from decision_config import (
    DECISION_WEIGHTS,
    validate_weights
)


# ============================================================
# COST SCORE
# ============================================================

def calculate_cost_score(
    candidate_cost,
    all_costs
):
    """
    Lower estimated monthly cost receives a higher score.

    This score is applied only to technically valid
    candidates.
    """

    valid_costs = [
        cost["total_monthly_cost_usd"]
        for cost in all_costs.values()
        if cost is not None
    ]

    if not valid_costs:
        return 0

    minimum_cost = min(
        valid_costs
    )

    maximum_cost = max(
        valid_costs
    )

    if candidate_cost is None:
        return 0

    candidate_value = (
        candidate_cost[
            "total_monthly_cost_usd"
        ]
    )

    # If all candidates have the same cost,
    # they receive the same maximum cost score.
    if maximum_cost == minimum_cost:
        return 100

    score = (
        (
            maximum_cost
            - candidate_value
        )
        /
        (
            maximum_cost
            - minimum_cost
        )
    ) * 100

    return round(
        score,
        2
    )


# ============================================================
# WORKLOAD SCORE
# ============================================================

def calculate_workload_score(
    volume_type,
    workload
):
    """
    Workload suitability score.

    These values are project-defined engineering
    preferences, not AWS-defined scores.
    """

    scores = {

        "random": {

            "gp3": 90,
            "gp2": 75,
            "io2": 100,
            "st1": 20,
            "sc1": 10
        },

        "sequential": {

            "gp3": 70,
            "gp2": 65,
            "io2": 80,
            "st1": 100,
            "sc1": 85
        },

        "mixed": {

            "gp3": 90,
            "gp2": 75,
            "io2": 100,
            "st1": 20,
            "sc1": 10
        },

        "general": {

            "gp3": 100,
            "gp2": 85,
            "io2": 80,
            "st1": 30,
            "sc1": 20
        }
    }

    return scores.get(
        workload,
        {}
    ).get(
        volume_type,
        0
    )


# ============================================================
# LATENCY SCORE
# ============================================================

def calculate_latency_score(
    volume_type,
    latency_sensitivity
):
    """
    Latency suitability score.

    These values are project-defined engineering
    preferences, not AWS-defined scores.
    """

    scores = {

        "very_high": {

            "io2": 100,
            "gp3": 75,
            "gp2": 70,
            "st1": 20,
            "sc1": 10
        },

        "high": {

            "io2": 100,
            "gp3": 90,
            "gp2": 75,
            "st1": 20,
            "sc1": 10
        },

        "medium": {

            "io2": 100,
            "gp3": 95,
            "gp2": 90,
            "st1": 70,
            "sc1": 60
        },

        "low": {

            "io2": 90,
            "gp3": 100,
            "gp2": 95,
            "st1": 90,
            "sc1": 85
        }
    }

    return scores.get(
        latency_sensitivity,
        {}
    ).get(
        volume_type,
        0
    )


# ============================================================
# BENCHMARK EVIDENCE SCORE
# ============================================================

def calculate_benchmark_score(
    volume_type,
    workload
):
    """
    Score based on availability of controlled
    benchmark evidence.

    IMPORTANT:
    This does NOT mean that a benchmarked volume
    is universally faster.

    It only measures whether this project has
    experimental evidence for the candidate.

    Scoring:
        100 = controlled benchmark evidence exists
         50 = candidate has not been benchmarked
          0 = no benchmark mapping is available

    "Not measured" is intentionally different from
    "poor performance".
    """

    benchmark_mapping = {

        "random":
            "random_read",

        "sequential":
            "sequential_read",

        "mixed":
            "mixed",

        "general":
            "random_read"
    }

    benchmark_workload = (
        benchmark_mapping.get(
            workload
        )
    )

    if benchmark_workload is None:

        return {
            "score": 0,
            "status": "not_applicable"
        }

    evidence = get_benchmark_evidence(
        volume_type,
        benchmark_workload
    )

    if evidence.get(
        "available",
        False
    ):

        return {
            "score": 100,
            "status": "measured"
        }

    return {
        "score": 50,
        "status": "not_measured"
    }


# ============================================================
# DECISION SCORE
# ============================================================

def calculate_decision_score(
    volume_type,
    workload,
    latency_sensitivity,
    candidate_cost,
    all_costs
):

    # --------------------------------------------------------
    # Individual component scores
    # --------------------------------------------------------

    cost_score = calculate_cost_score(
        candidate_cost,
        all_costs
    )

    workload_score = calculate_workload_score(
        volume_type,
        workload
    )

    latency_score = calculate_latency_score(
        volume_type,
        latency_sensitivity
    )

    benchmark_result = calculate_benchmark_score(
        volume_type,
        workload
    )

    benchmark_score = benchmark_result["score"]

    benchmark_status = benchmark_result["status"]


    # --------------------------------------------------------
    # CONFIGURABLE WEIGHTS
    # --------------------------------------------------------

    validate_weights()

    weights = DECISION_WEIGHTS


    # --------------------------------------------------------
    # FINAL WEIGHTED SCORE
    # --------------------------------------------------------

    final_score = (

        cost_score
        * weights["cost"]

        +

        workload_score
        * weights["workload"]

        +

        latency_score
        * weights["latency"]

        +

        benchmark_score
        * weights["benchmark"]
    )


    return {

        "final_score":
            round(
                final_score,
                2
            ),

        "components": {

            "cost_score":
                cost_score,

            "workload_score":
                workload_score,

            "latency_score":
                latency_score,

            "benchmark_evidence_score":
                benchmark_score,

            "benchmark_evidence_status":
                benchmark_status
        },

        "weights":
            weights
    }


# ============================================================
# RANK CANDIDATES
# ============================================================

def rank_candidates(
    candidates,
    workload,
    latency_sensitivity,
    costs
):
    """
    Rank only candidates that have already passed
    the technical filtering stage.
    """

    rankings = []

    for volume_type in candidates:

        score = calculate_decision_score(

            volume_type,

            workload,

            latency_sensitivity,

            costs.get(
                volume_type
            ),

            costs
        )

        rankings.append({

            "volume":
                volume_type,

            "score":
                score
        })


    rankings.sort(

        key=lambda item:
        item["score"]["final_score"],

        reverse=True
    )


    return rankings


# ============================================================
# EXPLANATION
# ============================================================

def explain_decision(
    rankings
):
    """
    Convert the scoring results into a structured
    explanation that can later be displayed in
    the web UI.
    """

    explanations = []

    for item in rankings:

        volume = item[
            "volume"
        ]

        score = item[
            "score"
        ]

        components = score[
            "components"
        ]

        explanations.append({

            "volume":
                volume,

            "final_score":
                score[
                    "final_score"
                ],

            "reason": {

                "cost":
                    components[
                        "cost_score"
                    ],

                "workload":
                    components[
                        "workload_score"
                    ],

                "latency":
                    components[
                        "latency_score"
                    ],

                "benchmark_evidence":
                    components[
                        "benchmark_evidence_score"
                    ],

                "benchmark_evidence_status":
                    components[
                        "benchmark_evidence_status"
                    ]
            },

            "weights":
                score[
                    "weights"
                ]
        })


    return explanations


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Example technically valid candidates
    # --------------------------------------------------------

    candidates = [

        "gp3",

        "io2"
    ]


    # --------------------------------------------------------
    # Example costs
    # --------------------------------------------------------

    costs = {

        "gp3": {

            "total_monthly_cost_usd":
                52.5221
        },

        "io2": {

            "total_monthly_cost_usd":
                693.10
        }
    }


    # --------------------------------------------------------
    # Calculate ranking
    # --------------------------------------------------------

    rankings = rank_candidates(

        candidates,

        workload="random",

        latency_sensitivity="high",

        costs=costs
    )


    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    print(
        "\n========================================"
    )

    print(
        "DECISION ANALYSIS"
    )

    print(
        "========================================"
    )


    print(
        "\nDecision Weights:"
    )


    for key, value in (
        DECISION_WEIGHTS.items()
    ):

        print(
            f"  {key}: "
            f"{value * 100:.1f}%"
        )


    print(
        "\nCandidate Scores:"
    )


    for item in explain_decision(
        rankings
    ):

        print(
            "\n----------------------------------------"
        )

        print(
            f"Volume: "
            f"{item['volume']}"
        )

        print(
            f"Final Score: "
            f"{item['final_score']}"
        )

        print(
            f"Cost Score: "
            f"{item['reason']['cost']}"
        )

        print(
            f"Workload Score: "
            f"{item['reason']['workload']}"
        )

        print(
            f"Latency Score: "
            f"{item['reason']['latency']}"
        )

        print(
            f"Benchmark Evidence Score: "
            f"{item['reason']['benchmark_evidence']}"
        )

        print(
            f"Benchmark Evidence Status: "
            f"{item['reason']['benchmark_evidence_status']}"
        )
