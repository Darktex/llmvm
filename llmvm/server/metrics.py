"""Timing and metrics utilities for LLMVM."""
import time
import logging
from contextlib import contextmanager
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class Metrics:
    """Simple metrics collector for request timing."""

    def __init__(self, request_id: str):
        self.request_id = request_id
        self.timings: Dict[str, float] = {}
        self.start_time = time.perf_counter()

    @contextmanager
    def measure(self, stage: str):
        """Context manager to measure a stage."""
        stage_start = time.perf_counter()
        try:
            yield
        finally:
            stage_end = time.perf_counter()
            self.timings[stage] = (stage_end - stage_start) * 1000  # ms

    def get_total_ms(self) -> float:
        """Get total elapsed time in milliseconds."""
        return (time.perf_counter() - self.start_time) * 1000

    def log(self, log: Optional[logging.Logger] = None):
        """Log all metrics."""
        total = self.get_total_ms()

        metrics_str = " ".join([
            f"{k}={v:.1f}ms" for k, v in self.timings.items()
        ])

        msg = f"LLMVM_SERVER_METRICS: request_id={self.request_id} {metrics_str} total={total:.1f}ms"

        if log:
            log.info(msg)
        else:
            logger.info(msg)

    def to_dict(self) -> Dict[str, float]:
        """Return metrics as dictionary."""
        return {
            "request_id": self.request_id,
            **self.timings,
            "total_ms": self.get_total_ms()
        }
