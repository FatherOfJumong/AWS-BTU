
from botocore.exceptions import ClientError


def create_rds_instance(rds_client, db_instance_identifier, security_group_id, region):
    try:
        response = rds_client.create_db_instance(
            DBInstanceIdentifier=db_instance_identifier,
            DBInstanceClass='db.t3.micro',
            Engine='mysql',
            MasterUsername='admin',
            MasterUserPassword='password123',
            AllocatedStorage=60,
            VpcSecurityGroupIds=[security_group_id],
            PubliclyAccessible=True,
            StorageType='gp2',
            BackupRetentionPeriod=0,
            MultiAZ=False,
            EngineVersion='8.0.35'
        )
        
        print(f"RDS instance {db_instance_identifier} creation initiated...")
        
        waiter = rds_client.get_waiter('db_instance_available')
        print("Waiting for RDS instance to become available...")
        waiter.wait(
            DBInstanceIdentifier=db_instance_identifier,
            WaiterConfig={
                'Delay': 30,
                'MaxAttempts': 60
            }
        )
        
        db_instance = rds_client.describe_db_instances(
            DBInstanceIdentifier=db_instance_identifier
        )
        
        endpoint = db_instance['DBInstances'][0]['Endpoint']['Address']
        port = db_instance['DBInstances'][0]['Endpoint']['Port']
        
        print(f"RDS instance created successfully!")
        print(f"Endpoint: {endpoint}")
        print(f"Port: {port}")
        print(f"Username: admin")
        print(f"Password: password123")
        
        return {
            'endpoint': endpoint,
            'port': port,
            'username': 'admin',
            'password': 'password123'
        }
        
    except ClientError as e:
        print(f"Error creating RDS instance: {e}")
        return None

def delete_rds_instance(rds_client, db_instance_identifier):
    try:
        rds_client.delete_db_instance(
            DBInstanceIdentifier=db_instance_identifier,
            SkipFinalSnapshot=True
        )
        print(f"RDS instance {db_instance_identifier} deletion initiated...")
        return True
    except ClientError as e:
        print(f"Error deleting RDS instance: {e}")
        return False

def list_rds_instances(rds_client):
    try:
        response = rds_client.describe_db_instances()
        instances = response['DBInstances']
        
        if not instances:
            print("No RDS instances found.")
            return []
        
        print("RDS Instances:")
        for instance in instances:
            print(f"  ID: {instance['DBInstanceIdentifier']}")
            print(f"  Engine: {instance['Engine']}")
            print(f"  Status: {instance['DBInstanceStatus']}")
            if 'Endpoint' in instance:
                print(f"  Endpoint: {instance['Endpoint']['Address']}")
            print("-" * 40)
        
        return instances
    except ClientError as e:
        print(f"Error listing RDS instances: {e}")
        return []

def increase_rds_storage(rds_client, db_instance_identifier):
    try:
        response = rds_client.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)
        current_storage = response['DBInstances'][0]['AllocatedStorage']
        new_storage = int(current_storage * 1.25)
        
        print(f"Current storage: {current_storage} GB")
        print(f"New storage: {new_storage} GB")
        
        rds_client.modify_db_instance(
            DBInstanceIdentifier=db_instance_identifier,
            AllocatedStorage=new_storage,
            ApplyImmediately=True
        )
        
        print(f"Storage increase initiated for {db_instance_identifier}")
        return True
    except ClientError as e:
        print(f"Error increasing storage: {e}")
        return False

def create_rds_snapshot(rds_client, db_instance_identifier, snapshot_identifier):
    try:
        response = rds_client.create_db_snapshot(
            DBSnapshotIdentifier=snapshot_identifier,
            DBInstanceIdentifier=db_instance_identifier
        )
        
        print(f"Manual snapshot creation initiated: {snapshot_identifier}")
        
        waiter = rds_client.get_waiter('db_snapshot_completed')
        print("Waiting for snapshot to complete...")
        waiter.wait(
            DBSnapshotIdentifier=snapshot_identifier,
            WaiterConfig={
                'Delay': 30,
                'MaxAttempts': 60
            }
        )
        
        print(f"Snapshot {snapshot_identifier} created successfully!")
        return True
    except ClientError as e:
        print(f"Error creating snapshot: {e}")
        return False