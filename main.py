import boto3
import datetime
import json
from botocore.exceptions import ClientError

# Get the region
region_input = input("Enter the region you want to select : Default -> us-east-1 ")

if region_input == "":
    region_name = "us-east-1"
else:
    region_name = region_input

# Initialize the client for ec2 and s3
ec2_client = boto3.client('ec2', region_name)
s3_client = boto3.client('s3', region_name)
s3_resource = boto3.resource('s3')

# Delete EC2 Instances

# Array to store the Instance IDs
instanceIds = []

# Get the tag from input
input_tag, input_value = input("Enter the tag and value with a space between them : ").split(" ")

# Get all the instances using Tags
response = ec2_client.describe_instances(
    Filters=[{
        'Name': f'tag:{input_tag}',
        'Values': [
            f'{input_value}'
        ]
    },
    {
        'Name': 'instance-state-name',
        'Values': [
            'running',
            'stopped'
        ]
    }
    ]
)

# Get the Instance Id from the response
for i in response["Reservations"]:
    instance_id = i["Instances"][0]["InstanceId"]
    instanceIds.append(instance_id)

# Delete Buckets

# Get S3 buckets
s3_client = boto3.client('s3', region_name='us-east-1')

response = s3_client.list_buckets()

buckets = []

for response in response["Buckets"]:
    bucket = response["Name"]
    try:
        bucket_tagging_response = s3_client.get_bucket_tagging(
        Bucket=bucket
        )
        for tags in bucket_tagging_response['TagSet']:
            if tags['Key'] == input_tag and tags['Value'] == input_value:
                buckets.append(bucket)
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchTagSet':
            print(f"Bucket {bucket} has no tags")

# Dry Run

# Method to delete all resources
def deleteresources():
# Terminate the instances
    if len(instanceIds) > 0:
        response = ec2_client.terminate_instances(
            InstanceIds=instanceIds
            )
        print(response)

    # Delete Buckets
    if len(buckets) > 0:
        for bucket in buckets:
            bucket_versioning = s3_client.get_bucket_versioning(
                Bucket=bucket
            )
            # print(f"For bucket : {bucket}")
            status = bucket_versioning.get('Status')
            obj_buck = s3_resource.Bucket(bucket)
            if status == "Enabled":
                obj_buck.object_versions.delete()
                obj_buck.delete()
                exit(0)
            else:
                obj_buck.objects.all().delete()
                obj_buck.delete()
                exit(0)


print(f"Following instances will be deleted : {instanceIds} ")
print(f"Following buckets will be deleted : {buckets}")

decision = input("Do you wish to continue ( y/N ) : ")

if decision == "":
    print("Nothing was deleted")
    exit(0)
elif decision == "y":
    print("Deleting all the mentioned resources !!")
    deleteresources()