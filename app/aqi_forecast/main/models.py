from django.db import models


class AqiData(models.Model):
    city = models.OneToOneField('City', models.DO_NOTHING, primary_key=True)  # The composite primary key (city_id, date) found, that is not supported. The first column is selected.
    date = models.DateTimeField()
    aqi = models.IntegerField(blank=True, null=True)
    wind = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'aqi_data'
        unique_together = (('city', 'date'),)


class City(models.Model):
    id = models.BigIntegerField(primary_key=True)
    name = models.TextField(blank=True, null=True)
    lat = models.FloatField(blank=True, null=True)
    lon = models.FloatField(blank=True, null=True)
    region = models.TextField(blank=True, null=True)
    name_transliterated = models.TextField(blank=True, null=True)
    area = models.FloatField(blank=True, null=True)
    population = models.IntegerField(blank=True, null=True)
    density = models.FloatField(blank=True, null=True)
    city_code = models.TextField(unique=True, blank=True, null=True)
    city_code_id = models.TextField(unique=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'city'


class Factory(models.Model):
    place_id = models.TextField(primary_key=True)
    place_name = models.TextField(blank=True, null=True)
    google_place_url = models.TextField(blank=True, null=True)
    sf_industry = models.TextField(blank=True, null=True)
    full_address = models.TextField(blank=True, null=True)
    city = models.TextField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    closed_status = models.TextField(blank=True, null=True)
    store_type = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    is_global = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'factory'


class MeteopostMeteodataArchive(models.Model):
    city_code = models.OneToOneField(City, models.DO_NOTHING, db_column='city_code', primary_key=True)
    date = models.DateTimeField()
    visibility_range = models.FloatField(blank=True, null=True)
    clouds = models.IntegerField(blank=True, null=True)
    wind_dir = models.IntegerField(blank=True, null=True)
    wind_speed = models.IntegerField(blank=True, null=True)
    temperature = models.FloatField(blank=True, null=True)
    dewpoint = models.FloatField(blank=True, null=True)
    pressure = models.FloatField(blank=True, null=True)
    precipitation = models.FloatField(blank=True, null=True)
    state = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'meteopost_meteodata_archive'
        unique_together = (('city_code', 'date'),)


class MeteopostWeatherArchive(models.Model):
    city_code = models.OneToOneField(City, models.DO_NOTHING, db_column='city_code', primary_key=True)  # The composite primary key (city_code, date) found, that is not supported. The first column is selected.
    temperature = models.IntegerField(blank=True, null=True)
    pressure = models.IntegerField(blank=True, null=True)
    wind_dir = models.IntegerField(blank=True, null=True)
    wind_speed = models.IntegerField(blank=True, null=True)
    humidity = models.IntegerField(blank=True, null=True)
    state = models.TextField(blank=True, null=True)
    date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'meteopost_weather_archive'
        unique_together = (('city_code', 'date'),)


class Sinoptik(models.Model):
    city = models.OneToOneField(City, models.DO_NOTHING, primary_key=True)  # The composite primary key (city_id, date) found, that is not supported. The first column is selected.
    date = models.DateTimeField()
    state = models.TextField(blank=True, null=True)
    temperature = models.FloatField(blank=True, null=True)
    feels_like = models.FloatField(blank=True, null=True)
    pressure = models.FloatField(blank=True, null=True)
    humidity = models.FloatField(blank=True, null=True)
    wind_dir = models.TextField(blank=True, null=True)
    wind_speed = models.FloatField(blank=True, null=True)
    precipitation = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sinoptik'
        unique_together = (('city', 'date'),)
