# 별표·풀이 기록 기기 연동

별표, O/X, 풀이 기록은 브라우저에 먼저 저장되고, 같은 이메일로 로그인하면 Supabase `study_progress` 표와 맞춰집니다.

`content/supabase.json`은 git에 넣지 않습니다. anon 키만 넣고, service_role 키는 넣지 않습니다.

```bash
cp content/supabase.example.json content/supabase.json
```

표:

```sql
create table if not exists public.study_progress (
  user_id uuid primary key references auth.users (id) on delete cascade,
  payload jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);
alter table public.study_progress enable row level security;
create policy "read own progress" on public.study_progress
  for select using (auth.uid() = user_id);
create policy "insert own progress" on public.study_progress
  for insert with check (auth.uid() = user_id);
create policy "update own progress" on public.study_progress
  for update using (auth.uid() = user_id) with check (auth.uid() = user_id);
```

Auth의 Site URL과 Redirect에 `https://coinyak.github.io/pn-study/PN_study_split.html`을 넣습니다.

```bash
python3 scripts/build.py
```
