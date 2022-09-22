import boto3

#Initialize boto3 for AWS SDK
client = boto3.client('ec2', region_name='us-west-1')
ec2Resource = boto3.resource('ec2', region_name='us-west-1')

TAG_SERVER_NAME = "mcserver"

class MyInstance():
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
				if tag['Key'] == "Name" and tag['Value'] == TAG_SERVER_NAME:
					print("Server is already running.")
					return MyInstance(instance['InstanceType'], [], False)
	return None

def startServer():
	"""
	Returns a type MyInstance
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
	            	'LaunchTemplateName': 'mc-server-fleet', 
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
		print('Error creating spot fleet request')
		return MyInstance("", resp['Errors'], False)

	instance = MyInstance(resp['Instances'][0]['InstanceType'], resp['Errors'], True)
	print(f"Spot Fleet request success. Instance type: {instance.instanceType}")
	return instance

