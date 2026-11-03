-- #7 Oura connection: one row holding the OAuth tokens for Ava's Oura account.
-- Tokens are secrets: never select them into logs or screenshots.
create table if not exists oura_connection (
    id smallint primary key default 1 check (id = 1),
    access_token text not null,
    refresh_token text not null,
    expires_at timestamptz not null,
    scope text not null,
    connected_at timestamptz not null default now()
);

-- RLS on with no policies: only the app's secret key can read or write.
alter table oura_connection enable row level security;
