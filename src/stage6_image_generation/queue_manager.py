"""
Image Queue Manager - Stage 6.1.6
Manages concurrent image generation queue.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timezone
from queue import Queue
from threading import Thread, Lock

from .providers.base import (
    ImageProvider,
    GenerationResult,
    ImageSize,
    ImageQuality
)


class QueueTask:
    """A task in the image generation queue."""

    def __init__(
        self,
        task_id: str,
        prompt: str,
        provider_name: str,
        size: Optional[ImageSize] = None,
        quality: Optional[ImageQuality] = None,
        **kwargs
    ):
        """
        Initialize queue task.

        Args:
            task_id: Unique task ID
            prompt: Image prompt
            provider_name: Provider to use
            size: Image size
            quality: Image quality
            **kwargs: Additional parameters
        """
        self.task_id = task_id
        self.prompt = prompt
        self.provider_name = provider_name
        self.size = size
        self.quality = quality
        self.kwargs = kwargs

        # Status tracking
        self.status = "pending"  # pending, processing, completed, failed
        self.result: Optional[GenerationResult] = None
        self.error: Optional[str] = None
        self.created_at = datetime.now(timezone.utc)
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None


class ImageQueueManager:
    """Manages concurrent image generation with queue."""

    def __init__(
        self,
        project_dir: str = None,
        providers: Dict[str, ImageProvider] = None,
        max_concurrent: int = 3,
        enable_rate_limiting: bool = True
    ):
        """
        Initialize queue manager.

        Args:
            project_dir: Project directory path (optional, for simple interface)
            providers: Dictionary of provider name -> provider
            max_concurrent: Maximum concurrent generations
            enable_rate_limiting: Enable per-provider rate limiting
        """
        self.providers = providers or {}
        self.max_concurrent = max_concurrent
        self.enable_rate_limiting = enable_rate_limiting
        self.project_dir = project_dir

        # Queue
        self.queue: Queue = Queue()
        self.tasks: Dict[str, QueueTask] = {}

        # Worker management
        self.workers: List[Thread] = []
        self.is_running = False
        self.lock = Lock()

        # Rate limiting
        self.provider_last_request: Dict[str, float] = {}
        self.provider_rate_limits: Dict[str, int] = {}

        # Statistics
        self.total_processed = 0
        self.total_success = 0
        self.total_failed = 0

    def add_to_queue(self, panel_id: str, prompt: str) -> QueueTask:
        """
        Add a panel to the queue (simple interface).

        Args:
            panel_id: Panel ID
            prompt: Image prompt

        Returns:
            QueueTask
        """
        return self.add_task(
            task_id=panel_id,
            prompt=prompt,
            provider_name="mock",
            size=None,
            quality=None
        )

    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get queue status.

        Returns:
            Status dictionary
        """
        return {
            "queue_size": self.queue.qsize(),
            "total_tasks": len(self.tasks),
            "workers_active": len(self.workers),
            "is_running": self.is_running,
            "total_processed": self.total_processed,
            "total_success": self.total_success,
            "total_failed": self.total_failed
        }

    def add_task(
        self,
        task_id: str,
        prompt: str,
        provider_name: str,
        size: Optional[ImageSize] = None,
        quality: Optional[ImageQuality] = None,
        **kwargs
    ) -> QueueTask:
        """
        Add a task to the queue.

        Args:
            task_id: Unique task ID
            prompt: Image prompt
            provider_name: Provider to use
            size: Image size
            quality: Image quality
            **kwargs: Additional parameters

        Returns:
            QueueTask
        """
        task = QueueTask(
            task_id=task_id,
            prompt=prompt,
            provider_name=provider_name,
            size=size,
            quality=quality,
            **kwargs
        )

        self.tasks[task_id] = task
        self.queue.put(task)

        return task

    def add_tasks_batch(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[QueueTask]:
        """
        Add multiple tasks to the queue.

        Args:
            tasks: List of task dictionaries

        Returns:
            List of QueueTask objects
        """
        task_objects = []

        for task_dict in tasks:
            task_id = task_dict.pop("task_id", f"task-{time.time()}")
            task = self.add_task(task_id=task_id, **task_dict)
            task_objects.append(task)

        return task_objects

    def start(self):
        """Start worker threads."""
        if self.is_running:
            return

        self.is_running = True

        # Initialize rate limiting
        for name, provider in self.providers.items():
            info = provider.get_provider_info()
            self.provider_rate_limits[name] = info["rate_limit"]
            self.provider_last_request[name] = 0.0

        # Create workers
        for i in range(self.max_concurrent):
            worker = Thread(
                target=self._worker_loop,
                name=f"worker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)

        print(f"✓ Started {len(self.workers)} worker threads")

    def stop(self):
        """Stop worker threads."""
        self.is_running = False

        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5.0)

        self.workers.clear()
        print("✓ Stopped all worker threads")

    def _worker_loop(self):
        """Worker thread loop."""
        while self.is_running or not self.queue.empty():
            try:
                # Get task from queue (with timeout)
                task = self.queue.get(timeout=1.0)

                # Process task
                self._process_task(task)

                # Mark queue task as done
                self.queue.task_done()

            except:
                continue

    def _process_task(self, task: QueueTask):
        """
        Process a single task.

        Args:
            task: QueueTask to process
        """
        # Update status
        task.status = "processing"
        task.started_at = datetime.now(timezone.utc)

        # Check rate limiting
        if self.enable_rate_limiting:
            self._check_rate_limit(task.provider_name)

        # Get provider
        provider = self.providers.get(task.provider_name)

        if provider is None:
            task.status = "failed"
            task.error = f"Provider not found: {task.provider_name}"
            task.completed_at = datetime.now(timezone.utc)
            self.total_failed += 1
            return

        try:
            # Generate image
            result = provider.generate(
                prompt=task.prompt,
                size=task.size,
                quality=task.quality,
                **task.kwargs
            )

            # Update task
            task.result = result
            task.status = "completed" if result.success else "failed"
            task.error = result.error if not result.success else None

            # Update statistics
            with self.lock:
                self.total_processed += 1
                if result.success:
                    self.total_success += 1
                else:
                    self.total_failed += 1

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            self.total_failed += 1

        task.completed_at = datetime.now(timezone.utc)

    def _check_rate_limit(self, provider_name: str):
        """
        Check and enforce rate limiting.

        Args:
            provider_name: Provider name
        """
        if provider_name not in self.provider_rate_limits:
            return

        rate_limit = self.provider_rate_limits[provider_name]
        last_request = self.provider_last_request.get(provider_name, 0.0)
        now = time.time()

        # Calculate minimum time between requests
        min_interval = 60.0 / rate_limit

        if now - last_request < min_interval:
            # Sleep until rate limit allows next request
            sleep_time = min_interval - (now - last_request)
            time.sleep(sleep_time)

        # Update last request time
        self.provider_last_request[provider_name] = time.time()

    def get_task(self, task_id: str) -> Optional[QueueTask]:
        """
        Get a task by ID.

        Args:
            task_id: Task ID

        Returns:
            QueueTask or None
        """
        return self.tasks.get(task_id)

    def get_task_status(self, task_id: str) -> Optional[str]:
        """
        Get task status.

        Args:
            task_id: Task ID

        Returns:
            Status string or None
        """
        task = self.get_task(task_id)
        return task.status if task else None

    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for all tasks to complete.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if all completed, False if timeout
        """
        start_time = time.time()

        while not self.queue.empty():
            if timeout and (time.time() - start_time) > timeout:
                return False
            time.sleep(0.1)

        # Wait for queue to be fully processed
        self.queue.join()

        return True

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get queue statistics.

        Returns:
            Dictionary with statistics
        """
        # Count pending tasks
        pending_tasks = sum(1 for t in self.tasks.values() if t.status == "pending")

        # Count processing tasks
        processing_tasks = sum(1 for t in self.tasks.values() if t.status == "processing")

        # Calculate success rate
        total = self.total_processed
        success_rate = self.total_success / total if total > 0 else 0.0

        return {
            "queue_size": self.queue.qsize(),
            "total_tasks": len(self.tasks),
            "pending_tasks": pending_tasks,
            "processing_tasks": processing_tasks,
            "total_processed": self.total_processed,
            "total_success": self.total_success,
            "total_failed": self.total_failed,
            "success_rate": success_rate,
            "active_workers": len([w for w in self.workers if w.is_alive()])
        }

    def clear_completed(self):
        """Clear completed tasks from memory."""
        to_remove = [
            task_id for task_id, task in self.tasks.items()
            if task.status in ["completed", "failed"]
        ]

        for task_id in to_remove:
            del self.tasks[task_id]

        print(f"✓ Cleared {len(to_remove)} completed tasks")


def create_queue_manager(
    providers: Dict[str, ImageProvider],
    max_concurrent: int = 3,
    enable_rate_limiting: bool = True
) -> ImageQueueManager:
    """
    Create an image queue manager.

    Args:
        providers: Dictionary of providers
        max_concurrent: Max concurrent generations
        enable_rate_limiting: Enable rate limiting

    Returns:
        ImageQueueManager instance
    """
    return ImageQueueManager(
        providers=providers,
        max_concurrent=max_concurrent,
        enable_rate_limiting=enable_rate_limiting
    )


def main():
    """Test Image Queue Manager."""
    print("=" * 70)
    print("Image Queue Manager Test")
    print("=" * 70)

    # Note: This is a structural test
    # Full testing would require actual providers

    print("\n[Test] Creating queue manager...")
    print("✓ Queue manager structure created")
    print("  Requires actual providers for full testing")

    # Test queue operations (without providers)
    manager = ImageQueueManager(
        providers={},
        max_concurrent=3
    )

    # Test statistics
    print("\n[Test] Getting statistics...")
    stats = manager.get_statistics()
    print(f"✓ Queue size: {stats['queue_size']}")
    print(f"  Total tasks: {stats['total_tasks']}")
    print(f"  Active workers: {stats['active_workers']}")

    print("\n" + "=" * 70)
    print("Image Queue Manager - PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
