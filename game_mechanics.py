from matching_mechanics import (_check_horizontal_matches, 
                               _check_vertical_matches, 
                               _check_diagonal_matches)

from game_mechanics_errors import (FallerAlreadyActiveError, FallerNotActiveError,
                                    InvalidFallerJewelNumbers, InvalidMoveError,
                                    InvalidColumnError)

EMPTY = 0 # represents an empty cell in the field

class GameState:
    def __init__(self, dimensions: tuple) -> None:
        """ Initializes GameState object with all required attributes. """

        self._rows, self._columns = dimensions
        self._field = self._initialize_field() # creates two "hidden" rows to help manage the new fallers offscreen
        self._faller = None # no faller in beginning by default
        self._faller_landed = False
        self._matches = [] # will contain tuples of coordinates representing locations of current matches
        self._match_found_previous_tick = False # matches found on one tick, then removed on the subsequent tick
        self._game_over = False 
    
    def rows(self) -> int:
        """ Returns number of visible rows in the field. """
        return self._rows
    
    def columns(self) -> int:
        """ Returns number of visible columns in the field. """
        return self._columns
    
    def last_row_index(self) -> int:
        """ Returns the index of the last row in the field. """
        return self._rows + 1
    
    def get_jewel(self, coordinates: tuple) -> str:
        """ Returns the jewel at the given coordinate-- returns 0 if empty. """

        row, column = coordinates
        return self._field[row - 1][column - 1]

    def fill_initial_field(self, jewels: list[list[str]]) -> None: 
        """ Given a 2D list of jewels from user input, the field is 
            filled with them and brings all floating jewels down. """

        self._load_initial_jewel_positions(jewels)
        self._bring_floating_jewels_down()
        self._update_new_matches() # check for any matches that occur by default 
                
    def tick(self) -> bool: 
        """  Moves active faller down if no collisions or matches to be cleared.
            Returns False if nothing on the field actually moved (matches cleared/collision detected)
            Returns True if there was visible movement on the field. """
        
        # only check for matches when no active faller
        # when a match is found, display the matches but don't delete immediately  
        
        if self._faller == None and not self._match_found_previous_tick:
            raise FallerNotActiveError() 
            # entering an empty line with no active faller and all frozen jewels is invalid move-- nothing changes
        elif self._faller == None and self._match_found_previous_tick: 
            # removes any matched jewels on the tick AFTER they are displayed, and bring floating jewels down
            self._clear_matched_jewels()
            self._bring_floating_jewels_down()
            self._update_new_matches() # check for any subsequent matches    

            # check for rare case where leftover faller jewel is still out of the field. 
            # check if any frozen jewels outside field
            if self._check_out_of_bounds_frozen_jewels():
                self._game_over = True
            return False   
        elif self._faller != None and self._collision_next_tick() and not self._faller_landed:
            # changes the faller to its landing state with bars | | (previously had brackets [ ])            
            self._move_faller_down()
            self._faller_landed = True
            return False 
        elif self._faller != None and self._faller_landed and len(self._matches) == 0:
            # freezes faller in its current position, removes the bars | |
            # check for any potential new matches upon being FROZEN

            new_matches_found = self._update_new_matches()
            if new_matches_found:
                self._faller = None # deactivates faller   
                self._faller_landed = False
                return False
            else:
                if self._check_out_of_bounds_faller():
                    self._game_over = True
                    
                self._faller = None # deactivates faller   
                self._faller_landed = False
                return False

        # if no collisions on next tick or matches to clear, then the faller is shifted down one row
        self._move_faller_down()
        return True
    
    def game_over(self) -> bool:
        """ Returns True if game is over (parts of faller frozen out of field)
            and False if game is still running.  """
        
        return self._game_over
               
    def create_faller(self, jewels: list, column: int) -> None:
        """ Creates a new faller given a list of jewels and the column
            where they should start falling. """
        
        if not self._require_valid_faller_conditions(jewels, column):
            return
        
        new_faller = dict()
        new_faller['jewels'] = jewels
        new_faller['positions'] = []

        # initialize coordinate positions for each of the jewels and update the field with those positions
        for i in range(len(jewels)):        
            new_faller['positions'].append([i, column - 1]) # subtract one from column to convert to list index
            self._field[i][column - 1] = jewels[i] # update field with the new faller jewel

        # handle case where newly created faller immediately lands 
        bottom_row = new_faller['positions'][-1][0]
        bottom_column = new_faller['positions'][-1][1]
        if self._field[bottom_row + 1][bottom_column] != EMPTY:
            self._faller_landed = True
            
        self._faller = new_faller

    
    def rotate_faller(self) -> dict:
        """ Rotates the jewels in the faller and returns the new faller. """
        
        if self._faller == None:
            raise FallerNotActiveError()
        
        faller_jewel_list = self._faller['jewels']
        rotated_jewel_list = faller_jewel_list[2:] + faller_jewel_list[:2] # shift last jewel to front

        # create new faller with the shifted jewels, but same positions 
        new_faller = dict()
        new_faller['jewels'] = rotated_jewel_list
        new_faller['positions'] = self._faller['positions']
        self._faller = new_faller 

        # update game state field to reflect the new faller's position
        for i in range(len(self._faller['positions'])):
            row = self._faller['positions'][i][0]
            column = self._faller['positions'][i][1]
            self._field[row][column] = self._faller['jewels'][i]

        return new_faller
    
    def shift_faller(self, direction: str) -> bool:
        """ Shifts currently active faller to either left or right.
            Returns True if successfully shifted in the given direction. """

        # make sure faller is shifted in the appropriate situation
        self._require_valid_shift_conditions(direction)
            
        # if no collision, then modify the faller AND the field
        for i in range(len(self._faller['positions'])):
            coords = self._faller['positions'][i]
            self._field[coords[0]][coords[1]] = EMPTY
            if direction == "left":
                self._faller['positions'][i] = [coords[0], coords[1] - 1]
                self._field[coords[0]][coords[1] - 1] = self._faller['jewels'][i]
            elif direction == "right":
                self._faller['positions'][i] = [coords[0], coords[1] + 1]
                self._field[coords[0]][coords[1] + 1] = self._faller['jewels'][i]
            
        # if shifting the faller causes it to be floating, take it out of its landing status (and vice versa)
        if self._faller_currently_floating():
            self._faller_landed = False
        else:
            self._faller_landed = True
        
        return True
    
    def coordinate_in_faller(self, coordinates: tuple) -> bool:
        """ Returns True if the given coordinate position on the field is 
            occupied by an active faller, otherwise returns False. """

        if self._faller != None: 
            if list(coordinates) in self._faller['positions']:
                return True
        
        return False
    
    # ------------------- Protected methods ----------------------- #
            
    def _check_out_of_bounds_faller(self) -> bool:
        """ Returns True if any part of the active faller is out of bounds of the field,
            returns false if otherwise. """

        if self._faller != None:
            for coord in self._faller['positions']:
                row_index = coord[0]
                if row_index <= 1: 
                    return True
                            
        return False
    
    def _check_out_of_bounds_frozen_jewels(self) -> bool:
        for row_index in range(0, 2):
            for column_index in range(len(self._field[0])):
                if self._field[row_index][column_index] != EMPTY:
                    return True
        
        return False

    def _update_new_matches(self) -> bool:
        """ Looks for new matches and updates the game state matches and field 
            attributes. Returns True if new matches found, otherwise returns False.  """
        
        new_matches = self._check_matches()
        self._matches = new_matches

        if len(self._matches) > 0: # if matches found, they are displayed on current tick and removed on next tick
            self._match_found_previous_tick = True
            return True
        else: 
            self._match_found_previous_tick = False
            return False

    def _check_matches(self) -> list[tuple]:
        """ Returns a list of tuple coordinates in the field containing all of the 
            matches in the current game state. Returns empty list if no matches. """

        current_matches = []

        horizontal_matches = _check_horizontal_matches(self._field)
        vertical_matches = _check_vertical_matches(self._field)
        diagonal_matches = _check_diagonal_matches(self._field)

        current_matches = list(set(horizontal_matches + vertical_matches + diagonal_matches))
        # remove duplicate coordinate pairs with set() function

        return current_matches

    def _faller_currently_floating(self) -> bool:
        """ Returns True if the active faller is currently floating 
            (no frozen jewels) directly below it, otherwise returns False. """

        bottom_row_index = self._faller['positions'][-1][0] # use lowest jewel to determine if floating
        faller_column_index = self._faller['positions'][-1][1]
        if bottom_row_index + 1 <= self.last_row_index() and \
            self._field[bottom_row_index + 1][faller_column_index] == EMPTY:
            return True
        return False
    
    def _collision_on_shift(self, coords: list, direction: str):
        """ Returns true if shifting in a given direction will result in a collision. """

        row, column = coords
        if direction == "left" and (column - 1 < 0 or self._field[row][column - 1] != EMPTY):
            return True
        elif direction == "right" and (column + 1 > self.columns() - 1 or self._field[row][column + 1] != EMPTY):
            return True
        
        return False

    def _move_faller_down(self):
        """ Moves currently active faller down one row. """

        top_jewel_row = self._faller['positions'][0][0] # row index of topmost jewel, will have to reset to EMPTY later
            
        for i in range(len(self._faller['positions'])):
            # update faller (make go down one square)
            self._faller['positions'][i][0] += 1
                
            row = self._faller['positions'][i][0]
            column = self._faller['positions'][i][1]

            # update field 
            self._field[row][column] = self._faller['jewels'][i]
        
        self._field[top_jewel_row][column] = EMPTY
    
    def _collision_next_tick(self):
        """ Check if the next tick will have a collision (either with bottom of field
            or with a frozen jewel) that will cause it to become in "landed" status. """

        bottom_jewel_coordinates = self._faller['positions'][-1]
        bottom_jewel_row, bottom_jewel_column = bottom_jewel_coordinates
        if not self._faller_landed:
            if bottom_jewel_row + 2 >= self._rows + 2: # check 2 indices ahead because landed status is right before they collide
                return True    
            elif self._field[bottom_jewel_row + 2][bottom_jewel_column] != EMPTY:
                return True
        
        return False

    def _clear_matched_jewels(self) -> None:
        """ Remove the matched jewels from the field (so they are no longer displayed)
            and reset the matches attribite. """

        for coord in self._matches:
            row, column = coord
            self._field[row][column] = EMPTY
        self._matches = []

    def _load_initial_jewel_positions(self, jewels: list[list[str]]) -> None:
        """ Load the field matrix with the user input of default jewels they 
            want to start with. """

        current_field_row = self.last_row_index()
        for i in range(len(jewels) - 1, -1, -1):
            for j in range(len(jewels[i])):
                if jewels[i][j] == " ": # check this
                    self._field[current_field_row][j] = EMPTY
                else:
                    self._field[current_field_row][j] = jewels[i][j]
            current_field_row -= 1

    def _bring_floating_jewels_down(self) -> None:
        """ Look for any floating jewels (jewels with empty spaces directly below them)
            and shift them down until there is no more empty space. """

        for i in range(len(self._field) - 1, -1, -1): # exclude two "hidden" rows at the top
            for j in range(len(self._field[i])):
                current_row = i
                while (self._field[current_row][j] != EMPTY and 
                       current_row < self.last_row_index() and 
                       self._field[current_row + 1][j] == EMPTY):
                    
                    self._field[current_row + 1][j] = self._field[current_row][j]
                    self._field[current_row][j] = EMPTY 
                    current_row += 1
                    
    def _initialize_field(self) -> list[list[str]]:
        """ Returns a 2D list representing the field with 
            2 default "hidden rows" for the fallers off-screen. """
        
        field = []
        for i in range(self._rows + 2): # start with two "hidden" rows to help manage the new fallers off-screen
            new_row = []
            for j in range(self._columns):
                new_row.append(EMPTY)

            field.append(new_row)
        
        return field

    def _require_valid_faller_conditions(self, jewels: list, column: int) -> bool:
        """ Makes sure that a new faller is being created in the appropriate 
            situation. Returns False is game is over from creation of faller, 
            or raises errors due to invalid moves. Returns True if valid conditions. """
        
        if len(self._matches) > 0: # cannot create a new faller while matching is occuring
            raise InvalidMoveError()
        elif column > self.columns() or column <= 0:
            raise InvalidColumnError()
        elif self._faller != None: # make sure no other fallers are active
            raise FallerAlreadyActiveError()
        elif len(jewels) != 3: # a faller can only consist of exactly 3 jewels
            raise InvalidFallerJewelNumbers()
        elif self._field[2][column - 1] != EMPTY: # user creates a faller in full column, causing game to end
            self._game_over = True
            return False
        
        return True

    def _require_valid_shift_conditions(self, direction: str) -> bool:
        """ Makes sure that the faller is being shifted left or right in the 
            appropriatae situation. Throws an error if not, and returns True
            if valid conditions have been met. """
        
        if self._faller == None:
            raise FallerNotActiveError()
        
        # invalid move if there is a collision 
        for coords in self._faller['positions']:
            shifted_position = coords
            if direction == "left" and self._collision_on_shift(shifted_position, "left"):
                raise InvalidMoveError()
            elif direction == "right" and self._collision_on_shift(shifted_position, "right"):
                raise InvalidMoveError()
            
        return True