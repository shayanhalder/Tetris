from game_mechanics import GameState
import game_mechanics
import pygame
import random
import asyncio

# Global game configuration constants
EMPTY = 0
_FRAME_RATE = 10

# field and grid fractional constants
_FIELD_ROWS = 13
_FIELD_COLUMNS = 6
_GRID_COLOR = (0, 0, 0) # grid is black
_LINE_WIDTH_PROPORTION = 0.0035 # lines inside the grid
_GRID_OUTLINE_PROPORTION = 0.004 # outline of the grid 
_FALLING_JEWEL_OUTLINE_PROPORTION = 0.0125 # falling jewels are not completely filled with their color 
# and have a "donut"-like outline to them
_CROSS_JEWEL_OUTLINE_PROPORTION = 0.0050 # matched jewels are indicated with an X displayed on them

# grid dimension proportion constants (fractional coordinates)
_GRID_X_START_POSITION = 0.25 # fractional coordinates, starts 1/4th of the display width
_GRID_Y_START_POSITION = 0.0125 # fractional coordinates, starts 1/80th of the display height
_GRID_WIDTH_PROPORTION = 0.5 # grid takes up half of the display width
_GRID_HEIGHT_PROPORTION = 0.975 # grid takes up 97.5% of the display height (leaves some space above and below)

# game over font
_FONT_SIZE = 0.10 # 3% of view width
_FROZEN_JEWEL_COLORS = { # colors for each jewel after they freeze
    "S": (245, 96, 66),
    "T": (66, 245, 233),
    "V": (245, 66, 227),
    "W": (66, 245, 170),
    "X": (245, 227, 66),
    "Y": (66, 75, 245),
    "Z": (245, 138, 66)
}

_LANDED_JEWEL_COLORS = { # colors for each jewel when they land (slightly faded)
    "S": (255, 162, 143),
    "T": (187, 252, 248),
    "V": (250, 145, 239),
    "W": (162, 252, 214),
    "X": (250, 242, 175),
    "Y": (139, 144, 247),
    "Z": (245, 185, 144)
}

def setup_field(window_dimensions: tuple[int, int]) -> GameState:
    """ Creates a GameState object using all of the user input 
        parameters (dimensions, initial state, etc..) 
        and returns the GameState object. """
    
    rows, columns = window_dimensions
    game_state = GameState((rows, columns))

    return game_state

def check_game_over(game_state: GameState) -> bool:
    """ If the game is over, it prints "GAME OVER" to the screen 
        and closes the program. """
    
    if game_state.game_over():
        print("GAME OVER")
        return True
    
    return False


class ColumnsGame:
    def __init__(self) -> None:
        """ Initialies attributes for the Columns Game State. """

        self._running = True
        self._game_over_displayed = False
        self._state = game_mechanics.GameState((_FIELD_ROWS, _FIELD_COLUMNS))
        self._faller_moving_right = False
        self._faller_moving_left = False
        self._faller_rotating = False
        self._faller_speeding_down = False

    def run(self) -> None:
        """ Executes the columns game in a separate window. """

        pygame.init()

        self._resize_surface((800, 800))
        clock = pygame.time.Clock()
        tick_counter = 0 # only tick the faller by default every second
        # when tick counter reaches the frame rate, then it ticks the faller by default and resets it to 0
        # this allows us to set a higher framerate so the response to user input on the display is quick,
        # while still maintaing a faller that ticks 1 per second by default. 
    
        # display grid/field and actively falling jewels
        while self._running:
            clock.tick(_FRAME_RATE)
            self._handle_faller_motion()
            tick_counter = self._default_faller_tick(tick_counter)
            if check_game_over(self._state):
                self._running = False
                self._game_over_displayed = True
                break
            self._redraw()
            tick_counter += 1
        
        game_over_clock = pygame.time.Clock()

        # display game over message
        while self._game_over_displayed: 
            game_over_clock.tick(_FRAME_RATE)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._game_over_displayed = False
                    break
                if event.type == pygame.VIDEORESIZE:
                    self._resize_surface(event.size)
            self._draw_game_over_message('GAME OVER', pygame.font.SysFont(None, int(_FONT_SIZE * pygame.display.get_surface().get_width())))
            pygame.display.flip()
            
        
        pygame.quit()


    def _handle_faller_motion(self) -> None:
        """ Handles all user input that changes and moves the faller. """
        try:
            self._handle_events()
            self._move_faller()
        except (game_mechanics.FallerAlreadyActiveError, game_mechanics.InvalidMoveError,
                game_mechanics.FallerNotActiveError):
            pass
    
    def _default_faller_tick(self, tick_counter: int) -> int:
        """ Ticks the faller by default every second based on the frame rate."""

        try: # tick the faller only when tick counter reaches frame rate so that it happens only once per second. 
            if tick_counter == _FRAME_RATE:  
                self._state.tick()
            elif tick_counter > _FRAME_RATE:
                tick_counter = 0 # reset tick counter once the faller is ticked so it happens every second
        except (game_mechanics.FallerNotActiveError):
            self._create_random_faller() # once a faller freezes, create a new random faller in a random column
        finally:
            return tick_counter # return tick counter so it can be updated in the run() method

    def _move_faller(self) -> None:
        """ Rotates, shifts, or ticks the faller depending on the game state.
            Allows player to hold down key and have the input effect repeatedly occur."""
        
        if self._faller_moving_right:
            self._state.shift_faller('right')
        if self._faller_moving_left:
            self._state.shift_faller('left')
        if self._faller_rotating:
            self._state.rotate_faller()
        if self._faller_speeding_down:
            self._state.tick()
    
    def _create_random_faller(self) -> None:
        """ Creates a faller with random jewels to be dropped in a random column. """

        new_column = None
        if self._all_columns_full(): # choose any random column for new faller if all columns are full
            new_column = random.randint(1, _FIELD_COLUMNS)
        else: # otherwise keep randomly choosing a column until you choose one that isn't full
            while True:
                new_column = random.randint(1, _FIELD_COLUMNS)
                if self._state._field[0][new_column - 1] != EMPTY: # subtract 1 from new_column to convert to index
                    continue # keep searching if the chosen column is full with frozen jewels
                break # exit once an empty column has been found 

        new_jewels = random.choices(list(_FROZEN_JEWEL_COLORS.keys()), k=3) # choose 3 random jewels
        self._state.create_faller(new_jewels, new_column)
    
    def _all_columns_full(self) -> bool:
        """ Scans top row of the field and returns True if 
            all of the columns are full, otherwise returns False. """
        
        for top_cell in self._state._field[2]: # index 2 because first two rows in ._field are hidden
            if top_cell == EMPTY:
                return False
        return True

    def _handle_events(self) -> None:
        """ Handles both user keydown and keyup events to move the faller. """

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
            if event.type == pygame.VIDEORESIZE:
                self._resize_surface(event.size)
            self._handle_keydown_input(event)
            self._handle_keyup_input(event)
    
    def _handle_keydown_input(self, event: pygame.event) -> None:
        """ Handles all user input for keydown events. """

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                self._faller_moving_right = True
            if event.key == pygame.K_LEFT:
                self._faller_moving_left = True
            if event.key == pygame.K_SPACE:
                self._faller_rotating = True
            if event.key == pygame.K_DOWN:
                self._faller_speeding_down = True
        if event.type == pygame.VIDEORESIZE:
            self._resize_surface(event.size)

    def _handle_keyup_input(self, event: pygame.event) -> None:
        """ Handles all user input for keyup events. """

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_RIGHT:
                self._faller_moving_right = False
            if event.key == pygame.K_LEFT:
                self._faller_moving_left = False
            if event.key == pygame.K_SPACE:
                self._faller_rotating = False
            if event.key == pygame.K_DOWN:
                self._faller_speeding_down = False


    def _redraw(self) -> None:
        """ Draws the current state of the field and faller to the screen. """ 

        surface, grid_x_pos, grid_y_pos, grid_width, grid_height = self._get_grid_dimensions()
        row_gap, column_gap = self._get_grid_gaps(grid_width, grid_height)
        line_width = _LINE_WIDTH_PROPORTION * surface.get_width() # width of lines inside the grid

        surface.fill(pygame.Color(255, 255, 255)) # fill background with white

        self._draw_grid(surface, grid_x_pos, grid_y_pos, grid_width, grid_height)
        self._draw_vertical_grid_lines(surface, grid_x_pos, grid_y_pos, grid_width, grid_height, column_gap, line_width)
        self._draw_horizontal_grid_lines(surface, grid_x_pos, grid_y_pos, grid_width, grid_height, row_gap, line_width)
        self._draw_jewels(surface, grid_x_pos, grid_y_pos, row_gap, column_gap, line_width)
        
        pygame.display.flip()


    def _draw_jewels(self, surface: pygame.Surface, grid_x_pos: float, grid_y_pos: float, row_gap: float,
                      column_gap: float, line_width: float) -> None:
        """ Draws all the jewels on the field display using the GameState field attribute. """
        
        visible_field = self._state._field[2:] # first two rows are "hidden" so they are not displayed
        current_y_pos = grid_y_pos # will increase to progress through rows

        for row_index in range(len(visible_field)):
            current_x_pos = grid_x_pos # will increase to progress through columns
            
            for column_index in range(len(visible_field[row_index])):
                current_jewel = visible_field[row_index][column_index]

                top_left_x_pos = current_x_pos + line_width
                top_left_y_pos = current_y_pos + line_width
                
                if current_jewel in _FROZEN_JEWEL_COLORS.keys():
                    current_jewel_color = _FROZEN_JEWEL_COLORS[current_jewel]
                    current_jewel_position = (top_left_x_pos, top_left_y_pos, column_gap - line_width + 1, 
                                             row_gap - line_width + 1)
                    
                    current_jewel_coordinates = [row_index + 2, column_index] # add 2 to i because 2 hidden rows 

                    self._draw_correct_jewel_type(surface, current_jewel_coordinates, current_jewel_position,
                                                  current_jewel_color, current_jewel, current_x_pos,
                                                  current_y_pos, column_gap, row_gap, top_left_x_pos, 
                                                  top_left_y_pos, line_width)
                current_x_pos += column_gap
            current_y_pos += row_gap

    def _draw_correct_jewel_type(self, surface: pygame.surface, current_jewel_coordinates: list[int, int],
                                 current_jewel_position: tuple, current_jewel_color: tuple,
                                 current_jewel: str, current_x_pos: int, current_y_pos: int,
                                 column_gap: int, row_gap: int, top_left_x_pos: int,
                                 top_left_y_pos: int, line_width: float) -> None:
        """ Draws the correct representation of a given jewel if it is in an active faller,
            currently landed, or frozen. """
        
        falling_jewel_outline = int(_FALLING_JEWEL_OUTLINE_PROPORTION * surface.get_width())
        cross_jewel_outline = int(_CROSS_JEWEL_OUTLINE_PROPORTION * surface.get_width())

        if self._state._faller != None \
            and current_jewel_coordinates in self._state._faller['positions'] \
            and not self._state._faller_landed: # draws a currently falling jewel 
                pygame.draw.rect(surface, current_jewel_color, current_jewel_position, width=falling_jewel_outline)
        elif self._state._faller != None \
            and current_jewel_coordinates in self._state._faller['positions'] \
            and self._state._faller_landed: 
                # draws a jewel that has landed (colors made faded to show it is not final)
                landed_color = _LANDED_JEWEL_COLORS[current_jewel]
                pygame.draw.rect(surface, landed_color, current_jewel_position)
        elif tuple(current_jewel_coordinates) in self._state._matches: 
            # draws X on matched jewels to indicate matching
            pygame.draw.rect(surface, current_jewel_color, current_jewel_position)
            bottom_right_x_pos = current_x_pos + column_gap - line_width + 1
            bottom_right_y_pos = current_y_pos + row_gap - line_width + 1
                        
            pygame.draw.line(surface, _GRID_COLOR, (top_left_x_pos, top_left_y_pos),
                                                    (bottom_right_x_pos,bottom_right_y_pos),
                                                    width=cross_jewel_outline)
            pygame.draw.line(surface, _GRID_COLOR, (top_left_x_pos, bottom_right_y_pos), 
                                                    (bottom_right_x_pos, top_left_y_pos),
                                                    width=cross_jewel_outline)
        else: # draws a normal frozen jewel (colors full saturated and not faded)
            pygame.draw.rect(surface, current_jewel_color, current_jewel_position)

    def _get_grid_dimensions(self) -> tuple[pygame.Surface, float, float, float, float]:
        """ Returns the display surface object and grid dimensions to be 
            used for drawing the grid. """
        
        surface = pygame.display.get_surface()
        window_width = surface.get_width()
        window_height = surface.get_height()  

        # use fractional constants to convert grid dimensions to pixels for the current display size

        # top left coordinates of the grid 
        grid_x_pos = window_width * _GRID_X_START_POSITION
        grid_y_pos = window_height * _GRID_Y_START_POSITION

        # width and height of grid 
        grid_width = window_width * _GRID_WIDTH_PROPORTION
        grid_height = window_height * _GRID_HEIGHT_PROPORTION

        return (surface, grid_x_pos, grid_y_pos, grid_width, grid_height)
    
    def _draw_grid(self, surface: pygame.Surface, grid_x_pos: float, grid_y_pos: float, 
                   grid_width: float, grid_height: float) -> None:
        
        """ Draws the outline of the field grid. """
        grid_outline_width = int(_GRID_OUTLINE_PROPORTION * surface.get_width())
        
        pygame.draw.rect(surface, _GRID_COLOR, (grid_x_pos, grid_y_pos, grid_width, grid_height), width=grid_outline_width)
    
    def _draw_vertical_grid_lines(self, surface: pygame.surface, grid_x_pos: float,
                                  grid_y_pos: float, grid_width: float, grid_height: float,
                                  column_gap: float, line_width: float) -> None:
        """ Draws vertical lines of the field grid. """

        for i in range(1, _FIELD_COLUMNS):
            position = (grid_x_pos + (i * column_gap), grid_y_pos, line_width, grid_height)
            pygame.draw.rect(surface, _GRID_COLOR, position)

    def _draw_horizontal_grid_lines(self, surface: pygame.surface, grid_x_pos: float,
                                    grid_y_pos: float, grid_width: float, grid_height: float,
                                    row_gap: float, line_width: float) -> None:
        """ Draws horizontal lines of the field grid. """

        for i in range(1, _FIELD_ROWS):
            position = (grid_x_pos, grid_y_pos + (i * row_gap), grid_width, line_width)
            pygame.draw.rect(surface, _GRID_COLOR, position)

    def _check_game_over(self) -> bool: 
        """ If the game is over, it prints "GAME OVER" to the screen 
        and closes the program. """
    
        if self._state.game_over():
            print("GAME OVER")
            self._running = False
            return True
        
        return False
    
    def _get_grid_gaps(self, grid_width: float, grid_height: float) -> tuple:
        """ Calculates and returns the gaps between each row and column 
            given the number of field rows and columns we want. """
        
        column_gap = (grid_width / _FIELD_COLUMNS)  
        row_gap = (grid_height / _FIELD_ROWS)

        return (row_gap, column_gap)
    
    def _draw_game_over_message(self, text: str, font: pygame.font.SysFont) -> None:
        surface = pygame.display.get_surface()
        text_image = font.render(text, True, _GRID_COLOR)
        surface.blit(text_image, (int(0.55 * surface.get_width() / 2), int(0.85 * surface.get_height() / 2)))

    def _resize_surface(self, new_size: tuple[int, int]) -> None:
        """ Resizes surface in response to user input. """

        pygame.display.set_mode(new_size, pygame.RESIZABLE)
    

async def main():
    game = ColumnsGame()
    game.run()
    await asyncio.sleep(0) 


asyncio.run(main())