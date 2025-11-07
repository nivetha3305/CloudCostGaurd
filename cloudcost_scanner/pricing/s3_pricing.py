def get_cost(resource):
    # Approximation: $0.023/GB/month for first 50TB
    size_gb = 100  # you can make this dynamic later
    return round(size_gb * 0.023, 2)
