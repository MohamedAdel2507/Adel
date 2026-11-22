"""Central Data Manager: single store for inputs, module outputs, the assumptions ledger and the
inter-module data-transfer log. Modules never read each other directly; the controller moves
values through transfer(), which records every hand-off."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

MODULES = ("M01", "M02", "M03", "M04", "M05")
MODULE_NAMES = {"M01": "Feedstock Analyzer", "M02": "Process Yield Estimator",
                "M03": "Energy & Utilities", "M04": "Zero-Waste Manager", "M05": "Techno-Economic Analysis"}


@dataclass
class DataManager:
    inputs: dict = field(default_factory=dict)
    results: dict[str, Any] = field(default_factory=dict)
    derived: dict[str, Any] = field(default_factory=dict)      # integration-layer results (mass balance, etc.)
    status: dict[str, dict] = field(default_factory=lambda: {m: {"state": "pending", "message": ""} for m in MODULES})
    assumptions: list[dict] = field(default_factory=list)
    transfers: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks: list[dict] = field(default_factory=list)

    def assume(self, module: str, parameter: str, value: Any, unit: str, origin: str, note: str = "") -> None:
        """origin: 'user' | 'default' | 'calculated' | 'assumption'."""
        self.assumptions.append({"Module": module, "Parameter": parameter, "Value": value, "Unit": unit,
                                 "Origin": origin, "Note": note})

    def transfer(self, src: str, dst: str, name: str, value: float, unit: str, note: str = "") -> float:
        self.transfers.append({"From": src, "To": dst, "Variable": name, "Value": value, "Unit": unit, "Note": note})
        return value

    def set_status(self, module: str, state: str, message: str = "") -> None:
        self.status[module] = {"state": state, "message": message}

    def warn(self, msg: str) -> None:
        if msg not in self.warnings:
            self.warnings.append(msg)

    def check(self, name: str, passed: bool, detail: str) -> None:
        self.checks.append({"Check": name, "Result": "PASS" if passed else "FAIL", "Detail": detail})

    @property
    def completed(self) -> bool:
        return all(self.status[m]["state"] == "ok" for m in MODULES)
