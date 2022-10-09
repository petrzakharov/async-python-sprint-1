import logging
import multiprocessing

from tasks import DataAggregationTask, DataAnalyzingTask, DataCalculationTask

logger = logging.getLogger()


def forecast_weather():
    logging.basicConfig(
        filename='application-log.log',
        filemode='w',
        format='%(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    try:
        queue = multiprocessing.Queue()
        process_producer = DataCalculationTask(queue)
        process_consumer = DataAggregationTask(queue)
        process_producer.start()
        process_producer.join()
        process_consumer.start()
        process_consumer.join()
        DataAnalyzingTask().analyze()
    except Exception as exception:
        logger.error(exception)


if __name__ == '__main__':
    forecast_weather()
