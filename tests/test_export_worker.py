import pytest
from PySide6.QtCore import QCoreApplication

from workers.export_worker import ExportCancelled, ExportWorker


# Qt objects need an application. The worker runs in its own thread, like in the application;
# its signals are queued, then delivered by processEvents() once the thread has finished.
@pytest.fixture(scope="module", autouse=True)
def app():
    return QCoreApplication.instance() or QCoreApplication([])


# cancel_at: the export asks for a cancel (as the "Annuler" button does) when it reaches this percent.
def run(export_function, cancel_at=None):
    worker = ExportWorker(lambda on_progress: export_function(_cancelling(on_progress, worker, cancel_at)))
    events = []
    worker.progress_changed.connect(lambda percent: events.append(percent))
    worker.export_finished.connect(lambda: events.append("finished"))
    worker.export_failed.connect(lambda message: events.append(("failed", message)))
    worker.export_cancelled.connect(lambda: events.append("cancelled"))
    worker.start()
    assert worker.wait(10_000)
    QCoreApplication.processEvents()
    return events


def _cancelling(on_progress, worker, cancel_at):
    def report(percent):
        if cancel_at is not None and percent >= cancel_at:
            worker.cancel()
        on_progress(percent)
    return report


def test_progress_is_sent_then_finished():
    def export(on_progress):
        for percent in (0, 25, 50, 75, 100):
            on_progress(percent)
    assert run(export) == [0, 25, 50, 75, 100, "finished"]


def test_same_percent_is_sent_once_and_values_are_kept_between_0_and_100():
    def export(on_progress):
        for percent in (-5, 0, 10.2, 10.8, 10, 150):
            on_progress(percent)
    assert run(export) == [0, 10, 100, "finished"]


def test_100_is_sent_when_the_export_did_not_send_it():
    assert run(lambda on_progress: on_progress(40)) == [40, 100, "finished"]


def test_errors_are_sent_to_the_ui():
    def export(on_progress):
        on_progress(10)
        raise RuntimeError("disque plein")
    assert run(export) == [10, ("failed", "disque plein")]


def test_cancel_stops_the_export():
    reached = []

    def export(on_progress):
        for percent in range(0, 101, 10):
            on_progress(percent)
            reached.append(percent)
    events = run(export, cancel_at=30)
    assert events == [0, 10, 20, "cancelled"]
    assert reached == [0, 10, 20]


def test_export_cancelled_raised_by_the_export_is_a_cancel():
    def export(on_progress):
        raise ExportCancelled()
    assert run(export) == ["cancelled"]


def test_bad_export_function():
    with pytest.raises(ValueError):
        ExportWorker(None)
    with pytest.raises(TypeError):
        ExportWorker("export")
