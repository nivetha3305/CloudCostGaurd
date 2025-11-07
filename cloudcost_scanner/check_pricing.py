import boto3
client = boto3.client('pricing', region_name='us-east-1')
resp = client.get_products(ServiceCode='AmazonEC2', MaxResults=1, FormatVersion='aws_v1')
print("OK, got", len(resp.get('PriceList', [])), "items")
