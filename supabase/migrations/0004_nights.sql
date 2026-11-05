-- #8 Oura nights: one row per night, keyed on Oura's `day` (the date the night's sleep ended).
-- Any value can be null: Oura may have a sleep score but no readiness, or no main sleep for HRV.
-- Missing stays null, never zero.
create table if not exists nights (
    night_date date primary key,
    sleep_score int,
    readiness int,
    avg_hrv numeric,
    fetched_at timestamptz not null default now()
);

-- RLS on with no policies: only the app's secret key can read or write.
alter table nights enable row level security;
