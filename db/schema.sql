-- Run this in the Supabase SQL editor to set up tables.
-- Owner: Rabia — adjust columns as the app's needs grow.

create table if not exists messages (
    id bigint generated always as identity primary key,
    user_id uuid not null references auth.users(id) on delete cascade,
    role text not null check (role in ('user', 'assistant')),
    content text not null,
    created_at timestamptz not null default now()
);

create index if not exists messages_user_id_created_at_idx
    on messages (user_id, created_at);

-- Row Level Security: users can only read/write their own messages.
alter table messages enable row level security;

create policy "Users can view their own messages"
    on messages for select
    using (auth.uid() = user_id);

create policy "Users can insert their own messages"
    on messages for insert
    with check (auth.uid() = user_id);
