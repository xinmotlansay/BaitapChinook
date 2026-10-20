"""Suy luận: nạp model đã lưu và gợi ý, không huấn luyện lại.

Chạy: python -m ml.predict --customer 5 --k 10
"""
import argparse

from config import MODEL_PATH
from dal.AlbumDAO import AlbumDAO
from ml.features import FEATURE_COLUMNS
from ml.package import load_package
from ml.recommenders import (
    ArtistGenreProfile,
    ContentTfidf,
    GenreProfile,
    HybridRanker,
    Popularity,
    TrackHybrid,
)
from models.album import Track
from models.recommendation import Recommendation

class Predictor:

    def __init__(self, path=MODEL_PATH):
        state, ranker, track_ranker, albums, meta = load_package(path)
        if list(meta["feature_columns"]) != FEATURE_COLUMNS:
            raise ValueError("Thứ tự feature của model không khớp với code. Hãy chạy lại: python -m ml.train")

        self.state = state
        self.albums = albums.set_index("AlbumId")
        self.default_model = meta["default_model"]

        s = self.state
        self.models = {
            "M1": Popularity(s),
            "M2": GenreProfile(s),
            "M3": ArtistGenreProfile(s),
            "M4": ContentTfidf(s),
            "M5": HybridRanker(s, ranker),
        }
        self.track_model = TrackHybrid(s, track_ranker)

    def model_names(self):
        return {key: model.name for key, model in self.models.items()}

    def recommend(self, customer_id, k=10, model_key=None):
        """Top-k album cho customer đã có trong database. Không gợi ý lại album đã mua."""
        model = self.models[model_key or self.default_model]
        exclude = AlbumDAO.getPurchasedAlbumIds(customer_id)
        pairs = model.recommend(customer_id, k, exclude=exclude)

        features = self.state.feature_matrix(customer_id)
        results = []
        for album_id, score in pairs:
            row = features.iloc[self.state.album_index[album_id]]
            results.append(self._to_recommendation(customer_id, album_id, score, row))
        return results

    def cold_start(self, k=10, country=None, genres=None):
        """Gợi ý cho khách mới theo độ phổ biến, lọc theo quốc gia và/hoặc danh sách thể loại.

        Album được giữ nếu thuộc ít nhất một thể loại đã chọn.
        """
        s = self.state
        reasons = []
        if country in s.pop_country:
            scores = s.pop_country[country] + 1e-3 * s.pop_global
            reasons.append(f"Được khách hàng ở {country} mua nhiều")
        else:
            scores = s.pop_global.copy()
            reasons.append("Phổ biến trong cửa hàng")

        candidates = list(range(len(s.album_ids)))
        if genres:
            genre_idx = [s.genre_names.index(g) for g in genres]
            matched = (s.genre_mat[:, genre_idx] > 0).any(axis=1)
            candidates = [i for i in candidates if matched[i]]
            reasons.append("Thuộc thể loại: " + ", ".join(genres))

        order = sorted(candidates, key=lambda i: -scores[i])[:k]
        results = []
        for i in order:
            album_id = s.album_ids[i]
            results.append(Recommendation(
                album_id=int(album_id),
                title=self.albums.at[album_id, "Title"],
                artist=self.albums.at[album_id, "Artist"],
                genres=self.albums.at[album_id, "Genres"],
                score=float(scores[i]),
                reasons=list(reasons),
                tracks=self.album_tracks(None, album_id),
            ))
        return results

    def _to_recommendation(self, customer_id, album_id, score, row):
        album = self.albums.loc[album_id]
        return Recommendation(
            album_id=int(album_id),
            title=album["Title"],
            artist=album["Artist"],
            genres=album["Genres"],
            score=score,
            reasons=self._reasons(album["Artist"], album["Genres"], row),
            tracks=self.album_tracks(customer_id, album_id),
        )

    @staticmethod
    def _reasons(artist, genres, row):
        reasons = []
        if row["artist_bought"] >= 1:
            reasons.append(f"Bạn đã mua {int(row['artist_bought'])} album của {artist}")
        if row["genre_cos"] >= 0.5:
            reasons.append(f"Khớp thể loại yêu thích: {genres}")
        if row["tfidf_cos"] >= 0.3:
            reasons.append("Giống các album bạn đã mua (nghệ sĩ, nhạc sĩ, thể loại)")
        if row["pop_country"] > 0:
            reasons.append("Được khách hàng cùng quốc gia mua")
        if not reasons:
            reasons.append("Phổ biến trong cửa hàng")
        return reasons

    def album_tracks(self, customer_id, album_id):
        """Các track chưa mua của album, xếp theo điểm của mô hình track.

        customer_id là None (khách mới): xếp theo độ phổ biến của track trong train.
        Trả về danh sách (Track, điểm).
        """
        s = self.state
        if customer_id is None:
            scores = s.track_pop
            bought = set()
        else:
            scores = self.track_model.score_all(customer_id)
            bought = set(AlbumDAO.getPurchasedTrackIds(customer_id))

        tracks = [t for t in self.tracks_of(album_id) if t.track_id not in bought]
        ranked = sorted(tracks, key=lambda t: -scores[s.track_index[t.track_id]])
        return [(t, float(scores[s.track_index[t.track_id]])) for t in ranked]

    @staticmethod
    def tracks_of(album_id):
        df = AlbumDAO.getTracksByAlbum(int(album_id))
        return [
            Track(
                track_id=int(r.TrackId),
                name=r.TrackName,
                album_id=int(album_id),
                genre=r.Genre,
                composer=r.Composer if isinstance(r.Composer, str) else "Unknown",
                milliseconds=int(r.Milliseconds),
                unit_price=float(r.UnitPrice),
            )
            for r in df.itertuples(index=False)
        ]


def main():
    parser = argparse.ArgumentParser(description="Gợi ý album cho một customer")
    parser.add_argument("--customer", type=int, required=True)
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--model", default=None, choices=["M1", "M2", "M3", "M4", "M5"])
    args = parser.parse_args()

    predictor = Predictor()
    for rank, rec in enumerate(predictor.recommend(args.customer, args.k, args.model), start=1):
        print(f"{rank:2d}. {rec.title} — {rec.artist} [{rec.genres}] ({rec.score:.3f})")
        for reason in rec.reasons:
            print(f"      · {reason}")
        for track, score in rec.tracks:
            print(f"      ♪ {track.name} ({score:.3f})")


if __name__ == "__main__":
    main()
