def get_cost(resource):
    # NAT Gateway = ~$0.045/hour + data processing (ignore for now)
    hourly_cost = 0.045
    return round(hourly_cost * 24 * 30, 2)  # ~ $32.4/month
