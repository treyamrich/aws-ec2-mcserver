from typing import List
import boto3
import os
from core.logger import Logger
from core.config import Deployment, config

logger = Logger(os.path.basename(__file__), "debug")

# Initialize boto3 for AWS SDK
if config.GENERAL.deployment == Deployment.AWS_EC2:
    client = boto3.client("ec2", region_name=config.AWS.region)
    # ec2Resource = boto3.resource('ec2', region_name=REGION)


class EC2Instance:
    def __init__(self, publicIp, instanceType, errors, isNew):
        self.publicIp = publicIp
        self.instanceType = instanceType
        self.errors = errors
        self.isNew = isNew

    def from_error(errors: List[str]):
        return EC2Instance(None, None, errors, False)


def getServerInstance(instance_id=None):
    try:
        resp = client.describe_instances(
            **({"InstanceIds": [instance_id]} if instance_id else {})
        )

        for reservation in resp["Reservations"]:
            for instance in reservation["Instances"]:
                # If not a direct lookup, skip decommisioned instances that are no longer running
                if not instance_id and instance["State"]["Code"] != 16:
                    continue

                tag = next(
                    (
                        tag
                        for tag in instance["Tags"]
                        if tag["Key"] == "Name" and tag["Value"] == config.AWS.server_tag
                    ),
                    None,
                )

                if not tag:
                    continue

                networkInterfaces = instance.get("NetworkInterfaces", [])
                if networkInterfaces:
                    publicIp = (
                        networkInterfaces[0]
                        .get("Association", {})
                        .get("PublicIp", None)
                    )
                else:
                    publicIp = None

                return EC2Instance(publicIp, instance["InstanceType"], [], False)

    except Exception as e:
        logger.error(f"Error checking for running server instance.\n{e}")
        return EC2Instance.from_error([str(e)])

    return None


def startServer():
    """
    Returns a type EC2Instance
    """

    # Ensure more than one server will not run
    instance = getServerInstance()
    if instance:
        return instance

    try:
        # Make spot fleet request
        resp = client.create_fleet(
            LaunchTemplateConfigs=[
                {
                    "LaunchTemplateSpecification": {
                        "LaunchTemplateName": config.AWS.launch_template_name,
                        "Version": "$Latest",
                    }
                },
            ],
            TargetCapacitySpecification={
                "TotalTargetCapacity": 1,
                "SpotTargetCapacity": 1,
                "DefaultTargetCapacityType": "spot",
            },
            Type="instant",
        )

        # Check errs
        if len(resp["Errors"]) > 0:
            logger.error(f'Spot fleet request not fulfilled.\n{resp["Errors"]}')
            return EC2Instance.from_error(resp["Errors"])

        instance = resp["Instances"][0]
        instance_id = instance["InstanceIds"][0]
        instance_type = instance["InstanceType"]

        logger.info(
            f"Spot Fleet request success. Instance ID: {instance_id} Instance Type: {instance_type}"
        )

        instance = EC2Instance(None, instance_type, [], True)

    except Exception as e:
        logger.error(f"Error creating spot fleet request.\n{e}")
        instance = EC2Instance.from_error([str(e)])
    return instance
