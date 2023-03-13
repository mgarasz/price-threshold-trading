import pandas as pd
import pandas_datareader.data as pdr
import yfinance as yf
import time
from datetime import datetime

class Datahandler:
    
    def __init__(self):
        
        self.asset_class = None #crypto or traditional
        self.symbol = None
        self.date_start = None #datetime object
        self.date_end = None
        self.interval = None
        
        
    def period_to_seconds(self):
        
        if 'd' in self.interval:
            multiplier = 86400
        elif 'm' in self.interval:
            multiplier = 60
        elif 'h' in self.interval:
            multiplier = 3600
        else:
            raise ValueError("Not a valid period")            

        return int(self.interval[:-1]) * multiplier
        
    def get_unix_timestamp(self):
        
        return (time.mktime(self.date_start.timetuple()),
                time.mktime(self.date_end.timetuple()))
        
    
    def fetch_data(self):
        
        if self.asset_class == 'cypto': #switch data source instead of asset type
            
            unix_start, unix_end = self.get_unix_timestamp()
            period_seconds = self.period_to_seconds()
                        
            # too granular. Periods are in seconds: Valid values are 300, 900, 1800, 7200, 14400, and 86400
            weburl = f'https://poloniex.com/public?command=returnChartData&currencyPair={self.symbol}&start={unix_start}&end={unix_end}&period={period_seconds}&resolution=auto' 
            price_data = pd.read_json(weburl)
            price_data.set_index('date', inplace=True)[['open', 'high', 'low', 'close', 'volumne']]
                        
        elif self.asset_class == 'traditional':
        
            yf.pdr_override()
            price_data = pdr.get_data_yahoo(self.symbol, self.start, self.end, interval=self.interval)
            price_data.columns = list(price_data.columns.str.lower())
            price_data = price_data[['open', 'high', 'low', 'close', 'volumne']]
            
        return price_data

                        
                        
                    
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            