import os
from unittest.mock import patch
from dataclasses import dataclass, field

import pytest
pytestmark = pytest.mark.no_server

from api import vendo_env
from api.vendo_env import hydrate, unhydrate


@pytest.fixture(autouse=True)
def reset_native_tracker():
    """Reset module-level state so tests don't leak ownership info between runs."""
    vendo_env._VENDO_SET_NATIVE.clear()
    yield
    vendo_env._VENDO_SET_NATIVE.clear()


@dataclass
class FakeConn:
    slug: str
    fields: dict = field(default_factory=dict)


def test_hydrate_sets_vendo_namespaced_always(monkeypatch):
    env = {}
    monkeypatch.setattr(os, "environ", env)
    hydrate([FakeConn(slug="telegram", fields={"bot_token": "abc123"})])
    assert env["VENDO_CONN_TELEGRAM_BOT_TOKEN"] == "abc123"


def test_hydrate_sets_native_when_not_preset(monkeypatch):
    env = {}
    monkeypatch.setattr(os, "environ", env)
    hydrate([FakeConn(slug="telegram", fields={"bot_token": "abc123"})])
    assert env["TELEGRAM_BOT_TOKEN"] == "abc123"


def test_hydrate_does_not_overwrite_native_if_user_set(monkeypatch):
    env = {"TELEGRAM_BOT_TOKEN": "user-set"}
    monkeypatch.setattr(os, "environ", env)
    hydrate([FakeConn(slug="telegram", fields={"bot_token": "vendo-set"})])
    assert env["TELEGRAM_BOT_TOKEN"] == "user-set"
    assert env["VENDO_CONN_TELEGRAM_BOT_TOKEN"] == "vendo-set"


def test_hydrate_unknown_slug_only_namespaces(monkeypatch):
    env = {}
    monkeypatch.setattr(os, "environ", env)
    hydrate([FakeConn(slug="unknown_xyz", fields={"some_field": "v"})])
    assert env["VENDO_CONN_UNKNOWN_XYZ_SOME_FIELD"] == "v"
    # No native alias because no catalog entry
    assert "SOME_FIELD" not in env


def test_unhydrate_removes_vendo_only(monkeypatch):
    # First hydrate to populate _VENDO_SET_NATIVE tracker, then unhydrate
    env = {}
    monkeypatch.setattr(os, "environ", env)
    hydrate([FakeConn(slug="telegram", fields={"bot_token": "vendo"})])
    env["USER_SET"] = "stays"
    unhydrate(["telegram"])
    assert "VENDO_CONN_TELEGRAM_BOT_TOKEN" not in env
    assert "TELEGRAM_BOT_TOKEN" not in env  # was vendo-set, remove
    assert "USER_SET" in env
