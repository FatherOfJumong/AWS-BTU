#crud

from urllib.request import urlopen
import io
from hashlib import md5
from time import localtime


def get_objects(aws_s3_client, bucket_name) -> str:
  for key in aws_s3_client.list_objects(Bucket=bucket_name)['Contents']:
    print(f" {key['Key']}, size: {key['Size']}")


def download_file_and_upload_to_s3(aws_s3_client,
                                   bucket_name,
                                   url,
                                   keep_local=False) -> str:
  file_name = f'image_file_{md5(str(localtime()).encode("utf-8")).hexdigest()}.jpg'
  with urlopen(url) as response:
    content = response.read()
    aws_s3_client.upload_fileobj(Fileobj=io.BytesIO(content),
                                 Bucket=bucket_name,
                                 ExtraArgs={'ContentType': 'image/jpg'},
                                 Key=file_name)
  if keep_local:
    with open(file_name, mode='wb') as jpg_file:
      jpg_file.write(content)

  # public URL
  return "https://s3-{0}.amazonaws.com/{1}/{2}".format('us-west-2',
                                                       bucket_name, file_name)


def upload_file(aws_s3_client, filename, bucket_name):

    import os
    object_name = os.path.basename(filename)
    
    try:
        aws_s3_client.upload_file(filename, bucket_name, object_name)
        return True
    except Exception as e:
        print(f"Error uploading file: {e}")
        return False


def upload_file_obj(aws_s3_client, filename, bucket_name):
  with open(filename, "rb") as file:
    aws_s3_client.upload_fileobj(file, bucket_name, "hello_obj.txt")


def upload_file_put(aws_s3_client, filename, bucket_name):
  with open(filename, "rb") as file:
    aws_s3_client.put_object(Bucket=bucket_name,
                             Key="hello_put.txt",
                             Body=file.read())

def upload_large_file(aws_s3_client, file_path, bucket_name, object_name=None):

    import os
    

    if object_name is None:
        object_name = os.path.basename(file_path)
    
    mpu = aws_s3_client.create_multipart_upload(Bucket=bucket_name, Key=object_name)
    
    file_size = os.path.getsize(file_path)
    
    chunk_size = 5 * 1024 * 1024
    chunk_count = int(file_size / chunk_size) + 1

    parts = []
    
    try:
        print(f"Uploading file {file_path} to {bucket_name}/{object_name}")
        print(f"Total parts: {chunk_count}")
        

        with open(file_path, 'rb') as file:
            for i in range(chunk_count):

                file.seek(chunk_size * i)

                data = file.read(min(chunk_size, file_size - chunk_size * i))
                
                part = aws_s3_client.upload_part(
                    Body=data,
                    Bucket=bucket_name,
                    Key=object_name,
                    PartNumber=i + 1,
                    UploadId=mpu['UploadId']
                )
                
                parts.append({
                    'PartNumber': i + 1,
                    'ETag': part['ETag']
                })
                
                print(f"Uploaded part {i + 1}/{chunk_count}")
        
        aws_s3_client.complete_multipart_upload(
            Bucket=bucket_name,
            Key=object_name,
            MultipartUpload={'Parts': parts},
            UploadId=mpu['UploadId']
        )
        
        print(f"Upload completed for {object_name}")
        return True
    
    except Exception as e:
        aws_s3_client.abort_multipart_upload(
            Bucket=bucket_name,
            Key=object_name,
            UploadId=mpu['UploadId']
        )
        print(f"Upload failed: {e}")
        return False


def delete_object_from_bucket(aws_s3_client, bucket_name, file_key):
    try:
        aws_s3_client.delete_object(Bucket=bucket_name, Key=file_key)
        print(f"Successfully deleted file {file_key} from bucket {bucket_name}")
        return True
    except Exception as e:
        print(f"Error deleting file {file_key}: {e}")
        return False


def get_file_versions(aws_s3_client, bucket_name, file_key):
    try:
        response = aws_s3_client.list_object_versions(Bucket=bucket_name, Prefix=file_key)
        versions = response.get('Versions', [])
        if versions:
            print(f"Versions for file '{file_key}' in bucket '{bucket_name}':")
            for version in versions:
                print(f"Version ID: {version['VersionId']}, Last Modified: {version['LastModified']}")
            print(f"Total versions: {len(versions)}")
        else:
            print(f"No versions found for file '{file_key}' in bucket '{bucket_name}'.")
    except Exception as e:
        print(f"Error listing versions for file '{file_key}': {e}")


def upload_previous_version(aws_s3_client, bucket_name, file_key):
    try:
        response = aws_s3_client.list_object_versions(Bucket=bucket_name, Prefix=file_key)
        versions = response.get('Versions', [])

        if len(versions) < 2:
            print(f"Not enough versions for file '{file_key}' to upload the previous version.")
            return False

        previous_version = versions[1]  # The second most recent version
        version_id = previous_version['VersionId']

        file_obj = aws_s3_client.get_object(Bucket=bucket_name, Key=file_key, VersionId=version_id)
        file_content = file_obj['Body'].read()

        aws_s3_client.put_object(Bucket=bucket_name, Key=file_key, Body=file_content)
        print(f"Successfully uploaded the previous version of '{file_key}' as a new version.")
        return True
    except Exception as e:
        print(f"Error uploading previous version for file '{file_key}': {e}")
        return False



def upload_file_by_type(aws_s3_client, file_path, bucket_name):

    import os
    import magic
    
    try:

        file_name = os.path.basename(file_path)
        _, file_extension = os.path.splitext(file_name)

        folder_name = file_extension[1:].lower() if file_extension else "no_extension"

        mime = magic.Magic(mime=True)
        file_type = mime.from_file(file_path)
        
        s3_key = f"{folder_name}/{file_name}"
        
        print(f"File extension: {file_extension}")
        print(f"Uploading to folder: {folder_name}")
        print(f"Detected MIME type: {file_type}")
        print(f"Full S3 path: {bucket_name}/{s3_key}")

        aws_s3_client.upload_file(
            file_path, 
            bucket_name, 
            s3_key,
            ExtraArgs={'ContentType': file_type}
        )
        
        print(f"Successfully uploaded {file_path} to {bucket_name}/{s3_key}")
        return True
    except Exception as e:
        print(f"Error uploading file by extension: {e}")
        return False
    


def check_and_delete_old_versions(aws_s3_client, bucket_name, file_key=None, months=6):
    import datetime

    current_date = datetime.datetime.now(datetime.timezone.utc)
    cutoff_date = current_date - datetime.timedelta(days=30 * months)
    
    print(f"Checking for versions older than {cutoff_date.strftime('%Y-%m-%d')}")
    
    deleted_count = 0
    
    try:
        if file_key:
            response = aws_s3_client.list_object_versions(Bucket=bucket_name, Prefix=file_key)
            print(f"Checking versions for file: {file_key}")
            deleted_count += process_versions(aws_s3_client, bucket_name, response, cutoff_date)
        else:
            response = aws_s3_client.list_object_versions(Bucket=bucket_name)
            print(f"Checking versions for all files in bucket: {bucket_name}")
            deleted_count += process_versions(aws_s3_client, bucket_name, response, cutoff_date)
            
            while response.get('IsTruncated', False):
                kwargs = {
                    'Bucket': bucket_name,
                    'KeyMarker': response.get('NextKeyMarker'),
                    'VersionIdMarker': response.get('NextVersionIdMarker')
                }
                response = aws_s3_client.list_object_versions(**kwargs)
                deleted_count += process_versions(aws_s3_client, bucket_name, response, cutoff_date)
                
        print(f"Total versions deleted: {deleted_count}")
        return deleted_count
    
    except Exception as e:
        print(f"Error checking/deleting versions: {e}")
        return deleted_count

def process_versions(aws_s3_client, bucket_name, response, cutoff_date):

    deleted_count = 0

    if 'Versions' in response:
        for version in response['Versions']:
            key = version['Key']
            version_id = version['VersionId']
            last_modified = version['LastModified']
 
            if last_modified < cutoff_date:
                try:
                    print(f"Deleting old version of {key}, version: {version_id}, modified: {last_modified}")
                    aws_s3_client.delete_object(
                        Bucket=bucket_name,
                        Key=key,
                        VersionId=version_id
                    )
                    deleted_count += 1
                except Exception as e:
                    print(f"Error deleting version {version_id} of {key}: {e}")

    if 'DeleteMarkers' in response:
        for marker in response['DeleteMarkers']:
            key = marker['Key']
            version_id = marker['VersionId']
            last_modified = marker['LastModified']

            if last_modified < cutoff_date:
                try:
                    print(f"Deleting old delete marker of {key}, version: {version_id}, modified: {last_modified}")
                    aws_s3_client.delete_object(
                        Bucket=bucket_name,
                        Key=key,
                        VersionId=version_id
                    )
                    deleted_count += 1
                except Exception as e:
                    print(f"Error deleting delete marker {version_id} of {key}: {e}")
    
    return deleted_count