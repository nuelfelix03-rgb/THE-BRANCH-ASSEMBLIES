import os

bind = f"0.0.0.0:{os.environ.get('PORT', 8000)}"
workers = int(os.environ.get('WEB_CONCURRENCY', 4))
threads = 2
timeout = 120
accesslog = '-'
errorlog = '-'
capture_output = True
loglevel = os.environ.get('LOG_LEVEL', 'info')
