# src/crawler/items.py
import scrapy

class AkomodasiItem(scrapy.Item):
    hotel_id = scrapy.Field()
    sumber_url = scrapy.Field()
    nama_akomodasi = scrapy.Field()
    tipe_akomodasi = scrapy.Field()
    alamat_lengkap = scrapy.Field()
    kota = scrapy.Field()
    region = scrapy.Field()
    lokasi_sekitar = scrapy.Field()
    rating_review = scrapy.Field()
    jumlah_review = scrapy.Field()
    info_rating = scrapy.Field()
    harga_min = scrapy.Field()
    fasilitas = scrapy.Field()
    bintang_rating = scrapy.Field()
    tipe_kamar = scrapy.Field()
    harga_per_tipe_kamar = scrapy.Field()
    tanggal_crawling = scrapy.Field()