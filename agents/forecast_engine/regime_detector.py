"""
RACE Regime Detector — Market State Classification
===================================================
Uses a Hidden Markov Model (HMM) with 3 latent states to classify
the current market regime as STABLE, VOLATILE, or CRISIS.

Falls back to a rule-based volatility classifier if the HMM fails
(insufficient data, convergence issues, or missing hmmlearn).

Patent-relevant novelty: domain-specific feature engineering
combining rolling volatility, Hurst exponent estimation, kurtosis,
and price velocity to detect agricultural commodity market regimes.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, Optional
import warnings

warnings.filterwarnings("ignore")


@dataclass
class RegimeState:
    """Encapsulates the detected market regime and confidence metadata."""
    regime: str  # "STABLE", "VOLATILE", "CRISIS"
    confidence: float  # 0.0 – 1.0
    transition_prob: Dict[str, float] = field(default_factory=dict)
    features: Dict[str, float] = field(default_factory=dict)


class RegimeDetector:
    """
    Automatic market regime classification.

    Primary method: Hidden Markov Model (Gaussian HMM, 3 states).
    Fallback: Rule-based classification using rolling volatility
    and Bollinger Band width.
    """

    REGIME_MAP = {0: "STABLE", 1: "VOLATILE", 2: "CRISIS"}

    def __init__(self, n_states: int = 3, lookback: int = 60):
        self.n_states = n_states
        self.lookback = lookback
        self._hmm_available = False
        self._hmm = None

        try:
            from hmmlearn.hmm import GaussianHMM
            self._hmm = GaussianHMM(
                n_components=n_states,
                covariance_type="full",
                n_iter=200,
                random_state=42,
                verbose=False,
            )
            self._hmm_available = True
        except ImportError:
            pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect_regime(self, price_series: pd.Series) -> RegimeState:
        """
        Classify the current market regime from a price time-series.

        Parameters
        ----------
        price_series : pd.Series
            Daily modal prices, ordered chronologically.

        Returns
        -------
        RegimeState
        """
        if len(price_series) < 20:
            return RegimeState(regime="STABLE", confidence=0.3,
                               features={"reason": "insufficient_data"})

        features = self._engineer_features(price_series)

        # Try HMM first
        if self._hmm_available and len(price_series) >= 30:
            try:
                return self._hmm_classify(price_series, features)
            except Exception:
                pass

        # Fallback: rule-based
        return self._rule_based_classify(features)

    # ------------------------------------------------------------------
    # Feature Engineering
    # ------------------------------------------------------------------

    def _engineer_features(self, prices: pd.Series) -> Dict[str, float]:
        """Compute regime-detection features from raw prices."""
        returns = prices.pct_change().dropna()

        vol_7 = returns.iloc[-7:].std() if len(returns) >= 7 else returns.std()
        vol_14 = returns.iloc[-14:].std() if len(returns) >= 14 else returns.std()
        vol_30 = returns.iloc[-30:].std() if len(returns) >= 30 else returns.std()

        # Price velocity (annualised trend slope over last 14 days)
        recent = prices.iloc[-14:].values if len(prices) >= 14 else prices.values
        velocity = (recent[-1] - recent[0]) / (recent[0] + 1e-9)

        # Kurtosis of returns (fat-tails indicator)
        kurt = returns.kurtosis() if len(returns) >= 10 else 0.0

        # Hurst exponent estimate (simplified R/S method)
        hurst = self._hurst_exponent(prices.values)

        # Bollinger Band width (normalised)
        bb_mid = prices.rolling(20).mean()
        bb_std = prices.rolling(20).std()
        bb_width = ((2 * bb_std) / (bb_mid + 1e-9)).iloc[-1] if len(prices) >= 20 else 0.0

        return {
            "vol_7": float(vol_7),
            "vol_14": float(vol_14),
            "vol_30": float(vol_30),
            "velocity": float(velocity),
            "kurtosis": float(kurt),
            "hurst": float(hurst),
            "bb_width": float(bb_width),
        }

    @staticmethod
    def _hurst_exponent(ts: np.ndarray, max_lag: int = 20) -> float:
        """Simplified Hurst exponent via R/S analysis."""
        if len(ts) < max_lag + 2:
            return 0.5  # default → random walk
        lags = range(2, min(max_lag, len(ts) // 2))
        tau = []
        for lag in lags:
            chunks = [ts[i: i + lag] for i in range(0, len(ts) - lag, lag)]
            rs_values = []
            for chunk in chunks:
                if len(chunk) < 2:
                    continue
                mean_c = np.mean(chunk)
                deviations = np.cumsum(chunk - mean_c)
                r = np.max(deviations) - np.min(deviations)
                s = np.std(chunk, ddof=1) if np.std(chunk, ddof=1) > 0 else 1e-9
                rs_values.append(r / s)
            if rs_values:
                tau.append(np.mean(rs_values))
            else:
                tau.append(1.0)

        if len(tau) < 2:
            return 0.5

        log_lags = np.log(list(lags)[: len(tau)])
        log_tau = np.log(np.array(tau) + 1e-9)

        try:
            poly = np.polyfit(log_lags, log_tau, 1)
            return float(np.clip(poly[0], 0.0, 1.0))
        except Exception:
            return 0.5

    # ------------------------------------------------------------------
    # HMM Classification
    # ------------------------------------------------------------------

    def _hmm_classify(self, prices: pd.Series, features: Dict) -> RegimeState:
        """Fit a Gaussian HMM and classify the latest observation."""
        returns = prices.pct_change().dropna().values.reshape(-1, 1)

        self._hmm.fit(returns)
        hidden_states = self._hmm.predict(returns)
        current_state = int(hidden_states[-1])

        # Map states to labels by volatility (lowest vol → STABLE)
        state_vols = {}
        for s in range(self.n_states):
            mask = hidden_states == s
            if mask.sum() > 0:
                state_vols[s] = np.std(returns[mask])
            else:
                state_vols[s] = 0.0

        sorted_states = sorted(state_vols, key=state_vols.get)
        label_map = {}
        labels = ["STABLE", "VOLATILE", "CRISIS"]
        for idx, s in enumerate(sorted_states):
            label_map[s] = labels[min(idx, len(labels) - 1)]

        regime = label_map.get(current_state, "VOLATILE")

        # Transition probabilities from current state
        trans_probs = {}
        try:
            transmat = self._hmm.transmat_[current_state]
            for s_idx, prob in enumerate(transmat):
                trans_probs[label_map.get(s_idx, f"S{s_idx}")] = round(float(prob), 4)
        except Exception:
            trans_probs = {"STABLE": 0.33, "VOLATILE": 0.34, "CRISIS": 0.33}

        # Confidence: posterior probability of being in this state
        try:
            posteriors = self._hmm.predict_proba(returns)
            confidence = float(posteriors[-1][current_state])
        except Exception:
            confidence = 0.6

        features["hmm_state_raw"] = current_state
        return RegimeState(
            regime=regime,
            confidence=round(confidence, 4),
            transition_prob=trans_probs,
            features=features,
        )

    # ------------------------------------------------------------------
    # Rule-Based Fallback
    # ------------------------------------------------------------------

    def _rule_based_classify(self, features: Dict) -> RegimeState:
        """Deterministic rule-based regime classification."""
        vol_7 = features.get("vol_7", 0)
        vol_30 = features.get("vol_30", 0)
        bb_width = features.get("bb_width", 0)
        kurt = features.get("kurtosis", 0)

        # Crisis: very high short-term volatility OR fat tails
        if vol_7 > 0.06 or (kurt > 5 and vol_7 > 0.04):
            regime = "CRISIS"
            confidence = min(0.9, 0.5 + vol_7 * 5)
        # Volatile: elevated volatility
        elif vol_7 > 0.03 or bb_width > 0.15:
            regime = "VOLATILE"
            confidence = min(0.85, 0.5 + vol_7 * 3)
        else:
            regime = "STABLE"
            confidence = min(0.95, 0.7 + (0.03 - vol_7) * 5)

        return RegimeState(
            regime=regime,
            confidence=round(confidence, 4),
            transition_prob={"STABLE": 0.6, "VOLATILE": 0.3, "CRISIS": 0.1},
            features=features,
        )
