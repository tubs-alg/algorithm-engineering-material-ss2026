def verify_assignment(n, assignment: list[list[bool]]):
    for row_index, row in enumerate(assignment):
        s = sum(row)
        if s != 1:
            raise ValueError(f"Row {row_index} has {s} queens, expected 1")

    for col_index in range(n):
        s = sum(assignment[row_index][col_index] for row_index in range(n))
        if s != 1:
            raise ValueError(f"Column {col_index} has {s} queens, expected 1")

    for row_index, row in enumerate(assignment):
        for col_index, cell in enumerate(row):
            if not cell:
                continue
            for direction in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                for step in range(1, n):
                    r = row_index + direction[0] * step
                    c = col_index + direction[1] * step
                    if r < 0 or r >= n or c < 0 or c >= n:
                        break
                    if assignment[r][c]:
                        raise ValueError(
                            f"Queens at ({row_index}, {col_index}) and ({r}, {c}) "
                            "are attacking each other diagonally"
                        )
