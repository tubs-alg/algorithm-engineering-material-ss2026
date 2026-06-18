import pytest

from queens.model_sat import NQueensSATModeler


def test_known_good_solution():
    modeler = NQueensSATModeler(4)
    formula = modeler.create_formula(break_symmetries=False)
    assignment = [
        [False, True, False, False],
        [False, False, False, True],
        [True, False, False, False],
        [False, False, True, False],
    ]
    encoded = modeler.encode_assignment(assignment)
    encoded = set(encoded)
    assert len(encoded) == 16
    for clause in formula.clauses:
        assert any(lit in encoded for lit in clause), (
            f"Clause {clause} is not satisfied by the assignment"
        )


def test_known_bad_solution():
    modeler = NQueensSATModeler(4)
    formula = modeler.create_formula(break_symmetries=False)
    assignment = [
        [False, True, False, False],
        [False, False, False, True],
        [True, False, False, False],
        [False, True, False, False],
    ]
    encoded = modeler.encode_assignment(assignment)
    encoded = set(encoded)
    assert len(encoded) == 16
    with pytest.raises(AssertionError):
        for clause in formula.clauses:
            assert any(lit in encoded for lit in clause), (
                f"Clause {clause} is not satisfied by the assignment"
            )
