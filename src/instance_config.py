# ============================================================
# EC2 INSTANCE CONFIGURATION
# ============================================================

INSTANCE_TYPE = "t3.micro"

REGION = "ap-south-1"

# AWS-documented EBS performance limits for t3.micro.
#
# These are instance-level limits, not volume-level limits.
#
# AWS documentation:
# t3.micro maximum EBS IOPS: approximately 11,800
# t3.micro maximum EBS throughput:
# approximately 260.62 MB/s = 248.55 MiB/s
#
# These limits can become the bottleneck even when the
# attached EBS volume supports higher performance.

INSTANCE_PROFILE = {

    "instance_type": INSTANCE_TYPE,

    "region": REGION,

    "benchmark_environment": True,

    "max_ebs_iops": 11800,

    "max_ebs_throughput_mib_s": 248.55,

    "note":
        "Actual EBS performance is bounded by the EC2 "
        "instance capabilities. These values represent "
        "documented maximum EBS performance for t3.micro."
}


def get_instance_profile():

    return INSTANCE_PROFILE


if __name__ == "__main__":

    profile = get_instance_profile()

    print("EC2 Instance Profile")
    print("--------------------")
    print(f"Instance Type: {profile['instance_type']}")
    print(f"Region: {profile['region']}")
    print(f"Maximum EBS IOPS: {profile['max_ebs_iops']}")
    print(
        f"Maximum EBS Throughput: "
        f"{profile['max_ebs_throughput_mib_s']} MB/s"
    )
