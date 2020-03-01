import time
import datetime
import myfitnesspal
import logging
import os
import sys
from prometheus_client.core import Gauge, GaugeMetricFamily, REGISTRY, CounterMetricFamily
from prometheus_client import start_http_server

VERSION = "1.0.1"

class MyFitnesspalCollector(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self._connected = False
        self.connect()

    def connect(self):
        try:
            logging.info("connect as {} and {}".format(self.username, self.password))
            self.client = myfitnesspal.Client(self.username, password=self.password, login=True)
            self._connected = True
            logging.info("connected")
        except Exception as e:
            logging.info("connection failed: "+str(e))
            self._connected = False

    def collect(self):
        logging.info("i collect")
        if not self._connected:
            logging.info("reconnect")
            self.connect()
        try:
            today = self.client.get_date(datetime.date.today())
            totals = today.totals
            logging.info("got totals {}".format(str(totals)))
            goals = today.goals
            logging.info("got goals {}".format(str(goals)))
            #got goals {'calories': 1630, 'carbohydrates': 204, 'fat': 54, 'protein': 82, 'sodium': 2300, 'sugar': 61}
        except Exception as e:
            logging.critical("get userdata failed: "+str(e))
            self._connected = False
        try:
            weight_od = self.client.get_measurements("Weight")
            weight = weight_od[next(iter(weight_od.keys()))]
            logging.info("got weight {}".format(weight))
        except Exception as e:
            logging.critical("get weight failed: "+str(e))
            weight = 0

        logging.info("i collected")
#'calories': 2001,
#     'carbohydrates': 369,
#     'fat': 22,
#     'protein': 110,
#     'sodium': 3326,
#     'sugar': 103}

        up = GaugeMetricFamily("myfitnesspal_up", 'Help text', labels=['instance', 'user'])
        up.add_metric(['myfitnesspal', self.username], 1 if self._connected else 0)
        yield up
        build_info = GaugeMetricFamily('myfitnesspal_build_info', 'Build information', labels=['python_version', 'version'])
        build_info.add_metric(['.'.join([str(sys.version_info.major), str(sys.version_info.minor)]), VERSION], 1)
        yield build_info
        if self._connected:
            calories = GaugeMetricFamily("myfitnesspal_nutrition_joules_total", 'Help text', labels=['user'])
            calories.add_metric([self.username], totals.get("calories", 0) * 4.187 * 1000)
            yield calories
            carbohydrates = GaugeMetricFamily("myfitnesspal_nutrition_carbohydrates_grams_total", 'Help text', labels=['user'])
            carbohydrates.add_metric([self.username], totals.get("carbohydrates", 0))
            yield carbohydrates
            fat = GaugeMetricFamily("myfitnesspal_nutrition_fat_grams_total", 'Help text', labels=['user'])
            fat.add_metric([self.username], totals.get("fat", 0))
            yield fat
            protein = GaugeMetricFamily("myfitnesspal_nutrition_protein_grams_total", 'Help text', labels=['user'])
            protein.add_metric([self.username], totals.get("protein", 0))
            yield protein
            sodium = GaugeMetricFamily("myfitnesspal_nutrition_sodium_grams_total", 'Help text', labels=['user'])
            sodium.add_metric([self.username], totals.get("sodium", 0) / 1000)
            yield sodium
            sugar = GaugeMetricFamily("myfitnesspal_nutrition_sugar_grams_total", 'Help text', labels=['user'])
            sugar.add_metric([self.username], totals.get("sugar", 0))
            yield sugar
            gcalories = GaugeMetricFamily("myfitnesspal_nutrition_joules_goal", 'Help text', labels=['user'])
            gcalories.add_metric([self.username], goals.get("calories", 0) * 4.187 * 1000)
            yield gcalories
            gcarbohydrates = GaugeMetricFamily("myfitnesspal_nutrition_carbohydrates_grams_goal", 'Help text', labels=['user'])
            gcarbohydrates.add_metric([self.username], goals.get("carbohydrates", 0))
            yield gcarbohydrates
            gfat = GaugeMetricFamily("myfitnesspal_nutrition_fat_grams_goal", 'Help text', labels=['user'])
            gfat.add_metric([self.username], goals.get("fat", 0))
            yield gfat
            gprotein = GaugeMetricFamily("myfitnesspal_nutrition_protein_grams_goal", 'Help text', labels=['user'])
            gprotein.add_metric([self.username], goals.get("protein", 0))
            yield gprotein
            gsodium = GaugeMetricFamily("myfitnesspal_nutrition_sodium_grams_goal", 'Help text', labels=['user'])
            gsodium.add_metric([self.username], goals.get("sodium", 0) / 1000)
            yield gsodium
            gsugar = GaugeMetricFamily("myfitnesspal_nutrition_sugar_grams_goal", 'Help text', labels=['user'])
            gsugar.add_metric([self.username], goals.get("sugar", 0))
            yield gsugar
            if weight:
                kilos = GaugeMetricFamily("myfitnesspal_weight", 'Help text', labels=['user'])
                kilos.add_metric([self.username], weight)
                yield kilos


if __name__ == '__main__':
    log_handler = logging.StreamHandler()
    log_format = '[%(asctime)s] %(name)s.%(levelname)s %(threadName)s %(message)s'
    #formatter = JogFormatter(log_format) if args.json_logging else logging.Formatter(log_format)
    formatter = logging.Formatter(log_format)
    log_handler.setFormatter(formatter)

    #log_level = getattr(logging, args.log_level)
    log_level = getattr(logging, "DEBUG")
    logging.basicConfig(
        handlers=[log_handler],
        #level=logging.DEBUG if args.verbose else log_level
        level=logging.DEBUG
    )
    logging.captureWarnings(True)

    start_http_server(int(os.environ.get("MYFITNESSPAL_EXPORTER_PORT", "9681")))
    REGISTRY.register(MyFitnesspalCollector(os.environ["MYFITNESSPAL_USERNAME"], os.environ["MYFITNESSPAL_PASSWORD"]))
    while True:
        time.sleep(1)
