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

-- Face-recognition login: one row per user, storing their face encoding
-- (a 128-number vector from the face_recognition library) as JSON.
create table if not exists face_encodings (
    user_id uuid primary key references auth.users(id) on delete cascade,
    encoding jsonb not null,
    created_at timestamptz not null default now()
);

alter table face_encodings enable row level security;

-- Registration (register_face) runs as the signed-in user, so normal
-- per-user RLS applies here.
create policy "Users can view their own face encoding"
    on face_encodings for select
    using (auth.uid() = user_id);

create policy "Users can insert their own face encoding"
    on face_encodings for insert
    with check (auth.uid() = user_id);

create policy "Users can update their own face encoding"
    on face_encodings for update
    using (auth.uid() = user_id);

-- Login (verify_face) has to check a photo against EVERY user's
-- encoding before it knows who's logging in, which these per-user
-- policies intentionally don't allow — that step uses the service_role
-- key instead, which bypasses RLS by design. See db/face_auth.py.
