-- One row per night (#3). answers is a list of {"question": ..., "answer": ...}.
create table entries (
  id bigint generated always as identity primary key,
  entry_date date not null unique,
  answers jsonb not null,
  tags text[] not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- No policies: the public (anon) key can't read or write. The app uses the secret key server-side.
alter table entries enable row level security;
