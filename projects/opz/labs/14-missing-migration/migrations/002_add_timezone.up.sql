-- v2 shows each user's local time, so users need a timezone.
ALTER TABLE users ADD COLUMN timezone text NOT NULL;
