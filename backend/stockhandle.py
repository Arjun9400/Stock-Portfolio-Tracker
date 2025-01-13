import pandas as pd
import yfinance as yf
import os
import glob
import time as t
from datetime import datetime
from dateutil.relativedelta import relativedelta
import locale


    
def colgen(pos):
    if pos < 222:
        return 222,pos
    if pos > 221 and pos <444:
        pos2 = pos-222
        return 222-pos2,222
        
def colinter(x, x_min, x_max):
    y_min = 0
    y_max = 443
    """Linear interpolation function."""
    if x > x_max:
        x = x_max
    if x < x_min:
        x = x_min 
    inter = int(y_min + (y_max - y_min) * ((x - x_min) / (x_max - x_min)))
    return colgen(inter)


    


def vsround(value):
    try:
        value = round(value)
        return value
    except:
        return value

def ssround(value):
    try:
        if value < 10:
            return round(value,2)
        elif value >10 and value <100:
            return round(value,2)
        elif value >100 and value <1000:
            return round (value,1)
        else:
            return round(value)
    except:
        return 
        
def sround(value):  # smart round
    try:
        if value >= 100:
            return locale.format_string("%d", round(value), grouping=True)
        if 100 > value >= 10:
            return (locale.format_string("%.2f", round(value, 1), grouping=True))
        if value < 10:
            return (locale.format_string("%.2f", round(value, 2), grouping=True))
    except:
        return value
        
def commafy(value):
    # Set the locale to Indian English
    #locale.setlocale(locale.LC_NUMERIC, 'en_IN')
    
    # Format the number with commas based on Indian system
    try:
        value = locale.format_string("%d", value, grouping=True)
    except:
        return value
    
    return value
        

def merge_csv(df1, df2):
    df2 = df2.reset_index()
    df2 = pd.concat([df1,df2]).reset_index(drop=True)
    
    #df2 = pd.concat([df1,df2]).drop_duplicates().reset_index(drop=True)
    #df2 = df2.drop_duplicates()
    return df2

def update_csv(period): #"5d"
    # Define the path to the folder containing CSV files
    folder_path = 'stock history'

    # Use glob to find all CSV files in the folder
    csv_files = glob.glob(os.path.join(folder_path, '*.csv'))

    # Iterate through the CSV files and print their filenames
    for csv_file in csv_files:
        filename = os.path.basename(csv_file)[:-4]
        ticker = yf.Ticker(f"{filename}")
        new_df = ticker.history(period=f"{period}")
        #print(filename)
        old_df = pd.read_csv(f'stock history\{filename}.csv')
        updated_df = merge_csv(old_df, new_df)
        updated_df = updated_df.astype('str')
        updated_df = updated_df.drop_duplicates(subset=['Date'])
        updated_df.to_csv(f'stock history\{filename}.csv', index=False)
        print(filename)

        
def get_lastprice(stock_name,rowint):
    try:
        df = pd.read_csv(f'stock history\{stock_name}.csv')
    except:
        return None
        
    try:
        last_price = df['Close'].iloc[rowint]
    except:
        print('Could not get current price')
        return None
    return ssround(last_price)

def get_date(rowint):
    try:
        df = pd.read_csv(f'stock history\TCS.NS.csv')
    except:
        return None
        
    try:
        date = df['Date'].iloc[rowint]
    except:
        print('Could not get date')
        return None
    return date

def get_date_price(stock_name,date):
    try:
        df = pd.read_csv(f'stock history\{stock_name}.csv')
    except:
        return None
    try:
        date_price = df.loc[df['Date'] == date, 'Close'].values
    except:
        print('Could not get date')
        return None
    return date_price
    


def get_currentprice(stock_name):
    try:
        current_price = yf.Ticker(stock_name).info['currentPrice']
        #print(stock_name)
    except:
        #print(f'could not get current price of  {stock_name}')
        return None
    return ssround(current_price)


    


'''datacsv.iloc[1:,5] = datacsv.iloc[1:,1].apply(lambda x:get_currentprice(x))
datacsv['Total amount'] = datacsv['Qty'] * datacsv['Current Price']
total_holdings = datacsv['Total amount'].sum()
datacsv.to_csv('main holdings.csv',index=False)'''




def get_percent(stock_name,current_price,yearval,monthval,weekval,dayval):
    daysdif = []
    # Read the CSV file into a pandas DataFrame
    try:
        df = pd.read_csv(f'stock history\{stock_name}.csv')
    except:
        print(f'Could not find {stock_name}.csv')
        return None
    df['Date'] = df['Date'].str[:-6]
    # Convert 'Date' column to datetime type
    df['Date'] = pd.to_datetime(df['Date'])

    # Calculate the date one year ago from the latest date in the dataset
    now = datetime.now().replace(microsecond=0)
    
    one_year_ago = now - relativedelta(years=yearval,months=monthval,weeks=weekval,days=dayval)
    # Find the closest date available in the dataset to one year ago
    for a in range(0,len(df['Date'])):
            adate = df['Date'][a] - one_year_ago
            daysdif.append([abs(adate),a])
    #return min([val[0] for val in daysdif])
    #return min(daysdif),df['Open'][min(daysdif)[1]]
    priceyearago = df['Close'][min(daysdif)[1]]
    #current_price = df['Open'].iloc[-1]
    '''try:
        current_price = yf.Ticker(stock_name).info['currentPrice']
    except:
        print(f'could not get current price of  {stock_name}')'''
    try:
        dif = current_price - priceyearago
    except:
        return None
        
    if priceyearago ==0:
        return None
    percent = dif/priceyearago
    percent = percent*100
    #print(stock_name)
    return ssround(percent)
    
def calculate_total_holdings(introw):
    # Read existing holdings data
    holding_df = pd.read_csv('holdings.csv')
    
    # Load the main stock holdings data
    main_df = pd.read_csv('main.csv')
    
    # Create a list to store the results
    results = []
    
    # Loop through the past `introw` rows (from `introw` down to 1)
    for i in range(introw, 0, -1):  # Fixed the range to go backwards
        # Get the date for the current day
        date = get_date(i)
        
        # Skip this iteration if no valid date is found
        if date is None:
            continue
        
        # Initialize total amount for the current day
        total_amt = 0
        
        # Calculate the total amount for the current day
        for _, row in main_df.iterrows():
            stock_id = row['Stock ID']
            qty = row['Qty']
            
            # Skip if quantity is missing or NaN
            if pd.isna(qty):
                continue
            
            # Fetch the price for the stock on the given date
            try:
                price = get_date_price(stock_id, date).item()
            except Exception as e:
                print(f"Error retrieving price for {stock_id} on {date}: {e}")
                continue  # Skip if price retrieval fails
            
            # Skip if price is missing or NaN
            if pd.isna(price):
                continue
            
            # Add to the total amount
            total_amt += qty * price
        
        # Append the result to the list with the current date and total amount
        total_amt = int(total_amt)  # Ensure the total amount is an integer
        results.append({'Date': date, 'Total Amt': total_amt})
    
    # Create a DataFrame from the results
    results_df = pd.DataFrame(results)
    
    # Concatenate with existing holdings data, reset the index, and remove duplicates
    results_df = pd.concat([holding_df, results_df]).reset_index(drop=True)
    results_df = results_df.astype('str')
    results_df = results_df.drop_duplicates(subset=['Date'])
    
    # Write the updated DataFrame to holdings.csv
    results_df.to_csv('holdings.csv', index=False)

    
    


        
