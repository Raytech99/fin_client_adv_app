import numpy as np


class BagLearner:
    def __init__(self, learner, kwargs=None, bags=20, verbose=False):
        kwargs = kwargs or {}
        self.learners = [learner(**kwargs) for _ in range(bags)]

    def add_evidence(self, data_x, data_y):
        n = data_x.shape[0]
        for learner in self.learners:
            idx = np.random.choice(n, size=n, replace=True)
            learner.add_evidence(data_x[idx], data_y[idx])

    def query(self, points):
        preds = np.array([l.query(points) for l in self.learners])
        # majority vote across bags for each point
        result = np.array([
            self._mode(preds[:, i]) for i in range(preds.shape[1])
        ])
        return result

    @staticmethod
    def _mode(arr):
        vals, counts = np.unique(arr, return_counts=True)
        return float(vals[np.argmax(counts)])
