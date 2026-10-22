create table test_entries (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  note text not null
);

-- No policies: the public (anon) key can't read or write. The app uses the secret key server-side.
alter table test_entries enable row level security;
