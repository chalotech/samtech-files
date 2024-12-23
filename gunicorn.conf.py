import os

# Number of worker processes
workers = 4
worker_class = 'sync'

# Binding
bind = "0.0.0.0:" + os.environ.get("PORT", "10000")

# Timeouts
timeout = 120
keepalive = 120

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Prevent worker timeout issues
worker_timeout = 120
graceful_timeout = 120

# Restart workers after this many requests
max_requests = 1000
max_requests_jitter = 50

# Increase header timeout
limit_request_field_size = 8190
