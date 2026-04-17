import time
from collections import defaultdict
from typing import Dict
from utils.logger import logger

class PerformanceTracker:
    def __init__(self):
        self.operations = defaultdict(list)
        self.current_operations = {}
    
    def start_operation(self, operation_name: str):
        """Start tracking an operation"""
        self.current_operations[operation_name] = time.time()
        logger.debug(f"Started operation: {operation_name}")
    
    def end_operation(self, operation_name: str) -> float:
        """End tracking and record execution time"""
        if operation_name in self.current_operations:
            start_time = self.current_operations.pop(operation_name)
            execution_time = time.time() - start_time
            self.operations[operation_name].append(execution_time)
            logger.debug(f"Completed operation: {operation_name} in {execution_time:.3f}s")
            return execution_time
        return 0.0
    
    def get_average_time(self, operation_name: str) -> float:
        """Get average execution time for an operation"""
        times = self.operations.get(operation_name, [])
        if times:
            return sum(times) / len(times)
        return 0.0
    
    def get_all_stats(self) -> Dict:
        """Get all performance statistics"""
        stats = {}
        for op_name, times in self.operations.items():
            if times:
                stats[f"{op_name}_avg"] = sum(times) / len(times)
                stats[f"{op_name}_min"] = min(times)
                stats[f"{op_name}_max"] = max(times)
                stats[f"{op_name}_count"] = len(times)
        return stats