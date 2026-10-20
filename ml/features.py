import re

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

# Tên và thứ tự cột feature của M5 (album) và của mô hình track.
# Model lưu kèm danh sách này để kiểm tra khi suy luận.
FEATURE_COLUMNS = [
    "genre_cos", "artist_genre_cos", "tfidf_cos",
    "pop_global", "pop_country", "artist_bought", "artist_recency",
    "n_tracks", "log_total_ms", "mean_price", "composer_missing", "cust_n_albums",
]
TRACK_FEATURE_COLUMNS = [
    "t_genre_cos", "t_composer_cos", "t_artist_bought", "t_album_content_cos",
    "t_album_pop", "t_track_pop", "t_album_bought",
    "t_unit_price", "t_log_ms", "t_composer_missing", "t_cust_n_tracks",
]

COMPOSER_SPLIT = re.compile(r"[,/;]")
RECENCY_DAYS = 365.0


def _slug(text):
    return re.sub(r"\s+", "_", str(text).strip().lower())


def _composer_tokens(text):
    return [f"comp_{_slug(c)}" for c in COMPOSER_SPLIT.split(str(text)) if c.strip()]


def _unit(vec):
    return vec / (np.linalg.norm(vec) + 1e-12)


class ProfileState:
    """Thống kê rút ra từ một tập lịch sử mua (chỉ train).

    Nội dung album và track (genre, artist, composer) lấy từ catalog; phần thống kê hành vi
    (popularity, hồ sơ customer, recency) chỉ lấy từ lịch sử train, không bao giờ từ test.
    """

    def __init__(self, history, track_history, catalog, albums, customers):
        albums = albums.sort_values("AlbumId").reset_index(drop=True)
        self.album_ids = albums["AlbumId"].to_numpy()
        self.album_index = {a: i for i, a in enumerate(self.album_ids)}
        n = len(self.album_ids)

        # Ma trận nội dung album
        artist_ids = albums["ArtistId"].to_numpy()
        artist_codes = {a: j for j, a in enumerate(sorted(set(artist_ids)))}
        self.album_artist = np.array([artist_codes[a] for a in artist_ids])
        self.n_artists = len(artist_codes)
        onehot = np.zeros((n, self.n_artists))
        onehot[np.arange(n), self.album_artist] = 1.0

        genre_counts = (
            catalog.groupby(["AlbumId", "Genre"]).size().unstack(fill_value=0)
            .reindex(self.album_ids, fill_value=0)
        )
        genre_share = genre_counts.to_numpy(float)
        genre_share = genre_share / genre_share.sum(axis=1, keepdims=True)
        self.genre_names = list(genre_counts.columns)
        self.genre_mat = normalize(genre_share)
        self.album_profile = normalize(np.hstack([onehot, self.genre_mat]))

        album_tokens = {a: set() for a in self.album_ids}
        for row in catalog[["AlbumId", "ArtistId", "Genre", "Composer"]].itertuples(index=False):
            tokens = album_tokens[row.AlbumId]
            tokens.add(f"artist_{row.ArtistId}")
            tokens.add(f"genre_{_slug(row.Genre)}")
            tokens.update(_composer_tokens(row.Composer))
        docs = [" ".join(sorted(album_tokens[a])) for a in self.album_ids]
        self.tfidf = TfidfVectorizer(token_pattern=r"\S+", lowercase=False)
        self.tfidf_mat = self.tfidf.fit_transform(docs)

        album_meta = albums.set_index("AlbumId").loc[self.album_ids]
        self.n_tracks = album_meta["NTracks"].to_numpy(float)
        self.log_total_ms = np.log1p(album_meta["TotalMs"].to_numpy(float))
        self.mean_price = album_meta["MeanPrice"].to_numpy(float)
        self.composer_missing = album_meta["ComposerMissingShare"].to_numpy(float)

        # Thống kê hành vi ở mức album
        self.customer_country = dict(zip(customers["CustomerId"], customers["Country"]))
        hist = history.assign(idx=history["AlbumId"].map(self.album_index))
        self.hist = {
            cid: (g["idx"].to_numpy(int), g["FirstPurchase"].to_numpy("datetime64[ns]"))
            for cid, g in hist.groupby("CustomerId")
        }
        self.ref_date = np.datetime64(hist["FirstPurchase"].max(), "ns")

        n_customers = hist["CustomerId"].nunique()
        self.pop_global = np.bincount(hist["idx"], minlength=n) / max(n_customers, 1)

        self.pop_country = {}
        for country, g in hist.groupby("Country"):
            size = g["CustomerId"].nunique()
            self.pop_country[country] = np.bincount(g["idx"], minlength=n) / size

        self._build_track_parts(track_history, catalog)

    def _build_track_parts(self, track_history, catalog):
        tracks = catalog.drop_duplicates("TrackId").sort_values("TrackId").reset_index(drop=True)
        self.track_ids = tracks["TrackId"].to_numpy()
        self.track_index = {t: i for i, t in enumerate(self.track_ids)}
        n_t = len(self.track_ids)

        self.track_album = np.array([self.album_index[a] for a in tracks["AlbumId"]], dtype=int)
        self.track_artist = self.album_artist[self.track_album]

        genre_idx = {g: j for j, g in enumerate(self.genre_names)}
        track_genre = np.zeros((n_t, len(self.genre_names)))
        track_genre[np.arange(n_t), [genre_idx[g] for g in tracks["Genre"]]] = 1.0
        self.track_genre_mat = normalize(track_genre)

        composer_docs = [" ".join(sorted(set(_composer_tokens(c)))) for c in tracks["Composer"]]
        self.track_tfidf = TfidfVectorizer(token_pattern=r"\S+", lowercase=False).fit_transform(composer_docs).tocsr()

        self.track_unit_price = tracks["UnitPrice"].to_numpy(float)
        self.track_log_ms = np.log1p(tracks["Milliseconds"].to_numpy(float))
        self.track_composer_missing = tracks["ComposerMissing"].to_numpy(float)

        th = track_history.assign(idx=track_history["TrackId"].map(self.track_index))
        self.track_hist = {cid: g["idx"].to_numpy(int) for cid, g in th.groupby("CustomerId")}
        n_customers = th["CustomerId"].nunique()
        self.track_pop = np.bincount(th["idx"], minlength=n_t) / max(n_customers, 1)

    # ---------- album ----------

    def history_of(self, customer_id):
        if customer_id in self.hist:
            return self.hist[customer_id]
        return np.array([], dtype=int), np.array([], dtype="datetime64[ns]")

    def content_scores(self, customer_id):
        """Điểm cosine của mọi album với hồ sơ customer: genre, artist+genre, TF-IDF."""
        hidx, _ = self.history_of(customer_id)
        if len(hidx) == 0:
            zeros = np.zeros(len(self.album_ids))
            return zeros, zeros, zeros

        genre_scores = self.genre_mat @ _unit(self.genre_mat[hidx].mean(axis=0))
        profile_scores = self.album_profile @ _unit(self.album_profile[hidx].mean(axis=0))
        tfidf_profile = np.asarray(self.tfidf_mat[hidx].mean(axis=0)).ravel()
        tfidf_scores = self.tfidf_mat @ _unit(tfidf_profile)
        return genre_scores, profile_scores, tfidf_scores

    def feature_matrix(self, customer_id):
        """Feature của mọi album cho một customer, đúng thứ tự FEATURE_COLUMNS."""
        hidx, hdate = self.history_of(customer_id)
        genre_cos, profile_cos, tfidf_cos = self.content_scores(customer_id)

        n_artists = self.n_artists
        artist_bought = np.bincount(self.album_artist[hidx], minlength=n_artists)
        if len(hidx):
            age_days = (self.ref_date - hdate).astype("timedelta64[D]").astype(float)
            decay = np.exp(-age_days / RECENCY_DAYS)
            artist_recency = np.bincount(self.album_artist[hidx], weights=decay, minlength=n_artists)
        else:
            artist_recency = np.zeros(n_artists)

        country = self.customer_country.get(customer_id)
        pop_country = self.pop_country.get(country, np.zeros(len(self.album_ids)))

        X = pd.DataFrame({
            "genre_cos": genre_cos,
            "artist_genre_cos": profile_cos,
            "tfidf_cos": tfidf_cos,
            "pop_global": self.pop_global,
            "pop_country": pop_country,
            "artist_bought": artist_bought[self.album_artist],
            "artist_recency": artist_recency[self.album_artist],
            "n_tracks": self.n_tracks,
            "log_total_ms": self.log_total_ms,
            "mean_price": self.mean_price,
            "composer_missing": self.composer_missing,
            "cust_n_albums": np.full(len(self.album_ids), len(hidx), dtype=float),
        })
        return X[FEATURE_COLUMNS]

    # ---------- track ----------

    def track_history_of(self, customer_id):
        return self.track_hist.get(customer_id, np.array([], dtype=int))

    def track_feature_matrix(self, customer_id):
        """Feature của mọi track cho một customer, đúng thứ tự TRACK_FEATURE_COLUMNS."""
        hidx = self.track_history_of(customer_id)
        n_t = len(self.track_ids)

        if len(hidx):
            genre_cos = self.track_genre_mat @ _unit(self.track_genre_mat[hidx].mean(axis=0))
            composer_profile = np.asarray(self.track_tfidf[hidx].mean(axis=0)).ravel()
            composer_cos = self.track_tfidf @ _unit(composer_profile)
        else:
            genre_cos = np.zeros(n_t)
            composer_cos = np.zeros(n_t)

        artist_bought = np.bincount(self.track_artist[hidx], minlength=self.n_artists)
        album_bought = np.bincount(self.track_album[hidx], minlength=len(self.album_ids))
        album_content = self.content_scores(customer_id)[1][self.track_album]

        X = pd.DataFrame({
            "t_genre_cos": genre_cos,
            "t_composer_cos": composer_cos,
            "t_artist_bought": artist_bought[self.track_artist],
            "t_album_content_cos": album_content,
            "t_album_pop": self.pop_global[self.track_album],
            "t_track_pop": self.track_pop,
            "t_album_bought": album_bought[self.track_album],
            "t_unit_price": self.track_unit_price,
            "t_log_ms": self.track_log_ms,
            "t_composer_missing": self.track_composer_missing,
            "t_cust_n_tracks": np.full(n_t, len(hidx), dtype=float),
        })
        return X[TRACK_FEATURE_COLUMNS]
