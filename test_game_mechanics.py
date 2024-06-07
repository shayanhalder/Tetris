import unittest
from game_mechanics import GameState
from game_mechanics_errors import (FallerAlreadyActiveError, FallerNotActiveError,
                                    InvalidFallerJewelNumbers, InvalidMoveError,
                                    InvalidColumnError)

class TestGameMechanics(unittest.TestCase):
    def setUp(self) -> None:
        self._test_game_state = GameState((5, 4))

    def setup_default_test_faller(self): 
        # separate method for setting up faller since some methods testing edge cases 
        # will want fallers in differnet positions with differnet jewels.
        # allows us to "opt-in" to using it unlike the setUp method which always runs
        
        self._test_game_state.create_faller(['X', 'Y', 'Z'], 2)
    
    def test_created_default_field_correctly(self):
        self.setup_default_test_faller()
        self.assertEqual(self._test_game_state._field, 
                         [[0,"X",0,0],[0,"Y",0,0],[0,"Z",0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]]) 
        # added two more lists for the "hidden" rows at top for new fallers

    def test_created_empty_field_correctly(self):
        self.assertEqual(self._test_game_state._field, [[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]])
    
    def test_created_faller_correctly(self):
        self.setup_default_test_faller()
        self.assertEqual(self._test_game_state._faller, 
                         {'jewels': ["X", "Y", "Z"], "positions": [[0, 1], [1, 1], [2, 1]]})
        
        self._test_game_state._faller = None
        self._test_game_state.create_faller(['A', 'E', 'T'], 4)
        self.assertEqual(self._test_game_state._faller, {"jewels": ["A", "E", "T"], "positions": [[0, 3], [1, 3], [2, 3]]})

    def test_rotated_faller_correctly(self):
        self.setup_default_test_faller()
        self.assertEqual(self._test_game_state.rotate_faller(),
                         {"jewels": ["Z", "X", "Y"], "positions": [[0, 1], [1, 1], [2, 1]]})
        
    def test_moving_faller_down_a_row(self):
        self.setup_default_test_faller()
        self._test_game_state.tick()
        self.assertEqual(self._test_game_state._faller, 
                         {"jewels": ["X", "Y", "Z"], "positions": [[1, 1], [2, 1], [3, 1]]})
        
    def test_game_detects_downwards_landing_collision(self):
        self._test_game_state._field[3][1] = "A"
        self.setup_default_test_faller()
        self.assertEqual(self._test_game_state.tick(), False)

    def test_game_does_not_call_false_downwards_collision(self):
        self._test_game_state._field[4][2] = "A"
        self.setup_default_test_faller()
        self.assertEqual(self._test_game_state.tick(), True)

    def test_shift_faller_left(self):
        self.setup_default_test_faller()
        self.assertEqual(self._test_game_state.shift_faller("left"), True)
        self.assertEqual(self._test_game_state._faller['positions'][0], [0, 0])

    def test_shift_left_does_not_work_with_obstacle(self):
        self._test_game_state._field[2][0] = "A"
        self.setup_default_test_faller()
        self.assertRaises(InvalidMoveError, self._test_game_state.shift_faller, 'left')
    
    def test_shift_faller_right(self):
        self.setup_default_test_faller()
        self.assertEqual(self._test_game_state.shift_faller("right"), True)

    def test_shift_right_does_not_work_with_obstacle(self):
        self._test_game_state._field[2][2] = "A"
        self.setup_default_test_faller()
        self.assertRaises(InvalidMoveError, self._test_game_state.shift_faller, 'right')

    def test_multiple_horizontal_matches_recognized(self):
        # create 3 consecutive columns of the exact same faller
        # 9 cells in the field should be recognized as a match
        # 3 horizontal matches at the same time
        
        # bring first faller all the way down
        self.setup_default_test_faller()
        
        for i in range(5):
            self._test_game_state.tick()
        self._test_game_state.create_faller(["X", "Y", "Z"], 1)

        # bring second faller all the way down
        for i in range(5):
            self._test_game_state.tick()
        self._test_game_state.create_faller(["X", "Y", "Z"], 3)

        # bring third faller all the way down
        for i in range(5):
            self._test_game_state.tick()

        self.assertEqual(len(self._test_game_state._matches), 9) # matches recognized
    
    def test_vertical_matches_recognized(self):
        self._test_game_state.create_faller(['X', 'X', 'X'], 2) # override default faller for this test

        for i in range(5):
            self._test_game_state.tick()

        self.assertEqual(len(self._test_game_state._matches), 3) # matches recognized

    def test_matches_recognized_on_custom_field_creation(self):
        custom_field = [
            [ 0,   0,   0,   0],
            [ 0,   0,   0,   0],
            [ 0,   0,   0,   0],
            [ 0,   0,   0,  "X"],
            ["V",  0,  "X", "V"],
            ["T", "X", "T", "S"],
            ["X", "Y", "Y", "Y"],
        ]
        self._test_game_state.fill_initial_field(custom_field)
        self.assertEqual(len(self._test_game_state._matches), 7)          

    def test_faller_can_land_on_creation_of_custom_field(self):
        custom_field = [
            [ 0,   0,   0,   0],
            [ 0,   0,   0,   0],
            [ 0,   0,   0,   0],
            ["X",  0,   0,  "S"],
            ["V",  0,  "T", "V"],
            ["T", "S", "T", "S"],
            ["X", "Y", "V", "Y"],
        ]
        self._test_game_state.fill_initial_field(custom_field)
        self._test_game_state.create_faller(['X', 'X', 'Z'], 1)
        self.assertEqual(self._test_game_state._faller_landed, True)      

    def test_faller_throws_game_over_if_cannot_fit_in_column(self):
        custom_field = [
            [ 0,   0,   0,   0],
            [ 0,   0,   0,   0],
            ["Z",  0,   0,   0],
            ["X",  0,   0,  "S"],
            ["V",  0,  "T", "V"],
            ["T", "S", "T", "S"],
            ["X", "Y", "V", "Y"],
        ]
        self._test_game_state.fill_initial_field(custom_field)
        self._test_game_state.create_faller(['X', 'X', 'Z'], 1)
        self.assertEqual(self._test_game_state._game_over, True)
    
    def test_faller_saves_game_by_creating_match_on_full_column(self):
        custom_field = [
            [ 0,   0,   0,    0],
            [ 0,   0,   0,    0],
            [ 0,   0,   0,    0],
            ["X",  0,   0,   "S"],
            ["V",  0,  "T",  "V"],
            ["T", "S", "T",  "S"],
            ["X", "Y", "V",  "Y"],
        ]
        self._test_game_state.fill_initial_field(custom_field)
        self._test_game_state.create_faller(['X', 'X', 'X'], 1)
        self._test_game_state.tick()
        self.assertEqual(len(self._test_game_state._matches), 4)
        # make sure matches are removed after
        self._test_game_state.tick()
        self.assertEqual(len(self._test_game_state._matches), 0)
    
    def test_faller_saves_game_with_diagonal_match(self):
        custom_field = [ 
            [ 0,   0,   0,   0],
            [ 0,   0,   0,   0],
            [ 0,   0,  "Y",  0],
            ["X", "Y",  0,   0],
            ["V",  0,  "S", "V"],
            ["T", "S", "T", "S"],
            ["X", "Y", "V", "Y"],
        ]
        self._test_game_state.fill_initial_field(custom_field)
        self._test_game_state.create_faller(['Y', 'Y', 'Y'], 4)
        self._test_game_state.tick()
        self._test_game_state.tick()
        self.assertEqual(len(self._test_game_state._matches), 5) # test that diagonal and vertical matches are recognied

        # test that matches are removed after being displayed 
        self._test_game_state.tick()
        self.assertEqual(len(self._test_game_state._matches), 0)

    def test_multiple_matches_upon_creation_of_custom_field(self):
        # using sample output from project-write up
        self._test_game_state = GameState((4, 4)) # override default field dimensions for this test
        custom_field = [
            [ 0,   0,   0,   0],
            [ 0,   0,   0,   0],
            [ 0,   0,   0,   0],
            ["S",  0,  "V", "X"],
            ["T", "Y", "Y", "S"],
            ["X", "X", "X", "Y"],
        ]
        self._test_game_state.fill_initial_field(custom_field)
        self.assertEqual(len(self._test_game_state._matches), 3) # 3 horizontal matches for "X"
        self._test_game_state.tick()
        self.assertEqual(len(self._test_game_state._matches), 3) # 3 horizontal matches for "Y"
        self._test_game_state.tick()
        self.assertEqual(len(self._test_game_state._matches), 0) # no more matches after, should be 0

    def test_leftover_out_of_bounds_faller_jewels_cause_gameover(self):
        self._test_game_state = GameState((5, 4)) 
        custom_field = [ 
            [ 0,    0,   0,   0],
            [ 0,    0,   0,   0],
            [ 0,    0,   0,   0],
            [ 0,   "S", "Y",  0],
            ["S",  "T", "Z",  0],
            ["T",  "Y", "V", "S"],
            ["X",  "Y", "V", "Y"],
        ]
        self._test_game_state.fill_initial_field(custom_field)
        self._test_game_state.create_faller(['Y', 'X', 'S'], 3)
        self._test_game_state.tick()
        self.assertEqual(len(self._test_game_state._matches), 3) # test diagonal match recognized
        self._test_game_state.tick()
        # the leftover "Y" jewel from the faller is still not visible in the field, so the game should end
        self.assertEqual(self._test_game_state._game_over, True) 

    def test_inability_to_create_multiple_fallers(self):
        self.setup_default_test_faller()
        self.assertRaises(FallerAlreadyActiveError, self._test_game_state.create_faller, ['X', 'Y', 'Z'], 3)

    def test_inability_to_move_faller_when_no_fallers_active(self):
        # ticking when no faller is created should throw an error
        self.assertRaises(FallerNotActiveError, self._test_game_state.tick)

    def test_inability_to_create_out_of_bounds_faller(self):
        self.assertRaises(InvalidColumnError, self._test_game_state.create_faller, ['X', 'Y', 'Z'], 6)
        self.assertRaises(InvalidColumnError, self._test_game_state.create_faller, ['X', 'Y', 'Z'], 0)
        self.assertRaises(InvalidColumnError, self._test_game_state.create_faller, ['X', 'Y', 'Z'], -1)
    
    def test_fallers_can_only_have_exactly_three_jewels(self):
        self.assertRaises(InvalidFallerJewelNumbers, self._test_game_state.create_faller, ['X', 'Y', 'Z', 'S'], 3)
        self.assertRaises(InvalidFallerJewelNumbers, self._test_game_state.create_faller, ['X', 'Y'], 3)

    def test_identifying_coordinates_in_current_faller(self):
        self.setup_default_test_faller()
        self.assertEqual(self._test_game_state.coordinate_in_faller((0, 1)), True)
        self.assertEqual(self._test_game_state.coordinate_in_faller((1, 1)), True)
        self.assertEqual(self._test_game_state.coordinate_in_faller((2, 1)), True)

    def test_identifying_coordinates_outside_of_current_faller(self):
        self.setup_default_test_faller()
        self.assertEqual(self._test_game_state.coordinate_in_faller((0, 2)), False)
        self.assertEqual(self._test_game_state.coordinate_in_faller((1, 2)), False)
        self.assertEqual(self._test_game_state.coordinate_in_faller((2, 2)), False)

if __name__ == "__main__":
    unittest.main()


