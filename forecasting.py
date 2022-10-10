import multiprocessing

from tasks import DataAggregationTask, DataAnalyzingTask, DataCalculationTask, DataFetchingTask


def forecast_weather():
    queue = multiprocessing.Queue()
    process_producer = DataCalculationTask(queue)
    process_consumer = DataAggregationTask(queue)
    process_producer.start()
    process_producer.join()
    process_consumer.start()
    process_consumer.join()
    DataAnalyzingTask().analyze()


if __name__ == '__main__':
    forecast_weather()
