import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from behaviordisc import cp_detection_KSWIN
import re
from statsmodels.tsa.stattools import adfuller


# Test for multivariate ts
def stationary_test(data):  # df input
    """
    Tests for all variables if its stationary using adf-test.
    If at least one feature is not, returns false for the corresponding data
    :param data: df object, i.e. sd_log.data
    :return:
    """
    for feat in data.columns:
        result = adfuller(data[feat], autolag='AIC')
        if result[1] > 0.05:
            print(str(feat) + ' is not stationary')
            return False
    return True


def make_stationary(data, count=0):  # df input
    """
    Makes the data stationary using diff
    :param data: df object, i.e. sd_log.data
    :param count: counts order of differencing
    :return: stationary data as df and order of differencing
    """
    if stationary_test(data):
        return data, count
    else:
        return make_stationary(data.diff().dropna(), count + 1)



class Sdl:

    def __init__(self, path):
        self.data = pd.read_csv(path)
        self.raw_data = pd.read_csv(path)
        self.isStationary = stationary_test(self.data)
        self.data_diff = make_stationary(self.data)

        self.series = self.data.to_numpy()
        self.columns = self.data.columns
        self.tw = re.findall(r'\d+[A-Z]', self.columns[0])[0]  # time window of sd_log
        #  variables as string
        self.arrival_rate = [s for s in self.columns if "arrival" in s.lower()][0]
        self.finish_rate = [s for s in self.columns if "finish" in s.lower()][0]
        self.num_unique_resource = [s for s in self.columns if "resource" in s.lower()][0]
        self.process_active_time = [s for s in self.columns if "active" in s.lower()][0]
        self.service_time = [s for s in self.columns if "service" in s.lower()][0]
        # TODO
        self.time_in_process = [self.columns[5]][0]
        self.waiting_time = [s for s in self.columns if "waiting" in s.lower()][0]
        self.num_in_process = [self.columns[7]][0]
        # TODO
        self.relations = {}
        self.changepoints = {}
        self.behavior = {}

    def preprocess_rawData(self):
        #  TODO, currently expecting Active (preprocessed) sdLog
        data = self.rawData
        data = data.fillna(method='pad')  # filling missing values with previous ones

        return data

    # returns points as numpy array
    def get_points(self, col):
        return np.array(self.data[col])

    # plots all aspect
    def plot_all(self, title='All aspects plotted:', save=False):
        self.data.plot(subplots=True, xlabel="index",
                       figsize=(5, 10), grid=True)
        plt.show()
        if save:
            plt.savefig('pictures/' + title)

    def plot_all_with_cp(self):
        ax = self.data.plot(subplots=True, xlabel="index",
                            figsize=(5, 10), grid=True)

        for i, col in zip(ax, self.columns):
            detected = cp_detection_KSWIN(self.get_points(col), period=self.tw)
            if not detected:
                continue
            i.axvspan(0, detected[0], label="Change Point", color="red", alpha=0.3)
            for s in range(0, len(detected) - 2, 2):
                i.axvspan(detected[s], detected[s + 1], label="Change Point", color="green", alpha=0.3)
                i.axvspan(detected[s + 1], detected[s + 2], label="Change Point", color="red", alpha=0.3)
            i.axvspan(detected[-1], len(self.data), label="Change Point", color="green", alpha=0.3)
        plt.show()
