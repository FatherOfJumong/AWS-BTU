"main.py"

import logging
from botocore.exceptions import ClientError
from auth import init_client
from bucket.crud import *
from bucket.policy import *
from object.crud import *
from bucket.encryption import set_bucket_encryption, read_bucket_encryption
import argparse

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
  # https://docs.python.org/dev/library/argparse.html#action
  action="store_true")

parser.add_argument(
  "-cb",
  "--create_bucket",
  help="Flag to create bucket.",
  choices=["False", "True"],
  type=str,
  nargs="?",
  # https://jdhao.github.io/2018/10/11/python_argparse_set_boolean_params
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


def main():
  s3_client = init_client()
  args = parser.parse_args()

  if args.bucket_name:

    if args.delete_old_versions == "True":
        if not args.bucket_name:
            parser.error("Please provide a bucket name with --bucket_name")
            
        print(f"Checking for old versions in bucket {args.bucket_name}...")

        file_key = args.file_key if hasattr(args, 'file_key') else None
        
        if file_key:
            print(f"Looking at specific file: {file_key}")
    
        deleted_count = check_and_delete_old_versions(
            s3_client, 
            args.bucket_name, 
            file_key, 
            args.months
        )
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
      if (args.bucket_check == "True") and bucket_exists(
          s3_client, args.bucket_name):
        parser.error("Bucket already exists")
      if create_bucket(s3_client, args.bucket_name, args.region):
        print("Bucket successfully created")

    if (args.delete_bucket == "True") and delete_bucket(
        s3_client, args.bucket_name):
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
      if (args.download_upload == "True"):
        print(
          download_file_and_upload_to_s3(s3_client, args.bucket_name,
                                         args.object_link))
    if args.bucket_encryption == "True":
      if set_bucket_encryption(s3_client, args.bucket_name):
        print("Encryption set")
    if args.read_bucket_encryption == "True":
      print(read_bucket_encryption(s3_client, args.bucket_name))

    if (args.list_objects == "True"):
      get_objects(s3_client, args.bucket_name)

  if (args.list_buckets):
    buckets = list_buckets(s3_client)
    if buckets:
      for bucket in buckets['Buckets']:
        print(f'  {bucket["Name"]}')


if __name__ == "__main__":
  try:
    main()
  except ClientError as e:
    logging.error(e)


