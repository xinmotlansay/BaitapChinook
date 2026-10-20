import pandas as pd

from connectors.connector import Connector


class AlbumDAO:

    @staticmethod
    def getCatalog():
        """Toàn bộ track kèm album, artist, genre, media type."""
        sql = """
            SELECT t.TrackId, t.Name AS TrackName, t.AlbumId, al.Title AS AlbumTitle,
                   al.ArtistId, ar.Name AS Artist, t.GenreId, g.Name AS Genre,
                   t.MediaTypeId, t.Composer, t.Milliseconds, t.UnitPrice
            FROM Track t
            JOIN Album al ON al.AlbumId = t.AlbumId
            JOIN Artist ar ON ar.ArtistId = al.ArtistId
            JOIN Genre g ON g.GenreId = t.GenreId
        """
        return pd.read_sql_query(sql, Connector.ensureConnection())

    @staticmethod
    def getPurchaseLines():
        """Mọi dòng mua hàng kèm customer, ngày mua và quốc gia."""
        sql = """
            SELECT il.InvoiceLineId, i.InvoiceDate, i.CustomerId, c.Country,
                   il.TrackId, il.UnitPrice, il.Quantity
            FROM InvoiceLine il
            JOIN Invoice i ON i.InvoiceId = il.InvoiceId
            JOIN Customer c ON c.CustomerId = i.CustomerId
        """
        return pd.read_sql_query(sql, Connector.ensureConnection())

    @staticmethod
    def getTracksByAlbum(album_id):
        sql = """
            SELECT t.TrackId, t.Name AS TrackName, g.Name AS Genre,
                   t.Composer, t.Milliseconds, t.UnitPrice
            FROM Track t
            JOIN Genre g ON g.GenreId = t.GenreId
            WHERE t.AlbumId = ?
            ORDER BY t.TrackId
        """
        return pd.read_sql_query(sql, Connector.ensureConnection(), params=(album_id,))

    @staticmethod
    def getPurchasedAlbumIds(customer_id):
        sql = """
            SELECT DISTINCT t.AlbumId
            FROM Invoice i
            JOIN InvoiceLine il ON il.InvoiceId = i.InvoiceId
            JOIN Track t ON t.TrackId = il.TrackId
            WHERE i.CustomerId = ?
        """
        rows = Connector.ensureConnection().execute(sql, (customer_id,)).fetchall()
        return [r[0] for r in rows]

    @staticmethod
    def getPurchasedTrackIds(customer_id):
        sql = """
            SELECT DISTINCT il.TrackId
            FROM Invoice i
            JOIN InvoiceLine il ON il.InvoiceId = i.InvoiceId
            WHERE i.CustomerId = ?
        """
        rows = Connector.ensureConnection().execute(sql, (customer_id,)).fetchall()
        return [r[0] for r in rows]

    @staticmethod
    def getGenres():
        sql = "SELECT GenreId, Name FROM Genre ORDER BY Name"
        return pd.read_sql_query(sql, Connector.ensureConnection())
