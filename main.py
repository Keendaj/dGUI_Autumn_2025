from enum import Enum
from typing import List, Optional, Iterator

class DirectionType(Enum):
    RowDown = "Ю"     # Вниз
    RowUp = "С"       # Вверх
    RowLeft = "З"      # Влево
    RowRight = "В"     # Вправо
    DiagonalUpLeft = "СЗ"
    DiagonalDownRight = "ЮВ"


class FarmCellType(Enum):
    Garden = "Грядка"
    Soil = "Почва"
    Harvest = "Урожай"
    Greenhouse = "Теплица" 
    Water = "Вода"
    Barrier = "Барьёр"
    Finish = "Финиш"

class FarmCell:
    def __init__(self, cell_type: str, has_robot: bool):
        self.has_robot: bool = has_robot
        self.cell_type: str = cell_type

    def __repr__(self):
        robot_mark = "🤖" if self.has_robot else " "
        return f"{robot_mark}{self.cell_type}"



class FarmLabyrinth:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.cells: List[List[FarmCell]] = [
            [
                FarmCell(None) for _ in range(width)
            ] for _ in range(height)
        ]

    def initialize(self, cell_type: str):
        for y, row in enumerate(self.cells):
            for x, cell in enumerate(row):
                cell.cell_type = cell_type
                cell.x = x
                cell.y = y

    def place_ceil(self, x: int, y: int, cell_type):
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return False

        self.cells[y][x].cell_type = cell_type
        self.cells[y][x].x = x
        self.cells[y][x].y = y
        return True
    
    def place_robot(self, x: int, y: int) -> bool: 
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return False
        for row in self.cells:
            for cell in row:
                cell.has_robot = False
        
        self.cells[y][x].has_robot = True
        return True

    def get_neighbor(self, current_cell: FarmCell, direction: str) -> Optional[FarmCell]:
        dx, dy = self._direction_to_delta(direction)
        nx, ny = current_cell.x + dx, current_cell.y + dy

        if 0 <= nx < self.width and 0 <= ny < self.height:
            return self.cells[ny][nx]
        return None

    def get_iterator(self) -> Iterator[FarmCell]:
        for y in range(self.height):
            if y % 2 == 0:
                for x in range(self.width):
                    yield self.cells[y][x]
            else:
                for x in range(self.width - 1, -1, -1):
                    yield self.cells[y][x]

    def _direction_to_delta(self, direction: str):
        if direction == DirectionType.RowDown.value:
            return (0, -1)
        if direction == DirectionType.RowUp.value:
            return (0, 1)
        if direction == DirectionType.RowLeft.value:
            return (-1, 0)
        if direction == DirectionType.RowRight.value:
            return (1, 0)
        if direction == DirectionType.DiagonalUpLeft.value:
            return (-1, 1)
        if direction == DirectionType.DiagonalDownRight.value:
            return (-1, 1)
        return (0, 0) #Никуда не идём, т.к. такого направления нет


class RobotFarmer:
    def __init__(self, labyrinth: FarmLabyrinth):
        self.labyrinth = labyrinth

    def find_current_cell(self) -> Optional[FarmCell]:
        for cell in self.labyrinth.get_iterator():
            if cell.has_robot:
                self.current_cell = cell
                return cell
        return None

    def _move(self, direction: str) -> Optional[FarmCell]:
        if self.current_cell is None:
            self.current_cell = self.find_current_cell()
            if self.current_cell is None:
                return None
        
        next_cell = self.labyrinth.get_neighbor(self.current_cell, direction)
        
        if next_cell is None:
            return None
        if next_cell.cell_type in (FarmCellType.Water.value, FarmCellType.Barrier.value):
            return None
    
        self.current_cell.has_robot = False
        next_cell.has_robot = True
        self.current_cell = next_cell
        return self.current_cell

    def move_left(self) -> Optional[FarmCell]:
        return self._move(DirectionType.RowDown.value)

    def move_right(self) -> Optional[FarmCell]:
        return self._move(DirectionType.RowUp.value)

    def move_up(self) -> Optional[FarmCell]:
        return self._move(DirectionType.DiagonalDownRight.value)

    def move_down(self) -> Optional[FarmCell]:
        return self._move(DirectionType.DiagonalDownRight.value)

    def move_next_row(self) -> Optional[FarmCell]:
        return self._move(DirectionType.RowRight.value)

    def move_previous_row(self) -> Optional[FarmCell]:
        return self._move(DirectionType.RowLeft.value)

    def action_garden(self):
        if self.current_cell.cell_type == FarmCellType.Garden.value:
            self.current_cell.cell_type = FarmCellType.Harvest.value

    def action_soil(self):
        if self.current_cell.cell_type == FarmCellType.Soil.value:
            self.current_cell.cell_type = FarmCellType.Garden.value

    def __run_full_cycle(self):
        for cell in self.labyrinth.get_iterator():
            if cell.cell_type in (FarmCellType.Water.value, FarmCellType.Barrier.value):
                continue

            self._move_to_cell(cell)

            if cell.cell_type == FarmCellType.Soil.value:
                self.action_soil()
                self.action_bed()
            elif cell.cell_type == FarmCellType.Bed.value:
                self.action_bed()