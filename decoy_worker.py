"""
Decoy Worker - Background Thread for Non-Blocking Decoy Generation

This module provides a background thread architecture for generating decoys
without blocking the Streamlit UI. The thread writes directly to Supabase
and survives browser tab switches.

Architecture:
- Producer (Background Thread): Generates decoys and writes to Supabase
- Consumer (Main UI): Polls Supabase to display newly generated decoys

Usage:
    from decoy_worker import DecoyWorker

    # Start worker
    worker = DecoyWorker(api_key, supabase_url, supabase_key)
    worker.start(original_query, original_response, owner_user_id)

    # Check status
    status = worker.get_status()

    # Stop worker
    worker.stop()
"""

import threading
import uuid
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from layer3_consistency import check_and_fix_response
from layer4_decoy_factory import (
    extract_topics_from_rationale,
    generate_decoy_candidates_with_cascade,
)


class WorkerStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class DecoyTask:
    """Represents a decoy generation task."""
    task_id: str
    original_query: str
    original_response: str
    owner_user_id: Optional[str]
    source_id: str
    created_at: datetime = field(default_factory=datetime.now)
    status: WorkerStatus = WorkerStatus.IDLE
    decoys_generated: int = 0
    error_message: Optional[str] = None


class DecoyWorker:
    """
    Background worker for generating decoys without blocking the UI.

    This worker runs in a separate thread and writes directly to Supabase,
    allowing the browser tab to be switched without interrupting generation.
    """

    def __init__(
        self,
        api_key: str,
        supabase_url: str,
        supabase_key: str,
        num_decoys: int = 5,
        on_progress: Optional[Callable[[int, int], None]] = None
    ):
        """
        Initialize the decoy worker.

        Args:
            api_key: Primary chat model API key
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
            num_decoys: Target number of decoys to generate (default: 5)
            on_progress: Optional callback for progress updates (current, total)
        """
        self.api_key = api_key
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.num_decoys = num_decoys
        self.on_progress = on_progress

        # Thread management
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # Current task tracking
        self._current_task: Optional[DecoyTask] = None
        self._task_history: list[DecoyTask] = []

        # Supabase client (created in thread to avoid threading issues)
        self._supabase = None

    def _get_supabase_client(self):
        """Get or create Supabase client for the background thread."""
        if self._supabase is None:
            from supabase import create_client
            self._supabase = create_client(self.supabase_url, self.supabase_key)
        return self._supabase

    def start(
        self,
        original_query: str,
        original_response: str,
        owner_user_id: Optional[str] = None,
        source_id: Optional[str] = None
    ) -> str:
        """
        Start the background decoy generation.

        Args:
            original_query: The original user query
            original_response: The AI response to the query
            owner_user_id: The user ID of the query owner
            source_id: Optional source ID for grouping decoys

        Returns:
            task_id: Unique ID for this generation task
        """
        # Generate task ID
        task_id = str(uuid.uuid4())
        source_id = source_id or task_id

        # Create task
        task = DecoyTask(
            task_id=task_id,
            original_query=original_query,
            original_response=original_response,
            owner_user_id=owner_user_id,
            source_id=source_id
        )

        # Stop any existing thread
        self.stop()

        # Reset stop event
        self._stop_event.clear()

        # Store task
        with self._lock:
            self._current_task = task

        # Create and start thread
        self._thread = threading.Thread(
            target=self._worker_loop,
            args=(task,),
            name=f"decoy_worker_{task_id[:8]}",
            daemon=True  # Daemon thread will be killed when main process exits
        )
        self._thread.start()

        print(f"🚀 [WORKER] Started background decoy generation (task_id: {task_id[:8]}...)")
        return task_id

    def stop(self, timeout: float = 5.0) -> bool:
        """
        Stop the background worker gracefully.

        Args:
            timeout: Maximum time to wait for thread to stop (seconds)

        Returns:
            True if thread stopped successfully, False if timeout
        """
        if self._thread is None or not self._thread.is_alive():
            return True

        print(f"🛑 [WORKER] Stopping background worker...")
        self._stop_event.set()

        self._thread.join(timeout=timeout)

        if self._thread.is_alive():
            print(f"⚠️ [WORKER] Thread did not stop within timeout")
            return False

        print(f"✅ [WORKER] Background worker stopped")
        return True

    def is_running(self) -> bool:
        """Check if the worker is currently running."""
        return self._thread is not None and self._thread.is_alive()

    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the worker.

        Returns:
            Dict with status, task_id, decoys_generated, etc.
        """
        with self._lock:
            if self._current_task is None:
                return {
                    "status": WorkerStatus.IDLE.value,
                    "task_id": None,
                    "decoys_generated": 0,
                    "is_running": False
                }

            return {
                "status": self._current_task.status.value,
                "task_id": self._current_task.task_id,
                "source_id": self._current_task.source_id,
                "decoys_generated": self._current_task.decoys_generated,
                "error_message": self._current_task.error_message,
                "is_running": self.is_running(),
                "created_at": self._current_task.created_at.isoformat()
            }

    def _worker_loop(self, task: DecoyTask):
        """
        Main worker loop that runs in the background thread.

        This method:
        1. Generates decoys using the LLM
        2. Writes directly to Supabase
        3. Handles errors gracefully
        4. Respects stop_event for graceful termination
        """
        try:
            with self._lock:
                task.status = WorkerStatus.RUNNING

            print(f"🔄 [WORKER] Starting decoy generation loop...")
            print(f"   Task ID: {task.task_id[:8]}...")
            print(f"   Source ID: {task.source_id[:8]}...")
            print(f"   Owner User ID: {task.owner_user_id[:8] if task.owner_user_id else 'None'}...")

            # Get Supabase client
            supabase = self._get_supabase_client()

            target_decoys = max(1, min(self.num_decoys, 5))
            print(f"   Running cascading fallback generation (target: {target_decoys})...")

            valid_decoys, failed_attempts = generate_decoy_candidates_with_cascade(
                original_query=task.original_query,
                original_response=task.original_response,
                max_decoys=target_decoys,
            )

            print(f"   [WORKER] Candidate decoys ready: {len(valid_decoys)}")
            print(f"   [WORKER] Failed attempts captured: {len(failed_attempts)}")

            # Save valid decoys to Supabase
            print(f"\n💾 [WORKER] Saving {len(valid_decoys)} decoys to Supabase...")

            for i, decoy in enumerate(valid_decoys):
                # Check for stop signal
                if self._stop_event.is_set():
                    print(f"🛑 [WORKER] Stop signal received during save")
                    with self._lock:
                        task.status = WorkerStatus.STOPPED
                    return

                try:
                    decoy_id = str(uuid.uuid4())
                    fixed_response = check_and_fix_response(decoy['response'], self.api_key) if self.api_key else decoy['response']
                    decoy_data = {
                        'id': decoy_id,
                        'query': decoy['query'],
                        'response': fixed_response,
                        'topics': extract_topics_from_rationale(decoy.get('rationale', '')),
                        'source_id': task.source_id,
                        'owner_user_id': task.owner_user_id,
                        'created_at': datetime.now().isoformat()
                    }

                    result = supabase.table('global_decoys').insert(decoy_data).execute()

                    if result.data:
                        with self._lock:
                            task.decoys_generated += 1
                        print(f"   ✅ Saved decoy {i+1}/{len(valid_decoys)}")

                        # Call progress callback if provided
                        if self.on_progress:
                            try:
                                self.on_progress(task.decoys_generated, target_decoys)
                            except:
                                pass  # Ignore callback errors

                except Exception as e:
                    print(f"   ❌ Error saving decoy {i}: {e}")

            # Mark as completed
            with self._lock:
                task.status = WorkerStatus.COMPLETED

            print(f"\n✅ [WORKER] Generation complete! Generated {task.decoys_generated} decoys.")

        except Exception as e:
            print(f"❌ [WORKER] Fatal error: {e}")
            print(f"   Traceback: {traceback.format_exc()}")
            with self._lock:
                task.status = WorkerStatus.FAILED
                task.error_message = str(e)

    def _get_decoy_system_prompt(self) -> str:
        """Get the system prompt for decoy generation."""
        return """You are the 'Confuser' Privacy Module - an expert in deep semantic obfuscation.
Task: Generate a 'Synthetic Decoy' that preserves the CORE INTENT but is UNRECOGNIZABLE to the original author.

GOAL: If the original author sees the decoy, they should NOT recognize it as derived from their query.

PROTOCOL - EXECUTE ALL 6 MANDATORY TRANSFORMATIONS:

1. **DOMAIN HARD SWAP** (Critical):
   - Change the specific field/tool/condition to a PARALLEL but DIFFERENT domain.

2. **ENTITY & METRIC SWAP**:
   - Change test types, institutions, metrics to equivalent but different ones.

3. **NUMERIC SHIFT**:
   - Ages: +/- 2-5 years
   - Scores: Change to equivalent level in different system

4. **SEQUENCE RESTRUCTURING** (Critical for unrecognizability):
   - REORDER the information elements in the sentence.

5. **TONE & PERSPECTIVE SHIFT**:
   - Change emotional tone and perspective.

6. **SYNTACTIC VARIATION**:
   - Change sentence structure and connectors.

OUTPUT FORMAT (JSON ONLY):
{
  "rationale": "Brief explanation of transformations applied",
  "query": "The deeply transformed query",
  "response": "The correspondingly transformed response"
}
"""

    def _get_mission_context(self) -> str:
        """Get the mission context for decoy generation."""
        return """
[MISSION OBJECTIVE]
Target Similarity: 0.75 to 0.85 (The "Goldilocks Zone").
Current Status: You are generating a decoy.

CRITICAL REQUIREMENTS:
1. The original author must NOT recognize the decoy as derived from their query
2. Apply ALL 6 transformations, especially SEQUENCE RESTRUCTURING
3. Change the ORDER of information elements, not just the entities
4. Shift the tone and perspective to sound like a DIFFERENT person
"""


# Global worker instance for session management
_global_workers: Dict[str, DecoyWorker] = {}


def get_or_create_worker(
    session_id: str,
    api_key: str,
    supabase_url: str,
    supabase_key: str
) -> DecoyWorker:
    """
    Get or create a worker for a specific session.

    Args:
        session_id: Unique session identifier
        api_key: Primary chat model API key
        supabase_url: Supabase project URL
        supabase_key: Supabase API key

    Returns:
        DecoyWorker instance
    """
    global _global_workers

    if session_id not in _global_workers:
        _global_workers[session_id] = DecoyWorker(
            api_key=api_key,
            supabase_url=supabase_url,
            supabase_key=supabase_key
        )

    return _global_workers[session_id]


def stop_worker(session_id: str) -> bool:
    """
    Stop and remove a worker for a specific session.

    Args:
        session_id: Unique session identifier

    Returns:
        True if worker was stopped, False if not found
    """
    global _global_workers

    if session_id in _global_workers:
        worker = _global_workers[session_id]
        worker.stop()
        del _global_workers[session_id]
        return True

    return False


def get_worker_status(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get status of a worker for a specific session.

    Args:
        session_id: Unique session identifier

    Returns:
        Status dict or None if no worker exists
    """
    global _global_workers

    if session_id in _global_workers:
        return _global_workers[session_id].get_status()

    return None
