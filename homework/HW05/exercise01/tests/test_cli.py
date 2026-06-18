from queens.cli import cpsat_main, sat_main


def test_sat_cli_reports_solution(capsys):
    assert sat_main(["4"]) == 0
    out = capsys.readouterr().out
    assert "Status: solution found for n=4" in out
    assert "Model build time:" in out
    assert "Solve time:" in out


def test_cpsat_cli_reports_unsatisfiable(capsys):
    assert cpsat_main(["2"]) == 0
    out = capsys.readouterr().out
    assert "Status: n=2 is unsatisfiable" in out
    assert "Model build time:" in out
    assert "Solve time:" in out
