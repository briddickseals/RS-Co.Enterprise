"""
SharePoint Lists Connector
RS&Co. Enterprise Integration Layer

Reads To-Do and WBS task items from SharePoint Lists at:
  https://rslg.sharepoint.com/sites/RSEnterprise

Targets two list types:
  1. "To Dos"     — General task checklist items (SharePoint List)
  2. "WBS Tasks"  — Work Breakdown Structure items (SharePoint List)

Uses Microsoft Graph API beta + v1.0 endpoints for SharePoint Lists.
Graph docs: https://learn.microsoft.com/en-us/graph/api/listitem-list
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

import requests

from src.auth.graph_auth import get_token_provider

logger = logging.getLogger(__name__)

SHAREPOINT_SITE_URL: str = os.environ.get(
    "SHAREPOINT_SITE_URL", "https://rslg.sharepoint.com/sites/RSEnterprise"
)
GRAPH_BASE = "https://graph.microsoft.com/v1.0"

# SharePoint List display names — override via env if different in your tenant
TODO_LIST_NAME: str = os.environ.get("SP_TODO_LIST_NAME", "To Dos")
WBS_LIST_NAME: str = os.environ.get("SP_WBS_LIST_NAME", "WBS Tasks")

# Column internal names (SharePoint field names) — adjust to match your list schema
_TODO_FIELDS = "Title,Status,DueDate,AssignedTo,Priority,Notes,D365TaskId"
_WBS_FIELDS = (
    "Title,Phase,TaskCode,StartDate,DueDate,Status,"
    "AssignedTo,PercentComplete,Dependencies,D365ProjectTaskId"
)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class SPToDoItem:
    """A To-Do item from the SharePoint 'To Dos' list."""

    id: str                # SharePoint list item ID
    title: str
    status: str            # e.g. "Not Started", "In Progress", "Completed"
    due_date: str          # ISO 8601
    assigned_to: str
    priority: str          # "High", "Normal", "Low"
    notes: str
    d365_task_id: str      # Linked D365 Task activityid (empty if not yet synced)

    @classmethod
    def from_graph(cls, item: dict) -> "SPToDoItem":
        f = item.get("fields", {})
        return cls(
            id=item["id"],
            title=f.get("Title", ""),
            status=f.get("Status", "Not Started"),
            due_date=f.get("DueDate", ""),
            assigned_to=_resolve_person(f.get("AssignedTo")),
            priority=f.get("Priority", "Normal"),
            notes=f.get("Notes", ""),
            d365_task_id=f.get("D365TaskId", ""),
        )


@dataclass
class SPWBSTask:
    """A WBS task item from the SharePoint 'WBS Tasks' list."""

    id: str                # SharePoint list item ID
    title: str
    phase: str             # e.g. "Phase 1: Planning and Analysis"
    task_code: str         # e.g. "1.1", "2.3"
    start_date: str
    due_date: str
    status: str
    assigned_to: str
    percent_complete: float
    dependencies: str
    d365_project_task_id: str  # Linked D365 WBS task GUID

    @classmethod
    def from_graph(cls, item: dict) -> "SPWBSTask":
        f = item.get("fields", {})
        return cls(
            id=item["id"],
            title=f.get("Title", ""),
            phase=f.get("Phase", ""),
            task_code=f.get("TaskCode", ""),
            start_date=f.get("StartDate", ""),
            due_date=f.get("DueDate", ""),
            status=f.get("Status", "Not Started"),
            assigned_to=_resolve_person(f.get("AssignedTo")),
            percent_complete=float(f.get("PercentComplete", 0)),
            dependencies=f.get("Dependencies", ""),
            d365_project_task_id=f.get("D365ProjectTaskId", ""),
        )


def _resolve_person(value: Any) -> str:
    """Extract display name from a SharePoint person/group field."""
    if isinstance(value, dict):
        return value.get("LookupValue", value.get("Title", ""))
    if isinstance(value, list) and value:
        return value[0].get("LookupValue", "")
    return str(value or "")


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class SharePointClient:
    """
    Reads from and writes to SharePoint Lists via Microsoft Graph API.
    Resolves the site-id automatically on first use.
    """

    def __init__(self, site_url: str = SHAREPOINT_SITE_URL):
        self._site_url = site_url
        self._token_provider = get_token_provider()
        self._site_id: str | None = None         # resolved lazily
        self._list_ids: dict[str, str] = {}      # display name → list GUID

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        token = self._token_provider.get_graph_token()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _get(self, url: str, params: dict | None = None) -> dict:
        resp = requests.get(url, headers=self._headers(), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _patch(self, url: str, payload: dict) -> None:
        resp = requests.patch(url, headers=self._headers(), json=payload, timeout=30)
        resp.raise_for_status()

    def _site_id_url(self) -> str:
        """Build the Graph /sites/{site-id} base URL, resolving on first call."""
        if not self._site_id:
            # Graph accepts the SharePoint hostname + path to resolve site id
            hostname = self._site_url.replace("https://", "").split("/")[0]
            site_path = "/".join(self._site_url.replace("https://", "").split("/")[1:])
            data = self._get(f"{GRAPH_BASE}/sites/{hostname}:/{site_path}")
            self._site_id = data["id"]
            logger.debug("Resolved SharePoint site id: %s", self._site_id)
        return f"{GRAPH_BASE}/sites/{self._site_id}"

    def _list_id(self, display_name: str) -> str:
        if display_name not in self._list_ids:
            data = self._get(f"{self._site_id_url()}/lists/{display_name}")
            self._list_ids[display_name] = data["id"]
        return self._list_ids[display_name]

    # ------------------------------------------------------------------
    # To-Do items
    # ------------------------------------------------------------------

    def get_todos(self, status_filter: str | None = None) -> list[SPToDoItem]:
        """
        Fetch all To-Do items from SharePoint.
        Pass status_filter="Not Started" to get only un-started items.
        """
        list_id = self._list_id(TODO_LIST_NAME)
        params: dict[str, Any] = {"$expand": f"fields($select={_TODO_FIELDS})"}
        if status_filter:
            params["$filter"] = f"fields/Status eq '{status_filter}'"

        items = self._paginate(
            f"{self._site_id_url()}/lists/{list_id}/items", params
        )
        return [SPToDoItem.from_graph(i) for i in items]

    def mark_todo_complete(self, item_id: str, d365_task_id: str = "") -> None:
        """Set a To-Do item Status to 'Completed' and store the linked D365 id."""
        list_id = self._list_id(TODO_LIST_NAME)
        url = f"{self._site_id_url()}/lists/{list_id}/items/{item_id}/fields"
        payload: dict[str, Any] = {"Status": "Completed"}
        if d365_task_id:
            payload["D365TaskId"] = d365_task_id
        self._patch(url, payload)
        logger.info("Marked SharePoint To-Do %s as Completed", item_id)

    def update_todo_d365_id(self, item_id: str, d365_task_id: str) -> None:
        """Write the D365 activityid back to the SharePoint item."""
        list_id = self._list_id(TODO_LIST_NAME)
        url = f"{self._site_id_url()}/lists/{list_id}/items/{item_id}/fields"
        self._patch(url, {"D365TaskId": d365_task_id})

    # ------------------------------------------------------------------
    # WBS Task items
    # ------------------------------------------------------------------

    def get_wbs_tasks(self, phase: str | None = None) -> list[SPWBSTask]:
        """
        Fetch WBS tasks from SharePoint.
        Optionally filter by phase name (e.g. "Phase 1: Planning and Analysis").
        """
        list_id = self._list_id(WBS_LIST_NAME)
        params: dict[str, Any] = {"$expand": f"fields($select={_WBS_FIELDS})"}
        if phase:
            params["$filter"] = f"fields/Phase eq '{phase}'"

        items = self._paginate(
            f"{self._site_id_url()}/lists/{list_id}/items", params
        )
        return [SPWBSTask.from_graph(i) for i in items]

    def update_wbs_task_progress(
        self,
        item_id: str,
        percent_complete: float,
        status: str = "",
        d365_project_task_id: str = "",
    ) -> None:
        """Write progress/status back to the SharePoint WBS task item."""
        list_id = self._list_id(WBS_LIST_NAME)
        url = f"{self._site_id_url()}/lists/{list_id}/items/{item_id}/fields"
        payload: dict[str, Any] = {"PercentComplete": percent_complete}
        if status:
            payload["Status"] = status
        if d365_project_task_id:
            payload["D365ProjectTaskId"] = d365_project_task_id
        self._patch(url, payload)
        logger.info(
            "Updated SharePoint WBS Task %s → %.0f%% %s",
            item_id,
            percent_complete,
            status,
        )

    # ------------------------------------------------------------------
    # Pagination helper
    # ------------------------------------------------------------------

    def _paginate(self, url: str, params: dict) -> list[dict]:
        """Follow @odata.nextLink until all pages are collected."""
        results: list[dict] = []
        resp = self._get(url, params)
        results.extend(resp.get("value", []))
        while next_link := resp.get("@odata.nextLink"):
            resp = self._get(next_link)
            results.extend(resp.get("value", []))
        return results
