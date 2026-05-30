from __future__ import annotations
import datetime
from typing import Dict, List, Optional, Type, Any

from .datastore import DataStore, DataStoreError

__all__ = ["AnnotationStep", "AnnotationEngine", "engine"]


class AnnotationStep:
    """
    Base class for a single declarative, idempotent annotation step.

    Subclasses set class-level `name` and `dependencies`, and implement `apply()`.

    Register subclasses with the module-level `engine` singleton:
        from VRTstatistics.annotation import engine
        engine.register(MyAnnotationStep)
    """
    name: str = ""
    dependencies: List[str] = []

    def apply(self, ds: DataStore, **params) -> Dict[str, Any]:
        """
        Apply this annotation to the DataStore.

        Called only when this step is not yet in ds.applied_annotations.
        Returns a metadata dict that is stored as ds.applied_annotations[self.name].
        """
        raise NotImplementedError


class AnnotationEngine:
    """
    Declarative, dependency-driven, idempotent annotation runner.

    Maintains a registry of AnnotationStep classes. Call ensure() to apply a
    named annotation (and all its dependencies) to a DataStore, skipping any
    that are already applied.
    """

    def __init__(self) -> None:
        self._registry: Dict[str, Type[AnnotationStep]] = {}

    def register(self, step_class: Type[AnnotationStep]) -> None:
        """Register an AnnotationStep class by its name."""
        if not step_class.name:
            raise ValueError(f"AnnotationStep class {step_class} has no name")
        self._registry[step_class.name] = step_class

    def ensure(self, ds: DataStore, name: str, **params) -> None:
        """
        Ensure annotation `name` has been applied to `ds`.

        If already present in ds.applied_annotations, returns immediately.
        Otherwise ensures all dependencies first (with no params), then applies.
        """
        if name in ds.applied_annotations:
            return
        step_class = self._registry.get(name)
        if step_class is None:
            raise DataStoreError(f"Unknown annotation step '{name}'. Registered: {list(self._registry)}")
        for dep in step_class.dependencies:
            self.ensure(ds, dep)
        step = step_class()
        result = step.apply(ds, **params)
        ds.applied_annotations[name] = result if result is not None else {}


engine = AnnotationEngine()


class ComponentRoleAnnotation(AnnotationStep):
    """
    Stamps component_role on every record using the component_map discovered
    by SessionNormalizer and stored in ds.session_metadata["component_map"].
    """
    name = "component_role"
    dependencies: List[str] = []

    def apply(self, ds: DataStore, **params) -> Dict[str, Any]:
        component_map: Dict[str, str] = ds.session_metadata.get("component_map", {})
        if not component_map:
            raise DataStoreError("component_map not found in session_metadata — was SessionNormalizer run?")
        for record in ds.data:
            comp = record.get("component", "")
            record["component_role"] = component_map.get(comp, "")
        roles = ds.session_metadata.get("roles", [])
        return {"roles": roles}


class LatencyAnnotation(AnnotationStep):
    """
    Records experiment metadata (sender/receiver roles, protocol, nTiles, etc.)
    into ds.applied_annotations["latency"].

    Params:
        sender: role name of the point-cloud sender (default: roles[0])
        receiver: role name of the point-cloud receiver (default: roles[1])
    """
    name = "latency"
    dependencies = ["component_role"]

    def apply(self, ds: DataStore, **params) -> Dict[str, Any]:
        roles = ds.session_metadata.get("roles", [])
        sender = params.get("sender", roles[0] if roles else "sender")
        receiver = params.get("receiver", roles[1] if len(roles) > 1 else "receiver")

        role_topology = ds.session_metadata.get("role_topology", {})
        sender_topo = role_topology.get(sender, {})

        user_names = ds.session_metadata.get("user_names", {})

        return {
            "sender": sender,
            "receiver": receiver,
            "protocol": sender_topo.get("protocol"),
            "nTiles": sender_topo.get("nTiles", 1),
            "nQualities": sender_topo.get("nQualities", 1),
            "compressed": sender_topo.get("compressed", False),
            "sender_user": user_names.get(sender),
            "receiver_user": user_names.get(receiver),
        }


engine.register(ComponentRoleAnnotation)
engine.register(LatencyAnnotation)


def describe(ds: DataStore) -> str:
    """Return a short human-readable description of the session and annotations."""
    sm = ds.session_metadata
    ann = ds.applied_annotations

    start = sm.get("session_start_time", 0)
    dt = datetime.datetime.fromtimestamp(start).strftime("%d-%b-%Y %H:%M") if start else "unknown"

    lines = [dt]

    lat = ann.get("latency", {})
    if lat:
        sender_user = lat.get("sender_user") or lat.get("sender", "?")
        receiver_user = lat.get("receiver_user") or lat.get("receiver", "?")
        lines.append(f"{sender_user} → {receiver_user}")
        proto = lat.get("protocol")
        if proto:
            suffix = ""
            if lat.get("compressed"):
                suffix += ", compressed"
                nq = lat.get("nQualities", 1)
                if nq and nq > 1:
                    suffix += f" ({nq} levels)"
            nt = lat.get("nTiles", 1)
            if nt and nt > 1:
                suffix += f", {nt} tiles"
            lines.append(proto + suffix)
        desyncs = sm.get("desyncs", {})
        sender_role = lat.get("sender", "sender")
        desync = desyncs.get(sender_role, 0)
        lines.append(f"desync: {int(desync * 1000)} ms")
    else:
        roles = sm.get("roles", [])
        user_names = sm.get("user_names", {})
        for role in roles:
            user = user_names.get(role, role)
            lines.append(f"{role}: {user}")

    return "\n".join(lines)
