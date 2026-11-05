-- #12 Tag source: what Claude returned on the last "Suggest tags" for each entry.
-- `tags` stays the final list Ava saved; a tag in `tags` but not here was typed by Ava.
-- Entries saved before this have '{}', so all their tags read as typed.
alter table entries add column if not exists suggested_tags text[] not null default '{}';
