from __future__ import annotations

from behave.formatter.base import Formatter


class RequestResponseFormatter(Formatter):
    """Human-friendly Behave formatter for API diagnostics.

    Keeps output focused on scenario/step progression and explicit failure reasons,
    while request/response payloads are still printed by step definitions.
    """

    def __init__(self, stream_opener, config):
        super().__init__(stream_opener, config)
        self.current_feature = None
        self.current_scenario = None

    def feature(self, feature):
        self.current_feature = feature
        self.stream.write(f"\n=== Feature: {feature.name} ===\n")

    def scenario(self, scenario):
        self.current_scenario = scenario
        self.stream.write(f"\n--- Scenario: {scenario.name} ---\n")

    def step(self, step):
        self.stream.write(f"➡ {step.keyword.strip()} {step.name}\n")

    def result(self, step_result):
        raw_status = str(getattr(step_result, "status", "unknown")).upper()
        status = raw_status.split(".")[-1]
        duration = getattr(step_result, "duration", None)
        duration_text = f" ({duration:.3f}s)" if isinstance(duration, (int, float)) else ""

        if status == "PASSED":
            icon = "✅"
        elif status in {"FAILED", "ERROR"}:
            icon = "❌"
        elif status == "SKIPPED":
            icon = "⏭"
        else:
            icon = "•"

        self.stream.write(f"{icon} Step status: {status}{duration_text}\n")

        if status in {"FAILED", "ERROR"}:
            error_message = getattr(step_result, "error_message", None)
            exception = getattr(step_result, "exception", None)
            if error_message:
                self.stream.write("Failure details:\n")
                for line in str(error_message).splitlines():
                    self.stream.write(f"  {line}\n")
            elif exception:
                self.stream.write(f"Failure details: {exception}\n")

    def eof(self):
        self.stream.write("\n=== End of execution ===\n")
