---
status: Draft v1
owner: Ros
created_at: 2026-10-23
spec_ref: docs/features/snapshot-freshness-badge/spec.md
design_ref: docs/features/snapshot-freshness-badge/design.md
---

# Tasks: snapshot-freshness-badge

Усі тести живуть в одному новому файлі `test_freshness.py` (stdlib `unittest`, без нових залежностей),
тому задачі виконуються послідовно — паралельних немає. Порядок: дані → логіка → API → UI → smoke.

- [x] T-001 — Додати запит `brand_freshness(conn)` у `lobby_db.py`
  - AC: §5 happy-4, error-1, invariant-1, invariant-2 (design D1, D2, D3)
  - Files: `lobby_db.py`, `test_freshness.py` (new — клас `BrandFreshnessQueryTest`, in-memory SQLite)
  - DoD: `python -m unittest test_freshness.BrandFreshnessQueryTest` проходить; тести покривають: два GEO → береться найновіший `ok`; новіший `error`/`partial` ігнорується; бренд без `ok` повертається з `last_ok_at = None`; свіжий скан іншого бренду не змінює результат цього.

- [x] T-002 — Додати чисту функцію `freshness_badge(last_ok_at, now)` в `app.py`
  - AC: §5 happy-1, happy-2, happy-3, error-1 (design D4, D7, D8, D9, D11)
  - Files: `app.py`, `test_freshness.py` (клас `FreshnessBadgeTest`)
  - DoD: `python -m unittest test_freshness.FreshnessBadgeTest` проходить; тести: 2h→`2h ago`/fresh, 12h→`12h ago`/stale, 3d→`3d ago`/old, `None`→`no data`/none; межі 5h59m/6h/23h59m/24h; `45m ago` і `0m ago`; майбутній час→`0m ago`/fresh; непарсабельний рядок→`no data`.

- [x] T-003 — Додати `freshness(conn, now)` і маршрут `GET /api/freshness` в `app.py`
  - AC: §5 error-1 («решта плиток нормально»), invariant-2 (design D5, D6, D9)
  - Files: `app.py`, `test_freshness.py` (клас `FreshnessEndpointTest`)
  - DoD: `python -m unittest test_freshness.FreshnessEndpointTest` проходить; тест: відповідь — список `{brand, last_ok_at, label, tier}` для кожного бренду, включно з брендом без `ok`; один бренд із битим `run_at` дає `no data`, інші без змін; відповідь не залежить від query-параметрів geo/brand/search.

- [x] T-004 — Додати контейнер `#freshnessGrid` під `#runProof` та CSS-блок з 4 tier-класами
  - AC: §5 happy-1, happy-2, happy-3, error-1 (стилі fresh / stale / old / none; design D10, D11)
  - Files: `static/index.html`, `static/styles.css`, `test_freshness.py` (клас `FreshnessStaticAssetsTest`)
  - DoD: `python -m unittest test_freshness.FreshnessStaticAssetsTest` проходить: `index.html` містить `id="freshnessGrid"` після `id="runProof"`, `styles.css` містить `.freshness--fresh`, `.freshness--stale`, `.freshness--old`, `.freshness--none`.

- [x] T-005 — Рендер плиток у `static/app.js`: fetch `/api/freshness` на boot, плитка = назва бренду + бейдж
  - AC: §5 happy-1, happy-2, happy-3, happy-4, error-1 (design D10, D11)
  - Files: `static/app.js`, `test_freshness.py` (клас `FreshnessStaticAssetsTest` — додаткова перевірка джерела)
  - DoD: `python -m unittest test_freshness.FreshnessStaticAssetsTest` проходить (`app.js` викликає `/api/freshness` і ставить клас `freshness--<tier>` та `title`); ручна перевірка: `python app.py`, у браузері видно по плитці на бренд з правильним написом/кольором, без помилок у консолі.
  - Перевірка (2026-10-23 ~19:30 UTC): автоматична перевірка в браузері (Claude через Playwright: Python `playwright`, headless Chromium, `python app.py` на `data/lobby_monitor.sqlite3`): `1h ago` / `12h ago` / `3d ago` з класами fresh / stale / old (RocketPlay / Lucky Dreams / OnlyWin; після T-011 плитки йдуть за алфавітом). Консоль браузера порожня, відповідей ≥ 400 немає. Сервер віддає 404 на `/favicon.ico`, але він був і до фічі (у `static/` на `master` немає favicon), а headless Chromium цей запит не робив. Людина цю перевірку не робила — **потребує підтвердження людиною перед /sdd:ship** (одним рядком у PR або скріншотом).

- [x] T-006 — Підключити `test_freshness.py` до `smoke_check.py`
  - AC: §5 invariant-3 (design §4, AGENTS.md testing gate)
  - Files: `smoke_check.py`, `test_freshness.py` (запускається, не змінюється)
  - DoD: `python smoke_check.py` завершується з кодом 0 і в виводі видно запуск `test_freshness.py`; навмисно зламаний тест у `test_freshness.py` валить `smoke_check.py` (перевірити й відкотити).

- [x] T-007 — Fix: панель freshness не має залежати від успіху `/api/meta` і `/api/overview` (verify-report #1, important)
  - AC: §5 error-1
  - Files: `static/app.js`, `test_freshness.py` (клас `FreshnessStaticAssetsTest`)
  - DoD: `loadFreshness()` стартує незалежно в `boot()` (не після `await refreshMeta()` / `await loadOverview()`); тест перевіряє це в тілі `boot`; `python smoke_check.py` проходить.

- [x] T-008 — Strengthen test for AC happy-1, happy-2, happy-3, error-1 (UI-частина) (verify-report #2, important)
  - AC: §5 happy-1, happy-2, happy-3, error-1
  - Files: `test_freshness.py` (клас `FreshnessStaticAssetsTest`), `tasks.md` (T-005 — запис ручної перевірки)
  - DoD: тест через `function_body("freshnessTile")` перевіряє `` `freshness-badge freshness--${row.tier}` ``, `badge.textContent = row.label`, `name.textContent = row.brand` і відсутність `innerHTML`; ручну перевірку в браузері задокументовано; `python smoke_check.py` проходить.

- [x] T-009 — Fix: тест `boot()` не ловить регресію T-007 (verify-report round 2, R2-1, important)
  - AC: §5 error-1
  - Files: `test_freshness.py` (клас `FreshnessStaticAssetsTest`)
  - DoD: тест прибирає `//`-коментарі з тіла `boot` і вимагає, щоб першим реальним рядком був `loadFreshness();` без жодного `await` перед ним; мутанти M1 (`await Promise.all([refreshMeta(), loadOverview()]); loadFreshness();`) і M2 (`// loadFreshness();`) валять `python smoke_check.py` (перевірити в копії й відкотити); `python smoke_check.py` на HEAD проходить.

- [x] T-010 — Strengthen tile wiring asserts (verify-report round 2, R2-2, nit)
  - AC: §5 happy-1, happy-2, happy-3, error-1 (UI-частина)
  - Files: `test_freshness.py` (клас `FreshnessStaticAssetsTest`)
  - DoD: тіло `freshnessTile` містить повний вираз `` badge.className = `freshness-badge freshness--${row.tier}` `` і `card.append(name, badge)`; тіло `loadFreshness` містить `el("freshnessGrid").replaceChildren(...rows.map(freshnessTile))`; мутанти M3–M6 з verify-report валять `python smoke_check.py` (перевірити в копії й відкотити); `python smoke_check.py` на HEAD проходить.

- [x] T-011 — Стабільний порядок плиток: `ORDER BY b.name` у `brand_freshness` (verify-report round 2, carried-over nit #5)
  - AC: §5 error-1 («решта плиток відображається нормально»), design D10
  - Files: `lobby_db.py`, `test_freshness.py` (клас `BrandFreshnessQueryTest`)
  - DoD: тест вставляє бренди в порядку `Zeta`, `Alpha` і очікує `brand_freshness` у порядку `Alpha`, `Zeta`; тест червоний до зміни SQL і зелений після; `python smoke_check.py` проходить.

- [ ] T-012 — Strengthen test for AC error-1: шлях fetch у `loadFreshness()` (verify-report round 3, N1, nit)
  - AC: §5 error-1
  - Files: `test_freshness.py` (клас `FreshnessStaticAssetsTest`)
  - DoD: тіло `loadFreshness` містить `const rows = await getJson("/api/freshness");` і `"Freshness unavailable."`, не містить `refreshMeta` / `loadOverview`; мутанти M1d, M10, M14 валять `python smoke_check.py` (перевірити в копії й відкотити); `python smoke_check.py` на HEAD проходить.

- [ ] T-013 — Strengthen test for AC happy-1, happy-3: кольори tier і `title` бейджа (verify-report round 3, N2, nit)
  - AC: §5 happy-1, happy-3, design D11
  - Files: `test_freshness.py` (клас `FreshnessStaticAssetsTest`)
  - DoD: блок `.freshness-badge.freshness--fresh` містить `var(--accent-dark)`, блок `--old` містить `#8a5a00`; тіло `freshnessTile` містить ``badge.setAttribute("title", `${row.tier}: ${row.label}`)``; мутанти C1, C2, M9b, M9c валять `python smoke_check.py`; `python smoke_check.py` на HEAD проходить.

- [ ] T-014 — Docs: оновити design §7 L6 і tasks.md (verify-report round 3, N3, N4, nit)
  - Files: `design.md`, `tasks.md`
  - DoD: L6 точно описує, які мутанти ще виживають (або посилається на T-012/T-013, якщо їх закрито); `tasks.md:2` має той самий статус, що spec/design; запис браузерної перевірки T-005 явно каже, чи вона була до чи після T-011.

- [ ] T-015 — `ORDER BY b.name COLLATE NOCASE` у `brand_freshness` або прийняти як обмеження в design §7 (verify-report round 3, N5, nit)
  - AC: design D10
  - Files: `lobby_db.py`, `test_freshness.py` (клас `BrandFreshnessQueryTest`)
  - DoD: тест із брендом у нижньому регістрі (напр. `betway`) очікує порядок без урахування регістру; тест червоний до зміни SQL і зелений після; `python smoke_check.py` проходить.

- [ ] T-016 — Test hygiene: прибрати надлишковий `test_boot_loads_freshness` і assertion, що ніколи не падає (verify-report round 3, N6, nit, optional)
  - Files: `test_freshness.py`
  - DoD: видалено `test_boot_loads_freshness` і `assertNotIn("await", stripped[:first_statement_end])`; мутанти M1/M2 і далі валять гейт; `python smoke_check.py` проходить.

> Spec updated 2026-10-23: `spec.md` §6 Open questions #2 і #3 закрито рішеннями design D7/D8. Пороги 6h/24h і формат лейбла `Xm/Xh/Xd ago` походять з інтерв'ю `/sdd:specify` — людина в автоматичному прогоні їх окремо не підтверджувала (verify-report #8, R2-4). **Потребує підтвердження людиною перед /sdd:ship.**

## Coverage

| AC | Tasks |
|---|---|
| happy-1 | T-002, T-004, T-005, T-008, T-010, T-013 |
| happy-2 | T-002, T-004, T-005, T-008, T-010 |
| happy-3 | T-002, T-004, T-005, T-008, T-010, T-013 |
| happy-4 | T-001, T-005 |
| error-1 | T-001, T-002, T-003, T-004, T-005, T-007, T-008, T-009, T-010, T-011, T-012 |
| invariant-1 | T-001 |
| invariant-2 | T-001, T-003 |
| invariant-3 | T-006 |
