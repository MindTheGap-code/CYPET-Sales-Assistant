from modules.database import Database


db = Database()

print()
print("========== CAMPAIGNS ==========")

campaigns = db.cursor.execute("""
    SELECT
        id,
        name,
        status,
        channel,
        created_at,
        updated_at
    FROM campaigns
    ORDER BY id
""").fetchall()

for c in campaigns:
    print(
        f"ID={c['id']} | "
        f"{c['name']} | "
        f"STATUS={c['status']} | "
        f"CHANNEL={c['channel']}"
    )

print()
print("========== CAMPAIGN STEPS ==========")

steps = db.cursor.execute("""
    SELECT
        s.id,
        s.campaign_id,
        s.step_number,
        s.name,
        s.delay_days,
        s.active
    FROM campaign_steps s
    ORDER BY s.campaign_id, s.step_number
""").fetchall()

for s in steps:
    print(
        f"Campaign={s['campaign_id']} | "
        f"Step={s['step_number']} | "
        f"{s['name']} | "
        f"Delay={s['delay_days']} days | "
        f"ACTIVE={s['active']}"
    )

print()
print("========== CAMPAIGN MEMBERS ==========")

members = db.cursor.execute("""
    SELECT
        m.id,
        m.campaign_id,
        m.prospect_id,
        m.status,
        m.current_step,
        m.next_action_date,
        p.domain,
        p.company_name
    FROM campaign_members m
    LEFT JOIN prospects p
        ON p.id = m.prospect_id
    ORDER BY m.campaign_id, m.id
""").fetchall()

for m in members:
    print(
        f"Member={m['id']} | "
        f"Campaign={m['campaign_id']} | "
        f"Prospect={m['prospect_id']} | "
        f"{m['company_name'] or m['domain']} | "
        f"STATUS={m['status']} | "
        f"STEP={m['current_step']} | "
        f"NEXT={m['next_action_date']}"
    )

print()
print("========== DUE MEMBERS ==========")

due = db.cursor.execute("""
    SELECT
        m.id,
        m.campaign_id,
        m.prospect_id,
        m.status,
        m.current_step,
        m.next_action_date,
        c.name AS campaign_name,
        c.status AS campaign_status,
        p.domain,
        p.company_name
    FROM campaign_members m
    JOIN campaigns c
        ON c.id = m.campaign_id
    JOIN prospects p
        ON p.id = m.prospect_id
    WHERE c.status = 'ACTIVE'
      AND m.status = 'ACTIVE'
      AND m.next_action_date <= date('now')
    ORDER BY m.next_action_date, m.id
""").fetchall()

for d in due:
    print(
        f"Member={d['id']} | "
        f"{d['company_name'] or d['domain']} | "
        f"Campaign={d['campaign_name']} | "
        f"STEP={d['current_step']} | "
        f"NEXT={d['next_action_date']}"
    )

print()
print(f"TOTAL CAMPAIGNS: {len(campaigns)}")
print(f"TOTAL STEPS: {len(steps)}")
print(f"TOTAL MEMBERS: {len(members)}")
print(f"DUE MEMBERS: {len(due)}")
print()