# needed for getpack
import subprocess
import importlib
import sys


# function that imports a library if it is installed, else installs it and then imports it
def getpack(package):
    try:
        return importlib.import_module(package)
        # import package
    except ImportError:
        subprocess.call([sys.executable, "-m", "pip", "install", package], stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
        return importlib.import_module(package)
        # import package


np = getpack("numpy")
scipy = getpack("scipy")
from scipy.stats import norm


# Value at risk historical method
def var_hist(returns, confidence, days):
    alpha = (1 - (confidence / 100))
    var_hist = -np.quantile(returns, alpha)
    var_hist *= np.sqrt(days)

    return var_hist


# Value at risk variance-covariance method
def var_vcov(returns, confidence, days):
    std_dev = returns.std()
    mean = returns.mean()

    alpha = (1 - (confidence / 100))
    var_var_covar = norm.ppf(1 - alpha) * std_dev - mean
    var_var_covar *= np.sqrt(days)

    return var_var_covar


# Expected Shortfall historical method
def cvar_hist(returns, var_hist, days):
    var_hist /= np.sqrt(days)
    es_hist = -returns[returns < -var_hist].mean()
    es_hist *= np.sqrt(days)
    return es_hist


# Expected Shortfall variance-covariance method
def cvar_vcov(returns, confidence, days):
    alpha = (1-(confidence/100))
    std_dev = returns.std()
    mean = returns.mean()

    es_var_covar = alpha**-1 * norm.pdf(norm.ppf(alpha))*std_dev-mean
    es_var_covar *= np.sqrt(days)

    return es_var_covar
