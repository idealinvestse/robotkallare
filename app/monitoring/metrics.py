from prometheus_client import Counter, Gauge, Histogram, start_http_server
import threading
import time
import logging
from functools import wraps

# Metrics definitions
QUEUE_DEPTH = Gauge('gdial_queue_depth', 'Number of messages in queue', ['queue_name'])
JOBS_PROCESSED = Counter('gdial_jobs_processed', 'Number of jobs processed', ['job_type', 'status'])
PROCESSING_TIME = Histogram('gdial_processing_time', 'Time to process a job', ['job_type'])
WORKER_COUNT = Gauge('gdial_worker_count', 'Number of active workers', ['worker_type'])

def start_metrics_server(port=8000):
    """Start the Prometheus metrics server"""
    start_http_server(port)
    logging.info(f"Started metrics server on port {port}")

def timed_function(job_type):
    """Decorator to time function execution and record metrics"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                JOBS_PROCESSED.labels(job_type=job_type, status='success').inc()
                return result
            except Exception as e:
                JOBS_PROCESSED.labels(job_type=job_type, status='error').inc()
                raise
            finally:
                PROCESSING_TIME.labels(job_type=job_type).observe(time.time() - start_time)
        return wrapper
    return decorator

def start_queue_monitor(rabbitmq_url, queue_names, check_interval=5):
    """Start a thread to monitor queue depths"""
    import pika
    
    def _monitor_queues():
        while True:
            try:
                connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
                channel = connection.channel()
                
                for queue_name in queue_names:
                    try:
                        queue = channel.queue_declare(queue=queue_name, passive=True)
                        QUEUE_DEPTH.labels(queue_name=queue_name).set(queue.method.message_count)
                    except Exception as e:
                        logging.error(f"Error getting queue depth for {queue_name}: {str(e)}")
                
                connection.close()
            except Exception as e:
                logging.error(f"Error in queue monitor: {str(e)}")
                
            time.sleep(check_interval)
    
    thread = threading.Thread(target=_monitor_queues, daemon=True)
    thread.start()
    logging.info("Started queue depth monitor thread")