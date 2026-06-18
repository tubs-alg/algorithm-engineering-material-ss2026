import copy

import pytest

from queens import verify


def test_verify_valid():
    verify.verify_assignment(
        4,
        [
            [False, True, False, False],
            [False, False, False, True],
            [True, False, False, False],
            [False, False, True, False],
        ],
    )


def test_verify_all_flips_invalid():
    base = [
        [False, True, False, False],
        [False, False, False, True],
        [True, False, False, False],
        [False, False, True, False],
    ]
    for flip_row in range(4):
        for flip_col in range(4):
            assignment = copy.deepcopy(base)
            assignment[flip_row][flip_col] = not assignment[flip_row][flip_col]
            with pytest.raises(ValueError):
                verify.verify_assignment(4, assignment)


def test_verify_all3_invalid():
    for x in range(2**9):
        assignment = [[False] * 3 for _ in range(3)]
        for i in range(3):
            for j in range(3):
                if x & (1 << (i * 3 + j)):
                    assignment[i][j] = True
        with pytest.raises(ValueError):
            verify.verify_assignment(3, assignment)
