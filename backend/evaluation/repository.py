"""
Evaluation Repository (Phase 13)

Provides CRUD and search capabilities over Evaluation entities, backed by MongoDB.
"""

from typing import List, Optional, Tuple, Dict, Any
from evaluation.models import Evaluation, EvaluationType, EvaluationStatus


class EvaluationRepository:
    """
    Thread-safe abstract repository for persisting Evaluations.
    Implemented as an in-memory dictionary for Phase 13 development/testing,
    with an interface compatible with Mongo.
    """
    
    def __init__(self):
        # Format: { evaluation_id: { version: Evaluation } }
        self._store: Dict[str, Dict[int, Evaluation]] = {}

    async def create(self, evaluation: Evaluation) -> Tuple[Evaluation, Optional[str]]:
        if evaluation.evaluation_id not in self._store:
            self._store[evaluation.evaluation_id] = {}
            
        if evaluation.version in self._store[evaluation.evaluation_id]:
            return None, f"Evaluation {evaluation.evaluation_id} version {evaluation.version} already exists."
            
        self._store[evaluation.evaluation_id][evaluation.version] = evaluation
        return evaluation, None

    async def get_by_id(self, evaluation_id: str, version: Optional[int] = None) -> Optional[Evaluation]:
        if evaluation_id not in self._store:
            return None
            
        versions = self._store[evaluation_id]
        if not versions:
            return None
            
        if version is not None:
            return versions.get(version)
            
        # Return the latest version
        latest_version = max(versions.keys())
        return versions[latest_version]

    async def update(self, evaluation: Evaluation) -> Tuple[Evaluation, Optional[str]]:
        # In a real Mongo repository this would be an upsert or replace_one
        if evaluation.evaluation_id not in self._store:
            return await self.create(evaluation)
            
        self._store[evaluation.evaluation_id][evaluation.version] = evaluation
        return evaluation, None

    async def search(self, 
                     task_id: Optional[str] = None, 
                     evaluation_type: Optional[EvaluationType] = None,
                     status: Optional[EvaluationStatus] = None,
                     limit: int = 50) -> List[Evaluation]:
        """
        Simple search filter.
        """
        results = []
        for eval_versions in self._store.values():
            if not eval_versions:
                continue
                
            latest = eval_versions[max(eval_versions.keys())]
            
            if task_id and latest.task_id != task_id:
                continue
            if evaluation_type and latest.evaluation_type != evaluation_type:
                continue
            if status and latest.status != status:
                continue
                
            results.append(latest)
            if len(results) >= limit:
                break
                
        return results
