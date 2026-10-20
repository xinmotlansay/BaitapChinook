import pandas as pd

from connectors.connector import Connector


class CustomerDAO:

    @staticmethod
    def getAll():
        sql = """
            SELECT CustomerId, FirstName || ' ' || LastName AS Name, Country
            FROM Customer
            ORDER BY CustomerId
        """
        return pd.read_sql_query(sql, Connector.ensureConnection())

    @staticmethod
    def getCountries():
        sql = "SELECT DISTINCT Country FROM Customer ORDER BY Country"
        return pd.read_sql_query(sql, Connector.ensureConnection())

    @staticmethod
    def getPurchaseHistory(customer_id):
        sql = """
            SELECT i.InvoiceDate, t.TrackId, t.Name AS TrackName, t.Composer,
                   al.AlbumId, al.Title AS AlbumTitle, ar.Name AS Artist, g.Name AS Genre
            FROM Invoice i
            JOIN InvoiceLine il ON il.InvoiceId = i.InvoiceId
            JOIN Track t ON t.TrackId = il.TrackId
            JOIN Album al ON al.AlbumId = t.AlbumId
            JOIN Artist ar ON ar.ArtistId = al.ArtistId
            JOIN Genre g ON g.GenreId = t.GenreId
            WHERE i.CustomerId = ?
            ORDER BY i.InvoiceDate
        """
        return pd.read_sql_query(sql, Connector.ensureConnection(), params=(customer_id,))
