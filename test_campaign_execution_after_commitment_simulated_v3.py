from modules.database import Database
from modules.campaign_execution_engine import CampaignExecutionEngine

SIMULATED_DATE = "2026-09-15"
CAMPAIGN_ID = 2
PROSPECT_ID = 5

print("CAMPAIGN EXECUTION AFTER COMMITMENT TEST - V3")
print(f"Simulated date: {SIMULATED_DATE}")
print()

db = Database()
engine = CampaignExecutionEngine(db)

member = db.cursor.execute(
    """
    SELECT
        m.id, m.status, m.current_step, m.next_action_date,
        m.commitment_type, m.commitment_date, m.commitment_note
    FROM campaign_members m
    WHERE m.campaign_id = ?
      AND m.prospect_id = ?
    LIMIT 1
    """,
    (CAMPAIGN_ID, PROSPECT_ID),
).fetchone()

if not member:
    raise RuntimeError("Campaign member not found.")

print(
    "BEFORE:"
    f" status={member['status']}"
    f" | step={member['current_step']}"
    f" | next={member['next_action_date']}"
    f" | commitment={member['commitment_date']}"
)

# Snapshot only IDs created by this simulation.
before_action = db.cursor.execute(
    "SELECT COALESCE(MAX(id), 0) AS id FROM automation_actions"
).fetchone()["id"]

before_event = db.cursor.execute(
    "SELECT COALESCE(MAX(id), 0) AS id FROM campaign_events"
).fetchone()["id"]

existing_zucchi = db.cursor.execute(
    """
    SELECT id, action_type, status, title, campaign_id,
           campaign_member_id, campaign_step_id
    FROM automation_actions
    WHERE campaign_id = ?
      AND campaign_member_id = ?
    ORDER BY id DESC
    """,
    (CAMPAIGN_ID, member["id"]),
).fetchall()

print()
print("EXISTING ZUCCHI CAMPAIGN ACTIONS:")
if not existing_zucchi:
    print("None")
else:
    for action in existing_zucchi:
        print(
            f"Action={action['id']} | TYPE={action['action_type']} "
            f"| STATUS={action['status']} | STEP_ID={action['campaign_step_id']}"
        )
        print(f"  TITLE: {action['title']}")

print()
print("RUNNING CAMPAIGN EXECUTION ENGINE...")
print("(The engine itself releases due customer commitments before checking due steps.)")

# IMPORTANT: the real CampaignExecutionEngine API is run(on_date=...).
# There is no release_due_commitments() method on CampaignExecutionEngine.
result = engine.run(
    campaign_id=CAMPAIGN_ID,
    on_date=SIMULATED_DATE,
)

print()
print(f"Due communications checked: {result['checked']}")
print(f"Commitments released: {result.get('released_commitments', 0)}")
print(f"Actions generated: {result['actions_generated']}")
print("No email sent.")

after_member = db.cursor.execute(
    """
    SELECT status, current_step, next_action_date, commitment_date
    FROM campaign_members
    WHERE id = ?
    """,
    (member["id"],),
).fetchone()

print()
print(
    "AFTER ENGINE RUN:"
    f" status={after_member['status']}"
    f" | step={after_member['current_step']}"
    f" | next={after_member['next_action_date']}"
    f" | commitment={after_member['commitment_date']}"
)

print()
print("ENGINE-GENERATED ACTIONS:")
if not result["actions"]:
    print("No new action returned by the engine.")
else:
    for action in result["actions"]:
        print(
            f"Action={action['id']} | TYPE={action['action_type']} "
            f"| PRIORITY={action['priority']}"
        )
        print(f"  TITLE: {action['title']}")
        print(f"  DESCRIPTION: {action['description']}")

print()
print("NEW AUTOMATION ACTION ROWS:")
new_actions = db.cursor.execute(
    """
    SELECT *
    FROM automation_actions
    WHERE id > ?
    ORDER BY id
    """,
    (before_action,),
).fetchall()

if not new_actions:
    print("None")
else:
    for action in new_actions:
        print(
            f"Action ID={action['id']} | TYPE={action['action_type']} "
            f"| STATUS={action['status']} | CAMPAIGN={action['campaign_id']} "
            f"| MEMBER={action['campaign_member_id']} "
            f"| STEP={action['campaign_step_id']}"
        )
        print(f"  TITLE: {action['title']}")

print()
print("NEW CAMPAIGN EVENTS:")
new_events = db.cursor.execute(
    """
    SELECT *
    FROM campaign_events
    WHERE id > ?
    ORDER BY id
    """,
    (before_event,),
).fetchall()

if not new_events:
    print("None")
else:
    for event in new_events:
        print(
            f"Event ID={event['id']} | TYPE={event['event_type']} "
            f"| MEMBER={event['member_id']} | PROSPECT={event['prospect_id']}"
        )
        print(f"  DETAILS: {event['details']}")

# Restore exact original member state.
db.cursor.execute(
    """
    UPDATE campaign_members
    SET
        status = ?,
        current_step = ?,
        next_action_date = ?,
        commitment_type = ?,
        commitment_date = ?,
        commitment_note = ?
    WHERE id = ?
    """,
    (
        member["status"],
        member["current_step"],
        member["next_action_date"],
        member["commitment_type"],
        member["commitment_date"],
        member["commitment_note"],
        member["id"],
    ),
)

# Delete only rows created by this test.
db.cursor.execute(
    "DELETE FROM automation_actions WHERE id > ?",
    (before_action,),
)
db.cursor.execute(
    "DELETE FROM campaign_events WHERE id > ?",
    (before_event,),
)

db.connection.commit()

restored = db.cursor.execute(
    """
    SELECT status, current_step, next_action_date, commitment_date
    FROM campaign_members
    WHERE id = ?
    """,
    (member["id"],),
).fetchone()

print()
print(
    "RESTORED:"
    f" status={restored['status']}"
    f" | step={restored['current_step']}"
    f" | next={restored['next_action_date']}"
    f" | commitment={restored['commitment_date']}"
)

print()
print("No email sent.")
print("Simulation complete.")
