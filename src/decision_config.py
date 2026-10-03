"""
Configuration for the EBS volume decision engine.

The weights represent engineering priorities used to compare
already-qualified volume candidates.

They are configurable rather than being hidden inside the
decision algorithm.
"""


# ============================================================
# DECISION WEIGHTS
# ============================================================

DECISION_WEIGHTS = {

    # Lower estimated monthly cost receives a higher score.
    "cost": 0.35,

    # How suitable the volume type is for the workload class.
    "workload": 0.30,

    # Suitability for the requested latency sensitivity.
    "latency": 0.20,

    # Availability of controlled benchmark evidence.
    "benchmark": 0.15
}


# ============================================================
# VALIDATION
# ============================================================

def validate_weights(weights=None):

    if weights is None:
        weights = DECISION_WEIGHTS

    required_keys = [
        "cost",
        "workload",
        "latency",
        "benchmark"
    ]

    for key in required_keys:

        if key not in weights:

            raise ValueError(
                f"Missing decision weight: {key}"
            )


    for key, value in weights.items():

        if not isinstance(value, (int, float)):

            raise ValueError(
                f"Weight for {key} must be numeric."
            )


        if value < 0:

            raise ValueError(
                f"Weight for {key} cannot be negative."
            )


    total = sum(
        weights.values()
    )


    if abs(total - 1.0) > 0.000001:

        raise ValueError(
            f"Decision weights must sum to 1.0. "
            f"Current total: {total}"
        )


    return True


# ============================================================
# DISPLAY CONFIGURATION
# ============================================================

def get_weight_percentages():

    validate_weights()

    return {

        key: round(
            value * 100,
            2
        )

        for key, value
        in DECISION_WEIGHTS.items()
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    validate_weights()

    print(
        "Decision weights are valid."
    )

    print(
        "\nConfigured weights:"
    )

    for key, percentage in (
        get_weight_percentages().items()
    ):

        print(
            f"  {key}: {percentage}%"
        )
