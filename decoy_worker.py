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
import time
import uuid
import json
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


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
        num_decoys: int = 3,
        on_progress: Optional[Callable[[int, int], None]] = None
    ):
        """
        Initialize the decoy worker.

        Args:
            api_key: DeepSeek API key
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
            num_decoys: Target number of decoys to generate (default: 3)
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
            owner_user_id: The user ID of the query owner (for email relay)
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

            # Import here to avoid circular imports and ensure fresh imports in thread
            from openai import OpenAI
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity

            # Initialize API client
            client = OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com")

            # Load embedding model for QC
            print(f"   Loading QC model...")
            qc_model = SentenceTransformer('BAAI/bge-small-en-v1.5')
            original_embedding = qc_model.encode([task.original_query], convert_to_numpy=True)

            # Get Supabase client
            supabase = self._get_supabase_client()

            # Configuration
            TARGET_DECOYS = self.num_decoys
            MAX_BATCHES = 4
            BATCH_SIZE = 5

            valid_decoys = []
            batch_count = 0

            # System prompt for decoy generation
            DECOY_SYSTEM_PROMPT = self._get_decoy_system_prompt()

            # Mission context
            mission_context = self._get_mission_context()
            user_content = f"{mission_context}\n\nOriginal Query: {task.original_query}\nOriginal Response: {task.original_response}"

            while len(valid_decoys) < TARGET_DECOYS and batch_count < MAX_BATCHES:
                # Check for stop signal
                if self._stop_event.is_set():
                    print(f"🛑 [WORKER] Stop signal received, exiting...")
                    with self._lock:
                        task.status = WorkerStatus.STOPPED
                    return

                batch_count += 1
                print(f"\n📦 [WORKER] Batch {batch_count}/{MAX_BATCHES}...")

                batch_candidates = []

                for attempt in range(BATCH_SIZE):
                    # Check for stop signal
                    if self._stop_event.is_set():
                        print(f"🛑 [WORKER] Stop signal received during batch")
                        with self._lock:
                            task.status = WorkerStatus.STOPPED
                        return

                    try:
                        response = client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[
                                {"role": "system", "content": DECOY_SYSTEM_PROMPT},
                                {"role": "user", "content": user_content}
                            ],
                            temperature=1.0,
                            response_format={"type": "json_object"},
                            max_tokens=2000
                        )

                        content = response.choices[0].message.content
                        if not content:
                            continue

                        result = json.loads(content)
                        if not isinstance(result, dict):
                            continue

                        decoy_query = result.get('query', '').strip()
                        decoy_response = result.get('response', '').strip()
                        rationale = result.get('rationale', '')

                        if not decoy_query or not decoy_response:
                            continue

                        if decoy_query == task.original_query.strip():
                            continue

                        # Calculate similarity
                        decoy_embedding = qc_model.encode([decoy_query], convert_to_numpy=True)
                        similarity = float(cosine_similarity(original_embedding, decoy_embedding)[0][0])

                        decoy = {
                            'query': decoy_query,
                            'response': decoy_response,
                            'rationale': rationale,
                            'similarity': similarity
                        }

                        batch_candidates.append({'decoy': decoy, 'sim': similarity})

                        # Fast Track (Goldilocks Zone)
                        if 0.75 <= similarity <= 0.85:
                            print(f"   ⚡️ Fast Track Hit! (sim: {similarity:.3f})")
                            valid_decoys.append(decoy)
                            break

                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        print(f"   ⚠️ Attempt error: {e}")
                        continue

                # Judge fallback if no fast track hit
                if batch_candidates and len(valid_decoys) < TARGET_DECOYS:
                    if not any(0.75 <= c['sim'] <= 0.85 for c in batch_candidates):
                        # Pick closest to 0.80
                        best = min(batch_candidates, key=lambda x: abs(x['sim'] - 0.80))
                        if best['sim'] >= 0.60:  # Minimum threshold
                            print(f"   📋 Accepting best candidate (sim: {best['sim']:.3f})")
                            valid_decoys.append(best['decoy'])

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
                    decoy_data = {
                        'id': decoy_id,
                        'query': decoy['query'],
                        'response': decoy['response'],
                        'topics': [],
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
                                self.on_progress(task.decoys_generated, TARGET_DECOYS)
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
        api_key: DeepSeek API key
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
