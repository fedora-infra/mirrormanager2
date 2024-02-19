import typing

from rich.console import Console
from rich.table import Table
from rich.text import Text

from mirrormanager2.lib import model

if typing.TYPE_CHECKING:
    from .crawler import CrawlResult


class ProgressTask:
    def __init__(self, progress, host_id):
        self._progress = progress
        self._host_id = host_id
        self._name = Text(str(host_id))
        self._host_name = None
        self._action = None
        self._total = None
        self._task_id = None

    @property
    def name(self):
        if self._host_name:
            _name = self._host_name
        else:
            _name = Text(str(self.host_id))
        if self._action:
            _name = Text.assemble(_name, f" ({self._action})")
        padded = _name.copy()
        padded.pad_right(45 - len(self._name))
        return padded

    def _set_name(self):
        if self._task_id is not None:
            self._progress.update(self._task_id, description=self.name)

    def set_host_name(self, host_name):
        self._host_name = Text(host_name)
        self._host_name.truncate(40, overflow="ellipsis")
        self._set_name()

    def set_action(self, action):
        self._action = Text(action)
        self._set_name()

    def set_total(self, total):
        self.reset(total=total)

    def reset(self, **kwargs):
        if "total" in kwargs:
            self._total = kwargs["total"]
        if self._task_id is not None:
            self._progress.reset(self._task_id, **kwargs)

    def advance(self, amount=1):
        if self._task_id is None:
            self._task_id = self._progress.add_task(self.name, total=self._total)
        self._progress.advance(self._task_id, amount)

    def finish(self):
        if self._task_id is not None:
            self._progress.remove_task(self._task_id)


def report_crawl(ctx_obj, options: dict, results: list["CrawlResult"]):
    console = ctx_obj["console"]
    table = Table(title="Results")
    table.add_column("Host Name")
    table.add_column("Status")
    table.add_column("Duration")
    if options.get("canary"):
        table.add_column("Total directories")
        table.add_column("Unreadable directories")
        table.add_column("Changed to up2date")
        table.add_column("Changed to NOT up2date")
        table.add_column("Unchanged")
        table.add_column("Unknown")
        table.add_column("HostCategoryDirs created")
        table.add_column("HostCategoryDirs deleted")

    def _to_str(stats_or_none, attr):
        str(getattr(stats_or_none, attr)) if stats_or_none is not None else ""

    for result in results:
        row = [
            result.host_name,
            result.status,
            f"{result.duration:.0f}s",
        ]
        if options.get("canary"):
            row.extend(
                [
                    _to_str(result.stats, "total_directories"),
                    _to_str(result.stats, "unreadable"),
                    _to_str(result.stats, "up2date"),
                    _to_str(result.stats, "not_up2date"),
                    _to_str(result.stats, "unchanged"),
                    _to_str(result.stats, "unknown"),
                    _to_str(result.stats, "hcds_created"),
                    _to_str(result.stats, "hcds_deleted"),
                ]
            )
        table.add_row(*row)
    console.print(table)


def report_propagation(
    console: Console, session, repo_status: dict[int, dict[model.PropagationStatus, int]]
):
    table = Table(title="Results")
    table.add_column("Repo")
    for ps in model.PropagationStatus:
        table.add_column(ps.value)
    for repo_id in sorted(repo_status):
        repo = session.get(model.Repository, repo_id)
        status_counts = repo_status[repo_id]
        row = [repo.prefix]
        for ps in model.PropagationStatus:
            row.append(str(status_counts.get(ps.value, 0)))
        table.add_row(*row)
    console.print(table)
