import threading
import itertools
import time
import sys


#this will later be used to add a loading ... to some text
done=False
def dotdotdot(text):
    for c in itertools.cycle(['.', '..', '...','']):
        if done:
            break
        sys.stdout.write('\r'+text+c)
        sys.stdout.flush()
        time.sleep(0.3)
    sys.stdout.write('\nDone!')


# prepare a loading message
t = threading.Thread(target=dotdotdot, args=("Loading required modules",))

# starting loading... thread
t.start()

#needed for the next function
import subprocess
import importlib

# function that imports a library if it is installed, else installs it and then imports it
def getpack(package):
    try:
        return (importlib.import_module(package))
        # import package
    except ImportError:
        subprocess.call([sys.executable, "-m", "pip", "install", package],
  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return (importlib.import_module(package))
        # import package

#install/import other necessary modules
pd = getpack("pandas")
matplotlib = getpack("matplotlib")
plt = getpack("matplotlib.pyplot")
np=getpack("numpy")
datetime=getpack("datetime")
sns=getpack("seaborn")
scipy=getpack("scipy")
from scipy.stats import norm


subprocess.call([sys.executable, "-m", "pip", "install", "pandas-datareader"],
  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
from pandas_datareader import data


done=True
time.sleep(0.3)
print("\n")
end=""


results_df = pd.DataFrame(columns=["Date","Ticker","Confidence Level","Timeframe (days)","Sample Years","Historical VaR","Expected Shortfall (historical)","Var-Covar VaR","Expected Shortfall (Var-Covar)"])

while not "q" in end:

    Ticker=input("Type in a valid ticker for the VaR calculation and hit enter: ")
    years=int(input("How many years do you want to consider for the return sample (e.g. 5): "))
    days = int(input("Select the number of days you want to calculate the VaR for (Trading days): "))

    #set start and end date for the last five years
    now = datetime.datetime.now()

    start_date = now.replace(year = now.year - years).strftime("%Y-%m-%d")
    end_date = now.strftime("%Y-%m-%d")


    # request data
    closing_prices = data.DataReader(Ticker, 'yahoo', start_date, end_date)['Close']

    #current price
    current_price = closing_prices[-1]

    #daily returns
    returns = closing_prices.pct_change()
    #deleted missing values
    returns.dropna(inplace=True)

    std_dev=returns.std()
    mean=returns.mean()

    #confidence level for calculation
    confidences=[]

    loop=True
    # iterating till the range
    while loop:
        ele = float(input("Select the confidence level you want to use (format: XX.X): "))
        confidences.append(ele)  # adding the element
        loop=bool(input("Would you like do add another confidence level (y)? If not hit Enter."))



    for confidence in confidences:

        #make sure no queries are run twice
        if not results_df.loc[(results_df['Date'] == end_date) & (results_df['Ticker'] == Ticker) & (results_df['Confidence Level'] == str(confidence) + "%") & (results_df['Timeframe (days)'] == days) &(results_df["Sample Years"] == years)].empty:
            print("The following query has already been run and will be skipped")
            print(results_df.loc[(results_df['Date'] == end_date) & (results_df['Ticker'] == Ticker) & (results_df['Confidence Level'] == str(confidence) + "%")& (results_df['Timeframe (days)'] == days) & (results_df["Sample Years"] == years)])
            continue

        alpha=(1-(confidence/100))

        #Historical method
        VaR_hist=-np.quantile(returns,alpha)

        #Expected Shortfall
        ES_hist=-returns[returns<-VaR_hist].mean()

        VaR_hist*=np.sqrt(days)
        ES_hist*=np.sqrt(days)

        #Variance-covariance method
        VaR_var_covar=norm.ppf(1-alpha)*std_dev-mean
        ES_var_covar =alpha**-1 * norm.pdf(norm.ppf(alpha))*std_dev-mean


        VaR_var_covar*=np.sqrt(days)
        ES_var_covar*=np.sqrt(days)



        results_df.loc[len(results_df)]=[end_date, Ticker, str(confidence) + "%",days,years,VaR_hist,ES_hist,VaR_var_covar,ES_var_covar]


    for confidence in confidences:

        fig = plt.figure()
        ax = plt.subplot(111)

        plt.title('Value at risk for ' + str(Ticker))

        # Density Plot and Histogram of all arrival delays
        sns.distplot(returns*np.sqrt(days), hist=True, kde=True,
                     bins=36, color='#145374',
                     hist_kws={'edgecolor': 'black'},
                     kde_kws={'linewidth': 3})

        ax.axvline(x=- results_df.loc[(results_df['Date'] == end_date) & (results_df['Ticker'] == Ticker) & (results_df['Confidence Level'] == str(confidence)+"%") & (results_df["Sample Years"] == years),["Historical VaR"]].values, color='#af0404', linestyle='-', label=str(round(100-confidence,2))+"% VaR historical method", linewidth=2)
        ax.axvline(x=- results_df.loc[(results_df['Date'] == end_date) & (results_df['Ticker'] == Ticker) & (results_df['Confidence Level']== str(confidence)+"%")& (results_df["Sample Years"] == years),["Var-Covar VaR"] ].values, color='#f1bc31', linestyle='-', label=str(round(100-confidence,2))+"% VaR variance-covariance method",
                   linewidth=2)
        plt.xlabel('Return')
        plt.ylabel('Frequency')
        plt.margins(0)

        # Shrink current axis's height by 10% on the bottom
        box = ax.get_position()
        ax.set_position([box.x0, box.y0,
                         box.width, box.height])

        # Put a legend below current axis
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
                  fancybox=True, shadow=True, ncol=2)

        # fig1=plt.gcf()
        ax.annotate(u"\u03bc"+" = "+str(round(mean,3))+"\n"+u"\u03C3"+" = "+str(round(std_dev,3))+"\n"+"n = "+str(len(returns)),
                    xy=(.85, .99),
                    xycoords='axes fraction',
                    horizontalalignment='left',
                    verticalalignment='top')

        plt.show()

    print("\n")
    print(results_df)


    end+=(input("If you want to run another Simulation hit enter, else type q: "))

if input("If you want to export the VaR data press any key and hit enter, else just press enter: "):
    results_df.to_csv("./VaR_Sim_"+now.strftime("%m-%d-%Y-%m-%H"))
    print("Data exported.\n")


print("Thank you.\nGoodbye.")