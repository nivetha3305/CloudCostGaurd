def get_cost(resource):
    # Elastic IP (charged when not associated) ~ $0.005/hour
    hourly_cost = 0.005
    return round(hourly_cost * 24 * 30, 2)  # ~ $3.6/month
