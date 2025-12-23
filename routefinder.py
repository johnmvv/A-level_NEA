from retrive import fetch_board, fetch_service
import asyncio
import datetime
import heapq
from collections import defaultdict




class RouteFinder:
    def __init__(self):
        self._changers = ['ABD', 'ACR', 'AIG', 'AAP', 'ALT', 'APP', 'ACT', 'AHV', 'AFK', 'AVM', 'AYS', 'BAL', 'BAN', 'BKG', 'BNS', 'BTB', 'BAA', 'BRS', 'BTY', 'BIF', 'BRY', 'BSK', 'BTH', 'BAT', 'BCJ', 'BDM', 'BLG', 'BWK', 'BLY', 'BON', 'BDQ', 'BGN', 'BWG', 'BLN', 'BTN', 'BRI', 'BRX', 'BCU', 'BMS', 'BGV', 'BUR', 'CBG', 'CMD', 'CBE', 'CBW', 'CDF', 'CAR', 'CSR', 'CLC', 'CTN', 'CTM', 'CNM', 'CSH', 'CHD', 'CHM', 'CLJ', 'CPT', 'CLR', 'COL', 'COV', 'CRE', 'CDN', 'CYP', 'DAR', 'DFD', 'DMK', 'DBY', 'DID', 'DIS', 'DON', 'DOR', 'DVP', 'DUM', 'DEE', 'DHM', 'EAL', 'EBN', 'ESL', 'EDB', 'EFF', 'ELY', 'EPS', 'EVE', 'EXD', 'FKK', 'FNB', 'FAV', 'FEL', 'FPK', 'FTW', 'GTW', 'GLQ', 'GCR', 'GOD', 'GRA', 'GRV', 'GFD', 'GLD', 'HOH', 'HPL', 'HHE', 'HFD', 'HWY', 'HUD', 'HUL', 'IPS', 'KMK', 'LAN', 'LDS', 'LEI', 'LWS', 'LIC', 'LCN', 'LIV', 'LON', 'LBO', 'LTN', 'MAN', 'MBR', 'MKC', 'MTH', 'NCL', 'NMP', 'NRW', 'NOT', 'OXF', 'PYG', 'PNZ', 'PBO', 'PLY', 'PMS', 'PRE', 'RDG', 'RDH', 'RMD', 'RTR', 'RUG', 'SAL', 'SCA', 'SBY', 'SEV', 'SHF', 'SHR', 'SLO', 'SOU', 'SAC', 'STA', 'SVG', 'STG', 'SPT', 'SOT', 'SRA', 'SWA', 'SWI', 'TAU', 'TON', 'TOM', 'TRU', 'TWI', 'WKF', 'WSL', 'WAC', 'WRK', 'WRW', 'WFJ', 'WME', 'WGN', 'WIN', 'WOK', 'WOL', 'WOR', 'YRK'] #list of all change stations, sourced by scraping network rails blue pages

    
    async def h(self, crs, end):
        # check if a station is a 'junction', list sourced from blue pages
        if crs == end: # gotta make sure we don't accidently lose all the ones that go to the end
            return 1
        if crs in self._changers:
            return 1
        return 0



    async def get_nodes(self, node, date,end): # as named
        time = datetime.datetime(date.year, date.month, date.day, int(node[1][:2]), int(node[1][2:])) # convert time to datetime format
        services = await fetch_board(node[0])
        trains = []
        for service in services:
            if int(service[1]) > int(time.strftime('%H%M')) + 1: #if min 1 min later than arrival to station, giving time to change
                trains.append(service[0])
        nodes = []
        stops = []
        tasks = []
        for train in trains: 
            tasks.append(fetch_service(train, time)) #find the stops of each train
        items = await asyncio.gather(*tasks)
        for item in items:
            stops.extend(item)
        stops.sort(key=lambda x: x[1]) # sort by time
        visited = [node[0]]
        for stop in stops:
            if stop[2] > time.strftime('%H%M') and stop[0] not in visited and stop[1] != 'N/A' and await self.h(stop[0], end) == 1:
                nodes.append([stop[0], stop[1]])
                visited.append(stop[0])
        return nodes

    async def find_route_bfs(self, start, end, time): #a breadth first search, yeails the results as (begin time, end time, route)
        queue = [[[start, time]]]
        paths = []
        while queue: # while there are paths that are not complete
            print("finding route")
            path = queue.pop(0)
            node = path[-1]
            nodes = await self.get_nodes(node, datetime.datetime.today(), end)
            
            for n in nodes: #for every node, add a new path leading to that node
                new = list(path)
                new.append(n)
                queue.append(new)

            if end in [n[0] for n in nodes]: #if one path ends with end, yeild it
                new_node = [n for n in nodes if n[0] == end][0]
                path.append(new_node)
                yield [path[0][1], path[-1][1], path]

    def et(self, route, start, time): #earliest time, not an ideal implimentation as doesn't consider other trains along the same route, but not bad.
        for crs, arr, dep in route:
            if crs == start and dep >= time:
                return (crs, dep)
        return None
    
    def reconstruct(self, crs, previous, t_star): #reconstructs the path at the end of the search
        path = [((crs, t_star[crs]))]
        current = crs

        while current in previous:
            train, prev = previous[current]
            path.insert(0, (train, current))
            current = prev
        
        return path
    
    async def loop1(self, Q,stop): #middlemost loop, retrives a departure board, and then gathers loop2 as a task for each train
        departure_board = await fetch_board(stop)
        tasks = []
        for train_id, arr, dep, _ in departure_board:
            tasks.append(self.loop2(Q, train_id, arr, dep, stop))
        await asyncio.gather(*tasks)
        return None

    async def loop2(self, Q, train_id, arr, dep, stop): #innermost loop, finds the stop within the route and appends to the queue
        route = await fetch_service(train_id)
        for i, (stop_j, arr_j, dep_j) in enumerate(route):
            if stop_j == stop:
                heapq.heappush(Q, (i, route, stop)) # add route to Q
                break
        return None

    async def find_route_RAPTOR(self, start, end, start_time, max=8): #finds the route by a round-based search
        all_stops = self._changers.copy()
        all_stops.extend([start, end])
        t = defaultdict(lambda: float('inf'))
        t_star = defaultdict(lambda: float('inf')) #sets dictionarys with sefauls of inf
        previous = {}
        marked = set([start])
        t[start] = start_time
        t_star[start] = start_time
        previous_best = []
        current_best = []

        for k in range(max): #k is current round number, max is the maximum number of stops/maximum number of changes
            print(k)
            Q = []
            tasks = []
            for stop in marked:
                tasks.append(self.loop1(Q, stop))
            _ = await asyncio.gather(*tasks) #gathers the tasks as many api calls

            marked.clear()
            while Q: # until we have checked every route
                i, route, b_stop = heapq.heappop(Q)
                trip = None
                for j in range(i, len(route)):
                    stop_j, arr_j, dep_j = route[j]
                    if arr_j < start_time: # if time is next day, add 24 hours to reflect such
                        t_int = int(arr_j)
                        t_int += 2400
                        arr_j = str(t_int)
                    if trip and float(arr_j) < min(float(t_star[stop_j]), float(t_star[end])): #if before both our fastest tie to get to that stop, and our fastest time to get to the end
                        t[stop_j] = arr_j
                        t_star[stop_j] = arr_j
                        previous[stop_j] = (trip, b_stop)
                        marked.add(stop_j)
                    if t[b_stop] <= dep_j and not trip:
                        trip = self.et(route, b_stop, t[b_stop])
            current_best = self.reconstruct(end, previous, t_star) #reconstructs the best path with k changes
            print(current_best)
            if current_best != previous_best and len(current_best) > 1 and current_best[0][0][0] == start: #if route is valid, yield it
                print(current_best)
                yield [current_best[0][0][1], current_best[-1][1], current_best]
                previous_best = current_best
            if not marked:
                break

#print(asyncio.run(RouteFinder().find_route_RAPTOR("BRI", "EXC", datetime.datetime.now().strftime("%H%M"))))