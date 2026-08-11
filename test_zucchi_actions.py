from modules.database import Database

db = Database()

rows = db.cursor.execute(
    """
    SELECT
        id,
        action_type,
        status,
        title,
        due_date,
        campaign_id,
        campaign_member_id,
        campaign_step_id,
        contact_name,
        contact_email
    FROM automation_actions
    WHERE campaign_id = 2
      AND campaign_member_id = 2
    ORDER BY id DESC
    """
).fetchall()

print("========== ZUCCHI CAMPAIGN ACTIONS ==========")

if not rows:
    print("NO ACTIONS FOUND")
else:
    for r in rows:
        print(
            f"ID={r['id']} | "
            f"TYPE={r['action_type']} | "
            f"STATUS={r['status']} | "
            f"STEP={r['campaign_step_id']} | "
            f"DUE={r['due_date']}"
        )
        print(f"TITLE={r['title']}")
        print(f"CONTACT={r['contact_name']} | {r['contact_email']}")
        print()

print(f"TOTAL: {len(rows)}")
