import boto3
from botocore.exceptions import ClientError
import requests
import os
import time
import stat
import tempfile

def get_local_ip():
    try:
        response = requests.get('https://httpbin.org/ip')
        ip = response.json()['origin']
        return f"{ip}/32"
    except Exception as e:
        print(f"Error fetching local IP: {e}")
        return None

def create_security_group(ec2_client, vpc_id, group_name="btu-security-group"):
    try:
        response = ec2_client.create_security_group(
            GroupName=group_name,
            Description="Security group for BTU EC2 instance",
            VpcId=vpc_id
        )
        security_group_id = response['GroupId']
        print(f"Created security group: {security_group_id}")

        # Allow HTTP (port 80) from all IPs
        ec2_client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }
            ]
        )
        print("Added HTTP rule (port 80) for all IPs")

        # Allow SSH (port 22) from local machine's IP
        local_ip = get_local_ip()
        if local_ip:
            ec2_client.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': local_ip}]
                    }
                ]
            )
            print(f"Added SSH rule (port 22) for {local_ip}")
        else:
            print("Failed to fetch local IP, skipping SSH rule")

        return security_group_id
    except ClientError as e:
        print(f"Error creating security group: {e}")
        return None

def create_key_pair(ec2_client, key_name="btu-key-pair"):
    try:
        # Check if key pair already exists
        try:
            existing_keys = ec2_client.describe_key_pairs(KeyNames=[key_name])
            if existing_keys['KeyPairs']:
                print(f"Key pair {key_name} already exists, deleting it first...")
                ec2_client.delete_key_pair(KeyName=key_name)
        except ClientError as e:
            if e.response['Error']['Code'] != 'InvalidKeyPair.NotFound':
                print(f"Error checking existing key pair: {e}")
        
        response = ec2_client.create_key_pair(KeyName=key_name)
        key_material = response['KeyMaterial']
        
        # Use a more specific filename with timestamp to avoid conflicts
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        key_file = f"{key_name}_{timestamp}.pem"
        
        # Try different approaches to save the file
        try:
            # Method 1: Save to current directory
            with open(key_file, 'w') as f:
                f.write(key_material)
            file_path = os.path.abspath(key_file)
        except PermissionError:
            try:
                # Method 2: Save to user's home directory
                home_dir = os.path.expanduser("~")
                key_file = os.path.join(home_dir, f"{key_name}_{timestamp}.pem")
                with open(key_file, 'w') as f:
                    f.write(key_material)
                file_path = key_file
            except PermissionError:
                # Method 3: Save to temp directory
                temp_dir = tempfile.gettempdir()
                key_file = os.path.join(temp_dir, f"{key_name}_{timestamp}.pem")
                with open(key_file, 'w') as f:
                    f.write(key_material)
                file_path = key_file
        
        # Set file permissions to 400 (read-only for owner)
        try:
            os.chmod(file_path, stat.S_IRUSR)
            print(f"Created and saved key pair: {file_path}")
        except OSError as e:
            print(f"Warning: Could not set file permissions: {e}")
            print(f"Key pair saved to: {file_path}")
            print("Please manually set permissions to 400 (read-only for owner)")
        
        return key_name, file_path
    except ClientError as e:
        print(f"Error creating key pair: {e}")
        return None, None
    except Exception as e:
        print(f"Unexpected error creating key pair: {e}")
        return None, None

def launch_ec2_instance(ec2_client, vpc_id, subnet_id, region):
    try:
        # Create security group with unique name to avoid conflicts
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_sg_name = f"btu-security-group-{timestamp}"
        
        security_group_id = create_security_group(ec2_client, vpc_id, unique_sg_name)
        if not security_group_id:
            return None

        # Create key pair with unique name
        unique_key_name = f"btu-key-pair-{timestamp}"
        key_name, key_file = create_key_pair(ec2_client, unique_key_name)
        if not key_name:
            return None

        # Launch EC2 instance
        response = ec2_client.run_instances(
            ImageId='ami-0c02fb55956c7d316',
            InstanceType='t2.micro',
            MinCount=1,
            MaxCount=1,
            KeyName=key_name,
            SecurityGroupIds=[security_group_id],
            SubnetId=subnet_id,
            BlockDeviceMappings=[
                {
                    'DeviceName': '/dev/xvda',
                    'Ebs': {
                        'VolumeSize': 10,
                        'VolumeType': 'gp2',
                        'DeleteOnTermination': True
                    }
                }
            ],
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {'Key': 'Name', 'Value': f'btu-ec2-instance-{timestamp}'}
                    ]
                }
            ]
        )

        instance_id = response['Instances'][0]['InstanceId']
        print(f"Launched EC2 instance: {instance_id}")

        # Wait for instance to be running
        print("Waiting for instance to be running...")
        waiter = ec2_client.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        print(f"Instance {instance_id} is running")

        # Get public IP
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        public_ip = response['Reservations'][0]['Instances'][0].get('PublicIpAddress', None)
        if public_ip:
            print(f"Public IP assigned: {public_ip}")
        else:
            print("No public IP assigned")

        # Basic connectivity check
        try:
            instance_status = ec2_client.describe_instance_status(InstanceIds=[instance_id])
            if instance_status['InstanceStatuses']:
                print(f"Instance status: {instance_status['InstanceStatuses'][0]['InstanceState']['Name']}")
            else:
                print("Instance status not available yet")
        except Exception as e:
            print(f"Could not get instance status: {e}")

        return {
            'instance_id': instance_id,
            'public_ip': public_ip,
            'key_file': key_file,
            'security_group_id': security_group_id
        }
    except ClientError as e:
        print(f"Error launching EC2 instance: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error launching EC2 instance: {e}")
        return None