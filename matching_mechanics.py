EMPTY = 0

def _check_horizontal_matches(matrix: list[list[str]]) -> list[tuple]:
    """ Given a 2D list, a list of tuple coordinates are returned, 
        with the tuple coordinates representing horizontal matches. """

    match_indices = []
    for current_row_index in range(len(matrix) - 1, 1, -1):
        i = 0
        while True: # while loop used instead of for loop to iterate through the row so the iteration variable (i) can be incremented inside the loop
            if i > len(matrix[current_row_index]) - 1: # index out of bounds of the list
                break
            current_jewel = matrix[current_row_index][i]  
            counter = 0 # used to determine the size of the horizontal match
            current_jewel_reference = i
            while True:
                if current_jewel_reference > len(matrix[current_row_index]) - 1 or current_jewel == EMPTY: # index out of bounds
                    break
                if matrix[current_row_index][current_jewel_reference] != current_jewel: # match streak broken
                    break
                counter += 1
                current_jewel_reference += 1
            if counter >= 3: # horizontal match must be at least 3 jewels long
                current_match_index = current_jewel_reference - counter
                i += counter # skip over the matched jewels so we don't double count them
                for horizontal_match in range(current_match_index, current_match_index + counter):
                    match_indices.append((current_row_index, horizontal_match))
            else:
                i += 1
            # skip over match for next iteration
        
    return match_indices
    

def _check_vertical_matches(matrix: list[list[str]]) -> list[tuple]:
    """ Given a 2D list, a list of tuple coordinates are returned, 
        with the tuple coordinates representing vertical matches. """

    match_indices = []
    for i in range(len(matrix) - 1, -1, -1):
        for j in range(len(matrix[i])):
            vertical_index_counter = i
            current_jewel = matrix[i][j]
            counter = 0 # to determine how long the match is
            while True:
                if vertical_index_counter < 0 or current_jewel == EMPTY: # first two rows (index 0 and 1) are hidden from user display
                    break
                if matrix[vertical_index_counter][j] != current_jewel: # match streak broken
                    break
                counter += 1
                vertical_index_counter -= 1
            if counter >= 3:
                for vertical_match_column_index in range(vertical_index_counter + counter, vertical_index_counter, -1):
                    match_indices.append((vertical_match_column_index, j))
        
    return match_indices
    
def _check_diagonal_matches(matrix: list[list[str]]) -> list[tuple]:
    """ Given a 2D list, a list of tuple coordinates are returned, 
        with the tuple coordinates representing diagonal matches. """

    match_indices = []
    for i in range(len(matrix) - 1, -1, -1):
        for j in range(len(matrix[i])):
            right_diagonal_matches = _scan_diagonal_direction(matrix, i, j, 'right') 
            for diagonal_match in right_diagonal_matches:
                if diagonal_match not in match_indices:
                    match_indices.append(diagonal_match)

            left_diagonal_matches = _scan_diagonal_direction(matrix, i, j, 'left')
            for diagonal_match in left_diagonal_matches:
                if diagonal_match not in match_indices:
                    match_indices.append(diagonal_match)
        
    return match_indices


def _scan_diagonal_direction(matrix: list[list[str]], current_row_index: int, current_column_index: int, direction: str):
    """ Given either a 'right' or 'left' direction, the function will scan for diagonal
        matches only in that direction (up, right, up, etc...) or (up, left, up, etc...)"""

    match_indices = []
    vertical_index_counter = current_row_index
    horizontal_index_counter = current_column_index
    horizontal_index_delta = 1 if direction == "right" else (-1 if direction == "left" else None)
    current_jewel = matrix[current_row_index][current_column_index]
    counter = 0 # to determine how long the match is
    while True:
        if vertical_index_counter < 0 \
            or horizontal_index_counter > len(matrix[current_row_index]) - 1 \
            or horizontal_index_counter < 0: # handle out of bounds indices
                break
        if matrix[vertical_index_counter][horizontal_index_counter] != current_jewel \
            or matrix[vertical_index_counter][horizontal_index_counter] == EMPTY: # match streak broken
            break

        counter += 1
        vertical_index_counter += -1
        horizontal_index_counter += horizontal_index_delta
    if counter >= 3:
        for delta in range(counter):
            new_point = (current_row_index - delta, current_column_index + (delta * horizontal_index_delta))
            match_indices.append(new_point)

    return match_indices
