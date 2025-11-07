import boto3

def get_cost(resource):
    pricing = boto3.client('pricing', region_name='us-east-1')
    instance_type = resource.get("values", {}).get("instance_type", "t3.micro")

    response = pricing.get_products(
        ServiceCode='AmazonEC2',
        Filters=[
            {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
            {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': 'US East (N. Virginia)'},
            {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},
            {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
        ],
        MaxResults=1
    )

    if not response["PriceList"]:
        return 0.0

    import json
    product = json.loads(response["PriceList"][0])
    price_per_hour = float(
        list(product["terms"]["OnDemand"].values())[0]["priceDimensions"].popitem()[1]["pricePerUnit"]["USD"]
    )
    return round(price_per_hour * 24 * 30, 2)  # monthly
