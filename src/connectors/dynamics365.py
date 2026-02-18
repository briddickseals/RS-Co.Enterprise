"""
Dynamics 365 Web API Connector
RS&Co. Enterprise Integration Layer

Covers:
  - Activities (Tasks, To-Dos) — entity: tasks
  - WBS project tasks          — entity: msdyn_projecttasks (Project Operations)
  - Contacts, Leads, Opportunities (read helpers for context)

D365 Web API docs:
  https://learn.microsoft.com/en-us/power-apps/developer/data-platform/webapi/overview
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import requests

from src.auth.graph_auth import get_token_provider

logger = logging.getLogger(__name__)

D365_BASE_URL: str = os.environ.get(
    "D365_RESOURCE_URL", "https://org.crm.dynamics.com"
)
API_VERSION = "v9.2"
_BASE = f"{D365_BASE_URL}/api/data/{API_VERSION}"

# Standard OData headers required by D365
_HEADERS = {
    "OData-MaxVersion": "4.0",
    "OData-Version": "4.0",
    "Accept": "application/json",
    "Content-Type": "application/json; charset=utf-8",
    "Prefer": "odata.include-annotations=OData.Community.Display.V1.FormattedValue",
}


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class D365Task:
    """Represents a D365 Task activity (entity: task)."""

    subject: str
    description: str = ""
    scheduledend: str = ""       # ISO 8601 due date
    actualend: str = ""          # ISO 8601 completion date
    statecode: int = 0           # 0=Open, 1=Completed, 2=Cancelled
    statuscode: int = 2          # 2=Not Started, 3=In Progress, 5=Completed
    activityid: str = ""         # D365 GUID (populated on fetch)
    regardingobjectid: str = ""  # GUID of related record (deal/contact)
    regardingobjecttype: str = ""

    def to_api_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"subject": self.subject}
        if self.description:
            payload["description"] = self.description
        if self.scheduledend:
            payload["scheduledend"] = self.scheduledend
        if self.statecode:
            payload["statecode"] = self.statecode
        if self.statuscode:
            payload["statuscode"] = self.statuscode
        return payload


@dataclass
class D365ProjectTask:
    """Represents a D365 Project Operations WBS task (entity: msdyn_projecttask)."""

    msdyn_subject: str
    msdyn_scheduledstart: str = ""
    msdyn_scheduledend: str = ""
    msdyn_progress: float = 0.0       # 0–100
    msdyn_projecttaskid: str = ""     # GUID
    msdyn_projectid: str = ""         # Parent project GUID
    statecode: int = 0


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class Dynamics365Client:
    """
    Thin wrapper around D365 Web API.
    All requests automatically inject a fresh Bearer token.
    """

    def __init__(self, base_url: str = _BASE):
        self._base = base_url
        self._token_provider = get_token_provider()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _auth_headers(self) -> dict[str, str]:
        token = self._token_provider.get_d365_token()
        return {**_HEADERS, "Authorization": f"Bearer {token}"}

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{self._base}/{path}"
        resp = requests.get(url, headers=self._auth_headers(), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, payload: dict) -> dict | None:
        url = f"{self._base}/{path}"
        resp = requests.post(url, headers=self._auth_headers(), json=payload, timeout=30)
        resp.raise_for_status()
        if resp.status_code == 204:
            return None
        return resp.json()

    def _patch(self, path: str, payload: dict) -> None:
        url = f"{self._base}/{path}"
        resp = requests.patch(url, headers=self._auth_headers(), json=payload, timeout=30)
        resp.raise_for_status()

    # ------------------------------------------------------------------
    # Task Activities
    # ------------------------------------------------------------------

    def list_open_tasks(self, top: int = 100) -> list[dict]:
        """Return all open Task activities from D365."""
        data = self._get(
            "tasks",
            params={
                "$filter": "statecode eq 0",
                "$select": "activityid,subject,description,scheduledend,statecode,statuscode",
                "$top": top,
                "$orderby": "scheduledend asc",
            },
        )
        return data.get("value", [])

    def create_task(self, task: D365Task) -> str:
        """Create a new Task activity; returns the new activityid GUID."""
        payload = task.to_api_payload()
        resp = requests.post(
            f"{self._base}/tasks",
            headers=self._auth_headers(),
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        # D365 returns the new record URL in the OData-EntityId header
        entity_id_header = resp.headers.get("OData-EntityId", "")
        # Extract GUID from URL: …/tasks(GUID)
        guid = entity_id_header.split("(")[-1].rstrip(")")
        logger.info("Created D365 Task: %s  id=%s", task.subject, guid)
        return guid

    def complete_task(self, activity_id: str) -> None:
        """Mark a Task activity as Completed (statecode=1, statuscode=5)."""
        self._patch(
            f"tasks({activity_id})",
            {"statecode": 1, "statuscode": 5, "actualend": datetime.utcnow().isoformat() + "Z"},
        )
        logger.info("Completed D365 Task id=%s", activity_id)

    def upsert_task_by_subject(self, subject: str, defaults: D365Task) -> tuple[str, bool]:
        """
        Return (activityid, created).
        If a task with that subject already exists, return it; otherwise create.
        """
        data = self._get(
            "tasks",
            params={
                "$filter": f"subject eq '{subject.replace(chr(39), chr(39)*2)}'",
                "$select": "activityid,statecode",
                "$top": 1,
            },
        )
        existing = data.get("value", [])
        if existing:
            return existing[0]["activityid"], False
        guid = self.create_task(defaults)
        return guid, True

    # ------------------------------------------------------------------
    # WBS / Project Tasks  (Project Operations module)
    # ------------------------------------------------------------------

    def list_project_tasks(self, project_id: str, top: int = 200) -> list[dict]:
        """Return WBS tasks for a given Project Operations project GUID."""
        data = self._get(
            "msdyn_projecttasks",
            params={
                "$filter": f"_msdyn_project_value eq '{project_id}'",
                "$select": (
                    "msdyn_projecttaskid,msdyn_subject,"
                    "msdyn_scheduledstart,msdyn_scheduledend,"
                    "msdyn_progress,statecode"
                ),
                "$orderby": "msdyn_scheduledstart asc",
                "$top": top,
            },
        )
        return data.get("value", [])

    def update_project_task_progress(
        self, task_id: str, progress: float, complete: bool = False
    ) -> None:
        """Update the % complete on a WBS project task."""
        payload: dict[str, Any] = {"msdyn_progress": min(max(progress, 0.0), 100.0)}
        if complete:
            payload["statecode"] = 1
        self._patch(f"msdyn_projecttasks({task_id})", payload)
        logger.info("Updated WBS task id=%s progress=%.0f%%", task_id, payload["msdyn_progress"])

    def create_project_task(self, task: D365ProjectTask) -> str:
        """Create a WBS project task under a project."""
        payload: dict[str, Any] = {
            "msdyn_subject": task.msdyn_subject,
            "msdyn_progress": task.msdyn_progress,
        }
        if task.msdyn_scheduledstart:
            payload["msdyn_scheduledstart"] = task.msdyn_scheduledstart
        if task.msdyn_scheduledend:
            payload["msdyn_scheduledend"] = task.msdyn_scheduledend
        if task.msdyn_projectid:
            # Bind to parent project via OData binding
            payload["msdyn_project@odata.bind"] = f"/msdyn_projects({task.msdyn_projectid})"

        resp = requests.post(
            f"{self._base}/msdyn_projecttasks",
            headers=self._auth_headers(),
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        guid = resp.headers.get("OData-EntityId", "").split("(")[-1].rstrip(")")
        logger.info("Created WBS ProjectTask: %s  id=%s", task.msdyn_subject, guid)
        return guid
