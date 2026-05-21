import json

from mutually_exclusive_knapsack.cli import (
    baseline_solve_instance_main,
    generate_instance_main,
    solve_instance_main,
)
from mutually_exclusive_knapsack.models import KnapsackInstance


def test_generate_instance_cli_writes_json_file(tmp_path) -> None:
    output_path = tmp_path / "instance.json"

    exit_code = generate_instance_main(
        [
            str(output_path),
            "--num-items",
            "4",
            "--capacity",
            "10",
            "--min-weight",
            "1",
            "--max-weight",
            "2",
            "--min-efficiency",
            "1",
            "--max-efficiency",
            "3",
            "--mutual-exclusivity-p",
            "0.25",
        ]
    )

    assert exit_code == 0
    instance = KnapsackInstance.model_validate_json(output_path.read_text(encoding="utf-8"))
    assert len(instance.items) == 4
    assert instance.capacity == 10.0


def test_solve_cli_writes_json_to_stdout(tmp_path, capsys) -> None:
    instance_path = tmp_path / "instance.json"
    instance = KnapsackInstance(capacity=10.0, items=())
    instance_path.write_text(instance.model_dump_json(indent=2), encoding="utf-8")

    exit_code = solve_instance_main([str(instance_path)])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["solution"]["chosen_items"] == []
    assert payload["solution"]["objective_value"] == 0.0
    assert payload["solution"]["total_weight"] == 0.0
    assert payload["statistics"]["node_count"] >= 1
    assert payload["statistics"]["solve_time_seconds"] >= 0.0
    assert payload["statistics"]["lp_time_seconds"] >= 0.0
    if "best_solution_value" in payload["statistics"]:
        assert payload["statistics"]["best_solution_value"] == 0.0


def test_solve_cli_writes_json_file(tmp_path) -> None:
    instance_path = tmp_path / "instance.json"
    output_path = tmp_path / "solution.json"
    instance = KnapsackInstance(capacity=10.0, items=())
    instance_path.write_text(instance.model_dump_json(indent=2), encoding="utf-8")

    exit_code = solve_instance_main([str(instance_path), "--output", str(output_path)])

    assert exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["solution"]["chosen_items"] == []
    assert payload["statistics"]["node_count"] >= 1
    assert payload["statistics"]["solve_time_seconds"] >= 0.0
    assert payload["statistics"]["lp_time_seconds"] >= 0.0
    if "best_solution_value" in payload["statistics"]:
        assert payload["statistics"]["best_solution_value"] == 0.0


def test_baseline_solve_cli_writes_json_to_stdout(tmp_path, capsys) -> None:
    instance_path = tmp_path / "instance.json"
    instance = KnapsackInstance(capacity=10.0, items=())
    instance_path.write_text(instance.model_dump_json(indent=2), encoding="utf-8")

    exit_code = baseline_solve_instance_main([str(instance_path)])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["solution"]["chosen_items"] == []
    assert payload["solution"]["objective_value"] == 0.0
    assert payload["solution"]["total_weight"] == 0.0
    assert payload["statistics"]["solve_time_seconds"] >= 0.0
    assert payload["statistics"]["highs_solve_time_seconds"] >= 0.0
