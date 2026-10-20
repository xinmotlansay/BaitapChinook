import numpy as np
import pandas as pd

from config import BOOTSTRAP_N, K_VALUES, SEED

METRICS = ("Recall", "Precision", "NDCG", "MAP", "HitRate", "Diversity")


def per_customer_metrics(rank_fn, labels, item_col, index, item_vecs=None, ks=K_VALUES):
    """Metric cho từng customer.

    rank_fn(customer_id) trả về thứ tự index item đã loại lịch sử train.
    labels: (CustomerId, item_col) là các item cần đoán đúng.
    item_vecs: vector nội dung của item để tính diversity (None thì bỏ qua diversity).
    """
    max_k = max(ks)
    relevant_by_c = {}
    for cid, grp in labels.groupby("CustomerId"):
        relevant_by_c[cid] = {index[i] for i in grp[item_col] if i in index}

    rows, tops = [], {}
    for cid, relevant in relevant_by_c.items():
        top = rank_fn(cid)[:max_k]
        tops[cid] = top

        row = {"CustomerId": cid}
        n_rel = len(relevant)
        for k in ks:
            topk = top[:k]
            hits = np.array([i in relevant for i in topk], dtype=float)

            row[f"Recall@{k}"] = hits.sum() / n_rel
            row[f"Precision@{k}"] = hits.sum() / k
            row[f"HitRate@{k}"] = float(hits.sum() > 0)

            ranks = np.arange(len(hits))
            discount = 1.0 / np.log2(ranks + 2)
            dcg = (hits * discount).sum()
            idcg = discount[: min(n_rel, k)].sum()
            row[f"NDCG@{k}"] = dcg / idcg

            precisions = np.cumsum(hits) / (ranks + 1)
            row[f"MAP@{k}"] = (precisions * hits).sum() / min(n_rel, k)

            # Diversity: 1 - độ tương đồng nội dung trung bình giữa các cặp item trong danh sách
            if item_vecs is not None and len(topk) >= 2:
                sim = item_vecs[topk] @ item_vecs[topk].T
                off_diag = ~np.eye(len(topk), dtype=bool)
                row[f"Diversity@{k}"] = float((1.0 - sim[off_diag]).mean())
            else:
                row[f"Diversity@{k}"] = np.nan
        rows.append(row)

    return pd.DataFrame(rows).set_index("CustomerId"), tops


def bootstrap_ci(values, seed=SEED, n=BOOTSTRAP_N):
    """CI 95% của trung bình bằng bootstrap theo customer."""
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(values), size=(n, len(values)))
    means = values[idx].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def summarize(per_c, tops, n_items, ks=K_VALUES):
    """Bảng tổng hợp theo K, kèm coverage và CI 95% cho NDCG và Recall."""
    rows = []
    for k in ks:
        row = {"K": k}
        for m in METRICS:
            row[m] = per_c[f"{m}@{k}"].mean()
        recommended = np.concatenate([t[:k] for t in tops.values()])
        row["Coverage"] = len(np.unique(recommended)) / n_items
        row["NDCG_CI_low"], row["NDCG_CI_high"] = bootstrap_ci(per_c[f"NDCG@{k}"])
        row["Recall_CI_low"], row["Recall_CI_high"] = bootstrap_ci(per_c[f"Recall@{k}"])
        rows.append(row)
    return rows


def paired_vs_baseline(per_c, baseline_c, k=10):
    """So sánh cặp theo customer với baseline: trung bình chênh lệch NDCG@k và CI 95%."""
    aligned = per_c[f"NDCG@{k}"].reindex(baseline_c.index)
    diff = aligned - baseline_c[f"NDCG@{k}"]
    low, high = bootstrap_ci(diff)
    return {
        "K": k,
        "Mean_diff": float(diff.mean()),
        "CI_low": low,
        "CI_high": high,
        "Win": int((diff > 0).sum()),
        "Lose": int((diff < 0).sum()),
        "Tie": int((diff == 0).sum()),
    }
