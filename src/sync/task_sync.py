"""
Task Sync Engine
RS&Co. Enterprise Integration Layer

Orchestrates the bidirectional sync between SharePoint Lists and Dynamics 365:

  SharePoint "To Dos" list     ←→   D365 Task activities
  SharePoint "WBS Tasks" list  ←→   D365 Project Operations WBS tasks

Run modes:
  push   — Push SharePoint items into D365 (create if missing, update if changed)
  pull   — Pull D365 status back to SharePoint (update % complete, status)
  full   — push then pull (default)

Entry point: sync_all() or call from main.py / Power Automate HTTP action.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Literal

from src.connectors.dynamics365 import D365Task, D365ProjectTask, Dynamics365Client
from src.connectors.sharepoint import SharePointClient, SPToDoItem, SPWBSTask

logger = logging.getLogger(__name__)

RunMode = Literal["push", "pull", "full"]

# Project Operations project GUID — set via env or pass directly to sync functions
D365_PROJECT_ID: str = os.environ.get("D365_PROJECT_ID", "")

# Status mappings: SharePoint status → D365 statecode/statuscode
_SP_STATUS_TO_D365: dict[str, tuple[int, int]] = {
    "Not Started": (0, 2),
    "In Progress": (0, 3),
    "Completed": (1, 5),
    "Cancelled": (2, 6),
    "Waiting on someone else": (0, 4),
    "Deferred": (0, 4),
}
_D365_STATECODE_TO_SP: dict[int, str] = {
    0: "In Progress",
    1: "Completed",
    2: "Cancelled",
}


# ---------------------------------------------------------------------------
# Result tracking
# ---------------------------------------------------------------------------


@dataclass
class SyncResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0

    def __add__(self, other: "SyncResult") -> "SyncResult":
        return SyncResult(
            created=self.created + other.created,
            updated=self.updated + other.updated,
            skipped=self.skipped + other.skipped,
            errors=self.errors + other.errors,
        )

    def summary(self) -> str:
        return (
            f"created={self.created} updated={self.updated} "
            f"skipped={self.skipped} errors={self.errors}"
        )


# ---------------------------------------------------------------------------
# To-Do sync
# ---------------------------------------------------------------------------


def sync_todos(
    sp: SharePointClient,
    d365: Dynamics365Client,
    mode: RunMode = "full",
) -> SyncResult:
    """Sync SharePoint To-Do items with D365 Task activities."""
    result = SyncResult()

    todos: list[SPToDoItem] = sp.get_todos()
    logger.info("Found %d SharePoint To-Do items", len(todos))

    for todo in todos:
        try:
            if mode in ("push", "full"):
                result += _push_todo(todo, sp, d365)
            if mode in ("pull", "full") and todo.d365_task_id:
                result += _pull_todo(todo, sp, d365)
        except Exception as exc:
            logger.error("Error syncing To-Do '%s': %s", todo.title, exc, exc_info=True)
            result.errors += 1

    return result


def _push_todo(
    todo: SPToDoItem,
    sp: SharePointClient,
    d365: Dynamics365Client,
) -> SyncResult:
    statecode, statuscode = _SP_STATUS_TO_D365.get(todo.status, (0, 2))
    task = D365Task(
        subject=todo.title,
        description=todo.notes,
        scheduledend=todo.due_date,
        statecode=statecode,
        statuscode=statuscode,
    )
    activity_id, created = d365.upsert_task_by_subject(todo.title, task)

    if created:
        # Write D365 id back to SharePoint so future runs skip creation
        sp.update_todo_d365_id(todo.id, activity_id)
        logger.info("[To-Do] CREATED D365 Task: '%s'  id=%s", todo.title, activity_id)
        return SyncResult(created=1)

    # Existing: if SharePoint says completed but D365 is still open, close it
    if todo.status == "Completed" and statecode == 1:
        d365.complete_task(activity_id)
        logger.info("[To-Do] COMPLETED D365 Task: '%s'  id=%s", todo.title, activity_id)
        return SyncResult(updated=1)

    logger.debug("[To-Do] No change for '%s'", todo.title)
    return SyncResult(skipped=1)


def _pull_todo(
    todo: SPToDoItem,
    sp: SharePointClient,
    d365: Dynamics365Client,
) -> SyncResult:
    """Pull D365 task status back to SharePoint."""
    open_tasks = d365.list_open_tasks(top=500)
    d365_map = {t["activityid"]: t for t in open_tasks}

    if todo.d365_task_id not in d365_map:
        # Task not in open list — likely completed; mark SharePoint as Completed
        if todo.status != "Completed":
            sp.mark_todo_complete(todo.id, todo.d365_task_id)
            return SyncResult(updated=1)
        return SyncResult(skipped=1)

    d365_task = d365_map[todo.d365_task_id]
    d365_sp_status = _D365_STATECODE_TO_SP.get(d365_task["statecode"], "In Progress")

    if d365_sp_status != todo.status:
        # D365 is leading — update SharePoint
        sp.update_todo_d365_id(todo.id, todo.d365_task_id)  # refresh link
        logger.info(
            "[To-Do PULL] Updated SharePoint status '%s' → '%s' for '%s'",
            todo.status,
            d365_sp_status,
            todo.title,
        )
        return SyncResult(updated=1)

    return SyncResult(skipped=1)


# ---------------------------------------------------------------------------
# WBS Task sync
# ---------------------------------------------------------------------------


def sync_wbs_tasks(
    sp: SharePointClient,
    d365: Dynamics365Client,
    project_id: str = D365_PROJECT_ID,
    mode: RunMode = "full",
) -> SyncResult:
    """Sync SharePoint WBS Tasks with D365 Project Operations tasks."""
    result = SyncResult()

    if not project_id:
        logger.warning(
            "D365_PROJECT_ID not set — WBS sync will create tasks without project binding. "
            "Set D365_PROJECT_ID env var to link tasks to a D365 Project Operations project."
        )

    wbs_tasks: list[SPWBSTask] = sp.get_wbs_tasks()
    logger.info("Found %d SharePoint WBS Tasks", len(wbs_tasks))

    # Build an index of existing D365 project tasks for pull mode
    d365_task_index: dict[str, dict] = {}
    if mode in ("pull", "full") and project_id:
        for pt in d365.list_project_tasks(project_id):
            d365_task_index[pt["msdyn_projecttaskid"]] = pt

    for task in wbs_tasks:
        try:
            if mode in ("push", "full"):
                result += _push_wbs_task(task, sp, d365, project_id)
            if mode in ("pull", "full") and task.d365_project_task_id:
                result += _pull_wbs_task(task, sp, d365_task_index)
        except Exception as exc:
            logger.error("Error syncing WBS Task '%s': %s", task.title, exc, exc_info=True)
            result.errors += 1

    return result


def _push_wbs_task(
    task: SPWBSTask,
    sp: SharePointClient,
    d365: Dynamics365Client,
    project_id: str,
) -> SyncResult:
    if task.d365_project_task_id:
        # Already linked — update progress in D365
        is_complete = task.status == "Completed"
        d365.update_project_task_progress(
            task.d365_project_task_id,
            task.percent_complete,
            complete=is_complete,
        )
        logger.info(
            "[WBS PUSH] Updated D365 WBS task '%s' → %.0f%%",
            task.title,
            task.percent_complete,
        )
        return SyncResult(updated=1)

    # Not yet in D365 — create it
    pt = D365ProjectTask(
        msdyn_subject=f"{task.task_code} {task.title}".strip(),
        msdyn_scheduledstart=task.start_date,
        msdyn_scheduledend=task.due_date,
        msdyn_progress=task.percent_complete,
        msdyn_projectid=project_id,
    )
    guid = d365.create_project_task(pt)

    # Write D365 GUID back to SharePoint
    sp.update_wbs_task_progress(task.id, task.percent_complete, d365_project_task_id=guid)
    logger.info("[WBS PUSH] Created D365 WBS task '%s'  id=%s", task.title, guid)
    return SyncResult(created=1)


def _pull_wbs_task(
    task: SPWBSTask,
    sp: SharePointClient,
    d365_index: dict[str, dict],
) -> SyncResult:
    d365_pt = d365_index.get(task.d365_project_task_id)
    if not d365_pt:
        logger.debug("[WBS PULL] D365 task %s not found in index", task.d365_project_task_id)
        return SyncResult(skipped=1)

    d365_progress = float(d365_pt.get("msdyn_progress", 0))
    d365_statecode = d365_pt.get("statecode", 0)
    sp_status = "Completed" if d365_statecode == 1 else (
        "In Progress" if d365_progress > 0 else "Not Started"
    )

    if abs(d365_progress - task.percent_complete) > 0.5 or sp_status != task.status:
        sp.update_wbs_task_progress(
            task.id,
            d365_progress,
            status=sp_status,
            d365_project_task_id=task.d365_project_task_id,
        )
        logger.info(
            "[WBS PULL] SharePoint WBS task '%s' updated → %.0f%% / %s",
            task.title,
            d365_progress,
            sp_status,
        )
        return SyncResult(updated=1)

    return SyncResult(skipped=1)


# ---------------------------------------------------------------------------
# Top-level entry point
# ---------------------------------------------------------------------------


def sync_all(
    mode: RunMode = "full",
    project_id: str = D365_PROJECT_ID,
) -> dict[str, SyncResult]:
    """
    Run a full sync of both To-Dos and WBS Tasks.

    Returns a dict with keys 'todos' and 'wbs' containing SyncResult objects.
    """
    sp = SharePointClient()
    d365 = Dynamics365Client()

    logger.info("=== RS&Co. Enterprise Task Sync  mode=%s ===", mode)

    todo_result = sync_todos(sp, d365, mode=mode)
    wbs_result = sync_wbs_tasks(sp, d365, project_id=project_id, mode=mode)

    combined = todo_result + wbs_result
    logger.info("=== Sync Complete: todos[%s]  wbs[%s]  total[%s] ===",
                todo_result.summary(), wbs_result.summary(), combined.summary())

    return {"todos": todo_result, "wbs": wbs_result}
