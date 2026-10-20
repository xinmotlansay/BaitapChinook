import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

from config import TRAIN_RATIO, VALID_RATIO
from dal.AlbumDAO import AlbumDAO
from dal.CustomerDAO import CustomerDAO

logger = logging.getLogger(__name__)


@dataclass
class Prepared:
    catalog: pd.DataFrame       # track đã làm sạch, có cờ thiếu composer
    albums: pd.DataFrame        # một dòng cho mỗi album
    customers: pd.DataFrame     # customer kèm quốc gia
    interactions: pd.DataFrame  # customer x album, có thời gian mua
    track_interactions: pd.DataFrame  # customer x track (kèm album của track)
    report: pd.DataFrame        # báo cáo làm sạch


def _add_row(rows, step, before, after):
    rows.append({
        "Bước": step,
        "Số dòng trước": before,
        "Số dòng sau": after,
        "Bị loại": before - after,
    })
    logger.info("%s: %d -> %d", step, before, after)


def clean(catalog, lines):
    """Làm sạch dòng mua và catalog, trả về (catalog, lines, báo cáo)."""
    rows = []

    n = len(lines)
    lines = lines.drop_duplicates(subset=["InvoiceLineId"])
    _add_row(rows, "Dòng hóa đơn trùng lặp", n, len(lines))

    n = len(lines)
    lines = lines[lines["TrackId"].isin(catalog["TrackId"])]
    _add_row(rows, "Track không có trong catalog (mồ côi)", n, len(lines))

    n = len(lines)
    lines = lines[lines["Quantity"] > 0]
    _add_row(rows, "Quantity <= 0", n, len(lines))

    n = len(lines)
    lines = lines[lines["UnitPrice"] > 0]
    _add_row(rows, "Giá <= 0", n, len(lines))

    n = len(lines)
    lines = lines.assign(InvoiceDate=pd.to_datetime(lines["InvoiceDate"], errors="coerce"))
    lines = lines.dropna(subset=["InvoiceDate"])
    _add_row(rows, "Ngày mua sai định dạng", n, len(lines))

    n = len(catalog)
    catalog = catalog.assign(
        Artist=catalog["Artist"].str.strip(),
        Composer=catalog["Composer"].str.strip(),
    )
    missing = catalog["Composer"].isna() | (catalog["Composer"] == "")
    catalog = catalog.assign(
        ComposerMissing=missing.astype(int),
        Composer=catalog["Composer"].where(~missing, "Unknown"),
    )
    _add_row(rows, "Composer rỗng, đổi thành Unknown (giữ lại)", n, n)

    return catalog, lines.reset_index(drop=True), pd.DataFrame(rows)


def build_albums(catalog):
    """Bảng album: thông tin cơ bản, dùng làm nền cho feature."""
    genre_counts = (
        catalog.groupby(["AlbumId", "Genre"]).size().reset_index(name="n")
        .sort_values(["AlbumId", "n"], ascending=[True, False])
    )
    genres = genre_counts.groupby("AlbumId")["Genre"].agg(lambda s: ", ".join(s))

    albums = catalog.groupby("AlbumId").agg(
        Title=("AlbumTitle", "first"),
        ArtistId=("ArtistId", "first"),
        Artist=("Artist", "first"),
        NTracks=("TrackId", "nunique"),
        TotalMs=("Milliseconds", "sum"),
        MeanPrice=("UnitPrice", "mean"),
        ComposerMissingShare=("ComposerMissing", "mean"),
    )
    albums = albums.assign(Genres=genres).reset_index()
    return albums


def build_interactions(lines, catalog):
    """Gộp dòng mua thành (customer, album): số track đã mua, thời điểm mua."""
    tracks_per_album = (
        catalog.groupby("AlbumId")["TrackId"].nunique().rename("NTracksAlbum").reset_index()
    )
    merged = lines.merge(catalog[["TrackId", "AlbumId"]], on="TrackId")
    inter = (
        merged.groupby(["CustomerId", "AlbumId"])
        .agg(
            NTracksBought=("TrackId", "nunique"),
            FirstPurchase=("InvoiceDate", "min"),
            LastPurchase=("InvoiceDate", "max"),
        )
        .reset_index()
        .merge(tracks_per_album, on="AlbumId")
    )
    inter["Coverage"] = inter["NTracksBought"] / inter["NTracksAlbum"]
    return inter


def build_track_interactions(lines, catalog):
    """Mỗi (customer, track) một dòng, kèm album của track và ngày mua đầu tiên."""
    merged = lines.merge(catalog[["TrackId", "AlbumId"]], on="TrackId")
    return (
        merged.groupby(["CustomerId", "TrackId", "AlbumId"])
        .agg(FirstPurchase=("InvoiceDate", "min"))
        .reset_index()
    )


def track_rows_for(track_inter, album_pairs):
    """Lấy các track của đúng những cặp (customer, album) trong album_pairs.

    Track đi theo album nên không có track nào của album train xuất hiện trong nhãn test.
    """
    keys = album_pairs[["CustomerId", "AlbumId"]].drop_duplicates()
    return track_inter.merge(keys, on=["CustomerId", "AlbumId"])


def split_by_time(inter, head_ratio):
    """Với mỗi customer, sắp album theo ngày mua đầu tiên; head_ratio đầu vào phần head, còn lại vào phần tail."""
    inter = inter.sort_values(["CustomerId", "FirstPurchase", "AlbumId"]).reset_index(drop=True)
    rank = inter.groupby("CustomerId").cumcount()
    size = inter.groupby("CustomerId")["AlbumId"].transform("size")
    # Luôn để ít nhất 1 album ở mỗi phần khi customer có từ 2 album trở lên
    n_head = np.minimum(size - 1, np.maximum(1, np.round(size * head_ratio))).astype(int)
    head_mask = rank < n_head
    return inter[head_mask].reset_index(drop=True), inter[~head_mask].reset_index(drop=True)


def split_train_test(inter):
    train, test = split_by_time(inter, TRAIN_RATIO)

    # Kiểm tra chống rò rỉ: không album test nào nằm trong train của cùng customer
    merged = test.merge(train[["CustomerId", "AlbumId"]], on=["CustomerId", "AlbumId"])
    assert merged.empty, "Có album vừa thuộc train vừa thuộc test"

    # Mỗi customer trong test phải có lịch sử train
    test_customers = set(test["CustomerId"])
    train_customers = set(train["CustomerId"])
    assert test_customers <= train_customers, "Có customer test nhưng không có lịch sử train"

    logger.info("Chia train/test: %d train, %d test, %d customer", len(train), len(test), len(test_customers))
    return train, test


def split_valid(train):
    """Tách validation từ cuối phần train để chọn tham số."""
    sub_train, valid = split_by_time(train, 1 - VALID_RATIO)
    assert set(valid["CustomerId"]) <= set(sub_train["CustomerId"])
    return sub_train, valid


def prepare():
    catalog = AlbumDAO.getCatalog()
    lines = AlbumDAO.getPurchaseLines()
    customers = CustomerDAO.getAll().rename(columns={"Name": "CustomerName"})

    catalog, lines, report = clean(catalog, lines)
    albums = build_albums(catalog)
    interactions = build_interactions(lines, catalog)
    interactions = interactions.merge(
        customers[["CustomerId", "Country"]], on="CustomerId", how="left"
    )
    track_interactions = build_track_interactions(lines, catalog)

    return Prepared(
        catalog=catalog,
        albums=albums,
        customers=customers,
        interactions=interactions,
        track_interactions=track_interactions,
        report=report,
    )
