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

-- RAG (document Q&A): one row per uploaded document, plus its chunks
-- with embeddings. Owner: Rabia (storage) / Ghanwa (rag/ ingestion +
-- retrieval logic that reads/writes these tables via db/documents.py
-- and rag/vector_store.py).
create table if not exists documents (
    -- text, not uuid: rag_service.py generates real UUID strings in
    -- production, but Ghanwa's test suite (tests/test_rag_core.py) uses
    -- plain ids like "doc-a" for readability, matching her original
    -- SQLite TEXT column -- keep that contract intact.
    document_id text primary key,
    user_id uuid not null references auth.users(id) on delete cascade,
    filename text not null,
    mime_type text not null,
    uploaded_at timestamptz not null default now(),
    chunk_count integer not null
);

create index if not exists documents_user_id_idx on documents (user_id);

alter table documents enable row level security;

create policy "Users can view their own documents"
    on documents for select
    using (auth.uid() = user_id);

create policy "Users can insert their own documents"
    on documents for insert
    with check (auth.uid() = user_id);

create policy "Users can delete their own documents"
    on documents for delete
    using (auth.uid() = user_id);

-- embedding is a jsonb array of floats (Gemini embedding vector).
-- Similarity search is done in Python (see rag/vector_store.py), not in
-- SQL, so no pgvector extension is required.
create table if not exists chunks (
    id bigint generated always as identity primary key,
    document_id text not null references documents(document_id) on delete cascade,
    user_id uuid not null references auth.users(id) on delete cascade,
    filename text not null,
    chunk_index integer not null,
    page integer,
    text text not null,
    embedding jsonb not null,
    unique (document_id, chunk_index)
);

create index if not exists chunks_user_document_idx on chunks (user_id, document_id);

alter table chunks enable row level security;

create policy "Users can view their own chunks"
    on chunks for select
    using (auth.uid() = user_id);

create policy "Users can insert their own chunks"
    on chunks for insert
    with check (auth.uid() = user_id);

create policy "Users can delete their own chunks"
    on chunks for delete
    using (auth.uid() = user_id);
