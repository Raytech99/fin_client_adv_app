import numpy as np
class RTLearner:
    def __init__(self, leaf_size=5, verbose=False):
        self.leaf_size = leaf_size
        self.verbose = verbose
        self.tree = None

    @staticmethod
    def _mode(arr):
        vals, counts = np.unique(arr, return_counts=True)
        return float(vals[np.argmax(counts)])

    def add_evidence(self, data_x, data_y):
        self.tree = self._build_tree(data_x, data_y)

    def _build_tree(self, data_x, data_y):
        if data_x.shape[0] <= self.leaf_size:
            return np.array([[-1, self._mode(data_y), np.nan, np.nan]])

        if np.all(data_y == data_y[0]):
            return np.array([[-1, data_y[0], np.nan, np.nan]])

        best_feature = np.random.randint(0, data_x.shape[1])
        split_val = np.median(data_x[:, best_feature])

        left_idx = data_x[:, best_feature] <= split_val
        right_idx = ~left_idx

        if not left_idx.any() or not right_idx.any():
            return np.array([[-1, self._mode(data_y), np.nan, np.nan]])

        left_tree = self._build_tree(data_x[left_idx], data_y[left_idx])
        right_tree = self._build_tree(data_x[right_idx], data_y[right_idx])
        root = np.array([[best_feature, split_val, 1, len(left_tree) + 1]])
        return np.vstack([root, left_tree, right_tree])

    def _query_single(self, point):
        node_idx = 0
        while True:
            feature = int(self.tree[node_idx, 0])
            if feature == -1:
                return self.tree[node_idx, 1]
            if point[feature] <= self.tree[node_idx, 1]:
                node_idx += int(self.tree[node_idx, 2])
            else:
                node_idx += int(self.tree[node_idx, 3])

    def query(self, points):
        return np.array([self._query_single(p) for p in points])
