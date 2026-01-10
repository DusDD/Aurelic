def run_daily_update():
    from data.jobs.daily_pull import main
    main()


def run_backfill():
    from data.jobs.backfill import polygon_backfill
    polygon_backfill(days=30)
