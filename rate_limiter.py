import time
from collections import defaultdict
from typing import Dict, Tuple

class RateLimiter:
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if a client is allowed to make a request"""
        current_time = time.time()
        
        # Clean old requests outside the window
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < self.window_seconds
        ]
        
        # Check if under limit
        if len(self.requests[client_ip]) < self.max_requests:
            self.requests[client_ip].append(current_time)
            return True
        
        return False
    
    def get_remaining_requests(self, client_ip: str) -> int:
        """Get remaining requests for a client"""
        current_time = time.time()
        
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < self.window_seconds
        ]
        
        return max(0, self.max_requests - len(self.requests[client_ip]))
    
    def get_reset_time(self, client_ip: str) -> float:
        """Get time when rate limit resets for a client"""
        if not self.requests[client_ip]:
            return time.time()
        
        oldest_request = min(self.requests[client_ip])
        return oldest_request + self.window_seconds
    
    def reset_client(self, client_ip: str):
        """Reset rate limit for a specific client"""
        self.requests[client_ip].clear()
