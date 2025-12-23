import pygame
from staticmethods import StaticMethods
import retrive
import aiohttp
import os
import asyncio
import trainfinder
from objects import *
from trainfinder import *
import routefinder
import datetime

def do_nothing(): #does nothing
    pass

class DisplayManager:
    def __init__(self):
        self._dragging = False
        self.x_off = 0 #the x offset, the amount of pixels to the left that cannot be seen
        self.y_off = 0 #the y offset, the amount of pixels on the map above the screen
        self.zoom = 0 #zoom, doubles each increment
        self._loaded_tiles = {} #self explanatory

    async def display(self, screen):# async display screen
        screen.fill((255,255,255))# fill with white to clear
        for (x,y), tile in self._loaded_tiles.items():# for location and tile in loaded tiles:
            screen.blit(tile, ((x * 512) + self.x_off, (y * 512) + self.y_off))# show tile
        #self.menu.draw()# draw
        return True
    
    async def fetch_tiles(self, screen): #finds tiles on screen and downloads the image
        x_range, y_range = StaticMethods().get_tile_range(screen.get_width(), screen.get_height(), self.x_off, self.y_off, self.zoom)# get x and y ranges
        tasks = []
        async with aiohttp.ClientSession() as session:
            for x in x_range:
                for y in y_range:
                    file =  f'rail_tiles/{self.zoom}/tile_{x}_{y}.png'
                    if not os.path.exists(file):
                        tasks.append(retrive.fetch_map(session, "standard", self.zoom, x, y))
            await asyncio.gather(*tasks) #gather so all done in parallel to save time
    
    async def load_tiles(self,screen): #finds tiles on screen and loads the image
        x_range, y_range = StaticMethods().get_tile_range(screen.get_width(), screen.get_height(), self.x_off, self.y_off, self.zoom)# get x and y ranges
        for x in x_range:
            for y in y_range:
                if (x,y) not in self._loaded_tiles:
                    try:
                        file =  f'rail_tiles/{self.zoom}/tile_{x}_{y}.png'
                        self._loaded_tiles[(x, y)] = pygame.image.load(file)# add to leaded tiles
                    except Exception as e:
                        print(e)


    async def refresh(self, screen): #should be called every time the map veiw changes
        await self.fetch_tiles(screen)
        await self.load_tiles(screen)
    
    def handle_click(self, event):
        self._dragging = True #start dragging
        return do_nothing

    def handle_up(self, event):
        self._dragging = False #stop dragging
        return do_nothing

    def handle_drag(self, event):# handle motion
        if self._dragging:# if dragging, change offset
            self.x_off += event.rel[0]
            self.y_off += event.rel[1]
        
        return do_nothing

    def handle_key(self, event):
        try:
            match event.key:
                case pygame.K_z: #zoom in on z
                    self.zoom_to(self.zoom + 1, pygame.mouse.get_pos())
                case pygame.K_x: #zoom out if x
                    self.zoom_to(self.zoom - 1, pygame.mouse.get_pos())
                case _:
                    pass
        except:
            print("Error")

    def zoom_to(self, zoom, x_y):
        if zoom < 0 or zoom > 19:
            return
        x, y = x_y
        self.x_off = (self.x_off - x) * (2 ** (zoom - self.zoom)) + x # change offsets, should keep this point in the same position on screen
        self.y_off = (self.y_off - y) * (2 ** (zoom - self.zoom)) + y
        self.zoom = zoom # change zoom
        self._loaded_tiles.clear()# clear tiles
        
class TrainManager:
    def __init__(self):
        self.trains = [] #every train stored
        self.train_buttons = [] #every cutton (all the trains that have been loaded and can be displayed)
        self.searching = True
        self.showing = True #if not, 1 or 0 trains shown
        self.followed_train = None #the train shown if not self.showing
        self._tf = trainfinder.TrainFinder() #how we find trains

    async def search(self, display, screen):
        while self.searching: # the loop that looks for all the trains
            top, left = StaticMethods().get_latlon_from_xy(display.zoom, display.x_off, display.y_off)
            bottom, right = StaticMethods().get_latlon_from_xy(display.zoom, display.x_off + screen.get_width(), display.y_off + screen.get_height())
            new_trains = await self._tf.find_new_trains_in_box(top, left, bottom, right, [train.serviceUid for train in self.trains])
            if new_trains is not None and self.searching:
                self.trains.extend(new_trains)
            await asyncio.sleep(0) #I believe this helps with task allocation? so asyncio goes and does other stuff for a bit

    async def search_but_from_one_station(self, CRS):
        asyncio.wait(10)
        self.trains.clear()
        self.train_buttons.clear()
        while not self.searching:
            new_trains = await self._tf.find_new_trains([train.serviceUid for train in self.trains], [CRS], 16) #(16 not currently used, but will be the number of trains in future implimentations)
            if new_trains is not None:
                self.trains.extend(new_trains)
            break
            await asyncio.sleep(0)
                

    def show(self, screen): #draws the trains
        if self.showing:
            for button in self.train_buttons:
                button.show(screen)
        else:
            if self.followed_train is not None:
                for button in self.train_buttons:
                    if button.train == self.followed_train:
                        button.show(screen)
                        break

    def handle(self, event): #checks if a train has been clicked and handles it
        #print("handling")
        for button in self.train_buttons:
            if button.clicked(event):
                try:
                    self.followed_train = button.train
                except:
                    print("error")
                print(button)
                self.showing = not self.showing
                if not self.showing:
                    return button.x, button.y, button.train
        return None
    
    async def update_train_positions(self): #goes through every train (in batches of 100) and makes sure the position stored is up to date
        while True:
            try:
                for i in range(len(self.trains)//100+1): #batches of 100
                    tasks = []
                    for j in range(100): 
                        if i*100+j < len(self.trains):
                            tasks.append(self.trains[i*100+j].update_position())
                    await asyncio.gather(*tasks)
                await asyncio.sleep(0)
            except:
                pass

    async def render(self, display): #finds trains that we have the position of, and turns them into buttons
        if self.showing:
            tasks = []
            for train in self.trains:
                if train.current_position is not None:
                    tasks.append(self.new_train_button(train, display))
            return tasks
        elif self.followed_train is not None:
            return [self.new_train_button(self.followed_train,display)]
        else:
            return None

    async def new_train_button(self, train, display):#makes a train into the button
        try:
            lat, long = train.current_position
            x, y = StaticMethods().get_xy_from_latlong(display.zoom, lat, long)
            x += display.x_off
            y += display.y_off
            butt = TrainButton(x,y, 2*(1.3**display.zoom), train)
            self.train_buttons.append(butt)
        except:
            pass

class EventManager:
    def __init__(self):
        pass

    async def handle(self, event, display, train, menu, screen):
        match event.type: #big switch statement to check what the event is
            case pygame.QUIT:
                return pygame.quit() #exits program
            case pygame.MOUSEMOTION:
                return display.handle_drag(event) #this draggs if we are dragging
            case pygame.MOUSEBUTTONDOWN:
                if event.pos[0] < screen.get_width()//4: # if menu clicked
                    e = menu.handle(event)
                    #print(e)
                    match e: #switch depending on what button was presses
                        case "Back": #should return either home or to the last screen
                            if menu.current_screen == menu.searching and menu.tables[0].displayed_data != menu.tables[0].data: #if viewing a route, go back to viewing all routes
                                menu.tables[0].displayed_data = menu.tables[0].data
                            elif menu.current_screen == menu.train_info:
                                train.showing = True
                                menu.home()
                            elif menu.current_screen == menu.filter_trains: #if viewing a train, stop viewing just that train on the map
                                train.searching = True
                                train.showing = True
                                asyncio.create_task(train.search(display, screen))
                                menu.home()
                            else:
                                menu.home() #go to the home menu
                        case "Find Route":
                            menu.find_route() #find route menu
                        case "Refresh": #not implimented in final, good for debugging
                            train.searching = False
                            train.showing = True
                            train.trains.clear()
                            train.train_buttons.clear()
                            train.followed_train = None
                            await asyncio.sleep(3)
                            train.searching = True
                            asyncio.create_task(train.search(display, screen))

                        case "Search bfs (fast)": #search using bfs, called from searching menu
                            try:
                                await menu.searching(menu.input_boxes[0].writtenText, menu.input_boxes[1].writtenText, "bfs")
                            except Exception as e: #in case of issues with input sanitisation
                                print(e)
                                menu.find_route()

                        case "Search raptor (best)": #search using raptor, called from the searching menu
                            try:
                                await menu.searching(menu.input_boxes[0].writtenText, menu.input_boxes[1].writtenText, "raptor")
                            except Exception as e:#in case of issues with input sanitisation
                                print(e)
                                menu.find_route()

                        case "Filter Trains":
                            #opens filter train menu
                            menu.filter_trains()

                        case "Find Train(s)": #finds train/s, called within the fiter trains meu
                            if await retrive.get_trainline_id(menu.input_boxes[0].writtenText.upper()): #if a station
                                train.showing = True
                                train.searching = False
                                asyncio.create_task(train.search_but_from_one_station(menu.input_boxes[0].writtenText.upper()))
                            else: #if not a station
                                try:
                                    if await retrive.fetch_service(menu.input_boxes[0].writtenText.upper()) is not None: #if a service
                                        train.showing = False
                                        train.searching = True
                                        t = Train(menu.input_boxes[0].writtenText.upper())
                                        train.trains.append(t)
                                        train.followed_train = t
                                        await t.update_position()
                                        asyncio.create_task(train.update_train_positions())
                                        asyncio.create_task(menu.train_info(t))
                                except: #in case of bad input
                                    pass
                        case _:
                            pass
                else: #if map clicked
                    display.handle_click(event)#starts dragging
                    t_x, t_y, t_clicked = train.handle(event) #checks if a train is clicked
                    if t_clicked is not None:
                        #print("clicked train")
                        display.zoom_to(9, (t_x,t_y)) #zooms in on train (train not mouse as that doesn't work from too far out)
                        asyncio.create_task(menu.train_info(t_clicked)) #shows train details
                return True
            case pygame.MOUSEBUTTONUP:
                return display.handle_up(event) #stops dragging
            case pygame.KEYDOWN:
                if menu.handle_key(event): #if typing in a box
                    return True
                '''
                elif event.key == pygame.K_r: # test key, refreshes trains and searches
                    train.searching = False
                    train.showing = False
                    train.trains.clear()
                    train.train_buttons.clear()
                    train.followed_train = None
                    await asyncio.sleep(5)
                    train.searching = True
                    train.showing = True
                    asyncio.create_task(train.search(display, screen))
                    asyncio.create_task(train.update_train_positions())
                elif event.key == pygame.K_p: # test key, spawns 10000 trains
                    import random
                    train.searching = False
                    train.showing = True
                    for i in range(10000):
                        train.trains.append(Train(i))
                        for train_temp in train.trains:
                            train_temp.current_position = (round(random.uniform(-5, 1.1), 5), round(random.uniform(50, 58), 5))
                '''
                return display.handle_key(event)#if not typing, check if zooming
            case _:
                return do_nothing
            
class Menu:
    def __init__(self, screen):
        self.surface = pygame.Surface((screen.get_width()//4, screen.get_height())) #left quater of screen
        self.width = screen.get_width()//4
        self.height = screen.get_height()
        self.surface.fill((150,150,150)) #make gray
        self.buttons = []
        self.input_boxes = []
        self.tables = []
        self.current_screen = self.home


    def draw(self, screen): #draws everything
        screen.blit(self.surface,(0,0)) #draws a background to clear the previous
        for button in self.buttons: #every button
            button.show(screen)
        for box in self.input_boxes: #every input box
            box.show(screen)
        for table in self.tables: #and every table (should only be one at a time, but this makes it future-proof)
            table.show(screen)

    def handle(self, event): #handles the inputs
        for box in self.input_boxes:
            if box.clicked(event): #if a box had been clicked, it will handle it'self within the clicked function
                return True
            box.typing = False #if the box wasn't clicked, we shouldn't be tryping
        for button in self.buttons:
            if button.clicked(event):
                return button.text #for the switch statement in event manager
        for table in self.tables:
            table.clicked(event)

    def handle_key(self,event):
        for box in self.input_boxes: #if typing, type
            if box.is_active():
                box.take_input(event)
                return True
            
    def home(self): #home menu
        self.current_screen = self.home
        self.buttons.clear() #empty menu
        self.input_boxes.clear()
        self.tables.clear()
        self.buttons.append(MenuButton(10,10,self.width-20, self.height//10-10, "Find Route")) #for the find route menu
        self.buttons.append(MenuButton(10,self.height//10+10,self.width-20, self.height//10-10, "Filter Trains")) #for the filter train menu

    def filter_trains(self): #filter trains menu, lets you search for trains
        print("1")
        self.current_screen = self.filter_trains
        self.buttons.clear() #empty menu
        self.input_boxes.clear()
        self.tables.clear()
        print("2")
        self.buttons.append(MenuButton(10,10,self.width-20, self.height//10-10, "Back")) #to return home
        self.input_boxes.append(InputBox(10,self.height//10+10,self.width-20, self.height//10-10, "Station CRS or Train ID"))#function logic differentiates which
        self.buttons.append(MenuButton(10,2*self.height//10+10,self.width-20, self.height//10-10, "Find Train(s)"))#to
            
    def find_route(self): #find route menu, lets you find a route
        self.current_screen = self.find_route
        self.buttons.clear() #empty menu
        self.input_boxes.clear()
        self.tables.clear()
        self.buttons.append(MenuButton(10,10,self.width-20, self.height//10-10, "Back"))
        self.input_boxes.append(InputBox(10,self.height//10+10,self.width-20, self.height//10-10, "Start Station"))
        self.input_boxes.append(InputBox(10,2*self.height//10+10,self.width-20, self.height//10-10, "End Station"))
        self.buttons.append(MenuButton(10,3*self.height//10+10,self.width-20, self.height//10-10, "Search bfs (fast)"))
        self.buttons.append(MenuButton(10,4*self.height//10+10,self.width-20, self.height//10-10, "Search raptor (best)"))
    
    async def searching(self, start, end, type): #if finding route, display the routes
        self.buttons.clear() #empty menu
        self.input_boxes.clear()
        self.current_screen = self.searching
        if not await retrive.get_trainline_id(start.upper()) or not await retrive.get_trainline_id(end.upper()):
            self.find_route()
            return None
        self.buttons.append(MenuButton(10,10,self.width-20, self.height//10-10, "Back"))
        self.tables.append(RoutingTable(10, self.height//10+10, self.width-20, 9*self.height//10 - 20, "Leave/Arrive", []))
        if type == "bfs":
            asyncio.create_task(self.update_table_routes_bfs(start,end))
        else:
            asyncio.create_task(self.update_table_routes_raptor(start,end))

    async def train_info(self, train): #if looking at a train, display its details
        self.current_screen = self.train_info
        self.buttons.clear() #empty menu
        self.input_boxes.clear()
        self.tables.clear()
        self.buttons.append(MenuButton(10,10,self.width-20, self.height//10-10, "Back"))
        await train.update_info()
        self.tables.append(Table(10, self.height//10+10, self.width-20, 9*self.height//10 - 20, f'service uid/{train.serviceUid}', [['train id',train.info['trainIdentity']], ['atocCode', train.info['atocCode']],['origin', train.info['origin']], ['destination', train.info['destination']], ['delay', train.info['delay']]]))

    async def update_table_routes_raptor(self,start,end): #the round-based algorithm
        async for path in routefinder.RouteFinder().find_route_RAPTOR(start.upper(),end.upper(), datetime.datetime.now().strftime('%H%M')):
            self.tables[0].data.append(path)

    async def update_table_routes_bfs(self,start,end): #the quick algorithm
        async for path in routefinder.RouteFinder().find_route_bfs(start.upper(),end.upper(), datetime.datetime.now().strftime('%H%M')):
            self.tables[0].data.append(path)

        

