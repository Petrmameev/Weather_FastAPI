import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

from find_city import get_coords_by_name


def get_weather_forecast(name_city):
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": float(get_coords_by_name(name_city)[0]),
        "longitude": float(get_coords_by_name(name_city)[1]),
        "current": [
            "temperature_2m",
            "apparent_temperature",
            "precipitation",
            "rain",
            "showers",
            "snowfall",
        ],
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_hours",
            "precipitation_probability_max",
        ],
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    # print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    # print(f"Elevation {response.Elevation()} m asl")
    # print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
    # print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    # Current values. The order of variables needs to be the same as requested.
    current = response.Current()
    current_temperature_2m = current.Variables(0).Value()
    current_apparent_temperature = current.Variables(1).Value()
    current_precipitation = current.Variables(2).Value()
    current_rain = current.Variables(3).Value()
    current_showers = current.Variables(4).Value()
    current_snowfall = current.Variables(5).Value()

    # print(f"Current time {current.Time()}")
    # print(f"Current temperature_2m {current_temperature_2m}")
    # print(f"Current apparent_temperature {current_apparent_temperature}")
    # print(f"Current precipitation {current_precipitation}")
    # print(f"Current rain {current_rain}")
    # print(f"Current showers {current_showers}")
    # print(f"Current snowfall {current_snowfall}")

    # Process daily data. The order of variables needs to be the same as requested.
    daily = response.Daily()
    daily_temperature_2m_max = daily.Variables(0).ValuesAsNumpy()
    daily_temperature_2m_min = daily.Variables(1).ValuesAsNumpy()
    daily_precipitation_hours = daily.Variables(2).ValuesAsNumpy()
    daily_precipitation_probability_max = daily.Variables(3).ValuesAsNumpy()

    daily_data = {
        "date": pd.date_range(
            start=pd.to_datetime(daily.Time(), unit="s", utc=True),
            end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=daily.Interval()),
            inclusive="left",
        )
    }
    daily_data["temperature_2m_max"] = daily_temperature_2m_max
    daily_data["temperature_2m_min"] = daily_temperature_2m_min
    daily_data["precipitation_hours"] = daily_precipitation_hours
    daily_data["precipitation_probability_max"] = daily_precipitation_probability_max
    daily_data["current_temperature_2m"] = current_temperature_2m
    daily_data["current_apparent_temperature"] = current_apparent_temperature

    daily_dataframe = pd.DataFrame(data=daily_data)
    # print(daily_dataframe)
    return daily_dataframe
