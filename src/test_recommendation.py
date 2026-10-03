import sys

sys.path.insert(
    0,
    "/home/ec2-user/ebs-project/src"
)

from recommendation_engine import recommend


# ============================================================
# TEST HELPER
# ============================================================

def run_test(
    name,
    workload,
    iops,
    throughput,
    latency,
    capacity,
    expected_recommendation
):

    result = recommend(

        workload=workload,

        required_iops=iops,

        required_throughput=throughput,

        latency_sensitivity=latency,

        capacity_gib=capacity
    )

    actual = result.get(
        "recommendation"
    )

    if actual == expected_recommendation:

        print(
            f"PASS: {name}"
        )

        return True

    else:

        print(
            f"FAIL: {name}"
        )

        print(
            f"  Expected: "
            f"{expected_recommendation}"
        )

        print(
            f"  Actual: "
            f"{actual}"
        )

        return False


# ============================================================
# TEST 1
# NORMAL RANDOM WORKLOAD
# ============================================================

test1 = run_test(

    name="Normal random workload",

    workload="random",

    iops=10000,

    throughput=200,

    latency="high",

    capacity=100,

    expected_recommendation="gp3"
)


# ============================================================
# TEST 2
# SEQUENTIAL HIGH THROUGHPUT
# ============================================================
#
# IMPORTANT:
#
# 400 MiB/s exceeds the t3.micro EBS instance limit
# of approximately 248.55 MiB/s.
#
# Therefore there should be NO recommendation on this
# benchmark environment.
#

test2 = run_test(

    name="Sequential workload exceeding instance throughput",

    workload="sequential",

    iops=200,

    throughput=400,

    latency="low",

    capacity=500,

    expected_recommendation=None
)


# ============================================================
# TEST 3
# MIXED WORKLOAD
# ============================================================

test3 = run_test(

    name="Mixed workload",

    workload="mixed",

    iops=3000,

    throughput=100,

    latency="high",

    capacity=100,

    expected_recommendation="gp3"
)


# ============================================================
# TEST 4
# VERY HIGH IOPS
# ============================================================
#
# 50,000 IOPS exceeds the t3.micro EBS limit of 11,800.
#
# Even though io2 can support very high IOPS, the EC2
# instance becomes the bottleneck.
#

test4 = run_test(

    name="Very high IOPS exceeding EC2 limit",

    workload="random",

    iops=50000,

    throughput=100,

    latency="very_high",

    capacity=100,

    expected_recommendation=None
)


# ============================================================
# TEST 5
# EXTREME REQUIREMENTS
# ============================================================

test5 = run_test(

    name="Extreme requirements",

    workload="random",

    iops=300000,

    throughput=5000,

    latency="very_high",

    capacity=1,

    expected_recommendation=None
)


# ============================================================
# TEST 6
# INSTANCE THROUGHPUT LIMIT
# ============================================================
#
# The workload requires more throughput than t3.micro
# can provide.
#

test6 = run_test(

    name="Throughput exceeding EC2 limit",

    workload="sequential",

    iops=100,

    throughput=300,

    latency="low",

    capacity=500,

    expected_recommendation=None
)


# ============================================================
# TEST 7
# BELOW INSTANCE LIMIT
# ============================================================
#
# 200 MiB/s is below the t3.micro limit of approximately
# 248.55 MiB/s.
#
# gp3 should therefore remain eligible.
#

test7 = run_test(

    name="Workload within EC2 limits",

    workload="sequential",

    iops=200,

    throughput=200,

    latency="low",

    capacity=500,

    expected_recommendation="sc1"
)


# ============================================================
# TEST 8
# IO2 ELIGIBILITY WITHIN INSTANCE LIMIT
# ============================================================
#
# 11,000 IOPS is below the t3.micro limit of 11,800.
#
# gp3 supports this requirement too, so the decision engine
# should select based on the configured scoring system.
#

test8 = run_test(

    name="High IOPS within EC2 limit",

    workload="random",

    iops=11000,

    throughput=200,

    latency="very_high",

    capacity=100,

    expected_recommendation="io2"
)


# ============================================================
# FINAL RESULT
# ============================================================

all_tests = [

    test1,
    test2,
    test3,
    test4,
    test5,
    test6,
    test7,
    test8
]


print()
print(
    "========================================"
)

print(
    "TEST SUMMARY"
)

print(
    "========================================"
)

print(
    f"Passed: "
    f"{sum(all_tests)} / {len(all_tests)}"
)


if all(all_tests):

    print()
    print(
        "ALL TESTS PASSED"
    )

else:

    print()
    print(
        "SOME TESTS FAILED"
    )
