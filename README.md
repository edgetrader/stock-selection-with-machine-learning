# Stock Selection using Machine Learning Techniques

## Summary
Purpose of this analysis is to predict 1-month stock returns of securities in CSI 300. Based on predicted returns performance, each stock will be assigned to different performance categories. Stocks with good performance will be picked and invested at the end of the month.

This process will repeat every month and the strategy will be backtested to determine with whether the prediction model is good enough for consistent outperformance over the index/benchmark.

## Platform and Data
The analysis is entirely done on [JoinQuant](www.joinquant.com) research platform.  All data like index securities, factors and prices are downloaded on using JQData api on the platform.  Documentation are in Chinese.

## Notebook
1. https://github.com/edgetrader/stock-selection-with-machine-learning/blob/master/notebook/csi300-stock-selection.ipynb

---
# Trading Strategy

1. **Benchmark**: CSI300   
2. **Stock Universe**: All securities in CSI300  
3. **Trading Frequency**: Every last day business day of the month  
4. **Stock picking strategy**: Select a maximum of 10 securities that are predicted by a machine learning model that have high probability of making at least 10% returns in the following month.  
5. **ML model**: Light GBM - Multiclassification model.  Trained with 45 factors as features and performed multi-classification on returns in the following month.  Multi-classification as the returns are categorised to 5 levels based on their performance.  'A' being securities having at least 10% returns for example.  
6. **Other considerations**:   
  - Securities with incomplete or missing factor data are excluded from the selection process.  
  - All securities are sold before new ones are purchased.  This process can be improved to minimise selling and buying of the same security on the same day.
  - All selected securities are transacted with equal weights based on portfolio size at the point in time.  Weights of each security can be improved and efficiently determined based on modern portfolio theory and efficient frontier.

