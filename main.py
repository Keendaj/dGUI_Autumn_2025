from gui import *
from core import *

if __name__ == "__main__":
    root = tk.Tk()

    lab = FarmLabyrinth(width=10, height=10)

    lab.initialize(FarmCellType.Greenhouse)

    robot = RobotFarmer(lab)
    robot.place(0, 0)

    gui = FarmGUI(root, lab, robot)
    root.mainloop()