import retrive
import datetime
import asyncio



class Train: # holds train info
    def __init__(self, serviceUid):
        self.serviceUid = serviceUid
        self.current_position = None
        self.positions = [] #list of coordinates along the stretch of track the train is currently on
        self.next_station_time = None
        self.last_station_time = None
        self.info = { #shown on the info page
            'trainIdentity' : None,
            'atocCode' : None,
            'origin' : None,
            'destination' : None,
            'delay' : None
        }

    async def update_info(self): #calle when train info shown
        new_stuffs = await retrive.fetch_service_info(self.serviceUid)
        delay = await retrive.get_service_delay(self.serviceUid) #update info
        if new_stuffs:
            try:
                self.info = { # the list of info displayed when a train is clicked
                'trainIdentity' : new_stuffs[0],
                'atocCode' : new_stuffs[1],
                'origin' : new_stuffs[2],
                'destination' : new_stuffs[3],
                'delay' : delay
                }
                return
            except:
                pass
        asyncio.sleep(3)
        self.update_info()

    async def update_position(self): # should be called every now and then, ideally at least once per minute
        if self.current_position == None or self.positions == None or self.last_station_time == None or self.next_station_time == None or datetime.datetime.now().strftime('%H%M') >= self.next_station_time: #if missing any data or previous stretch passed
            new_stuffs = await TrainFinder.find_new_train_position(self.serviceUid)
            if new_stuffs == None:
                return None
            self.current_position, self.positions, self.last_station_time, self.next_station_time = await TrainFinder.find_new_train_position(self.serviceUid)
            return self.current_position
        else:
            self.current_position = self.positions[int((int(datetime.datetime.now().strftime('%H%M')) - int(self.last_station_time)) / (int(self.next_station_time) - int(self.last_station_time) * len(self.positions)))]
            return self.current_position
    
    async def get_position(self):
        return self.current_position
    
    async def set_position(self, position):
        self.current_position = position
        #print('Position set to', position)
    
    





class TrainFinder: # finds trains
    def __init__(self):
        self._checked_stations = []
        self._unchecked_stations = []

    async def find_new_train_position(train, date=datetime.datetime.now()): #finds the position of a train, returns current position, list of positions on current line, time left last station, time of arrival at next station
        stations = await retrive.fetch_service(train, date.date()) # list of stations the service stops at
        last = None
        next = None
        for i in range(len(stations)-1):
            last_station = stations[i]
            next_station = stations[i+1]
            if next_station[1] >= date.strftime('%H%M'): # if not passed the next station, so we're between last_station and next_station
                last = last_station[0]
                next = next_station[0]
                last_time = last_station[2] #departure time of last station
                next_time = next_station[1] #arrival time at next station
                break
        if last == None or next == None:
            #print('Train not found')
            return None
        if last_time == 'N/A' or next_time == 'N/A':
            positions = await retrive.get_rail_line(last, next)
            #print('Train times not found')
            return positions
        positions = await retrive.get_rail_line(last, next)
        if positions == None or len(positions) == 0:
            #print('Train positions not found')
            return None
        time_between = int(next_time) - int(last_time)
        time_since = int(date.strftime('%H%M')) - int(last_time)
        if time_between == 0: #stops a division by 0 error
            distance = 0
        else:
            distance = time_since / time_between # a ratio for how far along the train is
        if distance < 0:
            distance = 0
        return positions[int(distance*(len(positions)-1)//1)], positions, last_time, next_time
    
    async def find_new_trains(self, already_found_trains, stations, size): #finds new trains by searching the departure board of a list of stations
        print("finding")
        try:
            trains = []
            for station in stations: # goes through every station
                services = await retrive.fetch_board(station)
                print(services)
                for service in services:
                    if service[0] not in already_found_trains: # adds every tain we don't already habe
                        trains.append(Train(service[0]))
            #print(len(trains), "found")
            return trains
        except Exception as e:
            print(e) #prints the error
            return None
    
    async def find_new_trains_in_box(self, top_y, left_x, bottom_y, right_x, already_found_trains): # as it says
        timescale = 30
        in_box = []
        stations = await retrive.get_stations_in_box(top_y, left_x, bottom_y, right_x)
        unchecked_stations = [station for station in stations if station not in self._checked_stations and station != None]
        self._unchecked_stations.extend(unchecked_stations)
        if len(self._unchecked_stations) < 20: # if not at least 20 trains, we recycle through the stations, as new trains may be departing
            self._unchecked_stations.extend(self._checked_stations)
            self._checked_stations = []
        tasks = []
        for station in self._unchecked_stations[:20]: #only do 20 at a time
            tasks.append(retrive.fetch_board(station, time_limit=(datetime.datetime.now()+datetime.timedelta(minutes=timescale)).strftime('%H%M')))
        items = await asyncio.gather(*tasks) # quick corutine
        services = []
        for item in items:
            if item == None:
                continue
            services.extend(item)
        for service in services:
            if service[0] not in already_found_trains:
                in_box.append(Train(service[0]))
        self._checked_stations.extend(self._unchecked_stations[:50])
        self._unchecked_stations = self._unchecked_stations[50:]
        #print('Found', len(in_box), 'trains in box')
        return in_box

async def main(): # to test
    import asyncio
    pos = await TrainFinder.find_new_train_position('Y22711')
    trains = await TrainFinder.find_new_trains([], ['EXC'], 5)
    for train in trains:
        print(await train.update_position())

if __name__ == "__main__":
    asyncio.run(main())