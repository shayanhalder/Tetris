class FallerAlreadyActiveError(Exception):
    """ Raised when user tries to create a new faller while one is already active and falling. """
    pass

class FallerNotActiveError(Exception):
    """Raised when user ticks the game but there is no active faller. """
    pass

class InvalidFallerJewelNumbers(Exception):
    """ Raised when more or less than 3 jewels are given to create a new faller. """
    pass

class InvalidMoveError(Exception):
    """ Raised when user makes invalid move (ex: shifting faller to a freezed jewel or outside the field)"""
    pass

class InvalidColumnError(Exception):
    """ Raised when user tries to create a faller in an out-of-bounds column. """
    pass