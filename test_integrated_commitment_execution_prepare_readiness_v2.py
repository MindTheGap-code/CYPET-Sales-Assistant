from modules.database import Database
from modules.campaign_engine import CampaignEngine
from modules.campaign_execution_engine import CampaignExecutionEngine

CAMPAIGN_ID = 2
PROSPECT_ID = 5
SIMULATED_DATE = "2026-09-15"

print("INTEGRATED COMMITMENT -> EXECUTION -> PREPARE EMAIL READINESS TEST V2")
print(f"Campaign={CAMPAIGN_ID} | Prospect={PROSPECT_ID}")
print(f"Simulated date={SIMULATED_DATE}")
print()

db = Database()
campaign_engine = CampaignEngine(db)
execution_engine = CampaignExecutionEngine(db)

member = db.cursor.execute(
    """
    SELECT *
    FROM campaign_members
    WHERE campaign_id=? AND prospect_id=?
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
    WHERE campaign_id=?
      AND campaign_member_id=?
      AND campaign_step_id=?
      AND action_type='CAMPAIGN_STEP_DUE'
      AND status='OPEN'
    ORDER BY id DESC
    LIMIT 1
    """,
    (CAMPAIGN_ID, member["id"], member["current_step"]),
).fetchone()

if not action:
    raise RuntimeError("Open campaign action not found.")

member_state = dict(member)
action_state = dict(action)

before_event = db.cursor.execute(
    "SELECT COALESCE(MAX(id),0) id FROM campaign_events"
).fetchone()["id"]

before_action = db.cursor.execute(
    "SELECT COALESCE(MAX(id),0) id FROM automation_actions"
).fetchone()["id"]

print("========== INITIAL ==========")
print(
    f"Member={member['id']} | STATUS={member['status']} | "
    f"STEP={member['current_step']} | NEXT={member['next_action_date']} | "
    f"COMMITMENT={member['commitment_date']}"
)
print(
    f"Action={action['id']} | STATUS={action['status']} | "
    f"STEP={action['campaign_step_id']} | DUE={action['due_date']} | "
    f"TITLE={action['title']}"
)

print()
print("1) REGISTER CUSTOMER COMMITMENT")
commitment_result = campaign_engine.set_customer_commitment(
    campaign_id=CAMPAIGN_ID,
    prospect_id=PROSPECT_ID,
    commitment_type="FOLLOW_UP",
    commitment_date=SIMULATED_DATE,
    note="Customer requested follow-up in mid-September.",
    source="integrated_test",
)
print(f"set_customer_commitment() returned: {commitment_result}")

after_commitment_action = db.cursor.execute(
    """
    SELECT id,status,due_date,campaign_step_id,title
    FROM automation_actions
    WHERE id=?
    """,
    (action["id"],),
).fetchone()

print(
    f"Action after commitment: ID={after_commitment_action['id']} | "
    f"STATUS={after_commitment_action['status']} | "
    f"DUE={after_commitment_action['due_date']}"
)

print()
print("2) RUN CAMPAIGN EXECUTION ENGINE ON SIMULATED DATE")
result = execution_engine.run(
    campaign_id=CAMPAIGN_ID,
    on_date=SIMULATED_DATE,
)

print(f"Due communications checked: {result['checked']}")
print(f"Commitments released: {result['released_commitments']}")
print(f"Actions generated: {result['actions_generated']}")

after_member = db.cursor.execute(
    """
    SELECT status,current_step,next_action_date,commitment_date
    FROM campaign_members
    WHERE id=?
    """,
    (member["id"],),
).fetchone()

after_action = db.cursor.execute(
    """
    SELECT id,action_type,status,campaign_member_id,campaign_step_id,
           due_date,title,description
    FROM automation_actions
    WHERE id=?
    """,
    (action["id"],),
).fetchone()

open_count = db.cursor.execute(
    """
    SELECT COUNT(*) n
    FROM automation_actions
    WHERE campaign_id=?
      AND campaign_member_id=?
      AND campaign_step_id=?
      AND action_type='CAMPAIGN_STEP_DUE'
      AND status='OPEN'
    """,
    (CAMPAIGN_ID, member["id"], member["current_step"]),
).fetchone()["n"]

new_actions = db.cursor.execute(
    """
    SELECT id,action_type,status,title
    FROM automation_actions
    WHERE id>?
    ORDER BY id
    """,
    (before_action,),
).fetchall()

print()
print("========== FINAL ENGINE STATE ==========")
print(
    f"Member={member['id']} | STATUS={after_member['status']} | "
    f"STEP={after_member['current_step']} | NEXT={after_member['next_action_date']} | "
    f"COMMITMENT={after_member['commitment_date']}"
)
print(
    f"Action={after_action['id']} | TYPE={after_action['action_type']} | "
    f"STATUS={after_action['status']} | STEP={after_action['campaign_step_id']} | "
    f"DUE={after_action['due_date']} | TITLE={after_action['title']}"
)
print(f"OPEN CAMPAIGN_STEP_DUE COUNT={open_count}")
print(f"NEW ACTION ROWS CREATED={len(new_actions)}")

print()
print("========== VERIFICATION ==========")

checks = [
    (
        commitment_result is True,
        "PASS: customer commitment accepted.",
        "FAIL: customer commitment was not accepted.",
    ),
    (
        after_commitment_action["due_date"] == SIMULATED_DATE,
        "PASS: existing Action 23 rescheduled to 2026-09-15.",
        f"FAIL: Action due date is {after_commitment_action['due_date']}.",
    ),
    (
        after_member["status"] == "ACTIVE",
        "PASS: member released to ACTIVE.",
        f"FAIL: member status is {after_member['status']}.",
    ),
    (
        after_action["status"] == "OPEN",
        "PASS: Action 23 remains OPEN and ready for Prepare Email.",
        f"FAIL: Action status is {after_action['status']}.",
    ),
    (
        after_action["due_date"] == SIMULATED_DATE,
        "PASS: Action 23 is due on 2026-09-15.",
        f"FAIL: Action due date is {after_action['due_date']}.",
    ),
    (
        open_count == 1,
        "PASS: exactly one OPEN CAMPAIGN_STEP_DUE exists.",
        f"FAIL: found {open_count} OPEN CAMPAIGN_STEP_DUE actions.",
    ),
    (
        len(new_actions) == 0,
        "PASS: no duplicate action was created.",
        f"FAIL: {len(new_actions)} duplicate action(s) were created.",
    ),
]

for ok, good, bad in checks:
    print(good if ok else bad)

all_pass = all(c[0] for c in checks)

print()
print(
    "FINAL RESULT: PASS - ready for Prepare Email."
    if all_pass
    else "FINAL RESULT: FAIL - do not proceed to Outlook yet."
)

# Restore exact original state.
db.cursor.execute(
    """
    UPDATE campaign_members
    SET status=?,current_step=?,next_action_date=?,
        commitment_type=?,commitment_date=?,commitment_note=?,
        commitment_source=?
    WHERE id=?
    """,
    (
        member_state["status"],
        member_state["current_step"],
        member_state["next_action_date"],
        member_state["commitment_type"],
        member_state["commitment_date"],
        member_state["commitment_note"],
        member_state["commitment_source"],
        member["id"],
    ),
)

db.cursor.execute(
    """
    UPDATE automation_actions
    SET status=?,due_date=?,description=?
    WHERE id=?
    """,
    (
        action_state["status"],
        action_state["due_date"],
        action_state["description"],
        action["id"],
    ),
)

db.cursor.execute(
    "DELETE FROM automation_actions WHERE id>?",
    (before_action,),
)

db.cursor.execute(
    "DELETE FROM campaign_events WHERE id>?",
    (before_event,),
)

db.connection.commit()

restored_member = db.cursor.execute(
    """
    SELECT status,current_step,next_action_date,commitment_date
    FROM campaign_members WHERE id=?
    """,
    (member["id"],),
).fetchone()

restored_action = db.cursor.execute(
    "SELECT status,due_date FROM automation_actions WHERE id=?",
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
    f"Action={action['id']} | STATUS={restored_action['status']} | "
    f"DUE={restored_action['due_date']}"
)
print("No email sent.")
print("Simulation complete.")
