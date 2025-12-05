"""Adaptive risk scoring and behaviour analysis helpers.

This module implements the pieces that the test-suite exercises: a light
weight behavioural profile store backed by SQLite, feature extraction for
requests, and scoring helpers that assign risk levels and behavioural
patterns.  The implementation deliberately favours determinism and small
dependencies so it can run inside the unit tests without heavyweight ML
models.
"""

from __future__ import annotations

import datetime
import json
import math
import sqlite3
import threading
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, cast


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)

try:  # Optional dependency used only for array conversions
    import numpy as np
except Exception:  # pragma: no cover - numpy not installed
    np = None  # type: ignore

ML_AVAILABLE = np is not None

from app.models import EvaluateRequest, EvaluateResponse


SENSITIVE_KEYWORDS = {
    "password",
    "secret",
    "token",
    "credential",
    "confidential",
    "ssn",
    "social security",
    "credit card",
}


class RiskLevel(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    CRITICAL = "critical"


class BehaviorPattern(str, Enum):
    NORMAL = "normal"
    SUSPICIOUS = "suspicious"
    ANOMALOUS = "anomalous"
    MALICIOUS = "malicious"


@dataclass
class RiskFeatures:
    text_length: int
    endpoint_frequency: float
    time_of_day: int
    day_of_week: int
    user_violation_rate: float
    endpoint_violation_rate: float
    recent_violations: int
    sensitive_keywords: int
    data_entropy: float
    pattern_matches: int
    request_volume_spike: bool
    off_hours_access: bool
    geographic_anomaly: bool
    current_load: float
    error_rate: float

    def to_array(self) -> List[float]:
        values: List[float] = [
            float(self.text_length),
            self.endpoint_frequency,
            float(self.time_of_day),
            float(self.day_of_week),
            self.user_violation_rate,
            self.endpoint_violation_rate,
            float(self.recent_violations),
            float(self.sensitive_keywords),
            self.data_entropy,
            float(self.pattern_matches),
            1.0 if self.request_volume_spike else 0.0,
            1.0 if self.off_hours_access else 0.0,
            1.0 if self.geographic_anomaly else 0.0,
            self.current_load,
            self.error_rate,
        ]
        if ML_AVAILABLE and np is not None:
            return np.asarray(values, dtype=float).tolist()
        return values


@dataclass
class BehaviorProfile:
    identifier: str
    identifier_type: str  # e.g. "user" or "endpoint"
    total_requests: int
    violation_count: int
    violation_rate: float
    active_hours: List[int]
    active_days: List[int]
    request_frequency: float
    typical_text_length: float
    common_endpoints: List[str]
    sensitive_content_frequency: float
    recent_anomalies: int
    escalation_count: int
    last_violation: Optional[datetime.datetime]
    trust_score: float
    learning_rate: float
    created_at: datetime.datetime
    updated_at: datetime.datetime


@dataclass
class RiskAssessment:
    request: EvaluateRequest
    response: EvaluateResponse
    risk_score: float
    risk_level: RiskLevel
    behavior_pattern: BehaviorPattern
    confidence: float
    contributing_factors: List[str]
    anomaly_indicators: List[str]
    recommended_action: str
    adaptive_threshold: float
    timestamp: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))


class HistoricalDataManager:
    """Minimal persistence layer for behavioural data."""

    def __init__(self, db_path: str = "logs/risk_history.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialise_db()
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _initialise_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS policy_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_id TEXT,
                    endpoint TEXT,
                    agent_id TEXT,
                    decision TEXT,
                    risk_score REAL,
                    anomaly_score REAL,
                    rule_ids TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS behavior_profiles (
                    identifier TEXT NOT NULL,
                    identifier_type TEXT NOT NULL,
                    total_requests INTEGER NOT NULL,
                    violation_count INTEGER NOT NULL,
                    violation_rate REAL NOT NULL,
                    active_hours TEXT,
                    active_days TEXT,
                    request_frequency REAL,
                    typical_text_length REAL,
                    common_endpoints TEXT,
                    sensitive_content_frequency REAL,
                    recent_anomalies INTEGER,
                    escalation_count INTEGER,
                    last_violation TEXT,
                    trust_score REAL,
                    learning_rate REAL,
                    created_at TEXT,
                    updated_at TEXT,
                    PRIMARY KEY (identifier, identifier_type)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS risk_assessments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_id TEXT,
                    endpoint TEXT,
                    risk_score REAL,
                    risk_level TEXT,
                    behavior_pattern TEXT,
                    recommended_action TEXT
                )
                """
            )
            conn.commit()

    def _ensure_schema(self) -> None:
        expected_tables = {
            "policy_decisions": {
                "timestamp": "TEXT",
                "user_id": "TEXT",
                "endpoint": "TEXT",
                "agent_id": "TEXT",
                "decision": "TEXT",
                "risk_score": "REAL",
                "anomaly_score": "REAL",
                "rule_ids": "TEXT",
            },
            "behavior_profiles": {
                "total_requests": "INTEGER DEFAULT 0",
                "violation_count": "INTEGER DEFAULT 0",
                "violation_rate": "REAL DEFAULT 0",
                "active_hours": "TEXT",
                "active_days": "TEXT",
                "request_frequency": "REAL DEFAULT 0",
                "typical_text_length": "REAL DEFAULT 0",
                "common_endpoints": "TEXT",
                "sensitive_content_frequency": "REAL DEFAULT 0",
                "recent_anomalies": "INTEGER DEFAULT 0",
                "escalation_count": "INTEGER DEFAULT 0",
                "last_violation": "TEXT",
                "trust_score": "REAL DEFAULT 0.5",
                "learning_rate": "REAL DEFAULT 0.1",
                "created_at": "TEXT",
                "updated_at": "TEXT",
            },
            "risk_assessments": {
                "timestamp": "TEXT",
                "user_id": "TEXT",
                "endpoint": "TEXT",
                "risk_score": "REAL",
                "risk_level": "TEXT",
                "behavior_pattern": "TEXT",
                "recommended_action": "TEXT",
            },
        }

        with self._connect() as conn:
            for table, columns in expected_tables.items():
                existing = {
                    row[1]
                    for row in conn.execute(f"PRAGMA table_info({table})")
                }
                for column, definition in columns.items():
                    if column not in existing:
                        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_behavior_profiles_identifier_type
                ON behavior_profiles(identifier, identifier_type)
                """
            )
            conn.commit()

    def store_decision(
        self,
        request: EvaluateRequest,
        response: EvaluateResponse,
        features: RiskFeatures,
        risk_score: float,
        anomaly_score: float,
    ) -> None:
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO policy_decisions (
                        timestamp, user_id, endpoint, agent_id, decision,
                        risk_score, anomaly_score, rule_ids
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        _utcnow().isoformat(),
                        getattr(request, "user_id", None),
                        request.endpoint,
                        request.agent_id,
                        response.action,
                        risk_score,
                        anomaly_score,
                        json.dumps(response.rule_ids),
                    ),
                )
                conn.commit()

    def get_historical_data(self, days: int = 7) -> List[Dict[str, Any]]:
        cutoff = _utcnow() - datetime.timedelta(days=days)
        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT timestamp, user_id, endpoint, decision, risk_score, anomaly_score
                    FROM policy_decisions WHERE timestamp >= ? ORDER BY timestamp DESC
                    """,
                    (cutoff.isoformat(),),
                ).fetchall()

        result: List[Dict[str, Any]] = []
        for ts, user_id, endpoint, decision, risk_score, anomaly_score in rows:
            result.append(
                {
                    "timestamp": ts,
                    "user_id": user_id,
                    "endpoint": endpoint,
                    "decision": decision,
                    "risk_score": risk_score,
                    "anomaly_score": anomaly_score,
                }
            )
        return result

    def store_behavior_profile(self, profile: BehaviorProfile) -> None:
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO behavior_profiles (
                        identifier, identifier_type, total_requests, violation_count,
                        violation_rate, active_hours, active_days, request_frequency,
                        typical_text_length, common_endpoints, sensitive_content_frequency,
                        recent_anomalies, escalation_count, last_violation, trust_score,
                        learning_rate, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(identifier, identifier_type) DO UPDATE SET
                        total_requests=excluded.total_requests,
                        violation_count=excluded.violation_count,
                        violation_rate=excluded.violation_rate,
                        active_hours=excluded.active_hours,
                        active_days=excluded.active_days,
                        request_frequency=excluded.request_frequency,
                        typical_text_length=excluded.typical_text_length,
                        common_endpoints=excluded.common_endpoints,
                        sensitive_content_frequency=excluded.sensitive_content_frequency,
                        recent_anomalies=excluded.recent_anomalies,
                        escalation_count=excluded.escalation_count,
                        last_violation=excluded.last_violation,
                        trust_score=excluded.trust_score,
                        learning_rate=excluded.learning_rate,
                        updated_at=excluded.updated_at
                    """,
                    (
                        profile.identifier,
                        profile.identifier_type,
                        profile.total_requests,
                        profile.violation_count,
                        profile.violation_rate,
                        json.dumps(profile.active_hours),
                        json.dumps(profile.active_days),
                        profile.request_frequency,
                        profile.typical_text_length,
                        json.dumps(profile.common_endpoints),
                        profile.sensitive_content_frequency,
                        profile.recent_anomalies,
                        profile.escalation_count,
                        profile.last_violation.isoformat() if profile.last_violation else None,
                        profile.trust_score,
                        profile.learning_rate,
                        profile.created_at.isoformat(),
                        profile.updated_at.isoformat(),
                    ),
                )
                conn.commit()

    def record_assessment_summary(
        self,
        request: EvaluateRequest,
        assessment: RiskAssessment,
    ) -> None:
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO risk_assessments (
                        timestamp, user_id, endpoint, risk_score, risk_level,
                        behavior_pattern, recommended_action
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        assessment.timestamp.isoformat(),
                        getattr(request, "user_id", None),
                        request.endpoint,
                        assessment.risk_score,
                        assessment.risk_level.value,
                        assessment.behavior_pattern.value,
                        assessment.recommended_action,
                    ),
                )
                conn.commit()

    def get_behavior_profile(self, identifier: str, identifier_type: str) -> Optional[BehaviorProfile]:
        with self._lock:
            with self._connect() as conn:
                row = conn.execute(
                    """
                    SELECT identifier, identifier_type, total_requests, violation_count,
                           violation_rate, active_hours, active_days, request_frequency,
                           typical_text_length, common_endpoints, sensitive_content_frequency,
                           recent_anomalies, escalation_count, last_violation, trust_score,
                           learning_rate, created_at, updated_at
                    FROM behavior_profiles
                    WHERE identifier=? AND identifier_type=?
                    """,
                    (identifier, identifier_type),
                ).fetchone()

        if not row:
            return None

        (
            _identifier,
            _identifier_type,
            total_requests,
            violation_count,
            violation_rate,
            active_hours,
            active_days,
            request_frequency,
            typical_text_length,
            common_endpoints,
            sensitive_content_frequency,
            recent_anomalies,
            escalation_count,
            last_violation,
            trust_score,
            learning_rate,
            created_at,
            updated_at,
        ) = row

        def _loads(value: Optional[str]) -> List[Any]:
            if not value:
                return []
            try:
                loaded = json.loads(value)
                if isinstance(loaded, list):
                    return cast(List[Any], loaded)
            except json.JSONDecodeError:
                pass
            return []

        profile = BehaviorProfile(
            identifier=_identifier,
            identifier_type=_identifier_type,
            total_requests=total_requests,
            violation_count=violation_count,
            violation_rate=violation_rate,
            active_hours=[int(x) for x in _loads(active_hours)],
            active_days=[int(x) for x in _loads(active_days)],
            request_frequency=request_frequency or 0.0,
            typical_text_length=typical_text_length or 0.0,
            common_endpoints=[str(x) for x in _loads(common_endpoints)],
            sensitive_content_frequency=sensitive_content_frequency or 0.0,
            recent_anomalies=recent_anomalies or 0,
            escalation_count=escalation_count or 0,
            last_violation=datetime.datetime.fromisoformat(last_violation) if last_violation else None,
            trust_score=trust_score or 0.5,
            learning_rate=learning_rate or 0.1,
            created_at=datetime.datetime.fromisoformat(created_at)
            if created_at
            else _utcnow(),
            updated_at=datetime.datetime.fromisoformat(updated_at)
            if updated_at
            else _utcnow(),
        )

        return profile


class BehaviorAnalyzer:
    def __init__(self, data_manager: HistoricalDataManager):
        self.data_manager = data_manager

    def get_or_create_profile(self, identifier: str, identifier_type: str) -> BehaviorProfile:
        profile = self.data_manager.get_behavior_profile(identifier, identifier_type)
        if profile:
            return profile

        now = _utcnow()
        profile = BehaviorProfile(
            identifier=identifier,
            identifier_type=identifier_type,
            total_requests=0,
            violation_count=0,
            violation_rate=0.0,
            active_hours=[],
            active_days=[],
            request_frequency=0.0,
            typical_text_length=0.0,
            common_endpoints=[],
            sensitive_content_frequency=0.0,
            recent_anomalies=0,
            escalation_count=0,
            last_violation=None,
            trust_score=0.5,
            learning_rate=0.1,
            created_at=now,
            updated_at=now,
        )
        self.data_manager.store_behavior_profile(profile)
        return profile

    def update_profile(
        self,
        identifier: str,
        identifier_type: str,
        request: EvaluateRequest,
        response: EvaluateResponse,
    ) -> BehaviorProfile:
        profile = self.get_or_create_profile(identifier, identifier_type)

        violation = response.action in {"block", "flag"}
        profile.total_requests += 1
        if violation:
            profile.violation_count += 1
            profile.last_violation = _utcnow()
            profile.trust_score = max(0.0, profile.trust_score - 0.15)
        else:
            profile.trust_score = min(1.0, profile.trust_score + 0.05)

        profile.violation_rate = (
            profile.violation_count / profile.total_requests if profile.total_requests else 0.0
        )

        now = _utcnow()
        profile.updated_at = now

        # Maintain activity windows
        if now.hour not in profile.active_hours:
            profile.active_hours.append(now.hour)
        if now.weekday() not in profile.active_days:
            profile.active_days.append(now.weekday())

        profile.typical_text_length = _blend_average(
            profile.typical_text_length,
            len(request.text or ""),
            profile.total_requests,
        )

        if request.endpoint and request.endpoint not in profile.common_endpoints:
            profile.common_endpoints.append(request.endpoint)
            if len(profile.common_endpoints) > 10:
                profile.common_endpoints = profile.common_endpoints[-10:]

        sensitive_hit = any(keyword in (request.text or "").lower() for keyword in SENSITIVE_KEYWORDS)
        if sensitive_hit:
            total_hits = profile.sensitive_content_frequency * (profile.total_requests - 1) + 1
        else:
            total_hits = profile.sensitive_content_frequency * (profile.total_requests - 1)
        profile.sensitive_content_frequency = total_hits / max(profile.total_requests, 1)

        self.data_manager.store_behavior_profile(profile)
        return profile

    def detect_anomalies(
        self, identifier: str, identifier_type: str, request: EvaluateRequest
    ) -> List[str]:
        profile = self.get_or_create_profile(identifier, identifier_type)
        if profile.total_requests < 5:
            return []

        anomalies: List[str] = []
        now = datetime.datetime.now()

        if profile.active_hours and now.hour not in profile.active_hours:
            anomalies.append("unusual_time_access")
        if profile.active_days and now.weekday() not in profile.active_days:
            anomalies.append("unusual_day_access")
        if profile.common_endpoints and request.endpoint not in profile.common_endpoints:
            anomalies.append("unusual_endpoint")

        typical_length = profile.typical_text_length or 1.0
        deviation = abs(len(request.text or "") - typical_length) / typical_length
        if typical_length > 10 and deviation > 0.6:
            anomalies.append("text_length_deviation")

        return anomalies


class RiskScoringEngine:
    def __init__(self, data_manager: Optional[HistoricalDataManager] = None):
        self.data_manager = data_manager or HistoricalDataManager()
        self.behavior_analyzer = BehaviorAnalyzer(self.data_manager)

    def extract_features(self, request: EvaluateRequest) -> RiskFeatures:
        user_key = getattr(request, "user_id", None) or request.agent_id or "anonymous"
        user_profile = self.behavior_analyzer.get_or_create_profile(user_key, "user")
        endpoint_profile = self.behavior_analyzer.get_or_create_profile(request.endpoint, "endpoint")

        now = _utcnow()
        text = request.text or ""
        text_len = len(text)
        sensitive_hits = _count_keywords(text.lower(), SENSITIVE_KEYWORDS)

        features = RiskFeatures(
            text_length=text_len,
            endpoint_frequency=float(endpoint_profile.total_requests) / max(
                1, endpoint_profile.total_requests + endpoint_profile.violation_count
            ),
            time_of_day=now.hour,
            day_of_week=now.weekday(),
            user_violation_rate=user_profile.violation_rate,
            endpoint_violation_rate=endpoint_profile.violation_rate,
            recent_violations=min(user_profile.violation_count, 10),
            sensitive_keywords=sensitive_hits,
            data_entropy=_normalised_entropy(text),
            pattern_matches=0,
            request_volume_spike=False,
            off_hours_access=now.hour < 7 or now.hour > 20,
            geographic_anomaly=False,
            current_load=0.0,
            error_rate=0.0,
        )
        return features

    def _calculate_base_risk(self, features: RiskFeatures, response: EvaluateResponse) -> float:
        score = 0.0
        if response.action == "block":
            score += 0.25
        elif response.action == "flag":
            score += 0.18

        score += features.user_violation_rate * 0.25
        score += features.endpoint_violation_rate * 0.15
        score += min(features.recent_violations, 5) * 0.04
        score += min(features.sensitive_keywords, 5) * 0.05
        score += features.data_entropy * 0.1
        if features.off_hours_access:
            score += 0.05
        if features.request_volume_spike:
            score += 0.05
        if features.geographic_anomaly:
            score += 0.05

        return max(0.0, min(1.0, score))

    @staticmethod
    def _determine_risk_level(score: float) -> RiskLevel:
        if score >= 0.9:
            return RiskLevel.CRITICAL
        if score >= 0.75:
            return RiskLevel.VERY_HIGH
        if score >= 0.55:
            return RiskLevel.HIGH
        if score >= 0.35:
            return RiskLevel.MEDIUM
        if score >= 0.15:
            return RiskLevel.LOW
        return RiskLevel.VERY_LOW

    @staticmethod
    def _determine_behavior_pattern(score: float, anomalies: Sequence[str]) -> BehaviorPattern:
        if score >= 0.85 or len(anomalies) >= 3:
            return BehaviorPattern.MALICIOUS
        if len(anomalies) >= 2:
            return BehaviorPattern.ANOMALOUS
        if score >= 0.6 or anomalies:
            return BehaviorPattern.SUSPICIOUS
        return BehaviorPattern.NORMAL

    def _calculate_adaptive_threshold(
        self, request: EvaluateRequest, features: RiskFeatures, base_score: float
    ) -> float:
        user_key = getattr(request, "user_id", None) or request.agent_id or "anonymous"
        profile = self.behavior_analyzer.get_or_create_profile(user_key, "user")

        threshold = 0.5
        threshold += (0.5 - profile.trust_score) * 0.4
        threshold += features.user_violation_rate * 0.2
        threshold += features.endpoint_violation_rate * 0.1
        threshold += min(features.recent_violations, 5) * 0.02
        threshold = max(0.05, min(0.95, threshold))
        threshold = (threshold + base_score) / 2
        return threshold

    def assess_risk(self, request: EvaluateRequest, response: EvaluateResponse) -> RiskAssessment:
        features = self.extract_features(request)
        user_key = getattr(request, "user_id", None) or request.agent_id or "anonymous"
        anomalies = self.behavior_analyzer.detect_anomalies(user_key, "user", request)
        base_risk = self._calculate_base_risk(features, response)
        risk_score = min(1.0, base_risk + 0.1 * len(anomalies))
        risk_level = self._determine_risk_level(risk_score)
        behavior_pattern = self._determine_behavior_pattern(risk_score, anomalies)

        confidence = 0.85 if ML_AVAILABLE else 0.65
        contributing_factors = [
            f"user_violation_rate={features.user_violation_rate:.2f}",
            f"endpoint_violation_rate={features.endpoint_violation_rate:.2f}",
            f"sensitive_keywords={features.sensitive_keywords}",
        ]
        contributing_factors.extend(anomalies)

        adaptive_threshold = self._calculate_adaptive_threshold(request, features, base_risk)

        if risk_level in {RiskLevel.CRITICAL, RiskLevel.VERY_HIGH}:
            recommended_action = "block"
        elif risk_level in {RiskLevel.HIGH, RiskLevel.MEDIUM}:
            recommended_action = "flag"
        else:
            recommended_action = response.action or "allow"

        assessment = RiskAssessment(
            request=request,
            response=response,
            risk_score=risk_score,
            risk_level=risk_level,
            behavior_pattern=behavior_pattern,
            confidence=confidence,
            contributing_factors=contributing_factors,
            anomaly_indicators=list(anomalies),
            recommended_action=recommended_action,
            adaptive_threshold=adaptive_threshold,
        )
        return assessment

    def post_process_decision(
        self, request: EvaluateRequest, response: EvaluateResponse, anomaly_score: float
    ) -> RiskAssessment:
        features = self.extract_features(request)

        user_key = getattr(request, "user_id", None) or request.agent_id or "anonymous"
        self.behavior_analyzer.update_profile(user_key, "user", request, response)
        self.behavior_analyzer.update_profile(request.endpoint, "endpoint", request, response)

        assessment = self.assess_risk(request, response)

        self.data_manager.store_decision(request, response, features, assessment.risk_score, anomaly_score)
        self.data_manager.record_assessment_summary(request, assessment)

        return assessment

_risk_engine_singleton: Optional[RiskScoringEngine] = None


def get_risk_scoring_engine() -> RiskScoringEngine:
    global _risk_engine_singleton
    if _risk_engine_singleton is None:
        _risk_engine_singleton = RiskScoringEngine()
    return _risk_engine_singleton


def _blend_average(current: float, new_value: float, count: int) -> float:
    if count <= 1:
        return float(new_value)
    return ((current * (count - 1)) + new_value) / count


def _count_keywords(text: str, keywords: Iterable[str]) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def _normalised_entropy(text: str) -> float:
    if not text:
        return 0.0
    counts = Counter(text)
    total = float(len(text))
    entropy = -sum((count / total) * math.log2(count / total) for count in counts.values())
    # Normalise by maximum entropy for given alphabet size (cap at 32 for stability)
    max_entropy = math.log2(min(len(counts), 32) or 1)
    if max_entropy == 0:
        return 0.0
    return max(0.0, min(1.0, entropy / max_entropy))
