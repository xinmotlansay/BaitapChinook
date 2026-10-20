"""Huấn luyện: làm sạch → chia → chọn tham số trên validation → fit → đánh giá trên test → lưu model.

Chạy: python -m ml.train
"""
import logging

import pandas as pd

from config import ARTIFACTS_DIR, LGB_SEEDS, METRICS_PATH, MODEL_PATH, SEED
from ml.data_prep import prepare, split_train_test, split_valid, track_rows_for
from ml.evaluate import paired_vs_baseline, per_customer_metrics, summarize
from ml.features import FEATURE_COLUMNS, TRACK_FEATURE_COLUMNS, ProfileState
from ml.package import save_package
from ml.recommenders import (
    ArtistGenreProfile,
    ContentTfidf,
    GenreProfile,
    HybridRanker,
    Popularity,
    TrackHybrid,
    TrackPopularity,
    album_training,
    track_training,
    train_ranker,
)

logger = logging.getLogger(__name__)

# Lưới tham số của LambdaRank, chọn theo NDCG@10 trên validation
TUNE_GRID = [
    {"num_leaves": 7, "n_estimators": 100},
    {"num_leaves": 7, "n_estimators": 300},
    {"num_leaves": 15, "n_estimators": 100},
    {"num_leaves": 15, "n_estimators": 300},
]


def album_evaluator(model, state, labels, ks=(10,)):
    return per_customer_metrics(
        lambda c: model.rank(c, exclude_idx=state.history_of(c)[0])[0],
        labels, "AlbumId", state.album_index, state.genre_mat, ks=ks,
    )


def track_evaluator(model, state, labels, ks=(10,)):
    return per_customer_metrics(
        lambda c: model.rank(c, exclude_idx=state.track_history_of(c))[0],
        labels, "TrackId", state.track_index, state.track_genre_mat, ks=ks,
    )


def tune_ranker(builder, make_model, evaluator, state_a, pos_a, state_sub, valid, label):
    """Huấn luyện trên cửa sổ (state_a → pos_a), đánh giá trên cửa sổ sau (state_sub → valid).

    Cửa sổ validation không dùng nhãn của nó để huấn luyện, nên không bị rò rỉ khi chọn tham số.
    """
    results = []
    for params in TUNE_GRID:
        ranker = train_ranker([(state_a, pos_a)], params, SEED, builder)
        per_c, _ = evaluator(make_model(state_sub, ranker), state_sub, valid)
        score = per_c["NDCG@10"].mean()
        results.append({**params, "NDCG@10_valid": score})
        logger.info("[%s] Validation %s: NDCG@10 = %.4f", label, params, score)

    table = pd.DataFrame(results)
    best = table.sort_values("NDCG@10_valid", ascending=False).iloc[0]
    best_params = {"num_leaves": int(best["num_leaves"]), "n_estimators": int(best["n_estimators"])}
    logger.info("[%s] Tham số tốt nhất trên validation: %s", label, best_params)
    return best_params, table


def run():
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    prepared = prepare()
    logger.info("Báo cáo làm sạch:\n%s", prepared.report.to_string(index=False))

    catalog, albums, customers = prepared.catalog, prepared.albums, prepared.customers
    track_inter = prepared.track_interactions

    train, test = split_train_test(prepared.interactions)
    sub, valid = split_valid(train)
    sub_a, sub_b = split_valid(sub)

    # Cửa sổ album và track đi cùng nhau: track của mỗi album nằm đúng trong cửa sổ của album đó
    state_a = ProfileState(sub_a, track_rows_for(track_inter, sub_a), catalog, albums, customers)
    state_sub = ProfileState(sub, track_rows_for(track_inter, sub), catalog, albums, customers)
    state_train = ProfileState(train, track_rows_for(track_inter, train), catalog, albums, customers)

    # ----- Album -----
    params, tuning = tune_ranker(
        album_training, HybridRanker, album_evaluator,
        state_a, sub_b, state_sub, valid, "album",
    )
    # Huấn luyện cuối cùng dùng cả hai cửa sổ, trước khi đánh giá trên test
    rankers = {
        seed: train_ranker([(state_a, sub_b), (state_sub, valid)], params, seed, album_training)
        for seed in LGB_SEEDS
    }
    final_ranker = rankers[SEED]

    # ----- Track -----
    sub_b_tracks = track_rows_for(track_inter, sub_b)
    valid_tracks = track_rows_for(track_inter, valid)
    track_params, track_tuning = tune_ranker(
        track_training, TrackHybrid, track_evaluator,
        state_a, sub_b_tracks, state_sub, valid_tracks, "track",
    )
    track_ranker = train_ranker(
        [(state_a, sub_b_tracks), (state_sub, valid_tracks)],
        track_params, SEED, track_training,
    )

    # ----- Đánh giá album trên test -----
    models = {
        "M1": Popularity(state_train),
        "M2": GenreProfile(state_train),
        "M3": ArtistGenreProfile(state_train),
        "M4": ContentTfidf(state_train),
        "M5": HybridRanker(state_train, final_ranker),
    }

    rows, per_models = [], {}
    for key, model in models.items():
        per_c, tops = album_evaluator(model, state_train, test, ks=(5, 10, 20))
        per_models[key] = per_c
        for row in summarize(per_c, tops, len(state_train.album_ids)):
            rows.append({"Model": model.name, **row})
        logger.info("Đã đánh giá %s trên test", model.name)

    metrics = pd.DataFrame(rows)
    metrics.to_csv(METRICS_PATH, index=False)

    paired = pd.DataFrame([
        {"Model": models[key].name, **paired_vs_baseline(per_models[key], per_models["M3"])}
        for key in ("M1", "M2", "M4", "M5")
    ])
    paired.to_csv(ARTIFACTS_DIR / "paired_vs_m3.csv", index=False)

    seed_rows = []
    for seed, ranker in rankers.items():
        per_c, _ = album_evaluator(HybridRanker(state_train, ranker), state_train, test)
        seed_rows.append({"Seed": seed, "NDCG@10": per_c["NDCG@10"].mean(), "Recall@10": per_c["Recall@10"].mean()})
    seeds = pd.DataFrame(seed_rows)
    seeds.to_csv(ARTIFACTS_DIR / "m5_seeds.csv", index=False)
    tuning.to_csv(ARTIFACTS_DIR / "m5_tuning.csv", index=False)

    # ----- Đánh giá track trên test -----
    track_test = track_rows_for(track_inter, test)
    track_models = {
        "T1": TrackPopularity(state_train),
        "T2": TrackHybrid(state_train, track_ranker),
    }
    track_rows = []
    for model in track_models.values():
        per_c, tops = track_evaluator(model, state_train, track_test, ks=(5, 10, 20))
        for row in summarize(per_c, tops, len(state_train.track_ids)):
            track_rows.append({"Model": model.name, **row})
    track_metrics = pd.DataFrame(track_rows)
    track_metrics.to_csv(ARTIFACTS_DIR / "track_metrics.csv", index=False)
    track_tuning.to_csv(ARTIFACTS_DIR / "track_tuning.csv", index=False)

    meta = {
        "feature_columns": FEATURE_COLUMNS,
        "track_feature_columns": TRACK_FEATURE_COLUMNS,
        "default_model": "M5",
        "ranker_params": params,
        "track_ranker_params": track_params,
        "seed": SEED,
    }
    save_package(
        MODEL_PATH, state_train, final_ranker, track_ranker,
        albums[["AlbumId", "Title", "Artist", "Genres"]], meta,
    )

    logger.info("Kết quả album trên test:\n%s", metrics.round(4).to_string(index=False))
    logger.info("So sánh album với M3:\n%s", paired.round(4).to_string(index=False))
    logger.info("Ổn định theo seed (M5):\n%s", seeds.round(4).to_string(index=False))
    logger.info("Kết quả track trên test:\n%s", track_metrics.round(4).to_string(index=False))
    logger.info("Đã lưu model: %s", MODEL_PATH)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()
