import logging
import psutil
import os
import time
import threading
from datetime import datetime

logger = logging.getLogger("worker_health")

class HealthMonitor:
    """Simple health monitoring for worker processes"""
    
    def __init__(self, worker_name, check_interval=60, report_file=None):
        self.worker_name = worker_name
        self.check_interval = check_interval
        self.start_time = datetime.now()
        self.job_count = 0
        self.error_count = 0
        self.last_job_time = None
        self.report_file = report_file or f"logs/{worker_name}_health.log"
        self.running = False
        self.monitor_thread = None
        self.pid = os.getpid()
        
    def start(self):
        """Start the health monitoring thread"""
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"Started health monitor for {self.worker_name}")
        
    def stop(self):
        """Stop the health monitoring thread"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info(f"Stopped health monitor for {self.worker_name}")
        
    def record_job(self, success=True):
        """Record a processed job"""
        self.job_count += 1
        self.last_job_time = datetime.now()
        if not success:
            self.error_count += 1
            
    def get_stats(self):
        """Get current health stats"""
        now = datetime.now()
        uptime = (now - self.start_time).total_seconds()
        
        # Get process stats
        process = psutil.Process(self.pid)
        memory_info = process.memory_info()
        cpu_percent = process.cpu_percent(interval=0.1)
        
        return {
            "worker_name": self.worker_name,
            "pid": self.pid,
            "start_time": self.start_time.isoformat(),
            "uptime_seconds": uptime,
            "jobs_processed": self.job_count,
            "errors": self.error_count,
            "last_job_time": self.last_job_time.isoformat() if self.last_job_time else None,
            "memory_rss_mb": memory_info.rss / (1024 * 1024),
            "memory_vms_mb": memory_info.vms / (1024 * 1024),
            "cpu_percent": cpu_percent,
            "timestamp": now.isoformat()
        }
        
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.running:
            try:
                stats = self.get_stats()
                
                # Log health stats
                logger.info(f"Health stats: {stats}")
                
                # Write to report file
                if self.report_file:
                    os.makedirs(os.path.dirname(self.report_file), exist_ok=True)
                    with open(self.report_file, 'a') as f:
                        f.write(f"{stats['timestamp']} - {stats}\n")
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
                
            time.sleep(self.check_interval)