import boto3
import time
import botocore

# Configuration Constants
AMI_ID = 'ami-0942590d76b3c1a3b'
INSTANCE_TYPE = 't2.micro'
MAX_INSTANCES = 20
SECURITY_GROUP = ['sg-010603568c6b200af']
SUBNET_ID = 'subnet-02cc46c69f3b1e686'
KEY_NAME = 'pd-cc-2-web-tier'
SQS_REQUEST = 'https://sqs.us-east-1.amazonaws.com/474668424004/1229658367-req-queue'
SQS_RESPONSE = 'https://sqs.us-east-1.amazonaws.com/474668424004/1229658367-resp-queue'

def get_message_count(sqs, queue_url):
    """Retrieve the number of messages in the SQS queue."""
    response = sqs.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=['ApproximateNumberOfMessages']
    )
    return int(response['Attributes']['ApproximateNumberOfMessages'])


def get_running_instances(ec2):
    """Get the current running instances with the 'AppTier' tag."""
    response = ec2.describe_instances(
        Filters=[
            {'Name': 'instance-state-name', 'Values': ['running', 'pending']},
            {'Name': 'tag:Role', 'Values': ['AppTier']}
        ]
    )
    instances = [
        instance for reservation in response['Reservations']
        for instance in reservation['Instances']
    ]
    return instances


def extract_instance_numbers(instances):
    """Extract instance numbers from instance names."""
    numbers = []
    for instance in instances:
        for tag in instance.get('Tags', []):
            if tag['Key'] == 'Name' and 'app-tier-instance-' in tag['Value']:
                number = int(tag['Value'].split('-')[-1])
                numbers.append(number)
    return sorted(numbers)


def launch_instances(ec2, count, existing_numbers):
    """Launch new EC2 instances with the correct naming pattern."""
    print(f"Launching {count} instances...")
    instances = []

    # Find the next available instance numbers
    available_numbers = [
        num for num in range(1, MAX_INSTANCES + 1)
        if num not in existing_numbers
    ][:count]

    for number in available_numbers:
        instance_name = f'app-tier-instance-{number}'
        print(f"Launching {instance_name}...")
        instance = ec2.run_instances(
            ImageId=AMI_ID,
            InstanceType=INSTANCE_TYPE,
            MinCount=1,
            MaxCount=1,
            KeyName=KEY_NAME,
            SecurityGroupIds=SECURITY_GROUP,
            SubnetId=SUBNET_ID,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {'Key': 'Role', 'Value': 'AppTier'},
                        {'Key': 'Name', 'Value': instance_name}
                    ]
                }
            ]
        )
        instances.append(instance)
    return instances


def terminate_instances(ec2, count, existing_numbers, sqs):
    """Terminate the highest numbered EC2 instances."""

    time.sleep(5)
    print(f"Terminating {count} instances...")

    # Sort the numbers in descending order to terminate the highest ones first
    highest_numbers = sorted(existing_numbers, reverse=True)[:count]

    # Get the instance IDs for the highest numbered instances
    response = ec2.describe_instances(
        Filters=[
            {'Name': 'instance-state-name', 'Values': ['running']},
            {'Name': 'tag:Role', 'Values': ['AppTier']}
        ]
    )

    instances_to_terminate = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_name = next(
                (tag['Value'] for tag in instance['Tags'] if tag['Key'] == 'Name'), ''
            )
            number = int(instance_name.split('-')[-1])
            if number in highest_numbers:
                instances_to_terminate.append(instance['InstanceId'])

    if instances_to_terminate:
        ec2.terminate_instances(InstanceIds=instances_to_terminate)
        print(f"Terminated instances: {instances_to_terminate}")

        # # Purge the queues
        if get_req_count() > 0:
            purge_queue_with_retry(sqs, SQS_REQUEST)
        if get_suc_count() > 0:
            purge_queue_with_retry(sqs, SQS_RESPONSE)

        try:
            with open('ReqCount.txt', 'w') as f:
                f.truncate(0)
                f.close()
            with open('SucCount.txt', 'w') as f:
                f.truncate(0)
                f.close()
            print("Text files emptied.")
        except Exception as e:
            print(f"Error emptying text files: {e}")


def get_req_count():
    try:
        with open('ReqCount.txt', 'r') as f:
            content = f.read()
            f.close()
            return len(content)
    except FileNotFoundError:
        return 0


def get_suc_count():
    try:
        with open('SucCount.txt', 'r') as f:
            content = f.read()
            f.close()
            return len(content)
    except FileNotFoundError:
        return 0


def determine_instance_count(message_count):
    """Determine the required instance count based on the number of requests."""
    if message_count >= 50:
        return 20  # Cap at 20 instances
    elif 10 <= message_count < 50:
        return min(20, message_count)  # Gradually scale to 20 instances
    elif 0 < message_count < 10:
        return 10  # Gradually scale to 10 instances
    return 0


def purge_queue_with_retry(sqs, queue_url):
    max_attempts = 5
    base_delay = 2
    max_delay = 60

    for attempt in range(max_attempts):
        try:
            sqs.purge_queue(QueueUrl=queue_url)
            print(f"Queue {queue_url} purged successfully.")
            return
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'AWS.SimpleQueueService.PurgeQueueInProgress':
                delay = min(base_delay * 2 ** attempt, max_delay)
                print(f"Purge in progress, retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                raise


def autoscale(sqs, ec2):
    """Autoscaling logic to manage EC2 instances based on SQS messages."""
    global max_needed_instances
    running_instances = get_running_instances(ec2)
    existing_numbers = extract_instance_numbers(running_instances)

    req_count = get_req_count()
    print(f"Number of requests: {req_count}")
    suc_count = get_suc_count()
    print(f"Number of successful requests: {suc_count}")

    req_instances = determine_instance_count(req_count)

    current_instance_count = len(running_instances)

    try:
        max_needed_instances = max(req_instances, max_needed_instances)  # Update max_needed_instances
    except NameError:
        max_needed_instances = req_instances  # Initialize max_needed_instances if it's not defined yet
        print(f"Max needed instances : {max_needed_instances}")

    if req_instances > current_instance_count:
        launch_instances(ec2, req_instances - current_instance_count, existing_numbers)
    elif req_count == suc_count and req_count > 0:
        terminate_instances(ec2, current_instance_count, existing_numbers, sqs)


if __name__ == "__main__":
    # Initialize Boto3 clients
    ec2 = boto3.client('ec2')
    sqs = boto3.client('sqs')

    while True:
        try:
            autoscale(sqs, ec2)
            time.sleep(2)  # Adjust this sleep time based on your requirements
        except KeyboardInterrupt:
            print("Autoscaler stopped by user.")
            break
