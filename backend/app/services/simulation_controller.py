"""Centralized simulation execution controller for RadOnc MDT Simulator.

Provides lifecycle controls:
- 1-click full simulation orchestration (Rounds 1-4)
- Pause / Resume / Stop for whole simulation, individual rounds, and individual agents
- Selective agent execution
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.services import run_store

logger = logging.getLogger("radonc.simulation_controller")


class SimulationController:
    """Manages active simulation lifecycle, pause events, and cancellation states."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        # run_id -> asyncio.Event (is_set means RUNNING, clear means PAUSED)
        self._run_resume_events: dict[str, asyncio.Event] = {}
        # (run_id, round_number) -> asyncio.Event
        self._round_resume_events: dict[tuple[str, int], asyncio.Event] = {}
        # Sets of stopped entities
        self._stopped_runs: set[str] = set()
        self._stopped_rounds: set[tuple[str, int]] = set()
        self._stopped_agents: set[tuple[str, int, str]] = set()
        # Set of paused entities for quick sync checks
        self._paused_runs: set[str] = set()
        self._paused_rounds: set[tuple[str, int]] = set()

    def _get_run_event(self, run_id: str) -> asyncio.Event:
        if run_id not in self._run_resume_events:
            ev = asyncio.Event()
            ev.set()  # Default is running
            self._run_resume_events[run_id] = ev
        return self._run_resume_events[run_id]

    def _get_round_event(self, run_id: str, round_number: int) -> asyncio.Event:
        key = (run_id, round_number)
        if key not in self._round_resume_events:
            ev = asyncio.Event()
            ev.set()  # Default is running
            self._round_resume_events[key] = ev
        return self._round_resume_events[key]

    # -------------------------------------------------------------------------
    # Simulation Level Controls
    # -------------------------------------------------------------------------

    def pause_simulation(self, run_id: str) -> None:
        """Pause execution of the simulation run."""
        self._paused_runs.add(run_id)
        ev = self._get_run_event(run_id)
        ev.clear()
        run_store.mark_run_status(run_id, "paused")
        logger.info("Simulation %s paused.", run_id)

    def resume_simulation(self, run_id: str) -> None:
        """Resume execution of the paused simulation run."""
        self._paused_runs.discard(run_id)
        ev = self._get_run_event(run_id)
        ev.set()
        run_store.mark_run_status(run_id, "running")
        logger.info("Simulation %s resumed.", run_id)

    def stop_simulation(self, run_id: str) -> None:
        """Stop/abort the simulation run completely."""
        self._stopped_runs.add(run_id)
        self._paused_runs.discard(run_id)
        # Unblock any waiting events so coroutines can terminate immediately
        ev = self._get_run_event(run_id)
        ev.set()
        for round_num in (1, 2, 3, 4):
            r_ev = self._get_round_event(run_id, round_num)
            r_ev.set()
            self._stopped_rounds.add((run_id, round_num))
        run_store.mark_run_status(run_id, "stopped")
        run_store.mark_queued_agents_stopped(run_id)
        logger.info("Simulation %s stopped.", run_id)

    def is_simulation_paused(self, run_id: str) -> bool:
        return run_id in self._paused_runs

    def is_simulation_stopped(self, run_id: str) -> bool:
        return run_id in self._stopped_runs

    # -------------------------------------------------------------------------
    # Round Level Controls
    # -------------------------------------------------------------------------

    def pause_round(self, run_id: str, round_number: int) -> None:
        """Pause a specific round."""
        if round_number == 1:
            self.pause_simulation(run_id)
            return
        self._paused_rounds.add((run_id, round_number))
        ev = self._get_round_event(run_id, round_number)
        ev.clear()
        run_store.mark_round_status(run_id, round_number, "paused")
        logger.info("Simulation %s Round %d paused.", run_id, round_number)

    def resume_round(self, run_id: str, round_number: int) -> None:
        """Resume a paused round."""
        if round_number == 1:
            self.resume_simulation(run_id)
            return
        self._paused_rounds.discard((run_id, round_number))
        ev = self._get_round_event(run_id, round_number)
        ev.set()
        run_store.mark_round_status(run_id, round_number, "running")
        logger.info("Simulation %s Round %d resumed.", run_id, round_number)

    def stop_round(self, run_id: str, round_number: int) -> None:
        """Stop a specific round."""
        if round_number == 1:
            self.stop_simulation(run_id)
            return
        self._stopped_rounds.add((run_id, round_number))
        self._paused_rounds.discard((run_id, round_number))
        ev = self._get_round_event(run_id, round_number)
        ev.set()
        run_store.mark_round_status(run_id, round_number, "stopped")
        run_store.mark_queued_agents_stopped(run_id, round_number)
        logger.info("Simulation %s Round %d stopped.", run_id, round_number)

    def is_round_paused(self, run_id: str, round_number: int) -> bool:
        return (run_id, round_number) in self._paused_rounds or run_id in self._paused_runs

    def is_round_stopped(self, run_id: str, round_number: int) -> bool:
        return (run_id, round_number) in self._stopped_rounds or run_id in self._stopped_runs

    # -------------------------------------------------------------------------
    # Agent Level Controls
    # -------------------------------------------------------------------------

    def stop_agent(self, run_id: str, round_number: int, agent_id: str) -> None:
        """Stop an individual agent."""
        self._stopped_agents.add((run_id, round_number, agent_id))
        run_store.mark_agent_status(run_id, round_number, agent_id, "stopped")
        logger.info("Simulation %s Round %d Agent %s stopped.", run_id, round_number, agent_id)

    def clear_stopped_simulation(self, run_id: str) -> None:
        """Clear stopped/paused flags across all rounds so a simulation can restart cleanly."""
        self._stopped_runs.discard(run_id)
        self._paused_runs.discard(run_id)
        self._get_run_event(run_id).set()
        for round_num in (1, 2, 3, 4):
            self._stopped_rounds.discard((run_id, round_num))
            self._paused_rounds.discard((run_id, round_num))
            self._get_round_event(run_id, round_num).set()
        self._stopped_agents = {
            item for item in self._stopped_agents if item[0] != run_id
        }

    def clear_stopped_round(self, run_id: str, round_number: int) -> None:
        """Clear stopped/paused flags for a round so it can restart cleanly."""
        if round_number == 1:
            self.clear_stopped_simulation(run_id)
            return
        self._stopped_runs.discard(run_id)
        self._paused_runs.discard(run_id)
        self._get_run_event(run_id).set()
        self._stopped_rounds.discard((run_id, round_number))
        self._paused_rounds.discard((run_id, round_number))
        self._get_round_event(run_id, round_number).set()
        self._stopped_agents = {
            item
            for item in self._stopped_agents
            if not (item[0] == run_id and item[1] == round_number)
        }

    def clear_stopped_agent(self, run_id: str, round_number: int, agent_id: str) -> None:
        """Clear stopped/paused flags for an agent so it can be re-run cleanly."""
        self._stopped_agents.discard((run_id, round_number, agent_id))
        self._stopped_rounds.discard((run_id, round_number))
        self._stopped_runs.discard(run_id)
        self._paused_rounds.discard((run_id, round_number))
        self._paused_runs.discard(run_id)
        self._get_round_event(run_id, round_number).set()
        self._get_run_event(run_id).set()

    def is_agent_stopped(self, run_id: str, round_number: int, agent_id: str) -> bool:
        return (
            (run_id, round_number, agent_id) in self._stopped_agents
            or (run_id, round_number) in self._stopped_rounds
            or run_id in self._stopped_runs
        )

    # -------------------------------------------------------------------------
    # Execution Checkpoint Helper
    # -------------------------------------------------------------------------

    async def check_execution_allowed(self, run_id: str, round_number: int, agent_id: str | None = None) -> bool:
        """Wait if paused, and return True if execution should proceed or False if stopped."""
        # 1. Check if stopped
        if self.is_simulation_stopped(run_id) or self.is_round_stopped(run_id, round_number):
            return False
        if agent_id and self.is_agent_stopped(run_id, round_number, agent_id):
            return False

        # 2. Wait for simulation unpause if paused
        run_ev = self._get_run_event(run_id)
        if not run_ev.is_set():
            logger.info("Waiting for simulation %s unpause...", run_id)
            await run_ev.wait()

        # Re-check stopped
        if self.is_simulation_stopped(run_id) or self.is_round_stopped(run_id, round_number):
            return False

        # 3. Wait for round unpause if paused
        round_ev = self._get_round_event(run_id, round_number)
        if not round_ev.is_set():
            logger.info("Waiting for simulation %s round %d unpause...", run_id, round_number)
            await round_ev.wait()

        # Re-check stopped
        if self.is_simulation_stopped(run_id) or self.is_round_stopped(run_id, round_number):
            return False
        if agent_id and self.is_agent_stopped(run_id, round_number, agent_id):
            return False

        return True

    # -------------------------------------------------------------------------
    # Full 4-Round Pipeline Execution
    # -------------------------------------------------------------------------

    async def run_full_simulation(self, run_id: str) -> None:
        """Execute Round 1, Round 2, Round 3, and Round 4 sequentially on a single trigger."""
        from app.services.batch_runner import run_independent_assessments
        from app.services.mdt_rounds import run_mdt_round

        logger.info("Starting Full 4-Round MDT Simulation for run %s", run_id)
        
        # Round 1: Independent Assessments
        if not await self.check_execution_allowed(run_id, 1):
            logger.info("Full simulation %s stopped before R1.", run_id)
            return

        run_store.mark_run_status(run_id, "running")
        await run_independent_assessments(run_id)

        # Check R1 status
        if self.is_simulation_stopped(run_id):
            logger.info("Full simulation %s halted after R1 (stopped).", run_id)
            return

        # Round 2: MDT Debate
        if not await self.check_execution_allowed(run_id, 2):
            logger.info("Full simulation %s stopped before R2.", run_id)
            return

        run_store.mark_run_status(run_id, "running")
        try:
            run_store.create_round_job(run_id, 2)
        except Exception as exc:
            logger.warning("Round 2 already created or error for %s: %s", run_id, exc)

        await run_mdt_round(run_id, 2)

        # Check R2 status
        if self.is_simulation_stopped(run_id):
            logger.info("Full simulation %s halted after R2 (stopped).", run_id)
            return

        # Round 3: Adversarial Review
        if not await self.check_execution_allowed(run_id, 3):
            logger.info("Full simulation %s stopped before R3.", run_id)
            return

        run_store.mark_run_status(run_id, "running")
        try:
            run_store.create_round_job(run_id, 3)
        except Exception as exc:
            logger.warning("Round 3 already created or error for %s: %s", run_id, exc)

        await run_mdt_round(run_id, 3)

        # Check R3 status
        if self.is_simulation_stopped(run_id):
            logger.info("Full simulation %s halted after R3 (stopped).", run_id)
            return

        # Round 4: Chair Synthesis
        if not await self.check_execution_allowed(run_id, 4):
            logger.info("Full simulation %s stopped before R4.", run_id)
            return

        run_store.mark_run_status(run_id, "running")
        try:
            run_store.create_round_job(run_id, 4)
        except Exception as exc:
            logger.warning("Round 4 already created or error for %s: %s", run_id, exc)

        await run_mdt_round(run_id, 4)
        
        if not self.is_simulation_stopped(run_id) and not self.is_simulation_paused(run_id):
            run_store.mark_run_status(run_id, "completed")
        logger.info("Full 4-Round MDT Simulation completed for run %s.", run_id)


_GLOBAL_CONTROLLER: SimulationController | None = None


def get_simulation_controller() -> SimulationController:
    """Return singleton SimulationController."""
    global _GLOBAL_CONTROLLER
    if _GLOBAL_CONTROLLER is None:
        _GLOBAL_CONTROLLER = SimulationController()
    return _GLOBAL_CONTROLLER
