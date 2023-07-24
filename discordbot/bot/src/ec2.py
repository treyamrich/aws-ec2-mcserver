import boto3
import os
from util import config
from util.logger import Logger

logger = Logger(os.path.basename(__file__), config.LOGGER_PATH, 'debug')

#Initialize boto3 for AWS SDK
client = boto3.client('ec2', region_name=config.REGION)
#ec2Resource = boto3.resource('ec2', region_name=REGION)

class EC2Instance():
	def __init__(self, instanceType, errors, isNew):
		self.instanceType = instanceType
		self.errors = errors
		self.isNew = isNew

def getServerInstance(checkStartedInstance=False):
	resp = client.describe_instances()
	for reservation in resp['Reservations']:
		for instance in reservation['Instances']:
			#Skip instances that are not running
			if instance['State']['Code'] != 16:
				continue
			for tag in instance['Tags']:
				if tag['Key'] == "Name" and tag['Value'] == config.SERVER_TAG:
					logger.info("Server is already running.")
					return EC2Instance(instance['InstanceType'], [], False)
	return None

def startServer():
	"""
	Returns a type EC2Instance
	"""

	#Ensure more than one server will not run
	instance = getServerInstance()
	if instance: 
		return instance

	#Make spot fleet request
	resp = client.create_fleet(
	    LaunchTemplateConfigs=[
	        {
	            'LaunchTemplateSpecification': {
	            	'LaunchTemplateName': config.LAUNCH_TEMPLATE_NAME, 
	            	'Version': '$Latest'
	            }
	        },
	    ],
	    TargetCapacitySpecification={
	        'TotalTargetCapacity': 1,
	        'SpotTargetCapacity': 1,
	        'DefaultTargetCapacityType': 'spot',
	    },
	    Type='instant'
	)

	#Check errs
	if len(resp['Errors']) > 0:
		logger.error(f'Spot fleet request not fulfilled.\n{resp["Errors"]}')
		return EC2Instance("", resp['Errors'], False)

	instance = EC2Instance(resp['Instances'][0]['InstanceType'], resp['Errors'], True)
	logger.info(f"Spot Fleet request success. Instance type: {instance.instanceType}")
	return instance

