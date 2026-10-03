import json


REGION = "ap-south-1"
CURRENCY = "USD"


PRICING = {

    "gp3": {
        "storage_per_gib_month": 0.0912,
        "included_iops": 3000,
        "iops_per_month": 0.0057,
        "included_throughput_mib_s": 125,
        "throughput_per_mib_s_month": 0.0466944
    },

    "gp2": {
        "storage_per_gib_month": 0.114
    },

    "io2": {
        "storage_per_gib_month": 0.131,
        "iops_tier_1_limit": 32000,
        "iops_tier_1_per_month": 0.068,
        "iops_tier_2_limit": 64000,
        "iops_tier_2_per_month": 0.048,
        "iops_tier_3_per_month": 0.033
    },

    "st1": {
        "storage_per_gib_month": 0.051
    },

    "sc1": {
        "storage_per_gib_month": 0.0174
    }
}


def calculate_gp3_cost(
    capacity_gib,
    provisioned_iops,
    provisioned_throughput
):

    pricing = PRICING["gp3"]

    storage_cost = (
        capacity_gib
        * pricing["storage_per_gib_month"]
    )

    extra_iops = max(
        0,
        provisioned_iops
        - pricing["included_iops"]
    )

    iops_cost = (
        extra_iops
        * pricing["iops_per_month"]
    )

    extra_throughput = max(
        0,
        provisioned_throughput
        - pricing["included_throughput_mib_s"]
    )

    throughput_cost = (
        extra_throughput
        * pricing["throughput_per_mib_s_month"]
    )

    total_cost = (
        storage_cost
        + iops_cost
        + throughput_cost
    )

    return {
        "storage_cost_usd": round(storage_cost, 4),
        "iops_cost_usd": round(iops_cost, 4),
        "throughput_cost_usd": round(throughput_cost, 4),
        "total_monthly_cost_usd": round(total_cost, 4)
    }


def calculate_gp2_cost(capacity_gib):

    pricing = PRICING["gp2"]

    storage_cost = (
        capacity_gib
        * pricing["storage_per_gib_month"]
    )

    return {
        "storage_cost_usd": round(storage_cost, 4),
        "iops_cost_usd": 0,
        "throughput_cost_usd": 0,
        "total_monthly_cost_usd": round(storage_cost, 4)
    }


def calculate_io2_iops_cost(provisioned_iops):

    pricing = PRICING["io2"]

    remaining_iops = provisioned_iops
    total_iops_cost = 0

    tier_1_iops = min(
        remaining_iops,
        pricing["iops_tier_1_limit"]
    )

    total_iops_cost += (
        tier_1_iops
        * pricing["iops_tier_1_per_month"]
    )

    remaining_iops -= tier_1_iops

    if remaining_iops > 0:

        tier_2_iops = min(
            remaining_iops,
            pricing["iops_tier_2_limit"]
            - pricing["iops_tier_1_limit"]
        )

        total_iops_cost += (
            tier_2_iops
            * pricing["iops_tier_2_per_month"]
        )

        remaining_iops -= tier_2_iops

    if remaining_iops > 0:

        total_iops_cost += (
            remaining_iops
            * pricing["iops_tier_3_per_month"]
        )

    return total_iops_cost


def calculate_io2_cost(
    capacity_gib,
    provisioned_iops
):

    pricing = PRICING["io2"]

    storage_cost = (
        capacity_gib
        * pricing["storage_per_gib_month"]
    )

    iops_cost = calculate_io2_iops_cost(
        provisioned_iops
    )

    total_cost = (
        storage_cost
        + iops_cost
    )

    return {
        "storage_cost_usd": round(storage_cost, 4),
        "iops_cost_usd": round(iops_cost, 4),
        "throughput_cost_usd": 0,
        "total_monthly_cost_usd": round(total_cost, 4)
    }


def calculate_st1_cost(capacity_gib):

    storage_cost = (
        capacity_gib
        * PRICING["st1"]["storage_per_gib_month"]
    )

    return {
        "storage_cost_usd": round(storage_cost, 4),
        "iops_cost_usd": 0,
        "throughput_cost_usd": 0,
        "total_monthly_cost_usd": round(storage_cost, 4)
    }


def calculate_sc1_cost(capacity_gib):

    storage_cost = (
        capacity_gib
        * PRICING["sc1"]["storage_per_gib_month"]
    )

    return {
        "storage_cost_usd": round(storage_cost, 4),
        "iops_cost_usd": 0,
        "throughput_cost_usd": 0,
        "total_monthly_cost_usd": round(storage_cost, 4)
    }


def calculate_cost(
    volume_type,
    capacity_gib,
    provisioned_iops=0,
    provisioned_throughput=0
):

    if volume_type == "gp3":

        return calculate_gp3_cost(
            capacity_gib,
            provisioned_iops,
            provisioned_throughput
        )

    elif volume_type == "gp2":

        return calculate_gp2_cost(
            capacity_gib
        )

    elif volume_type == "io2":

        return calculate_io2_cost(
            capacity_gib,
            provisioned_iops
        )

    elif volume_type == "st1":

        return calculate_st1_cost(
            capacity_gib
        )

    elif volume_type == "sc1":

        return calculate_sc1_cost(
            capacity_gib
        )

    raise ValueError(
        f"Unsupported volume type: {volume_type}"
    )


if __name__ == "__main__":

    capacity = 100
    iops = 10000
    throughput = 200

    gp3 = calculate_cost(
        "gp3",
        capacity,
        iops,
        throughput
    )

    io2 = calculate_cost(
        "io2",
        capacity,
        iops,
        throughput
    )

    print(
        json.dumps(
            {
                "region": REGION,
                "currency": CURRENCY,

                "test_requirements": {
                    "capacity_gib": capacity,
                    "iops": iops,
                    "throughput_mib_s": throughput
                },

                "gp3": gp3,
                "io2": io2
            },
            indent=4
        )
    )
