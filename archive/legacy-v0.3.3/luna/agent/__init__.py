"""
luna/agent — Agent Runtime Kernel.

The core of Luna's agentic behaviour. Everything that makes Luna an
operator rather than a chatbot lives here.

Modules:
    schemas.py      TravelTask, TaskPattern, TaskStatus, PlannerOutput.
    task_manager.py In-memory CRUD for TravelTask objects.
    runtime.py      The Agent Runtime loop — receives InternalEvent,
                    calls the planner, manages tasks, returns a reply.

The runtime is the only component the Event Gateway talks to.
It coordinates memory, planner, and task manager internally.

Future additions (v0.0.5+):
    Tool dispatcher calls live here once tools are built.
    Confirmation gate lives here once policy layer is built.
    Multi-task routing lives here once task routing is built.
"""
