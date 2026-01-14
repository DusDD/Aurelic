def run_daily_update():
    from data.jobs.daily_prices import main
    main()


def run_backfill():
    from data.jobs.backfill_prices import polygon_backfill
    polygon_backfill(days=30)
