"""
Evaluation metrics — POD, FAR, CSI, ROC-AUC for binary landslide prediction vs NIDR labels.

Follows the standard confusion-matrix conventions for landslide susceptibility evaluation:
    TP = predicted unstable AND observed landslide
    FP = predicted unstable AND observed no landslide
    FN = predicted stable AND observed landslide
    TN = predicted stable AND observed no landslide

    POD (Probability of Detection) = TP / (TP + FN)  [recall]
    FAR (False Alarm Ratio)         = FP / (TP + FP)  [1 - precision]
    CSI (Critical Success Index)    = TP / (TP + FN + FP)  [Jaccard / IoU]
    F1                              = 2·TP / (2·TP + FP + FN)
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConfusionStats:
    tp: int
    fp: int
    fn: int
    tn: int

    @property
    def pod(self) -> float:
        d = self.tp + self.fn
        return self.tp / d if d else 0.0

    @property
    def far(self) -> float:
        d = self.tp + self.fp
        return self.fp / d if d else 0.0

    @property
    def csi(self) -> float:
        d = self.tp + self.fp + self.fn
        return self.tp / d if d else 0.0

    @property
    def f1(self) -> float:
        d = 2 * self.tp + self.fp + self.fn
        return (2 * self.tp) / d if d else 0.0

    @property
    def precision(self) -> float:
        d = self.tp + self.fp
        return self.tp / d if d else 0.0

    @property
    def recall(self) -> float:
        return self.pod

    def to_dict(self) -> dict:
        return {
            "tp": self.tp,
            "fp": self.fp,
            "fn": self.fn,
            "tn": self.tn,
            "POD": round(self.pod, 4),
            "FAR": round(self.far, 4),
            "CSI": round(self.csi, 4),
            "F1": round(self.f1, 4),
            "Precision": round(self.precision, 4),
        }


def confusion_from_arrays(pred: "np.ndarray", obs: "np.ndarray", valid_mask=None) -> ConfusionStats:
    """
    Compute confusion stats from two binary arrays (same shape).

    Args:
        pred: prediction (0/1), True = predicted unstable
        obs:  observation (0/1), True = observed landslide
        valid_mask: optional boolean mask — only count pixels where True

    Returns: ConfusionStats
    """
    import numpy as np

    p = pred.astype(bool)
    o = obs.astype(bool)
    if valid_mask is not None:
        m = valid_mask.astype(bool)
        p = p & m
        o = o & m
        tp = int(((p & o) & m).sum())
        fp = int(((p & ~o) & m).sum())
        fn = int(((~p & o) & m).sum())
        tn = int(((~p & ~o) & m).sum())
    else:
        tp = int((p & o).sum())
        fp = int((p & ~o).sum())
        fn = int((~p & o).sum())
        tn = int((~p & ~o).sum())
    return ConfusionStats(tp=tp, fp=fp, fn=fn, tn=tn)


def roc_auc(pred_score: "np.ndarray", obs: "np.ndarray", n_thresholds: int = 50) -> dict:
    """
    Compute ROC-AUC for continuous prediction score vs binary observation.

    Uses sklearn.metrics.roc_auc_score when available (exact, handles ties).
    Falls back to trapezoidal quantile integration otherwise.

    Args:
        pred_score: continuous score (e.g., q/q_cr ratio)
        obs: binary observation (0/1)
        n_thresholds: number of thresholds to evaluate (fallback path only)

    Returns: {auc, roc_points: [(fpr, tpr), ...]}
    """
    import numpy as np

    s = pred_score.ravel()
    o = obs.astype(bool).ravel()
    # Drop NaN
    valid = ~np.isnan(s)
    s = s[valid]
    o = o[valid]
    if len(s) == 0 or o.sum() == 0 or (~o).sum() == 0:
        return {"auc": 0.0, "roc_points": []}

    # Prefer sklearn (exact, handles rank ties correctly)
    try:
        from sklearn.metrics import roc_auc_score, roc_curve
        auc = float(roc_auc_score(o, s))
        fpr, tpr, _ = roc_curve(o, s)
        roc_points = list(zip(fpr.tolist(), tpr.tolist()))
        return {"auc": round(auc, 4), "roc_points": roc_points}
    except ImportError:
        pass

    # Fallback: quantile-threshold trapezoidal (less accurate near saturated scores)
    thresholds = np.unique(np.quantile(s, np.linspace(0, 1, n_thresholds)))
    roc = []
    # Always include the extrema so the curve touches (0,0) and (1,1)
    eps = 1e-12
    for t in np.concatenate([[s.max() + eps], thresholds, [s.min() - eps]]):
        p = s >= t
        tp = int((p & o).sum())
        fp = int((p & ~o).sum())
        fn = int((~p & o).sum())
        tn = int((~p & ~o).sum())
        tpr = tp / (tp + fn) if (tp + fn) else 0.0
        fpr = fp / (fp + tn) if (fp + tn) else 0.0
        roc.append((fpr, tpr))
    # AUC via trapezoidal (sort by fpr)
    roc_sorted = sorted(roc)
    auc = 0.0
    for i in range(1, len(roc_sorted)):
        x0, y0 = roc_sorted[i - 1]
        x1, y1 = roc_sorted[i]
        auc += (x1 - x0) * (y0 + y1) / 2.0
    return {"auc": round(auc, 4), "roc_points": roc_sorted}


if __name__ == "__main__":
    import numpy as np

    # Smoke test
    np.random.seed(0)
    obs = np.random.rand(100, 100) < 0.05
    pred = obs | (np.random.rand(100, 100) < 0.03)
    stats = confusion_from_arrays(pred, obs)
    print(stats.to_dict())
