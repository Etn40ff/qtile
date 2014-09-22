from base import Layout
from .. import utils

class _Tile(object):               
    def __init__(self, x0=0, y0=0, x1=0, y1=0, clients=[], dirty=True):            
        self.dirty = dirty
        self.x0 = x0                 
        self.y0 = y0                 
        self.x1 = x1                 
        self.y1 = y1                 
        self.clients = clients                       
        self.curr_pos = 0 if clients else None        
    
    def __repr__(self):
        return ("Tile in position %s containing %s clients"%((self.x0, self.y0,
            self.x1, self.y1),len(self.clients)))

    def __iter__(self):            
        return iter(self.clients)                    
                                   
    def add(self, client):         
        if self.curr_pos is not None:    
            self.curr_pos += 1
            self.clients.insert(self.curr_pos, client)
        else:                      
            self.clients.append(client)              
            self.curr_pos = 0       
                                   
    def remove(self, client):      
        if client in self.clients:                   
            pos = self.clients.index(client)         
            self.clients.remove(client)              
            if self.curr_pos >= pos:                  
                self.curr_pos -= 1                    
            if  self.curr_pos < 0:                    
                self.curr_pos = len(self.clients)-1 if self.clients else None
                              
    def next(self):                                                                                                                                                       
        if self.curr_pos is not None:     
            self.curr_pos = (self.curr_pos + 1) % len(self.clients)
                                   
    def previous(self):            
        if self.curr_pos is not None:     
            self.curr_pos = (self.curr_pos - 1) % len(self.clients)

    def current(self):
        if self.curr_pos is None:
            return None
        return self.clients[self.curr_pos]

    def previous(self):
        if self.curr_pos is not None:
            return self.clients[(self.curr_pos-1) % len(self.clients)]
        else:
            return None

class ManualTile(Layout):
    defaults = [
        ("border_focus", "#0000ff", "Border colour for the focused window."),
        ("border_normal", "#000000", "Border colour for un-focused winows."),
        ("border_width", 1, "Border width."),
        ("name", "manual_tile", "Name of this layout."),
        ("margin", 0, "Margin of the layout"),
    ]

    def __init__(self, tiles=[_Tile()], **config):
        Layout.__init__(self, **config)
        self.add_defaults(ManualTile.defaults)
        self.clients = []
        self.tiles = tiles
        self.focused = None
        self.focused_tile = 0

    def configure(self, client, screen):
        if self.clients and client in self.clients:
            tile = [ t for t in self.tiles if client in t ][0]
            if tile.current() == client:
                if tile.dirty:
                    other_tiles = [ t for t in self.tiles if t != tile ]
                    x0 = max([ t.x1 for t in other_tiles \
                            if t.x0 < tile.x0 and \
                            any([tile.y0 <= t.y0 <= tile.y1,
                                tile.y0 <= t.y1 <= tile.y1,
                                t.y0 <= tile.y0 and tile.y1 <= t.y1])\
                            ] + [screen.x])
                    x1 = min([ t.x0 for t in other_tiles \
                            if t.x0 > tile.x0 and \
                            any([tile.y0 <= t.y0 <= tile.y1,
                                tile.y0 <= t.y1 <= tile.y1,
                                t.y0 <= tile.y0 and tile.y1 <= t.y1])\
                            ] + [screen.width])
                    y0 = max([ t.y1 for t in other_tiles \
                            if t.y0 < tile.y0 and \
                            any([tile.x0 <= t.x0 <= tile.x1,
                                tile.x0 <= t.x1 <= tile.x1,
                                t.x0 <= tile.x0 and tile.x1 <= t.x1])\
                            ] + [screen.y])
                    y1 = min([ t.y0 for t in other_tiles \
                            if t.y0 > tile.y0 and \
                            any([tile.x0 <= t.x0 <= tile.x1,
                                tile.x0 <= t.x1 <= tile.x1,
                                t.x0 <= tile.x0 and tile.x1 <= t.x1])\
                            ] + [screen.height])
                    tile.x0 = x0
                    tile.y0 = y0
                    tile.x1 = x1
                    tile.y1 = y1
                    tile.dirty = False
                if client is self.focused:
                    bc = self.group.qtile.colorPixel(self.border_focus)
                else:
                    bc = self.group.qtile.colorPixel(self.border_normal)
                client.place(
                    tile.x0,
                    tile.y0,
                    tile.x1 - tile.x0 - self.border_width * 2,
                    tile.y1 - tile.y0 - self.border_width * 2,
                    self.border_width,
                    bc,
                    margin=self.margin,
                )
                client.unhide()
            else:
                client.hide()

    def add(self, client):
        self.clients.append(client)
        self.tiles[self.focused_tile].add(client)

    def remove(self, client):
        if client not in self.clients:
            return
        tile = [ t for t in self.tiles if client in t ][0]
        if self.focused is client:
            self.focused = tile.previous()
        tile.remove(client)
        self.clients.remove(client)
        if self.focused is None and self.clients:
            self.focused = self.clients[0]
            self.focused_tile = self.tiles.index([t for t in self.tiles if self.focused in t])
            self.tiles[self.focused_tile].curr_pos=self.tiles[self.focused_tile].index(self.focused)
        return self.focused

    def split_vertical(self):
        old_tile = self.tiles[self.focused_tile]
        right = old_tile.x1
        old_tile.x1 = old_tile.x0+int((right-old_tile.x0)/2)
        new_tile = _Tile(old_tile.x1,old_tile.y0,right,old_tile.y1,clients=[],dirty=False)
        index = self.tiles.index(old_tile)
        self.tiles.insert(index+1,new_tile)
        self.group.layoutAll(True)

    def split_horizontal(self):
        old_tile = self.tiles[self.focused_tile]
        left = old_tile.y1
        old_tile.y1 = old_tile.y0+int((left-old_tile.y0)/2)
        new_tile = _Tile(old_tile.x0,old_tile.y1,old_tile.x1,left,clients=[],dirty=False)
        index = self.tiles.index(old_tile)
        self.tiles.insert(index+1,new_tile)
        self.group.layoutAll(True)

    def join_vertical_right(self):
        current= self.tiles[self.focused_tile]
        to_join = [ t for t in self.tiles if t.x0 == current.x1 and \
                t.y0 == current.y0 and t.y1 == current.y1][0] or None
        if to_join:
            current.clients += to_join.clients
            current.x1 = to_join.x1
        self.tiles.remove(to_join)
        self.group.layoutAll(True)

    def join_horizontal_bottom(self):
        current= self.tiles[self.focused_tile]
        to_join = [ t for t in self.tiles if t.y0 == current.y1 and \
                t.x0 == current.x0 and t.x1 == current.x1][0] or None
        if to_join:
            current.clients += to_join.clients
            current.y1 = to_join.y1
        self.tiles.remove(to_join)
        self.group.layoutAll(True)

    def cmd_split_vertical(self):
        self.split_vertical()

    def cmd_split_horizontal(self):
        self.split_horizontal()

    def cmd_join_vertical_right(self):
        self.join_vertical_right()

    def cmd_join_horizontal_bottom(self):
        self.join_horizontal_bottom()

    def clone(self, group):
        c = Layout.clone(self, group)
        c.clients = []
        c.tiles = [_Tile()]
        return c

    def focus(self, client):
        self.focused = client

    def blur(self):
        self.focused = None

    def info(self):
        return dict(
            clients=[c.name for c in self.clients],
            tiles=[str(t) for t in self.tiles],
        )
    
    def circle_tiles(self):
        next_idx = (self.focused_tile + 1) % len(self.tiles)
        self.focused_tile = next_idx
        self.focused = self.tiles[self.focused_tile].current()
        self.group.layoutAll(True)

    def cmd_circle_tiles(self):
        self.circle_tiles()








    def up(self):
        if self.shift_windows:
            self.shift_up()
        else:
            self.shuffle(utils.shuffleUp)

    def down(self):
        if self.shift_windows:
            self.shift_down()
        else:
            self.shuffle(utils.shuffleDown)

    def shift_up(self):
        if self.clients:
            currentindex = self.clients.index(self.focused)
            nextindex = (currentindex + 1) % len(self.clients)
            self.shift(currentindex, nextindex)

    def shift_down(self):
        if self.clients:
            currentindex = self.clients.index(self.focused)
            previndex = (currentindex - 1) % len(self.clients)
            self.shift(currentindex, previndex)

    def focus_first(self):
        if self.clients:
            return self.clients[0]

    def focus_next(self, client):
        if client not in self.clients:
            return
        idx = self.clients.index(client)
        if len(self.clients) > idx + 1:
            return self.clients[idx + 1]

    def focus_last(self):
        if self.clients:
            return self.clients[-1]

    def focus_previous(self, client):
        if client not in self.clients:
            return
        idx = self.clients.index(client)
        if idx > 0:
            return self.clients[idx - 1]

    def shuffle(self, function):
        if self.clients:
            function(self.clients)
            self.group.layoutAll(True)


    def shift(self, idx1, idx2):
        if self.clients:
            self.clients[idx1], self.clients[idx2] = \
                self.clients[idx2], self.clients[idx1]
            self.group.layoutAll(True)


    def cmd_down(self):
        self.down()

    def cmd_up(self):
        self.up()

    def cmd_next(self):
        client = self.focus_next(self.focused) or self.focus_first()
        self.group.focus(client, False)

    def cmd_previous(self):
        client = self.focus_previous(self.focused) or self.focus_last()
        self.group.focus(client, False)

