from modules.database import Database
from modules.campaign_engine import CampaignEngine

CAMPAIGN_ID = 2
PROSPECT_ID = 5
SIMULATED_COMMITMENT_DATE = "2026-09-15"

print("CUSTOMER COMMITMENT -> EXISTING ACTION RESCHEDULE TEST")
print(f"Campaign: {CAMPAIGN_ID} | Prospect: {PROSPECT_ID}")
print(f"Simulated commitment date: {SIMULATED_COMMITMENT_DATE}")
print()

db = Database()
engine = CampaignEngine(db)

member = db.cursor.execute(
    """
    SELECT *
    FROM campaign_members
    WHERE campaign_id = ?
      AND prospect_id = ?
    LIMIT 1
    """,
    (CAMPAIGN_ID, PROSPECT_ID),
).fetchone()

if not member:
    raise RuntimeError("Campaign member not found.")

action = db.cursor.execute(
    """
    SELECT *
    FROM automation_actions
    WHERE campaign_id = ?
      AND campaign_member_id = ?
      AND campaign_step_id = ?
      AND action_type = 'CAMPAIGN_STEP_DUE'
      AND status = 'OPEN'
    ORDER BY id DESC
    LIMIT 1
    """,
    (CAMPAIGN_ID, member["id"], member["current_step"]),
).fetchone()

if not action:
    raise RuntimeError("Expected OPEN CAMPAIGN_STEP_DUE action not found.")

# Snapshot exact state for safe restoration.
member_state = dict(member)
action_state = dict(action)

before_events = db.cursor.execute(
    "SELECT COALESCE(MAX(id), 0) AS id FROM campaign_events"
).fetchone()["id"]

print("========== BEFORE ==========")
print(
    f"Member={member['id']} | STATUS={member['status']} | "
    f"STEP={member['current_step']} | NEXT={member['next_action_date']}"
)
print(
    f"Action={action['id']} | STATUS={action['status']} | "
    f"STEP={action['campaign_step_id']} | DUE={action['due_date']}"
)
print()

print("Applying customer commitment...")
result = engine.set_customer_commitment(
    campaign_id=CAMPAIGN_ID,
    prospect_id=PROSPECT_ID,
    commitment_type="FOLLOW_UP",
    commitment_date=SIMULATED_COMMITMENT_DATE,
    note="Customer requested follow-up in mid-September.",
    source="test_reschedule",
)

print(f"set_customer_commitment() returned: {result}")

after_member = db.cursor.execute(
    """
    SELECT status, current_step, next_action_date, commitment_date
    FROM campaign_members
    WHERE id = ?
    """,
    (member["id"],),
).fetchone()

after_action = db.cursor.execute(
    """
    SELECT id, status, campaign_step_id, due_date, title, description
    FROM automation_actions
    WHERE id = ?
    """,
    (action["id"],),
).fetchone()

action_count = db.cursor.execute(
    """
    SELECT COUNT(*) AS n
    FROM automation_actions
    WHERE campaign_id = ?
      AND campaign_member_id = ?
      AND campaign_step_id = ?
      AND action_type = 'CAMPAIGN_STEP_DUE'
    """,
    (CAMPAIGN_ID, member["id"], member["current_step"]),
).fetchone()["n"]

new_events = db.cursor.execute(
    """
    SELECT id, event_type, details
    FROM campaign_events
    WHERE id > ?
    ORDER BY id
    """,
    (before_events,),
).fetchall()

print()
print("========== AFTER COMMITMENT ==========")
print(
    f"Member={member['id']} | STATUS={after_member['status']} | "
    f"STEP={after_member['current_step']} | "
    f"NEXT={after_member['next_action_date']} | "
    f"COMMITMENT={after_member['commitment_date']}"
)
print(
    f"Action={after_action['id']} | STATUS={after_action['status']} | "
    f"STEP={after_action['campaign_step_id']} | "
    f"DUE={after_action['due_date']}"
)
print(f"CAMPAIGN_STEP_DUE ACTION COUNT FOR MEMBER/STEP: {action_count}")

if new_events:
    print("NEW EVENTS:")
    for event in new_events:
        print(
            f"Event={event['id']} | TYPE={event['event_type']} | "
            f"DETAILS={event['details']}"
        )
else:
    print("NEW EVENTS: none")

print()
print("========== VERIFICATION ==========")
print(
    "PASS: existing action was rescheduled."
    if after_action["due_date"] == SIMULATED_COMMITMENT_DATE
    else "FAIL: action due date was not rescheduled."
)
print(
    "PASS: no duplicate CAMPAIGN_STEP_DUE action."
    if action_count == 1
    else f"FAIL: expected 1 action, found {action_count}."
)
print(
    "PASS: member is WAITING_FOR_CUSTOMER."
    if after_member["status"] == "WAITING_FOR_CUSTOMER"
    else f"FAIL: member status is {after_member['status']}."
)

# Restore member fields exactly.
member_columns = [
    "status",
    "current_step",
    "next_action_date",
    "commitment_type",
    "commitment_date",
    "commitment_note",
    "commitment_source",
]
db.cursor.execute(
    """
    UPDATE campaign_members
    SET
        status = ?,
        current_step = ?,
        next_action_date = ?,
        commitment_type = ?,
        commitment_date = ?,
        commitment_note = ?,
        commitment_source = ?
    WHERE id = ?
    """,
    tuple(member_state[c] for c in member_columns) + (member["id"],),
)

# Restore the existing action exactly.
db.cursor.execute(
    """
    UPDATE automation_actions
    SET due_date = ?, description = ?
    WHERE id = ?
    """,
    (
        action_state["due_date"],
        action_state["description"],
        action["id"],
    ),
)

# Remove only events created by this test.
db.cursor.execute(
    "DELETE FROM campaign_events WHERE id > ?",
    (before_events,),
)

db.connection.commit()

restored_member = db.cursor.execute(
    """
    SELECT status, current_step, next_action_date, commitment_date
    FROM campaign_members
    WHERE id = ?
    """,
    (member["id"],),
).fetchone()

restored_action = db.cursor.execute(
    """
    SELECT id, status, campaign_step_id, due_date
    FROM automation_actions
    WHERE id = ?
    """,
    (action["id"],),
).fetchone()

print()
print("========== RESTORED ==========")
print(
    f"Member={member['id']} | STATUS={restored_member['status']} | "
    f"STEP={restored_member['current_step']} | "
    f"NEXT={restored_member['next_action_date']} | "
    f"COMMITMENT={restored_member['commitment_date']}"
)
print(
    f"Action={restored_action['id']} | STATUS={restored_action['status']} | "
    f"STEP={restored_action['campaign_step_id']} | "
    f"DUE={restored_action['due_date']}"
)
print()
print("No email sent.")
print("Simulation complete.")
