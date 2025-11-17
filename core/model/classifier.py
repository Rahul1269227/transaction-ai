"""
Embedding-based Transaction Classifier
Uses sentence transformers for embeddings + lightweight ML classifier
"""

import pickle
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
import logging

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers not installed. Using mock embeddings.")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    try:
        import xgboost as xgb
        LIGHTGBM_AVAILABLE = False
        XGBOOST_AVAILABLE = True
    except ImportError:
        LIGHTGBM_AVAILABLE = False
        XGBOOST_AVAILABLE = False
        logging.warning("Neither LightGBM nor XGBoost installed. Classifier training unavailable.")

from sklearn.preprocessing import LabelEncoder
from sklearn.calibration import CalibratedClassifierCV


class EmbeddingClassifier:
    """
    Embedding-based transaction classifier

    Architecture:
    1. Text -> Embeddings (sentence-transformers)
    2. Embeddings + Features -> LightGBM/XGBoost
    3. Calibration for confidence scores
    """

    def __init__(
        self,
        encoder_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        classifier_type: str = "lightgbm"
    ):
        """
        Initialize classifier

        Args:
            encoder_model: HuggingFace model name for embeddings
            classifier_type: 'lightgbm' or 'xgboost'
        """
        self.encoder_model_name = encoder_model
        self.classifier_type = classifier_type

        # Load encoder
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.encoder = SentenceTransformer(encoder_model)
                self.embedding_dim = self.encoder.get_sentence_embedding_dimension()
            except Exception as e:
                logging.warning(f"Failed to load encoder: {e}. Using mock embeddings.")
                self.encoder = None
                self.embedding_dim = 384
        else:
            self.encoder = None
            self.embedding_dim = 384

        # Classifier and label encoder
        self.classifier = None
        self.label_encoder = LabelEncoder()
        self.is_calibrated = False

        # Feature names for reference
        self.feature_names = []

    def encode_text(self, texts: List[str]) -> np.ndarray:
        """
        Encode texts to embeddings

        Args:
            texts: List of text strings

        Returns:
            numpy array of shape (n_texts, embedding_dim)
        """
        if self.encoder is not None:
            embeddings = self.encoder.encode(texts, show_progress_bar=False)
            return np.array(embeddings)
        else:
            # Mock embeddings for testing without model
            return np.random.randn(len(texts), self.embedding_dim)

    def extract_features(
        self,
        texts: List[str],
        handcrafted_features: Optional[List[Dict[str, Any]]] = None
    ) -> np.ndarray:
        """
        Extract combined features: embeddings + handcrafted features

        Args:
            texts: List of transaction texts
            handcrafted_features: List of dicts with handcrafted features

        Returns:
            Feature matrix of shape (n_samples, n_features)
        """
        # Get embeddings
        embeddings = self.encode_text(texts)

        # Combine with handcrafted features if provided
        if handcrafted_features:
            # Convert handcrafted features to matrix
            handcrafted_matrix = self._dict_features_to_matrix(handcrafted_features)
            features = np.hstack([embeddings, handcrafted_matrix])
        else:
            features = embeddings

        return features

    def _dict_features_to_matrix(self, features_list: List[Dict[str, Any]]) -> np.ndarray:
        """Convert list of feature dicts to numpy matrix"""
        if not features_list:
            return np.array([])

        # Get feature names from first dict
        if not self.feature_names:
            self.feature_names = sorted(features_list[0].keys())

        # Convert to matrix
        matrix = []
        for features in features_list:
            row = []
            for fname in self.feature_names:
                val = features.get(fname, 0)
                # Convert boolean to int
                if isinstance(val, bool):
                    val = int(val)
                # Convert string categories to hash (simple approach)
                elif isinstance(val, str):
                    val = hash(val) % 1000
                row.append(val)
            matrix.append(row)

        return np.array(matrix)

    def train(
        self,
        texts: List[str],
        labels: List[str],
        handcrafted_features: Optional[List[Dict[str, Any]]] = None,
        calibrate: bool = True,
        class_weights: Optional[dict] = None,
        **kwargs
    ):
        """
        Train classifier

        Args:
            texts: Training texts
            labels: Training labels (category names)
            handcrafted_features: Optional handcrafted features
            calibrate: Whether to calibrate probabilities
            class_weights: Optional dict of class weights {class_name: weight}
            **kwargs: Additional parameters for classifier
        """
        # Extract features
        X = self.extract_features(texts, handcrafted_features)

        # Encode labels
        y = self.label_encoder.fit_transform(labels)

        # Handle class weights
        weight_param = None
        if class_weights:
            # Convert class name weights to encoded weights
            weight_dict = {}
            for class_name, weight in class_weights.items():
                try:
                    class_idx = self.label_encoder.transform([class_name])[0]
                    weight_dict[class_idx] = weight
                except:
                    pass
            weight_param = weight_dict
        else:
            # Check for class imbalance
            from collections import Counter
            label_counts = Counter(labels)
            is_imbalanced = len(set(labels)) > 1 and (
                max(label_counts.values()) / min(label_counts.values()) > 2
            )
            weight_param = 'balanced' if is_imbalanced else None

        # Train classifier
        if self.classifier_type == "lightgbm" and LIGHTGBM_AVAILABLE:
            # Ensure num_leaves is compatible with max_depth
            max_depth = kwargs.get('max_depth', 10)
            num_leaves = kwargs.get('num_leaves', None)

            # If num_leaves is not explicitly set, calculate it based on max_depth
            if num_leaves is None:
                # Use 2^(max_depth-1) as a good default to avoid warnings
                num_leaves = min(2**(max_depth - 1), 4095)  # Cap at 4095 for performance

            self.classifier = lgb.LGBMClassifier(
                n_estimators=kwargs.get('n_estimators', 200),
                learning_rate=kwargs.get('learning_rate', 0.05),
                max_depth=max_depth,
                num_leaves=num_leaves,
                min_child_samples=kwargs.get('min_child_samples', 20),
                subsample=kwargs.get('subsample', 0.8),
                colsample_bytree=kwargs.get('colsample_bytree', 0.8),
                reg_alpha=kwargs.get('reg_alpha', 0.1),
                reg_lambda=kwargs.get('reg_lambda', 0.1),
                class_weight=weight_param,
                random_state=42,
                verbose=-1
            )
        elif XGBOOST_AVAILABLE:
            import xgboost as xgb
            self.classifier = xgb.XGBClassifier(
                n_estimators=kwargs.get('n_estimators', 100),
                learning_rate=kwargs.get('learning_rate', 0.1),
                max_depth=kwargs.get('max_depth', 7),
                random_state=42
            )
        else:
            # Fallback to sklearn
            from sklearn.ensemble import RandomForestClassifier
            self.classifier = RandomForestClassifier(
                n_estimators=kwargs.get('n_estimators', 100),
                max_depth=kwargs.get('max_depth', 7),
                random_state=42
            )

        # Train
        self.classifier.fit(X, y)

        # Calibrate if requested
        if calibrate:
            self.classifier = CalibratedClassifierCV(
                self.classifier,
                cv=3,
                method='isotonic'
            )
            self.classifier.fit(X, y)
            self.is_calibrated = True

        logging.info(f"Trained classifier on {len(texts)} samples")

    def predict(
        self,
        texts: List[str],
        handcrafted_features: Optional[List[Dict[str, Any]]] = None,
        top_k: int = 3
    ) -> List[List[Tuple[str, float]]]:
        """
        Predict categories with confidence scores

        Args:
            texts: List of transaction texts
            handcrafted_features: Optional handcrafted features
            top_k: Number of top predictions to return

        Returns:
            List of [(category, confidence), ...] for each input
        """
        if self.classifier is None:
            raise ValueError("Classifier not trained. Call train() first.")

        # Extract features
        X = self.extract_features(texts, handcrafted_features)

        # Predict probabilities
        probas = self.classifier.predict_proba(X)

        # Get top-k predictions for each sample
        results = []
        for proba in probas:
            # Get top-k indices
            top_indices = np.argsort(proba)[::-1][:top_k]

            # Convert to category names and confidences
            predictions = [
                (self.label_encoder.inverse_transform([idx])[0], proba[idx])
                for idx in top_indices
            ]
            results.append(predictions)

        return results

    def predict_single(
        self,
        text: str,
        handcrafted_features: Optional[Dict[str, Any]] = None,
        top_k: int = 3
    ) -> List[Tuple[str, float]]:
        """Predict for a single transaction"""
        hf = [handcrafted_features] if handcrafted_features else None
        results = self.predict([text], hf, top_k)
        return results[0]

    def save(self, path: str):
        """Save model to disk"""
        save_path = Path(path)
        save_path.mkdir(parents=True, exist_ok=True)

        # Save classifier
        if self.classifier:
            with open(save_path / "classifier.pkl", 'wb') as f:
                pickle.dump(self.classifier, f)

        # Save label encoder
        with open(save_path / "label_encoder.pkl", 'wb') as f:
            pickle.dump(self.label_encoder, f)

        # Save metadata
        metadata = {
            'encoder_model_name': self.encoder_model_name,
            'classifier_type': self.classifier_type,
            'embedding_dim': self.embedding_dim,
            'is_calibrated': self.is_calibrated,
            'feature_names': self.feature_names,
            'classes': self.label_encoder.classes_.tolist()
        }

        with open(save_path / "metadata.pkl", 'wb') as f:
            pickle.dump(metadata, f)

        logging.info(f"Model saved to {path}")

    def load(self, path: str):
        """Load model from disk"""
        load_path = Path(path)

        if not load_path.exists():
            raise FileNotFoundError(f"Model not found at {path}")

        # Load metadata
        with open(load_path / "metadata.pkl", 'rb') as f:
            metadata = pickle.load(f)

        self.encoder_model_name = metadata['encoder_model_name']
        self.classifier_type = metadata['classifier_type']
        self.embedding_dim = metadata['embedding_dim']
        self.is_calibrated = metadata['is_calibrated']
        self.feature_names = metadata['feature_names']

        # Load classifier
        with open(load_path / "classifier.pkl", 'rb') as f:
            self.classifier = pickle.load(f)

        # Load label encoder
        with open(load_path / "label_encoder.pkl", 'rb') as f:
            self.label_encoder = pickle.load(f)

        # Reload encoder model
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.encoder = SentenceTransformer(self.encoder_model_name)
            except:
                logging.warning("Failed to reload encoder model")
                self.encoder = None

        logging.info(f"Model loaded from {path}")

    def get_feature_importance(self, top_n: int = 20) -> List[Tuple[str, float]]:
        """Get feature importance scores"""
        if self.classifier is None:
            return []

        try:
            # Get feature importances
            if hasattr(self.classifier, 'feature_importances_'):
                importances = self.classifier.feature_importances_
            else:
                # For calibrated classifier, get base estimator
                base_estimator = self.classifier.base_estimator
                importances = base_estimator.feature_importances_

            # Create feature names (embeddings + handcrafted)
            feature_names = [f"emb_{i}" for i in range(self.embedding_dim)]
            feature_names.extend(self.feature_names)

            # Sort by importance
            indices = np.argsort(importances)[::-1][:top_n]
            return [(feature_names[i], importances[i]) for i in indices]

        except Exception as e:
            logging.warning(f"Could not get feature importance: {e}")
            return []
