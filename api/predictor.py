import json
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any

import numpy as np
import pandas as pd
import xgboost as xgb

logger = logging.getLogger(__name__)


class CryptoPredictor:

    FEATURES: List[str] = [
        'marketCap_change',
        'marketCap_ema',
        'rsi',
        'marketCap_change_ratio',
        'holders_growth',
        'volatility_to_volume_ratio'
    ]

    def __init__(self, model_path: str = "models/crypto_investment_model.json"):
        self.model_path = Path(model_path)
        self.model: xgb.Booster = None
        self._load_model()

    def _load_model(self):
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found at {self.model_path}")

        self.model = xgb.Booster()
        self.model.load_model(str(self.model_path))
        logger.info(f"Model loaded from {self.model_path}")

    def predict(self, features: Dict[str, float]) -> Tuple[str, float]:
        feature_values = []
        for f in self.FEATURES:
            val = features.get(f, 0.0)
            # ochrana proti NaN/inf
            if val is None or np.isnan(val) or np.isinf(val):
                val = 0.0
            feature_values.append(float(val))

        dmatrix = xgb.DMatrix([feature_values], feature_names=self.FEATURES)
        prob = float(self.model.predict(dmatrix)[0])

        prediction = "BUY" if prob > 0.5 else "NO BUY"
        confidence = prob if prob > 0.5 else (1.0 - prob)

        return prediction, confidence

    def compute_features(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        df = df.copy()
        df = df.sort_values('timestamp')

        # percentage change
        df['marketCap_change'] = df['marketCap'].pct_change().fillna(0)

        # EMA
        df['marketCap_ema'] = df['marketCap'].ewm(span=7).mean()

        # RSI-like indikátor
        pct_change = df['marketCap'].pct_change().fillna(0)
        rolling_mean = pct_change.rolling(window=7).mean()
        rolling_std = pct_change.rolling(window=7).std().replace(0, 1)
        df['rsi'] = 100 - (100 / (1 + rolling_mean / rolling_std))
        df['rsi'] = df['rsi'].fillna(50)  # default na neutral

        # change ratio
        shifted = df['marketCap'].shift(1)
        df['marketCap_change_ratio'] = (df['marketCap'] - shifted) / shifted
        df['marketCap_change_ratio'] = df['marketCap_change_ratio'].fillna(0)

        # holders growth
        df['holders_growth'] = df['numHolders'].diff().fillna(0)

        # volatility / volume
        volatility = df['marketCap_change'].rolling(window=7, min_periods=1).std().fillna(0)
        df['volatility_to_volume_ratio'] = volatility / (df['volume'] + 1)

        # cleanup
        df = df.replace([np.inf, -np.inf], 0)
        df = df.fillna(0)

        return df


class DataLoader:

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data: Dict[str, Any] = {}
        self._load_data()

    def _load_data(self):
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")

        json_files = list(self.data_dir.glob("coiny_bez_limitu*.json"))

        if not json_files:
            logger.warning(f"No data files in {self.data_dir}")
            return

        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                    self.data.update(file_data)
                logger.info(f"Loaded {file_path.name}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse {file_path}: {e}")

        logger.info(f"Total: {len(self.data)} tokens from {len(json_files)} files")

    def get_tokens(self) -> List[Dict[str, Any]]:
        tokens = []
        for mint, token_data in self.data.items():
            history = token_data.get("marketCapHistory", [])
            if len(history) >= 10:  # aspoň 10 data pointů
                tokens.append({
                    "symbol": token_data.get("symbol", "Unknown"),
                    "name": token_data.get("name", "Unknown"),
                    "data_points": len(history),
                    "mint": mint
                })

        tokens.sort(key=lambda x: x["data_points"], reverse=True)
        return tokens[:100]  # top 100

    def get_token_data(self, mint: str) -> pd.DataFrame:
        if mint not in self.data:
            raise ValueError(f"Token {mint} not found")

        token = self.data[mint]
        records = []

        for mc in token.get("marketCapHistory", []):
            timestamp = mc.get("timestamp", 0)
            # některý timestampy jsou v ms
            if timestamp > 1e10:
                timestamp = timestamp / 1000

            records.append({
                "timestamp": timestamp,
                "marketCap": mc.get("marketCap", 0),
                "symbol": token.get("symbol", "Unknown"),
                "volume": token.get("volume", 0),
                "numHolders": token.get("numHolders", 0),
                "sniperCount": token.get("sniperCount", 0),
                "progress": token.get("progress", 0),
                "buySellRatio": token.get("buySellRatio", 0),
                "liquidity": token.get("liquidity", 0),
                "volatility": token.get("volatility", 0)
            })

        df = pd.DataFrame(records)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
        df = df.sort_values('timestamp')
        df = df.dropna(subset=['timestamp'])

        return df
