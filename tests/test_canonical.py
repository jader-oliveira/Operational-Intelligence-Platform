from boip.collector.canonical import canonical_json, config_hash, diff_configs, keyed


def test_canonical_json_sorts_keys():
    assert canonical_json({"b": 1, "a": 2}) == '{"a":2,"b":1}'


def test_config_hash_stable_regardless_of_key_order():
    assert config_hash({"a": 1, "b": 2}) == config_hash({"b": 2, "a": 1})


def test_diff_configs_detects_changed_added_removed():
    old = {"cpu": 2, "disks": {"disk-0": {"capacity_gb": 40}}}
    new = {"cpu": 4, "disks": {"disk-0": {"capacity_gb": 80}}, "nic": "vmxnet3"}

    changes = diff_configs(old, new)
    paths = {c["path"]: c for c in changes}

    assert paths["cpu"] == {"path": "cpu", "old_value": 2, "new_value": 4}
    assert paths["disks.disk-0.capacity_gb"]["new_value"] == 80
    assert paths["nic"] == {"path": "nic", "old_value": None, "new_value": "vmxnet3"}


def test_diff_configs_no_changes_is_empty():
    config = {"cpu": 2}
    assert diff_configs(config, config) == []


def test_keyed_reorders_by_identity_field():
    items = [{"label": "disk-1", "capacity_gb": 40}, {"label": "disk-0", "capacity_gb": 80}]
    result = keyed(items, "label")
    assert result == {
        "disk-1": {"capacity_gb": 40},
        "disk-0": {"capacity_gb": 80},
    }
