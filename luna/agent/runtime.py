"""
luna/agent/runtime.py — Agent Runtime Kernel.

v0.0.7 runtime loop (13 steps):
  1.  Log inbound event.
  2.  Identify or create user.
  3.  Append inbound conversation turn.
  4.  Policy: check STOP/START → early return if command.
  5.  Policy: check inbound for sensitive data → early return if blocked.
  6.  Confirmation: check YES/NO against pending confirmation → early return if resolved.
  7.  List active tasks for this user.
  8.  Call planner → PlannerOutput.
  9.  Create a new TravelTask or update the most recent active one.
  10. Execute first selected tool (if any) via dispatcher → ToolResult.
  11. Policy: check outbound reply for fake booking claims.
  12. Compose: format reply through Response Composer.
  13. Append outbound turn, log, return reply.

Steps added in later milestones:
  v0.0.8  Proactive outbound path.
"""

from luna.agent import task_manager
from luna.agent.schemas import TravelTask
from luna.composer import response_composer as composer
from luna.confirmation import resolver as confirmation_resolver
from luna.events import logger as events
from luna.gateway.schemas import InternalEvent
from luna.memory import store as memory
from luna.policy import policy
from luna.reasoning import planner
from luna.tools import dispatcher
from luna.tools.schemas import ToolRequest, ToolStatus


def handle(event: InternalEvent) -> str:
    """
    Run the agent loop for one InternalEvent and return Luna's SMS reply.

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

    # ── Step 4: Policy — STOP / START ────────────────────────────────────────
    inbound_decision = policy.check_inbound(body)

    if inbound_decision.command in ("stop", "start"):
        events.log("policy_command", user_id, {"command": inbound_decision.command})
        return _send(user_id, inbound_decision.rewritten_reply)

    # ── Step 5: Policy — sensitive data block ────────────────────────────────
    if not inbound_decision.allowed:
        events.log("policy_blocked_inbound", user_id, {"reason": inbound_decision.reason})
        return _send(user_id, inbound_decision.rewritten_reply)

    # ── Step 6: Confirmation — YES / NO resolution ────────────────────────────
    confirmation_result = confirmation_resolver.resolve_inbound(user_id, body)
    if confirmation_result and confirmation_result.handled:
        status = (
            confirmation_result.confirmation.status
            if confirmation_result.confirmation
            else "no_pending"
        )
        events.log("confirmation_resolved", user_id, {"status": status})
        return _send(user_id, confirmation_result.reply)

    # ── Step 7: List active tasks ─────────────────────────────────────────────
    active_tasks = task_manager.list_active_tasks(user_id)

    # ── Step 8: Call planner ──────────────────────────────────────────────────
    plan = planner.run(body=body, user_profile=user, active_tasks=active_tasks)

    # ── Step 9: Create or update TravelTask ───────────────────────────────────
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

    # ── Step 10: Execute selected tool (if any) ───────────────────────────────
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

    raw_reply = (
        tool_result.reply_text
        if tool_result and tool_result.status == ToolStatus.ok
        else plan.reply_draft
    )

    # ── Step 11: Policy — outbound reply check ────────────────────────────────
    outbound_decision = policy.check_outbound(raw_reply)
    if not outbound_decision.allowed:
        events.log("policy_blocked_outbound", user_id, {"reason": outbound_decision.reason})

    # ── Step 12: Compose reply ────────────────────────────────────────────────
    composed = composer.compose(
        raw_reply,
        policy_decision=outbound_decision if not outbound_decision.allowed else None,
    )

    # ── Step 13: Log outbound and return ─────────────────────────────────────
    memory.append_turn(user_id, "luna", composed.body)
    events.log("outbound_sms_sent", user_id, {"body": composed.body})
    return composed.body


# ── Helpers ───────────────────────────────────────────────────────────────────

def _send(user_id: str, reply: str) -> str:
    """Compose, log, and return a reply for early-exit paths."""
    composed = composer.compose(reply)
    memory.append_turn(user_id, "luna", composed.body)
    events.log("outbound_sms_sent", user_id, {"body": composed.body})
    return composed.body


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
