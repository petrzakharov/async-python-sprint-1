import logging
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process

import pandas as pd

from api_client import YandexWeatherAPI
from utils import (CITIES, DF_TEMPLATE, GOOD_WEATHER, MAX_TIME_IN_EACH_DATE,
                   MIN_TIME_IN_EACH_DATE, MSG_CLEAR_QUEUE, MSG_CSV_SAVED,
                   MSG_FINAL, MSG_GET_ITEM_QUEUE, MSG_NOT_ENOUGH_DATA,
                   MSG_QUEUT_PUT, MSG_RECOMMENDED_CITIES)

logger = logging.getLogger()


class DataFetchingTask:
    @staticmethod
    def get_info_about_city(city: str) -> dict:
        return YandexWeatherAPI().get_forecasting(city)


class DataCalculationTask(Process):

    def __init__(self, queue):
        super().__init__()
        self.queue = queue

    @staticmethod
    def check_condition(condition: str) -> bool:
        if condition in GOOD_WEATHER:
            return True
        return False

    @staticmethod
    def temperature_and_condition_calc(hours: list) -> dict:
        temperature_by_hour = []
        cnt_good_hours = 0
        if len(hours) != 24:
            raise ValueError
        for hour in hours:
            if MIN_TIME_IN_EACH_DATE <= int(hour['hour']) <= MAX_TIME_IN_EACH_DATE:
                temperature_by_hour.append(hour['temp'])
                if DataCalculationTask.check_condition(hour['condition']):
                    cnt_good_hours += 1
        return {
            'avg_temp': sum(temperature_by_hour) / len(temperature_by_hour),
            'good_hours': cnt_good_hours
        }

    @staticmethod
    def general_calculate(city: str) -> list:
        temperature_all = []
        cnt_good_hours_all = []
        temperature, weather = dict(), dict()
        city_data = DataFetchingTask().get_info_about_city(city)
        for date_obj in city_data['forecasts']:
            date = date_obj['date']
            try:
                result_one_day = (
                    DataCalculationTask.temperature_and_condition_calc(date_obj['hours'])
                )
                temperature_all.append(result_one_day['avg_temp'])
                cnt_good_hours_all.append(result_one_day['good_hours'])
                temperature[date] = result_one_day['avg_temp']
                weather[date] = result_one_day['good_hours']
            except (ZeroDivisionError, ValueError):
                logger.debug(msg=MSG_NOT_ENOUGH_DATA.format(city=city, date=date))
                continue
            temperature['Среднее'] = sum(temperature_all) / len(temperature_all)
            weather['Среднее'] = sum(cnt_good_hours_all) / len(cnt_good_hours_all)
        return [
            {'Город/день': city, **DF_TEMPLATE[0], **temperature},
            {**DF_TEMPLATE[1], **weather}
        ]

    def run(self):
        with ThreadPoolExecutor() as pool:
            future = pool.map(self.general_calculate, CITIES.keys())
            for city_item in future:
                self.queue.put(city_item)
                logger.info(msg=MSG_QUEUT_PUT.format(item=city_item))


class DataAggregationTask(Process):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue

    def run(self):
        df_lists = []
        while True:
            if self.queue.empty():
                logger.info(msg=MSG_CLEAR_QUEUE)
                pd.DataFrame.from_dict(df_lists).to_csv('results.csv')
                logger.info(msg=MSG_CSV_SAVED)
                break
            item = self.queue.get()
            df_lists.extend(item)
            logger.info(msg=MSG_GET_ITEM_QUEUE.format(item=item))
            # почему-то не работает логгер ?!


class DataAnalyzingTask:
    @staticmethod
    def analyze():
        df = pd.read_csv('results.csv')
        df = (df.merge(df.groupby('Город/день')
                       .agg({'Среднее': 'sum'})
                       .rename(columns={'Среднее': 'Рейтинг'}), on='Город/день'))
        df['rank'] = df['Рейтинг'].rank(ascending=False)
        result = list(df[df['rank'] == df['rank'].min()]['Город/день'].unique())
        logger.info(msg=MSG_FINAL.format(cities=result))
        print(
            MSG_RECOMMENDED_CITIES.format(cities=result)
        )
