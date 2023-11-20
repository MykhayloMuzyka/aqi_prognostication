from numpy import sqrt, isnan


def error(real_value: float, predicted_value: float) -> float:
    return predicted_value - real_value


def bias(real, predicted) -> float:
    return sum([error(d, f) for f, d in zip(predicted, real)]) / len(real)


def MAPE(real, predicted) -> float:
    return sum([abs(error(d, f)) / d if d else abs(error(d, f)) / 1e-10 for f, d in zip(predicted, real)]) / len(real)


def MAE(real, predicted) -> float:
    return sum([abs(error(d, f)) for f, d in zip(predicted, real)]) / len(real)


def RMSE(real, predicted) -> float:
    return sqrt(sum([error(d, f)**2 for f, d in zip(predicted, real)]) / len(real))


def MSE(real, predicted) -> float:
    return sum([error(d, f)**2 for f, d in zip(predicted, real)]) / len(real)


def pearson(x, y):
    mean_x = sum(x) / len(x)
    mean_y = sum(y) / len(y)
    chys = 0
    for xi, yi in zip(x, y):
        chys += (xi - mean_x) * (yi - mean_y)
    znam_x, znam_y = 0, 0
    for xi, yi in zip(x, y):
        znam_x += (xi - mean_x) ** 2
        znam_y += (yi - mean_y) ** 2
    res = chys / sqrt((znam_x * znam_y))
    return res if not isnan(res) else 0
