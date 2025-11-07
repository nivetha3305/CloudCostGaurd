def get_cost(resource):
    # ALB: ~$0.0225/hour base
    hourly_cost = 0.0225
    return round(hourly_cost * 24 * 30, 2)  # ~ $16.2/month
