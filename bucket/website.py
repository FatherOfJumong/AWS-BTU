

def configure_website(s3_client, bucket_name, index_doc="index.html", error_doc="error.html"):
    s3_client.delete_public_access_block(Bucket=bucket_name)
    try:
        website_configuration = {
            'ErrorDocument': {'Key': error_doc},
            'IndexDocument': {'Suffix': index_doc}  
        }
        
        s3_client.put_bucket_website(
            Bucket=bucket_name,
            WebsiteConfiguration=website_configuration
        )
        return True
    except Exception as e:
        print(f"Error configuring website: {e}")
        return False
    

def get_website_url(bucket_name, region):
    if region == 'us-east-1':
        return f"http://{bucket_name}.s3-website-{region}.amazonaws.com"
    else:
        return f"http://{bucket_name}.s3-website.{region}.amazonaws.com"
    