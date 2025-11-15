from enum import Enum
from typing import List, Optional, Iterator
import json
import zlib
import base64

class DirectionType(Enum):
    RowDown = "Ю"          # вниз (y - 1)
    RowUp = "С"            # вверх (y + 1)
    RowLeft = "З"          # влево (x - 1)
    RowRight = "В"         # вправо (x + 1)
    DiagonalUpLeft = "СЗ"  # x - 1, y + 1
    DiagonalDownRight = "ЮВ" # x + 1, y - 1


class FarmCellType(Enum):
    Soil = 0
    Garden = 1
    Harvest = 2
    Greenhouse = 3
    Water = 4
    Barrier = 5
    Finish = 6


class FarmCell:
    def __init__(self, cell_type: int, has_robot: bool):
        self.has_robot = has_robot
        self.cell_type = FarmCellType(cell_type)
        self.x: int = 0
        self.y: int = 0

    def __repr__(self):
        return f"{'🤖' if self.has_robot else ' '}{self.cell_type}"


class FarmLabyrinth:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

        self.cells: List[List[FarmCell]] = [
            [FarmCell(0, False) for _ in range(width)]
            for _ in range(height)
        ]

    def _to_internal_y(self, y: int) -> int:
        return self.height - 1 - y

    def get_cell(self, x: int, y: int) -> Optional[FarmCell]:
        if 0 <= x < self.width and 0 <= y < self.height:
            iy = self._to_internal_y(y)
            return self.cells[iy][x]
        return None

    def initialize(self, cell_type: int):
        for y in range(self.height):
            for x in range(self.width):
                cell = self.cells[y][x]
                cell.cell_type = FarmCellType(cell_type)

        for y in range(self.height):
            for x in range(self.width):
                cell = self.cells[y][x]
                cell.x = x
                cell.y = self.height - 1 - y

    def place_cell(self, x: int, y: int, cell_type: int):
        if 0 <= x < self.width and 0 <= y < self.height:
            iy = self._to_internal_y(y)
            cell = self.cells[iy][x]
            cell.cell_type = FarmCellType(cell_type)
            cell.x = x
            cell.y = y
            return True
        return False

    def get_neighbor(self, current_cell: FarmCell, direction: str) -> Optional[FarmCell]:
        dx, dy = self._direction_to_delta(direction)
        nx = current_cell.x + dx
        ny = current_cell.y + dy
        return self.get_cell(nx, ny)


    def get_iterator(self) -> Iterator[FarmCell]:
        for y in range(self.height):
            row_index = self._to_internal_y(y)
            row = self.cells[row_index]

            if y % 2 == 0:
                for x in range(self.width):
                    yield row[x]
            else:
                for x in range(self.width - 1, -1, -1):
                    yield row[x]

    def _direction_to_delta(self, direction: str):
        if direction == DirectionType.RowUp.value:
            return (0, 1)
        if direction == DirectionType.RowDown.value:
            return (0, -1)
        if direction == DirectionType.RowLeft.value:
            return (-1, 0)
        if direction == DirectionType.RowRight.value:
            return (1, 0)
        if direction == DirectionType.DiagonalUpLeft.value:
            return (-1, 1)
        if direction == DirectionType.DiagonalDownRight.value:
            return (1, -1)
        return (0, 0)
    

class RobotFarmer:
    def __init__(self, labyrinth: FarmLabyrinth):
        self.labyrinth = labyrinth
        self.current_cell: Optional[FarmCell] = None

    def find_current_cell(self):
        for cell in self.labyrinth.get_iterator():
            if cell.has_robot:
                self.current_cell = cell
                return cell
        return None

    def _move(self, direction: str):
        if self.current_cell is None:
            self.find_current_cell()

        next_cell = self.labyrinth.get_neighbor(self.current_cell, direction)
        if not next_cell:
            return None

        if next_cell.cell_type in (FarmCellType.Water, FarmCellType.Barrier):
            return None

        self.current_cell.has_robot = False
        next_cell.has_robot = True
        self.current_cell = next_cell
        return next_cell

    def move_left(self):
        return self._move(DirectionType.RowLeft.value)

    def move_right(self):
        return self._move(DirectionType.RowRight.value)

    def move_up(self):
        return self._move(DirectionType.DiagonalUpLeft.value)

    def move_down(self):
        return self._move(DirectionType.DiagonalDownRight.value)

    def move_next_row(self):
        return self._move(DirectionType.RowUp.value)

    def move_previous_row(self):
        return self._move(DirectionType.RowDown.value)

    def action_garden(self):
        if self.current_cell.cell_type == FarmCellType.Garden:
            self.current_cell.cell_type = FarmCellType.Harvest
            return self.current_cell
        else:
            return None

    def action_soil(self):
        if self.current_cell.cell_type == FarmCellType.Soil:
            self.current_cell.cell_type = FarmCellType.Garden
            return self.current_cell
        else:
            return None

    def place(self, x: int, y: int) -> bool:
        cell = self.labyrinth.get_cell(x, y)
        if not cell:
            return False
        
        for row in self.labyrinth.cells:
            for c in row:
                c.has_robot = False

        cell.has_robot = True
        self.current_cell = cell
        return True
    
    def encode_state(self) -> str:
        data = {
            "width": self.labyrinth.width,
            "height": self.labyrinth.height,
            "cells": [[cell.cell_type.value for cell in row] for row in self.labyrinth.cells],
            "robot": {"x": self.current_cell.x, "y": self.current_cell.y}
        }

        json_bytes = json.dumps(data, separators=(',', ':')).encode('utf-8')
        compressed = zlib.compress(json_bytes)
        code = base64.urlsafe_b64encode(compressed).decode('utf-8')

        self._cells_backup = [[cell.cell_type for cell in row] for row in self.labyrinth.cells]
        self._robot_backup = {"x": self.current_cell.x, "y": self.current_cell.y}

        return code

    def decode_state(self, code: str):
        compressed = base64.urlsafe_b64decode(code.encode('utf-8'))
        json_bytes = zlib.decompress(compressed)
        data = json.loads(json_bytes)

        self.labyrinth.width = data["width"]
        self.labyrinth.height = data["height"]

        for y, row in enumerate(data["cells"]):
            for x, cell_type_value in enumerate(row):
                self.labyrinth.place_cell(x,self.labyrinth._to_internal_y(y),cell_type_value)

        self.place(data.get("robot").get("x"), data.get("robot").get("y"))
