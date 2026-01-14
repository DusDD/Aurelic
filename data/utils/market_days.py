from datetime import datetime, timedelta
import pandas_market_calendars as mcal

def get_last_trading_days(n=30):
    nyse = mcal.get_calendar("NYSE")
    today = datetime.utcnow().date()

    schedule = nyse.schedule(
        start_date=today - timedelta(days=n*3),
        end_date=today
    )

    return [d.date() for d in schedule.index[-n:]]
