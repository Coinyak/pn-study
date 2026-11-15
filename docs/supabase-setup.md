# 별표·풀이 기록 기기 연동

별표, O/X, 풀이 기록은 브라우저에 먼저 저장되고, 로그인 없이 같은 `study_progress` 행으로 다른 기기와 맞춰집니다.

`content/supabase.json`은 git에 넣지 않습니다. anon 키만 넣고, service_role 키는 넣지 않습니다.

```bash
cp content/supabase.example.json content/supabase.json
```

표:

```sql
create table if not exists public.study_progress (
  user_id uuid primary key,
  payload jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);
alter table public.study_progress enable row level security;
grant select, insert, update on table public.study_progress to anon;
create policy "read shared progress" on public.study_progress
  for select to anon, authenticated
  using (user_id = '00000000-0000-4000-8000-000000000001'::uuid);
create policy "insert shared progress" on public.study_progress
  for insert to anon, authenticated
  with check (user_id = '00000000-0000-4000-8000-000000000001'::uuid);
create policy "update shared progress" on public.study_progress
  for update to anon, authenticated
  using (user_id = '00000000-0000-4000-8000-000000000001'::uuid)
  with check (user_id = '00000000-0000-4000-8000-000000000001'::uuid);
```

그 행 하나만 쓰고, 로그인은 쓰지 않습니다.

```bash
python3 scripts/build.py
```
