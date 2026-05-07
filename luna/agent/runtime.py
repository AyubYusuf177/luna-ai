"""
luna/agent/runtime.py — Agent Runtime Kernel.

The single function handle(event) is what the Event Gateway calls for
every inbound InternalEvent. It is the replacement for the old
orchestrator stub and contains the real agent loop.

v0.0.5 runtime loop (10 steps):
  1.  Log inbound event.
  2.  Identify or create user.
  3.  Append inbound conversation turn to memory.
  4.  List active tasks for this user.
  5.  Call planner → PlannerOutput.
  6.  Create a new TravelTask or update the most recent active one.
  7.  Execute first selected tool (if any) via dispatcher → ToolResult.
  8.  Compose reply from ToolResult or PlannerOutput fallback.
  9.  Append outbound turn to memory.
  10. Log outbound event. Return reply.

Steps added in later milestones:
  v0.0.7  Policy check + confirmation gate.
  v0.0.7  Response Composer (SMS formatting rules).
  v0.0.8  Proactive outbound path.
"""

from luna.agent import task_manager
from luna.agent.schemas import TravelTask
from luna.events import logger as events
from luna.gateway.schemas import InternalEvent
from luna.memory import store as memory
from luna.reasoning import planner
from luna.tools import dispatcher
from luna.tools.schemas import ToolRequest, ToolStatus


def handle(event: InternalEvent) -> str:
    """
    Run the agent loop for one InternalEvent and return Luna's reply.

    Safe to call from any source (simulate, Twilio, scheduler).
    """
    user_id = event.user_id
    body = event.body or ""

    # ── Step 1: Log inbound ───────────────────────────────────────────────────
    events.log("inbound_sms_received", user_id, {"body": body, "source": event.source})

    # ── Step 2: Identify or create user ──────────────────────────────────────
    user = memory.get_user(user_id)
    is_new = user is None
    if is_new:
        user = memory.create_user(user_id)
    events.log("user_identified", user_id, {"is_new_user": is_new})

    # ── Step 3: Append inbound turn ───────────────────────────────────────────
    memory.append_turn(user_id, "user", body)

    # ── Step 4: List active tasks ─────────────────────────────────────────────
    active_tasks = task_manager.list_active_tasks(user_id)

    # ── Step 5: Call planner ──────────────────────────────────────────────────
    plan = planner.run(body=body, user_profile=user, active_tasks=active_tasks)

    # ── Step 6: Create or update TravelTask ───────────────────────────────────
    if active_tasks:
        task = _update_task(active_tasks[-1], plan)
        events.log("task_updated", user_id, {
            "task_id": task.task_id,
            "task_pattern": task.task_pattern,
            "next_action": task.next_action,
        })
    else:
        task = task_manager.create_task(
            user_id=user_id,
            source=event.source,
            goal=plan.goal,
        )
        task = _update_task(task, plan)
        events.log("task_created", user_id, {
            "task_id": task.task_id,
            "task_pattern": task.task_pattern,
            "next_action": task.next_action,
        })

    # ── Step 7: Execute selected tool (if any) ───────────────────────────────
    tool_result = None
    if plan.selected_tools:
        tool_name = plan.selected_tools[0]
        tool_result = dispatcher.dispatch(ToolRequest(
            tool_name=tool_name,
            args=plan.known_fields,
        ))
        events.log("tool_executed", user_id, {
            "tool_name": tool_name,
            "status": tool_result.status,
        })

    # ── Step 8: Compose reply ─────────────────────────────────────────────────
    if tool_result and tool_result.status == ToolStatus.ok:
        reply = tool_result.reply_text
    else:
        reply = plan.reply_draft

    # ── Step 9: Append outbound turn ──────────────────────────────────────────
    memory.append_turn(user_id, "luna", reply)

    # ── Step 10: Log outbound ─────────────────────────────────────────────────
    events.log("outbound_sms_sent", user_id, {"body": reply})

    return reply


# ── Helpers ───────────────────────────────────────────────────────────────────

def _update_task(task: TravelTask, plan) -> TravelTask:
    """Merge a PlannerOutput into an existing TravelTask and persist it."""
    task.goal = plan.goal
    task.task_pattern = plan.task_pattern
    task.known_fields.update(plan.known_fields)
    task.missing_fields = plan.missing_fields
    task.candidate_tools = plan.candidate_tools
    task.selected_tools = plan.selected_tools
    task.risk_level = plan.risk_level
    task.next_action = plan.next_action
    return task_manager.update_task(task)
