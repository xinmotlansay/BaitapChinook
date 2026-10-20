import logging

import lightgbm as lgb
import numpy as np

from config import NEG_RATIO
from ml.features import FEATURE_COLUMNS, TRACK_FEATURE_COLUMNS

logger = logging.getLogger(__name__)


class Recommender:
    """Giao diện chung: rank(customer, loại trừ) và recommend(customer, k, exclude)."""

    name = "base"

    def __init__(self, state):
        self.state = state

    def fit(self, *args, **kwargs):
        # Các mô hình baseline chỉ dựa trên thống kê trong state, không có tham số học.
        return self

    def score_all(self, customer_id):
        raise NotImplementedError

    def rank(self, customer_id, exclude_idx=()):
        """Thứ tự index item (giảm dần theo điểm), bỏ các item trong exclude_idx."""
        scores = self.score_all(customer_id)
        candidates = np.setdiff1d(np.arange(len(scores)), np.asarray(exclude_idx, dtype=int))
        order = candidates[np.argsort(-scores[candidates], kind="stable")]
        return order, scores

    def recommend(self, customer_id, k, exclude=()):
        exclude_idx = [self.state.album_index[a] for a in exclude if a in self.state.album_index]
        order, scores = self.rank(customer_id, exclude_idx)
        return [(self.state.album_ids[i], float(scores[i])) for i in order[:k]]


class Popularity(Recommender):
    name = "M1 Popularity"

    def score_all(self, customer_id):
        return self.state.pop_global


class GenreProfile(Recommender):
    name = "M2 Genre-profile"

    def score_all(self, customer_id):
        return self.state.content_scores(customer_id)[0]


class ArtistGenreProfile(Recommender):
    name = "M3 Artist+Genre profile"

    def score_all(self, customer_id):
        return self.state.content_scores(customer_id)[1]


class ContentTfidf(Recommender):
    name = "M4 Content TF-IDF"

    def score_all(self, customer_id):
        return self.state.content_scores(customer_id)[2]


class HybridRanker(Recommender):
    name = "M5 Hybrid LightGBM"

    def __init__(self, state, ranker):
        super().__init__(state)
        self.ranker = ranker

    def score_all(self, customer_id):
        X = self.state.feature_matrix(customer_id)[FEATURE_COLUMNS].to_numpy()
        return self.ranker.predict(X)


class TrackPopularity(Recommender):
    name = "T1 Track popularity"

    def score_all(self, customer_id):
        return self.state.track_pop


class TrackHybrid(Recommender):
    name = "T2 Track LightGBM"

    def __init__(self, state, ranker):
        super().__init__(state)
        self.ranker = ranker

    def score_all(self, customer_id):
        X = self.state.track_feature_matrix(customer_id)[TRACK_FEATURE_COLUMNS].to_numpy()
        return self.ranker.predict(X)


def _training_data(positives, item_col, index, history_of, feature_matrix, n_items, columns, rng):
    """Mẫu huấn luyện: item dương là nhãn của giai đoạn sau, item âm lấy ngẫu nhiên từ phần chưa mua."""
    blocks, labels, groups = [], [], []
    for cid, grp in positives.groupby("CustomerId"):
        pos = np.array([index[i] for i in grp[item_col]], dtype=int)
        hidx = history_of(cid)
        pool = np.setdiff1d(np.arange(n_items), np.concatenate([hidx, pos]))
        neg = rng.choice(pool, size=min(len(pool), NEG_RATIO * len(pos)), replace=False)

        idx = np.concatenate([pos, neg])
        blocks.append(feature_matrix(cid)[columns].to_numpy()[idx])
        labels.append(np.concatenate([np.ones(len(pos)), np.zeros(len(neg))]))
        groups.append(len(idx))
    return np.vstack(blocks), np.concatenate(labels), groups


def album_training(state, positives, rng):
    return _training_data(
        positives, "AlbumId", state.album_index,
        lambda c: state.history_of(c)[0], state.feature_matrix,
        len(state.album_ids), FEATURE_COLUMNS, rng,
    )


def track_training(state, positives, rng):
    return _training_data(
        positives, "TrackId", state.track_index,
        state.track_history_of, state.track_feature_matrix,
        len(state.track_ids), TRACK_FEATURE_COLUMNS, rng,
    )


def train_ranker(pairs, params, seed, builder):
    """pairs: danh sách (state, positives). builder tạo mẫu huấn luyện cho album hoặc track."""
    rng = np.random.default_rng(seed)
    X_parts, y_parts, groups = [], [], []
    for state, positives in pairs:
        X, y, g = builder(state, positives, rng)
        X_parts.append(X)
        y_parts.append(y)
        groups.extend(g)

    ranker = lgb.LGBMRanker(
        objective="lambdarank",
        learning_rate=0.05,
        min_child_samples=5,
        random_state=seed,
        verbose=-1,
        **params,
    )
    ranker.fit(np.vstack(X_parts), np.concatenate(y_parts), group=groups)
    logger.info("Đã huấn luyện LambdaRank (seed=%d, %s)", seed, params)
    return ranker
