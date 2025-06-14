"main.py"

import logging
from botocore.exceptions import ClientError
from auth import init_client
from bucket.crud import *
from bucket.policy import *
from object.crud import *
from ec2.operations import *
from bucket.encryption import set_bucket_encryption, read_bucket_encryption
from bucket.website import *
from utils import fetch_quote
import argparse
import tempfile
import os

from rds.operations import *


parser = argparse.ArgumentParser(
  description="CLI program that helps with S3 buckets.",
  usage='''
    How to download and upload directly:
    short:
        python main.py -bn new-bucket-btu-7 -ol https://cdn.activestate.com/wp-content/uploads/2021/12/python-coding-mistakes.jpg -du
    long:
       python main.py  --bucket_name new-bucket-btu-7 --object_link https://cdn.activestate.com/wp-content/uploads/2021/12/python-coding-mistakes.jpg --download_upload

    How to list buckets:
    short:
        python main.py -lb
    long:
        python main.py --list_buckets

    How to create bucket:
    short:
        -bn new-bucket-btu-1 -cb -region us-west-2
    long:
        --bucket_name new-bucket-btu-1 --create_bucket --region us-west-2

    How to assign missing policy:
    short:
        -bn new-bucket-btu-1 -amp
    long:
        --bn new-bucket-btu-1 --assign_missing_policy
    ''',
  prog='main.py',
  epilog='DEMO APP FOR BTU_AWS')

parser.add_argument(
  "-lb",
  "--list_buckets",
  help="List already created buckets.",
  action="store_true")

parser.add_argument(
  "-cb",
  "--create_bucket",
  help="Flag to create bucket.",
  choices=["False", "True"],
  type=str,
  nargs="?",
  const="True",
  default="False")

parser.add_argument("-bn",
                    "--bucket_name",
                    type=str,
                    help="Pass bucket name.",
                    default=None)

parser.add_argument("-bc",
                    "--bucket_check",
                    help="Check if bucket already exists.",
                    choices=["False", "True"],
                    type=str,
                    nargs="?",
                    const="True",
                    default="True")

parser.add_argument("-region",
                    "--region",
                    type=str,
                    help="Region variable.",
                    default=None)

parser.add_argument("-db",
                    "--delete_bucket",
                    help="flag to delete bucket",
                    choices=["False", "True"],
                    type=str,
                    nargs="?",
                    const="True",
                    default="False")

parser.add_argument("-be",
                    "--bucket_exists",
                    help="flag to check if bucket exists",
                    choices=["False", "True"],
                    type=str,
                    nargs="?",
                    const="True",
                    default="False")

parser.add_argument("-rp",
                    "--read_policy",
                    help="flag to read bucket policy.",
                    choices=["False", "True"],
                    type=str,
                    nargs="?",
                    const="True",
                    default="False")

parser.add_argument("-arp",
                    "--assign_read_policy",
                    help="flag to assign read bucket policy.",
                    choices=["False", "True"],
                    type=str,
                    nargs="?",
                    const="True",
                    default="False")

parser.add_argument("-amp",
                    "--assign_missing_policy",
                    help="flag to assign read bucket policy.",
                    choices=["False", "True"],
                    type=str,
                    nargs="?",
                    const="True",
                    default="False")

parser.add_argument("-du",
                    "--download_upload",
                    choices=["False", "True"],
                    help="download and upload to bucket",
                    type=str,
                    nargs="?",
                    const="True",
                    default="False")

parser.add_argument("-ol",
                    "--object_link",
                    type=str,
                    help="link to download and upload to bucket",
                    default=None)

parser.add_argument("-lo",
                    "--list_objects",
                    type=str,
                    help="list bucket object",
                    nargs="?",
                    const="True",
                    default="False")

parser.add_argument("-ben",
                    "--bucket_encryption",
                    type=str,
                    help="bucket object encryption",
                    nargs="?",
                    const="True",
                    default="False")

parser.add_argument("-rben",
                    "--read_bucket_encryption",
                    type=str,
                    help="list bucket object",
                    nargs="?",
                    const="True",
                    default="False")

parser.add_argument("-sf",
                    "--small_file",
                    type=str,
                    help="Path to small file for upload",
                    default=None)

parser.add_argument("-lf",
                    "--large_file",
                    type=str,
                    help="Path to large file for multipart upload",
                    default=None)

parser.add_argument("-slp",
                    "--set_lifecycle_policy",
                    help="Set lifecycle policy to delete objects after 120 days",
                    choices=["False", "True"],
                    type=str,
                    nargs="?",
                    const="True",
                    default="False")

parser.add_argument("-glp",
                    "--get_lifecycle_policy",
                    help="Get current lifecycle policy",
                    choices=["False", "True"],
                    type=str,
                    nargs="?",
                    const="True",
                    default="False")

parser.add_argument("-days",
                    "--days_until_deletion",
                    type=int,
                    help="Days until objects are deleted (for lifecycle policy)",
                    default=120)

parser.add_argument("-del",
                    "--delete_file",
                    help="Delete a specific file from the bucket.",
                    choices=["False", "True"],
                    type=str,
                    nargs="?",
                    const="True",
                    default="False")

parser.add_argument("-cv",
                    "--check_versioning",
                    help="Check if versioning is enabled on the bucket.",
                    choices=["False", "True"],
                    type=str,
                    nargs="?",
                    const="True",
                    default="False")

parser.add_argument("-cfv",
                    "--check_file_versions",
                    help="Show version count and creation dates of a file.",
                    choices=["False", "True"],
                    type=str,
                    nargs="?",
                    const="True",
                    default="False")

parser.add_argument("-upv",
                    "--upload_previous_version",
                    help="Upload the last previous version of a file as a new version.",
                    choices=["False", "True"],
                    type=str,
                    nargs="?",
                    const="True",
                    default="False")

parser.add_argument("-key",
                    "--file_key",
                    type=str,
                    help="File name",
                    default=None)

parser.add_argument("-uft",
                    "--upload_file_by_type",
                    help="Upload file to appropriate folder based on its type",
                    choices=["False", "True"],
                    type=str,
                    nargs="?",
                    const="True",
                    default="False")

parser.add_argument("-fp",
                    "--file_path",
                    type=str,
                    help="Path to file for type-based upload",
                    default=None)

parser.add_argument("-dov",
                    "--delete_old_versions",
                    help="Check and delete old versions of files in bucket",
                    choices=["False", "True"],
                    type=str,
                    nargs="?",
                    const="True",
                    default="False")

parser.add_argument("-m",
                    "--months",
                    type=int,
                    help="Number of months threshold for version deletion (default: 6)",
                    default=6)


parser.add_argument("host",
                   help="Host a static website on S3",
                   nargs="?") 

parser.add_argument("--source",
                   type=str,
                   help="Source for website files (GitHub URL or local folder)",
                   default=None)
parser.add_argument(
    "--inspire",
    type=str,
    nargs='?',
    const=True,
    default=None, 
    help="Fetch a random quote. Optionally provide an author name to filter quotes."
)

parser.add_argument(
    "-save",
    "--save_quote",
    action="store_true",
    help="Save the fetched quote to the specified S3 bucket as a JSON file. Requires --bucket_name."
)



parser.add_argument("--vpc_id", type=str, help="VPC ID for EC2 instance creation", default=None)
parser.add_argument("--subnet_id", type=str, help="Subnet ID for EC2 instance creation", default=None)
parser.add_argument("--launch_ec2", help="Flag to launch EC2 instance", choices=["False", "True"], type=str, nargs="?", const="True", default="False")


parser.add_argument("--create_rds", 
                   help="Create RDS MySQL instance", 
                   choices=["False", "True"], 
                   type=str, 
                   nargs="?", 
                   const="True", 
                   default="False")

parser.add_argument("--db_instance_id", 
                   type=str, 
                   help="RDS instance identifier", 
                   default=None)

parser.add_argument("--security_group_id", 
                   type=str, 
                   help="Security Group ID for RDS", 
                   default=None)

parser.add_argument("--delete_rds", 
                   help="Delete RDS instance", 
                   choices=["False", "True"], 
                   type=str, 
                   nargs="?", 
                   const="True", 
                   default="False")

parser.add_argument("--list_rds", 
                   help="List RDS instances", 
                   choices=["False", "True"], 
                   type=str, 
                   nargs="?", 
                   const="True", 
                   default="False")



def host_static_website(s3_client, args):
    if not args.bucket_name:
        parser.error("Please provide a bucket name with --bucket_name")
    
    if not args.source:
        parser.error("Please provide a source with --source")
    
    region = args.region if hasattr(args, 'region') and args.region else "us-east-1"

    if not bucket_exists(s3_client, args.bucket_name):
        print(f"Creating bucket {args.bucket_name}...")
        if not create_bucket(s3_client, args.bucket_name, region):
            print("Failed to create bucket")
            return False

    with tempfile.TemporaryDirectory() as temp_dir:
        source_dir = temp_dir

        if args.source.startswith('http') and 'github.com' in args.source:
            print(f"Cloning GitHub repository {args.source}...")
            if not clone_github_repo(args.source, temp_dir):
                print("Failed to clone repository")
                return False
        elif os.path.isdir(args.source):
            print(f"Using local directory {args.source}")
            source_dir = args.source
        else:
            print(f"Invalid source: {args.source}")
            return False
        print(f"Uploading files to bucket {args.bucket_name}...")
        if not upload_folder_to_s3(s3_client, source_dir, args.bucket_name):
            print("Failed to upload files")
            return False

    print("Configuring website hosting...")
    if not configure_website(s3_client, args.bucket_name):
        print("Failed to configure website hosting")
        return False

    print("Setting public read access...")
    if not set_website_policy(s3_client, args.bucket_name):
        print("Failed to set bucket policy")
        return False
    
    website_url = get_website_url(args.bucket_name, region)
    print(f"Website at: {website_url}")
    
    return website_url

def main():
    s3_client = init_client(service='s3')
    ec2_client = init_client(service='ec2')
    rds_client = init_client(service='rds')
    args = parser.parse_args()

    if args.create_rds == "True":
        if not args.db_instance_id or not args.security_group_id:
            parser.error("Please provide both --db_instance_id and --security_group_id for RDS creation")
        region = args.region if args.region else "us-east-1"
        result = create_rds_instance(rds_client, args.db_instance_id, args.security_group_id, region)
        if result:
            print("Connect using these details in your database tool (DBeaver, DataGrip, etc.)")

    if args.delete_rds == "True":
        if not args.db_instance_id:
            parser.error("Please provide --db_instance_id for RDS deletion")
        delete_rds_instance(rds_client, args.db_instance_id)

    if args.list_rds == "True":
        list_rds_instances(rds_client)

    if args.inspire:
        author_name = args.inspire if isinstance(args.inspire, str) else None
        fetched_quote = fetch_quote(author=author_name)
        if fetched_quote:
            print("-" * 30)
            print(f"\"{fetched_quote.get('content', 'N/A')}\"")
            print(f"-- {fetched_quote.get('author', {}).get('name', 'Unknown Author')}")
            print("-" * 30)
            if args.save_quote:
                if args.bucket_name:
                    save_quote_to_s3(s3_client, args.bucket_name, fetched_quote)
                else:
                    print("Error: --bucket_name is required when using -save/--save_quote.")

    if args.bucket_name:
        if args.host and args.source:
            host_static_website(s3_client, args)

        if args.delete_old_versions == "True":
            if not args.bucket_name:
                parser.error("Please provide a bucket name with --bucket_name")
            print(f"Checking for old versions in bucket {args.bucket_name}...")
            file_key = args.file_key if hasattr(args, 'file_key') else None
            if file_key:
                print(f"Looking at specific file: {file_key}")
            deleted_count = check_and_delete_old_versions(s3_client, args.bucket_name, file_key, args.months)
            if deleted_count > 0:
                print(f"Successfully deleted {deleted_count} old versions")
            else:
                print("No old versions found to delete")

        if args.upload_file_by_type == "True" and args.file_path:
            print(f"Uploading {args.file_path} to bucket {args.bucket_name} based on file type...")
            from object.crud import upload_file_by_type
            if upload_file_by_type(s3_client, args.file_path, args.bucket_name):
                print(f"Successfully uploaded {args.file_path} to {args.bucket_name} in appropriate folder")
            else:
                print(f"Failed to upload {args.file_path}")

        if args.check_versioning == "True":
            check_bucket_versioning(s3_client, args.bucket_name)

        if args.check_file_versions == "True" and args.file_key:
            get_file_versions(s3_client, args.bucket_name, args.file_key)

        if args.upload_previous_version == "True" and args.file_key:
            upload_previous_version(s3_client, args.bucket_name, args.file_key)

        if args.delete_file == "True" and args.bucket_name and args.file_key:
            print(f"Attempting to delete file {args.file_key} from bucket {args.bucket_name}...")
            delete_object_from_bucket(s3_client, args.bucket_name, args.file_key)

        if args.set_lifecycle_policy == "True":
            if set_lifecycle_policy(s3_client, args.bucket_name, args.days_until_deletion):
                print(f"Successfully set lifecycle policy to delete objects after {args.days_until_deletion} days")

        if args.get_lifecycle_policy == "True":
            lifecycle_policy = get_lifecycle_policy(s3_client, args.bucket_name)
            if lifecycle_policy:
                print("Current lifecycle policy:")
                print(lifecycle_policy)

        if args.small_file:
            if not args.bucket_name:
                parser.error("Please provide a bucket name with --bucket_name")
            print(f"Uploading {args.small_file} to bucket {args.bucket_name}...")
            if upload_file(s3_client, args.small_file, args.bucket_name):
                print(f"Successfully uploaded {args.small_file} to {args.bucket_name}")
            else:
                print(f"Failed to upload {args.small_file}")

        if args.large_file:
            if upload_large_file(s3_client, args.large_file, args.bucket_name):
                print(f"Successfully uploaded large file {args.large_file} to {args.bucket_name}")

        if args.create_bucket == "True":
            if not args.region:
                parser.error("Please provide region for bucket --region REGION_NAME")
            if args.bucket_check == "True" and bucket_exists(s3_client, args.bucket_name):
                parser.error("Bucket already exists")
            if create_bucket(s3_client, args.bucket_name, args.region):
                print("Bucket successfully created")

        if args.delete_bucket == "True" and delete_bucket(s3_client, args.bucket_name):
            print("Bucket successfully deleted")

        if args.bucket_exists == "True":
            print(f"Bucket exists: {bucket_exists(s3_client, args.bucket_name)}")

        if args.read_policy == "True":
            print(read_bucket_policy(s3_client, args.bucket_name))

        if args.assign_read_policy == "True":
            assign_policy(s3_client, "public_read_policy", args.bucket_name)

        if args.assign_missing_policy == "True":
            assign_policy(s3_client, "multiple_policy", args.bucket_name)

        if args.object_link:
            if args.download_upload == "True":
                print(download_file_and_upload_to_s3(s3_client, args.bucket_name, args.object_link))

        if args.bucket_encryption == "True":
            if set_bucket_encryption(s3_client, args.bucket_name):
                print("Encryption set")

        if args.read_bucket_encryption == "True":
            print(read_bucket_encryption(s3_client, args.bucket_name))

        if args.list_objects == "True":
            get_objects(s3_client, args.bucket_name)

    if args.launch_ec2 == "True":
        if not args.vpc_id or not args.subnet_id:
            parser.error("Please provide both --vpc_id and --subnet_id for EC2 instance creation")
        region = args.region if args.region else "us-east-1"
        print(f"Launching EC2 instance in VPC {args.vpc_id}, Subnet {args.subnet_id}...")
        result = launch_ec2_instance(ec2_client, args.vpc_id, args.subnet_id, region)
        if result:
            print(f"EC2 instance launched successfully: {result['instance_id']}")
            print(f"Public IP: {result['public_ip']}")
            print(f"Key pair saved to: {result['key_file']}")
            print("To verify SSH access, run:")
            print(f"ssh -i {result['key_file']} ec2-user@{result['public_ip']}")
        else:
            print("Failed to launch EC2 instance")

    if args.list_buckets:
        buckets = list_buckets(s3_client)
        if buckets:
            for bucket in buckets['Buckets']:
                print(f'  {bucket["Name"]}')


if __name__ == "__main__":
  try:
    main()
  except ClientError as e:
    logging.error(e)


