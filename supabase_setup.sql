-- Table clips
create table if not exists clips (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  filename text not null,
  tags text[] default '{}',
  created_at timestamp with time zone default now()
);

-- Table sounds
create table if not exists sounds (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  filename text not null,
  type text not null check (type in ('intro', 'whoosh')),
  created_at timestamp with time zone default now()
);
