from modules.database import Database

CAMPAIGN_ID = 2
MEMBER_ID = 2
COMMITMENT_DATE = "2026-09-15"

db = Database()

before = db.cursor.execute(
    """
    SELECT id, due_date, status, title
    FROM automation_actions
    WHERE campaign_id = ?
      AND campaign_member_id = ?
      AND campaign_step_id = 2
      AND action_type = 'CAMPAIGN_STEP_DUE'
      AND status = 'OPEN'
    ORDER BY id DESC
    LIMIT 1
    """,
    (CAMPAIGN_ID, MEMBER_ID),
).fetchone()

print("========== BEFORE RESCHEDULE ==========")
if before:
    print(
        f"Action={before['id']} | STATUS={before['status']} | "
        f"DUE={before['due_date']} | TITLE={before['title']}"
    )
else:
    print("NO OPEN STEP 2 ACTION FOUND")

print()
print("This verification script is READ-ONLY.")
print("It does not change the database.")
print()
print("EXPECTED AFTER APPLYING V3 PATCH:")
if before:
    print(
        f"Action {before['id']} remains OPEN and its DUE DATE becomes "
        f"{COMMITMENT_DATE}."
    )
    print("No second CAMPAIGN_STEP_DUE action should be created.")
else:
    print("A future commitment will not have an existing action to reschedule.")
