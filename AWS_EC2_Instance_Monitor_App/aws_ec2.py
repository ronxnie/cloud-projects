from datetime import timezone

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from config import Config

FALLBACK_INSTANCE_TYPES = [
    "t2.micro",
    "t2.small",
    "t2.medium",
    "t3.micro",
    "t3.small",
    "t3.medium",
    "t3.large",
    "m5.large",
    "m5.xlarge",
    "m6i.large",
    "m6i.xlarge",
]

OS_CATALOG = [
    {
        "id": "amazon-linux-2023",
        "label": "Amazon Linux 2023",
        "owner": "amazon",
        "name_pattern": "al2023-ami-2023*-x86_64",
        "architecture": "x86_64",
        "username": "ec2-user",
    },
    {
        "id": "amazon-linux-2",
        "label": "Amazon Linux 2",
        "owner": "amazon",
        "name_pattern": "amzn2-ami-hvm-*-x86_64-gp2",
        "architecture": "x86_64",
        "username": "ec2-user",
    },
    {
        "id": "ubuntu-24-04",
        "label": "Ubuntu Server 24.04 LTS",
        "owner": "099720109477",
        "name_pattern": "ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*",
        "architecture": "x86_64",
        "username": "ubuntu",
    },
    {
        "id": "ubuntu-22-04",
        "label": "Ubuntu Server 22.04 LTS",
        "owner": "099720109477",
        "name_pattern": "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*",
        "architecture": "x86_64",
        "username": "ubuntu",
    },
    {
        "id": "debian-12",
        "label": "Debian 12",
        "owner": "136693071363",
        "name_pattern": "debian-12-amd64-*",
        "architecture": "x86_64",
        "username": "admin",
    },
    {
        "id": "rhel-9",
        "label": "Red Hat Enterprise Linux 9",
        "owner": "309956199498",
        "name_pattern": "RHEL-9.*_HVM-*-x86_64-*-Hourly2-GP3",
        "architecture": "x86_64",
        "username": "ec2-user",
    },
    {
        "id": "windows-2022",
        "label": "Windows Server 2022 Base",
        "owner": "amazon",
        "name_pattern": "Windows_Server-2022-English-Full-Base-*",
        "architecture": "x86_64",
        "username": "Administrator",
    },
]


def ec2_client():
    return boto3.client("ec2", region_name=Config.AWS_REGION)


def get_os_catalog():
    return OS_CATALOG


def find_os(os_id):
    return next((os_item for os_item in OS_CATALOG if os_item["id"] == os_id), None)


def get_latest_ami(os_id):
    os_item = find_os(os_id)
    if not os_item:
        raise ValueError("Selected operating system is not available.")

    response = ec2_client().describe_images(
        Owners=[os_item["owner"]],
        Filters=[
            {"Name": "name", "Values": [os_item["name_pattern"]]},
            {"Name": "architecture", "Values": [os_item["architecture"]]},
            {"Name": "root-device-type", "Values": ["ebs"]},
            {"Name": "state", "Values": ["available"]},
            {"Name": "virtualization-type", "Values": ["hvm"]},
        ],
    )
    images = sorted(response["Images"], key=lambda image: image["CreationDate"], reverse=True)
    if not images:
        raise RuntimeError(f"No AMI found for {os_item['label']} in {Config.AWS_REGION}.")
    return images[0], os_item


# def get_instance_types():
#     try:
#         paginator = ec2_client().get_paginator("describe_instance_types")
#         types = []
#         for page in paginator.paginate(
#             Filters=[
#                 {"Name": "processor-info.supported-architecture", "Values": ["x86_64"]},
#                 {"Name": "supported-virtualization-type", "Values": ["hvm"]},
#             ]
#         ):
#             for item in page["InstanceTypes"]:
#                 types.append(item["InstanceType"])
#             if len(types) <= 300:
#                 break
#             for item in FALLBACK_INSTANCE_TYPES:
#                 types.append(item)
                
#             print(f"Found {len(types)} instance types, returning the first 10,000.")
            
#             for item in types:
#                 print(f"Instance Type: {item}")
#         return sorted(set(types))[:10000]
#     except (BotoCoreError, ClientError):
#         return FALLBACK_INSTANCE_TYPES
   
   
def get_instance_types():
    """
    Returns a list of all available EC2 instance types in the given region.
    """
    try: 
        ec2 = boto3.client("ec2", region_name=Config.AWS_REGION)
        paginator = ec2.get_paginator("describe_instance_types")

        instance_types = []

        for page in paginator.paginate():
            for itype in page["InstanceTypes"]:
                instance_types.append(itype["InstanceType"])

        return sorted(set(instance_types))[:10000]   
    except (BotoCoreError, ClientError):
        return FALLBACK_INSTANCE_TYPES
    

# if __name__ == "__main__":
#     instance_types = get_instance_types()
#     print(f"Found {len(instance_types)} instance types, returning the first 10,000.")
#     for item in instance_types:
#         print(f"Instance Type: {item}")    
    
    
    


def launch_instance(form_data):
    image, os_item = get_latest_ami(form_data["os_id"])
    tag_name = form_data.get("name") or f"{os_item['label']} EC2"

    run_args = {
        "ImageId": image["ImageId"],
        "InstanceType": form_data["instance_type"],
        "MinCount": 1,
        "MaxCount": int(form_data.get("count", 1)),
        "TagSpecifications": [
            {
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "Name", "Value": tag_name},
                    {"Key": "ManagedBy", "Value": "Monitor_EC2_instance"},
                    {"Key": "OperatingSystem", "Value": os_item["label"]},
                ],
            }
        ],
    }

    optional_fields = {
        "key_name": "KeyName",
        "security_group_ids": "SecurityGroupIds",
        "subnet_id": "SubnetId",
        "iam_instance_profile": "IamInstanceProfile",
    }

    for form_key, aws_key in optional_fields.items():
        value = form_data.get(form_key)
        if not value:
            continue
        if form_key == "security_group_ids":
            run_args[aws_key] = [item.strip() for item in value.split(",") if item.strip()]
        elif form_key == "iam_instance_profile":
            run_args[aws_key] = {"Name": value}
        else:
            run_args[aws_key] = value

    volume_size = form_data.get("volume_size")
    if volume_size:
        run_args["BlockDeviceMappings"] = [
            {
                "DeviceName": image.get("RootDeviceName", "/dev/xvda"),
                "Ebs": {
                    "VolumeSize": int(volume_size),
                    "VolumeType": "gp3",
                    "DeleteOnTermination": True,
                },
            }
        ]

    response = ec2_client().run_instances(**run_args)
    return [normalize_instance(instance, os_item["label"]) for instance in response["Instances"]]


def list_instances_from_aws():
    paginator = ec2_client().get_paginator("describe_instances")
    instances = []
    for page in paginator.paginate():
        for reservation in page.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                instances.append(normalize_instance(instance))
    return instances


def start_instance(instance_id):
    ec2_client().start_instances(InstanceIds=[instance_id])


def stop_instance(instance_id):
    ec2_client().stop_instances(InstanceIds=[instance_id])


def terminate_instance(instance_id):
    ec2_client().terminate_instances(InstanceIds=[instance_id])


def normalize_instance(instance, os_name=None):
    tags = {tag["Key"]: tag["Value"] for tag in instance.get("Tags", [])}
    launch_time = instance.get("LaunchTime")
    if launch_time:
        launch_time = launch_time.astimezone(timezone.utc).replace(tzinfo=None)

    return {
        "instance_id": instance["InstanceId"],
        "name": tags.get("Name"),
        "instance_type": instance.get("InstanceType"),
        "image_id": instance.get("ImageId"),
        "os_name": os_name or tags.get("OperatingSystem"),
        "state": instance.get("State", {}).get("Name", "unknown"),
        "public_ip": instance.get("PublicIpAddress"),
        "private_ip": instance.get("PrivateIpAddress"),
        "availability_zone": instance.get("Placement", {}).get("AvailabilityZone"),
        "launch_time": launch_time,
    }
