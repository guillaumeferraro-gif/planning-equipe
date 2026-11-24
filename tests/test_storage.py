import json
from pathlib import Path
import pytest
from planning.storage import Store, StorageError, import_legacy
from conftest import assign

def test_atomic_save_conflict_backup_and_corruption(tmp_path, state):
    store = Store(tmp_path)
    saved = store.save(state, expected_revision=0)
    assert saved["revision"] == 1 and store.load()["revision"] == 1
    with pytest.raises(StorageError):
        store.save(state, expected_revision=0)
    saved["oat"]["2026"] = 60000
    saved = store.save(saved, expected_revision=1)
    assert (tmp_path/"planning-state.backup.json").exists()
    (tmp_path/"planning-state.json").write_text("{broken")
    with pytest.raises(StorageError):
        store.load()

def test_legacy_import_preserves_source_and_does_not_validate(tmp_path, state):
    source = tmp_path/"planning_2026_11.json"
    source.write_text(json.dumps({"IDE fictive": {"1":"☀️ JOUR","2":"🌙 NUIT","3":"-"}}))
    before=source.read_bytes()
    result, warnings = import_legacy(state,tmp_path)
    assert source.read_bytes()==before
    nurse = next(n for n in result["nurses"] if n["name"]=="IDE fictive")
    assert result["assignments"]["2026-11-01"][nurse["id"]]["shift"]=="J"
    assert result["assignments"]["2026-11-01"][nurse["id"]]["confirmed"] is False
    assert warnings
