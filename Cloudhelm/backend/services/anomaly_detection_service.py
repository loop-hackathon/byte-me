"""
Anomaly detection service using ML models (ECOD and IsolationForest).
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
import json
import numpy as np

from backend.models.health import ServiceMetric, MetricsAnomaly

logger = logging.getLogger(__name__)

# Try to import ML libraries
try:
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    logger.warning("scikit-learn not available, IsolationForest disabled")
    SKLEARN_AVAILABLE = False

try:
    from pyod.models.ecod import ECOD
    PYOD_AVAILABLE = True
except ImportError:
    logger.warning("pyod not available, ECOD disabled")
    PYOD_AVAILABLE = False


class AnomalyDetectionService:
    """Service for ML-based anomaly detection in service metrics."""
    
    def __init__(self, contamination: float = 0.1):
        """
        Initialize anomaly detection models.
        
        Args:
            contamination: Expected proportion of anomalies (0.0-0.5)
        """
        self.contamination = contamination
        
        # Initialize models if libraries are available
        if SKLEARN_AVAILABLE:
            self.isolation_forest = IsolationForest(
                contamination=contamination,
                random_state=42,
                n_estimators=100
            )
        else:
            self.isolation_forest = None
        
        if PYOD_AVAILABLE:
            self.ecod_model = ECOD(contamination=contamination)
        else:
            self.ecod_model = None
    
    @staticmethod
    def get_metric_features(
        db: Session,
        service_name: str,
        hours: int = 24
    ) -> np.ndarray:
        """
        Extract feature vectors from service metrics.
        
        Args:
            db: Database session
            service_name: Service name
            hours: Number of hours to look back
        
        Returns:
            NumPy array of shape (n_samples, n_features)
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        metrics = db.query(ServiceMetric).filter(
            ServiceMetric.service_name == service_name,
            ServiceMetric.timestamp >= cutoff_time
        ).order_by(ServiceMetric.timestamp).all()
        
        if not metrics:
            return np.array([])
        
        # Extract features: [request_rate, error_rate, latency_p99, cpu_usage, memory_usage]
        features = []
        for m in metrics:
            features.append([
                m.request_rate,
                m.error_rate,
                m.latency_p99,
                m.cpu_usage,
                m.memory_usage
            ])
        
        return np.array(features)
    
    def detect_anomalies(
        self,
        db: Session,
        service_name: str,
        hours: int = 24
    ) -> List[Dict]:
        """
        Detect anomalies in service metrics using ML models.
        
        Args:
            db: Database session
            service_name: Service name
            hours: Number of hours to analyze
        
        Returns:
            List of detected anomalies
        """
        # Get feature vectors
        features = self.get_metric_features(db, service_name, hours)
        
        if len(features) < 10:
            logger.warning(f"Insufficient data for anomaly detection: {len(features)} samples")
            return []
        
        # Get corresponding metrics
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        metrics = db.query(ServiceMetric).filter(
            ServiceMetric.service_name == service_name,
            ServiceMetric.timestamp >= cutoff_time
        ).order_by(ServiceMetric.timestamp).all()
        
        anomalies = []
        
        # Run IsolationForest if available
        if self.isolation_forest and SKLEARN_AVAILABLE:
            try:
                # Fit and predict
                predictions = self.isolation_forest.fit_predict(features)
                scores = self.isolation_forest.score_samples(features)
                
                # Normalize scores to 0-1 range (higher = more anomalous)
                # IsolationForest scores are negative, lower = more anomalous
                normalized_scores = 1.0 / (1.0 + np.exp(scores))
                
                # Find anomalies (predictions == -1)
                for i, (pred, score) in enumerate(zip(predictions, normalized_scores)):
                    if pred == -1:
                        anomaly = self._create_anomaly_dict(
                            metrics[i],
                            score,
                            features[i],
                            features,
                            'IsolationForest'
                        )
                        anomalies.append(anomaly)
                
                logger.info(f"IsolationForest detected {len([p for p in predictions if p == -1])} anomalies")
            except Exception as e:
                logger.error(f"IsolationForest error: {e}")
        
        # Run ECOD if available
        if self.ecod_model and PYOD_AVAILABLE:
            try:
                # Fit and predict
                self.ecod_model.fit(features)
                predictions = self.ecod_model.labels_  # 0 = normal, 1 = anomaly
                scores = self.ecod_model.decision_scores_
                
                # Normalize scores to 0-1 range
                if len(scores) > 0:
                    min_score = scores.min()
                    max_score = scores.max()
                    if max_score > min_score:
                        normalized_scores = (scores - min_score) / (max_score - min_score)
                    else:
                        normalized_scores = scores
                else:
                    normalized_scores = scores
                
                # Find anomalies (predictions == 1)
                for i, (pred, score) in enumerate(zip(predictions, normalized_scores)):
                    if pred == 1:
                        anomaly = self._create_anomaly_dict(
                            metrics[i],
                            score,
                            features[i],
                            features,
                            'ECOD'
                        )
                        # Only add if not already detected by IsolationForest
                        if not any(a['timestamp'] == anomaly['timestamp'] for a in anomalies):
                            anomalies.append(anomaly)
                
                logger.info(f"ECOD detected {len([p for p in predictions if p == 1])} anomalies")
            except Exception as e:
                logger.error(f"ECOD error: {e}")
        
        return anomalies
    
    def _create_anomaly_dict(
        self,
        metric: ServiceMetric,
        anomaly_score: float,
        feature_vector: np.ndarray,
        all_features: np.ndarray,
        detector: str
    ) -> Dict:
        """
        Create anomaly dictionary from detection results.
        
        Args:
            metric: ServiceMetric that is anomalous
            anomaly_score: Anomaly score (0-1)
            feature_vector: Feature vector for this metric
            all_features: All feature vectors for comparison
            detector: Name of detector ('IsolationForest' or 'ECOD')
        
        Returns:
            Anomaly dictionary
        """
        # Identify affected metrics
        affected_metrics = self.identify_affected_metrics(feature_vector, all_features)
        
        # Assign severity
        severity = self.assign_severity(anomaly_score)
        
        # Create description
        description = f"{detector} detected anomaly in {', '.join(affected_metrics)}"
        
        return {
            'service_name': metric.service_name,
            'timestamp': metric.timestamp,
            'anomaly_type': 'metric_deviation',
            'severity': severity,
            'anomaly_score': float(anomaly_score),
            'affected_metrics': affected_metrics,
            'description': description
        }
    
    @staticmethod
    def assign_severity(anomaly_score: float) -> str:
        """
        Assign severity level based on anomaly score.
        
        Args:
            anomaly_score: Anomaly score (0-1)
        
        Returns:
            Severity: 'low', 'medium', 'high', or 'critical'
        """
        if anomaly_score >= 0.8:
            return 'critical'
        elif anomaly_score >= 0.6:
            return 'high'
        elif anomaly_score >= 0.4:
            return 'medium'
        else:
            return 'low'
    
    @staticmethod
    def identify_affected_metrics(
        feature_vector: np.ndarray,
        all_features: np.ndarray
    ) -> List[str]:
        """
        Identify which metrics are anomalous by comparing to historical data.
        
        Args:
            feature_vector: Feature vector for anomalous point
            all_features: All feature vectors for comparison
        
        Returns:
            List of affected metric names
        """
        metric_names = ['request_rate', 'error_rate', 'latency_p99', 'cpu_usage', 'memory_usage']
        affected = []
        
        if len(all_features) < 2:
            return metric_names  # Not enough data to compare
        
        # Calculate mean and std for each feature
        means = all_features.mean(axis=0)
        stds = all_features.std(axis=0)
        
        # Check each feature for deviation (> 2 standard deviations)
        for i, (value, mean, std) in enumerate(zip(feature_vector, means, stds)):
            if std > 0 and abs(value - mean) > 2 * std:
                affected.append(metric_names[i])
        
        # If no specific metrics identified, return all
        return affected if affected else metric_names
    
    @staticmethod
    def store_anomaly(
        db: Session,
        anomaly: Dict
    ) -> MetricsAnomaly:
        """
        Store detected anomaly in database.
        
        Args:
            db: Database session
            anomaly: Anomaly dictionary
        
        Returns:
            Created MetricsAnomaly
        """
        # Check if anomaly already exists
        existing = db.query(MetricsAnomaly).filter(
            MetricsAnomaly.service_name == anomaly['service_name'],
            MetricsAnomaly.timestamp == anomaly['timestamp'],
            MetricsAnomaly.anomaly_type == anomaly['anomaly_type']
        ).first()
        
        if existing:
            logger.debug(f"Anomaly already exists for {anomaly['service_name']} at {anomaly['timestamp']}")
            return existing
        
        # Create new anomaly
        anomaly_record = MetricsAnomaly(
            service_name=anomaly['service_name'],
            timestamp=anomaly['timestamp'],
            anomaly_type=anomaly['anomaly_type'],
            severity=anomaly['severity'],
            anomaly_score=anomaly['anomaly_score'],
            affected_metrics=json.dumps(anomaly['affected_metrics']),
            description=anomaly['description']
        )
        
        db.add(anomaly_record)
        db.commit()
        db.refresh(anomaly_record)
        
        logger.info(f"Stored {anomaly['severity']} anomaly for {anomaly['service_name']}")
        return anomaly_record


# Singleton instance
anomaly_detection_service = AnomalyDetectionService()
