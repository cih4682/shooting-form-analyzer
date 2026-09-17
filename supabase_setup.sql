-- ============================================================
-- Shooting Motion Analysis — Supabase 초기 설정
-- 실행: Supabase 대시보드 → SQL Editor → 붙여넣고 Run
-- ============================================================

-- 1. 승인된 사용자 -------------------------------------------
create table if not exists public.approved_users (
    email      text primary key,          -- upsert 때문에 PK 필수
    role       text not null default 'user',   -- user | admin | superadmin
    created_at timestamptz not null default now()
);

-- 2. 승인 대기 사용자 ----------------------------------------
create table if not exists public.pending_users (
    email      text primary key,
    created_at timestamptz not null default now()
);

-- 3. 앱 설정 (수업 모드 등) -----------------------------------
create table if not exists public.app_settings (
    key        text primary key,
    value      text not null,
    updated_at timestamptz not null default now()
);

-- 수업 모드 행이 없으면 토글이 아무것도 안 하므로 미리 넣어둔다
insert into public.app_settings (key, value)
values ('class_mode', 'off')
on conflict (key) do nothing;

-- 4. RLS 전면 차단 --------------------------------------------
-- 정책을 하나도 만들지 않는다 = anon 키로는 아무것도 못 읽고 못 쓴다.
-- 앱은 secret 키(sb_secret_...)로 접속하므로 RLS를 우회한다(서버에만 보관).
-- 위치: Settings > API Keys > Publishable and secret API keys 탭
alter table public.approved_users enable row level security;
alter table public.pending_users  enable row level security;
alter table public.app_settings   enable row level security;

-- 5. 첫 관리자 등록 -------------------------------------------
-- 아래 이메일을 본인 것으로 바꾸고 실행하세요.
-- (Auth에서 회원가입도 따로 해야 로그인이 됩니다)
insert into public.approved_users (email, role)
values ('publicsky7@gmail.com', 'superadmin')
on conflict (email) do update set role = 'superadmin';
