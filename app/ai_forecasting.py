import pandas as pd
import datetime
from sklearn.linear_model import LinearRegression

def generate_forecast(df, date_col, metric_col, forecast_periods=7, freq='D'):
    """
    A domain-agnostic forecasting engine using Linear Regression.
    """
    # 1. Sort data chronologically just to be safe
    df = df.sort_values(by=date_col)

    # 2. Initialize the Machine Learning model
    model = LinearRegression()

    # 3. Math doesn't understand "March 20th", so we convert dates to numbers (ordinals)
    df['date_ordinal'] = pd.to_datetime(df[date_col]).map(datetime.datetime.toordinal)

    X = df[['date_ordinal']]  # The independent variable (Time)
    y = df[metric_col]        # The dependent variable (Revenue/Volume)

    # 4. Train the AI model on the historical data
    model.fit(X, y)

    # 5. Generate future dates based on the user's selected grouping
    last_date = df[date_col].max()
    
    if freq == 'D':
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=forecast_periods, freq='D')
    elif freq == 'W':
        future_dates = pd.date_range(start=last_date + pd.Timedelta(weeks=1), periods=forecast_periods, freq='W-MON')
    else: # Month
        future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=forecast_periods, freq='ME')

    # 6. Prepare the future dataframe
    future_df = pd.DataFrame({date_col: future_dates})
    future_df['date_ordinal'] = future_df[date_col].map(datetime.datetime.toordinal)

    # 7. PREDICT THE FUTURE!
    future_df['predicted_value'] = model.predict(future_df[['date_ordinal']])

    # 8. Clean up (Business Logic: Revenue cannot be negative)
    future_df['predicted_value'] = future_df['predicted_value'].apply(lambda x: max(0, x))
    
    # Tag these rows so the dashboard knows they are fake future numbers
    future_df['is_forecast'] = True
    future_df['Type'] = 'Forecast (AI)'
    
    # Format the historical data to match
    df['predicted_value'] = df[metric_col]
    df['is_forecast'] = False
    df['Type'] = 'Historical Data'

    # Combine the past and the future into one single timeline
    combined_df = pd.concat([df[[date_col, 'predicted_value', 'is_forecast', 'Type']], 
                             future_df[[date_col, 'predicted_value', 'is_forecast', 'Type']]], 
                             ignore_index=True)

    return combined_df