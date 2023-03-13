import matplotlib.pyplot as plt
from matplotlib import gridspec
import numpy as np

class Backtester:
    
    def __init__(self, historical_price_prediction_data, periods, buy_or_hold, threshold):
        
        self.historical_price_prediction_data = historical_price_prediction_data
        self.assumed_hold_time = periods
        self.buy_or_hold = buy_or_hold
        self.price_variable = 'high'
        self.price_threshold = threshold
        self.nominal_stop_loss = 0.
        self.percentage_stop_loss = 0.
        
        self.trade_record = None

    def simulate_trades(self):
        
        trade_record = self.historical_price_prediction_data[['open',
                                                             'high',
                                                             'low',
                                                             'close',
                                                             'volume',
                                                             'y_pred',
                                                             'y_test']]
        
        trade_record.loc[:, 'price_yesterday'] = trade_record[self.price_variable].shift(self.assumed_hold_time)
        trade_record.loc[:, 'decision_yesterday'] = trade_record['y_pred'].shift(self.assumed_hold_time)
            
        trade_record.loc[:, 'net_gain'] = trade_record['decision_yesterday']* \
            (trade_record['price_yesterday'] - trade_record[self.price_variable])
            
        self.trade_record = trade_record
        
        
    def simulate_trades_corrected(self):
        
        trade_record = self.historical_price_prediction_data[['open',
                                                             'high',
                                                             'low',
                                                             'close',
                                                             'volume',
                                                             'y_pred',
                                                             'y_test']].copy()
        
        trade_record.loc[:, 'price_today'] = trade_record[self.price_variable]
        trade_record.loc[:, 'price_next_period'] = trade_record[self.price_variable].shift(-self.assumed_hold_time)
        trade_record.loc[:, 'eod_price_next_period'] = trade_record['close'].shift(-self.assumed_hold_time)
        
        #clip our gains 
        trade_record.loc[:, 'predicted_price'] = trade_record['price_today']*self.price_threshold
        trade_record.loc[:, 'actual_price_change'] = trade_record['price_next_period'] - trade_record['price_today']
        trade_record.loc[:, 'predicted_price_change'] = trade_record['predicted_price'] - trade_record['price_today']
      
        trade_record.loc[:, 'net_gain'] = trade_record[['actual_price_change', 'predicted_price_change']].min(axis=1)
        
        #if take profit is never hit... close
        trade_record.loc[:, 'net_gain'] = np.where((trade_record['y_test'] - trade_record['y_pred'] == -1),
                trade_record['eod_price_next_period'] - trade_record['price_today'],
                trade_record['net_gain']
                )
                
        
        trade_record.loc[:, 'net_gain'] = np.where(trade_record['y_pred'] == 1, trade_record['net_gain'], 0)
        
        if self.nominal_stop_loss > 0 and self.percentage_stop_loss > 0:
            raise ValueError('You cannot have both a nominal and a percentage stop loss')

        elif self.nominal_stop_loss > 0:
            #trade_record.loc[:, 'net_gain'] = trade_record['net_gain'].clip(-self.nominal_stop_loss)
            trade_record.loc[:, 'lowest_price_next_period'] = trade_record['low'].shift(-self.assumed_hold_time)
            trade_record.loc[:, 'net_gain'] = np.where(trade_record['lowest_price_next_period'] - trade_record['price_today'] <= -self.nominal_stop_loss,
                -self.nominal_stop_loss,
                trade_record['net_gain'])
            trade_record.loc[:, 'net_gain'] = np.where(trade_record['y_pred'] == 1, trade_record['net_gain'], 0)

                
        elif self.percentage_stop_loss > 0:
            trade_record.loc[:, 'lowest_price_next_period'] = trade_record['low'].shift(-self.assumed_hold_time)
            trade_record.loc[:, 'net_gain'] = np.where(trade_record['lowest_price_next_period'] - trade_record['price_today'] <= -(self.percentage_stop_loss * trade_record['price_today']),
                -(self.percentage_stop_loss * trade_record['price_today']),
                trade_record['net_gain'])
            trade_record.loc[:, 'net_gain'] = np.where(trade_record['y_pred'] == 1, trade_record['net_gain'], 0)

        trade_record.loc[:, 'portfolio_value'] = trade_record['net_gain'].cumsum()
            
        self.trade_record = trade_record.copy()
        
        
    def visualize_trades(self):
        
        if self.buy_or_hold == 'buy':
            marker_details = ['^', 'g']
        else:
            marker_details = ['v', 'r']
        
        self.trade_record.loc[:, 'decision_outcome'] = self.trade_record[self.price_variable] * self.trade_record['y_pred']
        self.trade_record.loc[:, 'actual_outcome']= self.trade_record[self.price_variable] * self.trade_record['y_test']
        
        bugfix1 = self.trade_record[self.trade_record['decision_outcome'] > 0].copy()
        bugfix2 = self.trade_record[self.trade_record['actual_outcome'] > 0].copy()
        
        fig = plt.figure()
        gs = gridspec.GridSpec(3, 1, height_ratios=[3, 1, 1])
        ax0 = plt.subplot(gs[0])
        ax1 = plt.subplot(gs[1])
        ax2 = plt.subplot(gs[2])
        
        ax0.plot(self.trade_record[self.price_variable])
        ax0.plot(bugfix1['decision_outcome'], marker_details[0], color=marker_details[1], label='Predicted')
        ax0.plot(bugfix2['actual_outcome'], 'x', color='orange', label='Actual')
        
        ax1.plot(self.trade_record['net_gain'])
        ax2.plot(self.trade_record['portfolio_value'])
       
        #plt.plot(self.trade_record[self.price_variable])
        #plt.plot(bugfix1['decision_outcome'], marker_details[0], color=marker_details[1], label='Predicted')
        #plt.plot(bugfix2['actual_outcome'], 'x', color='orange', label='Actual')
        #plt.legend()  
            
        print('\n=================TRADING HISTORY==================')
        print(f'{self.trade_record.index[0].year}-{self.trade_record.index[0].month}-{self.trade_record.index[0].day} to {self.trade_record.index[-1].year}-{self.trade_record.index[-1].month}-{self.trade_record.index[-1].day}')
    
        print('\nNumber of entries made: ', self.trade_record['y_pred'].sum())    
        print('Number of losing trades: ', self.trade_record[self.trade_record['net_gain'] < 0]['net_gain'].count())    
        print('Expected value per trade: ', self.trade_record[self.trade_record['net_gain'] != 0]['net_gain'].mean())    
        print('Max_drawdown: ', self.trade_record['net_gain'].min())    
        print('Cumulative loss: ', self.trade_record[self.trade_record['net_gain'] < 0]['net_gain'].sum())    
        print('Average loss: ', self.trade_record[self.trade_record['net_gain'] < 0]['net_gain'].mean())    
        print('Average gain: ', self.trade_record[self.trade_record['net_gain'] > 0]['net_gain'].mean())    
        print('\nOverall gain: ', self.trade_record['net_gain'].sum())
        
        
        
        
        