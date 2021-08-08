import numpy as np
import cv2
import time
from Stimulator import Customer, mx
from a_star import find_path, Node
import random

NEW_CUSTOMERS_PER_MINUTE = 0.02 # lambda of poisson distribution
SIMULATE_MINUTES = 15*60  # one day

POSSIBLE_MOVES = [(0,1),(0,-1),(1,0),(-1,0)]

TILE_SIZE = 32
OFS = 50

MARKET = """
###################
##...............##
##B..#S..#D..#F..##
##B..#S..#D..#F..##
##B..#S..#D..#F..##
##B..#S..#D..#F..##
##B..#S..#D..#F..##
##...............##
##C..CC..CC..C#..##
##C..CC..CC..C#..##
##...............##
##G..G########G.G##
""".strip()

AISLE_POSITIONS = {
   'checkout': (3, 4, 8, 9),
   'drinks': (3, 4, 2, 6),
   'spices': (7, 8, 2, 6),
   'dairy': (11, 12, 2, 6),
   'fruit': (15, 16, 2, 6),
   'exit': (3, 4, 11, 11),
}
ENTRYX, ENTRYY = 15, 11

class SupermarketMap:
    """Visualizes the supermarket background"""

    def __init__(self, layout, tiles):
        """
        layout : a string with each character representing a tile
        tiles   : a numpy array containing all the tile images
        """
        self.tiles = tiles
        # split the layout string into a two dimensional matrix
        self.contents = [list(row) for row in layout.split("\n")]
        self.ncols = len(self.contents[0])
        self.nrows = len(self.contents)
        self.image = np.zeros(
            (self.nrows*TILE_SIZE, self.ncols*TILE_SIZE, 3), dtype=np.uint8
        )
        self.prepare_map()

    def extract_tile(self, row, col):
        """extract a tile array from the tiles image"""
        y = row*TILE_SIZE
        x = col*TILE_SIZE
        return self.tiles[y:y+TILE_SIZE, x:x+TILE_SIZE]

    def get_tile(self, char):
        """returns the array for a given tile character"""
        if char == "#":
            return self.extract_tile(2, 0)
        elif char == "C":
            return self.extract_tile(3, 8)
        elif char == "G":
            return self.extract_tile(7, 3)
        elif char == 'B':  #drinks
            return self.extract_tile(3,13)
        elif char == 'S':   #spices
            return self.extract_tile(2,3)
        elif char == "D":   #dairy
            return self.extract_tile(7,11)
        elif char == "F":   #fruit
            return self.extract_tile(1,5)      
        else:
            return self.extract_tile(1, 0)
    

    def prepare_map(self):
        """prepares the entire image as a big numpy array"""
        for y, line in enumerate(self.contents):
            for x, char in enumerate(line):
                bm = self.get_tile(char)
                self.image[
                    y * TILE_SIZE : (y + 1) * TILE_SIZE,
                    x * TILE_SIZE : (x + 1) * TILE_SIZE,
                ] = bm
    def prepare_grid(self):
        """returns binary array for the A*-algorithm"""
        grid = [[0 if c=='.' else 1 for c in row] for row in self.contents]
        return np.array(grid, dtype=np.uint8)

    def draw(self, frame):
        """
        draws the image into a frame and offsets from the corner
        """
        frame[OFS : OFS + self.image.shape[0], OFS : OFS + self.image.shape[1]] = self.image

    def write_image(self, filename):
        """writes the image into a file"""
        cv2.imwrite(filename, self.image)


class CustomerSprite:

   def __init__(self, customer, supermarket, image, col, row):
      """
      supermarket: A SuperMarketMap object
      image : a numpy array containing a 32x32 tile image
      row: the starting row
      col: the starting column
      """
      self.customer = customer

      self.supermarket = supermarket
      self.image = image
      self.row = row
      self.col = col
      self.path = []

   def __repr__(self):
        return f'Customer {self.customer.id} is in {self.customer.location}'
    
   def get_target_position(self, aisle):
        minx, maxx, miny, maxy = AISLE_POSITIONS[aisle]
        targetx = random.randint(minx, maxx)
        targety = random.randint(miny, maxy)
        return targety, targetx



   def set_new_path(self):
        """set path to next aisle of the customer"""
        self.customer.next_state()
        target = self.get_target_position(self.customer.location)
        # pick one of 3 checkouts
        if self.customer.location == 'checkout':
            target = target[0], target[1] + 4 * random.randint(0, 2)
        grid = self.supermarket.prepare_grid()
        target = target
        pos = (self.row, self.col)
        # add some waiting time
        wait = [pos] * 20
        self.path = wait + find_path(grid, pos, target, POSSIBLE_MOVES) 

   @property
   def active(self):
        return self.customer.location != 'exit' or len(self.path) >= 1

   def move(self):
        if self.path:
            self.row, self.col = self.path.pop(0)
        else:
            self.set_new_path()
   

   def draw(self, frame):
      col_pos = OFS+self.col * TILE_SIZE
      row_pos = OFS+self.row * TILE_SIZE
      frame[row_pos:row_pos+self.image.shape[0], col_pos:col_pos+self.image.shape[1]] = self.image

class SupermarketVisualization:
    """Simulates and visualizes multiple customers"""

    def __init__(self):
        self.customers = []
        self.last_id = 0
        self.minutes = 0

    def __repr__(self):
    
        return f"{self.get_time}"
    @property

    def get_time(self):
        hour = 7 + self.minutes // 60
        min = self.minutes % 60
        return f"{hour:02}:{min:02}:00"

    def move(self):
        """move each customer"""
        self.minutes += 1
        for c in self.customers:
            c.move()
            self.print_row(c)

    def draw(self, frame):
        for c in self.customers:
            c.draw(frame)

    def add_new_customers(self):
        """new customers randomly enter the shop"""
        n = np.random.poisson(NEW_CUSTOMERS_PER_MINUTE)
        for i in range(n):
            # uses composition
            self.last_id += 1
            c = Customer(self.last_id)
            cs = CustomerSprite(c, supermarket, pac, ENTRYX, ENTRYY)
            self.customers.append(cs)
            self.print_row(cs)

    def remove_exited_customers(self):
        """removes customers that are done shopping"""
        self.customers = [c for c in self.customers if c.active]
    
    def print_row(self, customer):
        """prints one row """
        row = str(self) + ", " + str(customer)
        print(row)


if __name__ == "__main__":

    background = np.zeros((500, 700, 3), np.uint8)
    tiles = cv2.imread('tiles.png')
    pac = tiles[7*32:8*32, 32:64, :]
    

    supermarket = SupermarketMap(MARKET, tiles)  # supermarket background
    s = SupermarketVisualization()  #instanciate visualization class


    for i in range(SIMULATE_MINUTES):
        frame = background.copy()  # black frame
        supermarket.draw(frame)   #draws image into a frame
        s.move()  
        s.draw(frame)
        s.add_new_customers()
        s.remove_exited_customers()

        cv2.imshow('frame', frame)

        key = chr(cv2.waitKey(1) & 0xFF)
        if key == 'q':
            break

        time.sleep(0.05)

    cv2.destroyAllWindows()