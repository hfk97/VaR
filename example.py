# import custom module
from VaR import *

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


# install/import other necessary modules
pd = getpack("pandas")
matplotlib = getpack("matplotlib")
plt = getpack("matplotlib.pyplot")
np = getpack("numpy")
datetime = getpack("datetime")
sns = getpack("seaborn")
subprocess.call([sys.executable, "-m", "pip", "install", "pandas-datareader"], stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL)
from pandas_datareader import data


# prepare dataframe for results
results_df = pd.DataFrame(columns=["Date", "Ticker", "Confidence Level", "Timeframe (days)", "Sample Years",
                                   "Historical VaR", "Expected Shortfall (historical)", "Var-Covar VaR",
                                   "Expected Shortfall (Var-Covar)"])


def main():
    end = ""

    # execute this loop until user decides to quit
    while "q" not in end:

        # user input for necessary information
        ticker = input("Type in a valid ticker for the VaR calculation and hit enter: ")
        years = int(input("How many years do you want to consider for the return sample (e.g. 5): "))
        days = int(input("Select the number of days you want to calculate the VaR for (Trading days): "))

        # set start and end date for the last five years
        now = datetime.datetime.now()

        # start and end date
        start_date = now.replace(year=now.year - years).strftime("%Y-%m-%d")
        end_date = now.strftime("%Y-%m-%d")

        # request data
        closing_prices = data.DataReader(ticker, 'yahoo', start_date, end_date)['Close']

        # daily returns
        returns = closing_prices.pct_change()
        # deleted missing values
        returns.dropna(inplace=True)

        # confidence level for calculation
        confidences = []

        loop = True
        # read in confidence intervals
        while loop:
            ele = float(input("Select the confidence level you want to use (format: XX.X): "))
            confidences.append(ele)  # adding the element
            loop = bool(input("Would you like do add another confidence level (y)? If not hit Enter."))

        # for each confidence interval calculate VaR
        for confidence in confidences:

            # make sure no queries are run twice
            if not results_df.loc[(results_df['Date'] == end_date) & (results_df['Ticker'] == ticker) &
                                  (results_df['Confidence Level'] == str(confidence) + "%") &
                                  (results_df['Timeframe (days)'] == days) & (results_df["Sample Years"] == years)].empty:
                print("The following query has already been run and will be skipped")
                print(results_df.loc[(results_df['Date'] == end_date) & (results_df['Ticker'] == ticker) &
                                     (results_df['Confidence Level'] == str(confidence) + "%") &
                                     (results_df['Timeframe (days)'] == days) & (results_df["Sample Years"] == years)])
                continue

            # Historical method
            VaR_hist = var_hist(returns, confidence, days)
            ES_hist = cvar_hist(returns, VaR_hist, days)

            # Variance-covariance method
            VaR_var_covar = var_vcov(returns, confidence, days)
            ES_var_covar = cvar_vcov(returns, confidence, days)

            results_df.loc[len(results_df)] = [end_date, ticker, str(confidence) + "%", days, years, VaR_hist, ES_hist,
                                               VaR_var_covar, ES_var_covar]

        # plot the results of the calculations
        for confidence in confidences:

            fig = plt.figure()
            ax = plt.subplot(111)

            plt.title(f"Value at risk for {ticker} ({days} days)")

            # Density Plot and Histogram of all arrival delays
            sns.distplot(returns*np.sqrt(days), hist=True, kde=True,
                         bins=36, color='#145374',
                         hist_kws={'edgecolor': 'black'},
                         kde_kws={'linewidth': 3})

            # plot VaR
            ax.axvline(x=- results_df.loc[(results_df['Date'] == end_date) & (results_df['Ticker'] == ticker) &
                                          (results_df['Confidence Level'] == str(confidence)+"%") &
                                          (results_df["Sample Years"] == years), ["Historical VaR"]].values, color='#af0404',
                       linestyle='-', label=str(round(100-confidence, 2))+"% VaR historical method", linewidth=2)

            ax.axvline(x=- results_df.loc[(results_df['Date'] == end_date) & (results_df['Ticker'] == ticker) &
                                          (results_df['Confidence Level'] == str(confidence)+"%") &
                                          (results_df["Sample Years"] == years), ["Var-Covar VaR"] ].values, color='#f1bc31',
                       linestyle='-', label=str(round(100-confidence, 2))+"% VaR variance-covariance method", linewidth=2)

            # plot CVaR
            ax.axvline(x=- results_df.loc[(results_df['Date'] == end_date) & (results_df['Ticker'] == ticker) &
                                          (results_df['Confidence Level'] == str(confidence)+"%") &
                                          (results_df["Sample Years"] == years), ["Expected Shortfall (historical)"]].values, color='black',
                       linestyle='-', label=str(round(100-confidence, 2))+"% ES (historical)", linewidth=2, alpha=0.5)

            ax.axvline(x=- results_df.loc[(results_df['Date'] == end_date) & (results_df['Ticker'] == ticker) &
                                          (results_df['Confidence Level'] == str(confidence)+"%") &
                                          (results_df["Sample Years"] == years), ["Expected Shortfall (Var-Covar)"]].values, color='grey',
                       linestyle='-', label=str(round(100-confidence, 2))+"% ES (Var-Covar)", linewidth=2, alpha=0.5)

            plt.xlabel('Return')
            plt.ylabel('Frequency')
            plt.margins(0)

            # layout editing for legend and annotations
            box = ax.get_position()
            ax.set_position([box.x0, box.y0,
                             box.width, box.height])

            # Put a legend below current axis
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1),
                      fancybox=True, shadow=True, ncol=2)

            mean = returns.mean()
            std_dev = returns.std()
            # add sigma, mu and n in legend
            ax.annotate(u"\u03bc"+" = "+str(round(mean, 3))+"\n"+u"\u03C3"+" = "+str(round(std_dev, 3))+"\n"+"n = " +
                        str(len(returns)), xy=(.85, .99), xycoords='axes fraction', horizontalalignment='left',
                        verticalalignment='top')

            plt.show()

        print("\n")
        # print the result dataframe
        print(results_df)

        # allow the user to run more simulations
        end += (input("If you want to run another Simulation hit enter, else type q: "))

    # data export option
    if input("If you want to export the VaR data press any key and hit enter, else just press enter: "):
        results_df.to_csv(f"./VaR_Sim_{now.strftime('%m-%d-%Y-%m-%H')}")
        print("Data exported.\n")

    print("Thank you.\nGoodbye.")


if __name__ == "__main__":
    main()
