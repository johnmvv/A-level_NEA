import asyncio
import aiohttp
import base64
import datetime
import os
import csv


class Retrive():
    @staticmethod # so doesn't need a self to reference
    async def fetch_board(crs, time=datetime.date.today(), time_limit=None, fails=0):
        '''
        inputs: CRS code for station, time of check (optional), time window (optional), fails (optional, used for recurtions)
        returns : list containng [[uid,bookeddeptime,realdeptime,tiploc],[]...]
        '''
        username = rttapi_username #has been ommited due to api agreements, but an eqivilant can be sorced from api.rtt.io
        password = rttapi_pw #has been ommited due to api agreements, but an eqivilant can be sorced from api.rtt.io
        board_base_url = "https://api.rtt.io/api/v1/json/search/"
        service_base_url = "https://api.rtt.io/api/v1/json/service/"
        auth = base64.b64encode(f"{username}:{password}".encode()).decode() # to get the header used for api calls
        
        url = f"{board_base_url}{crs}"
        #print(url)
        headers = {
            "Authorization": f"Basic {auth}"
        }
        async with aiohttp.ClientSession() as session: #syntax outline as recommended by the aiohttp docs
            try:
                async with session.get(url, headers=headers) as response: #returns a json response containing our data
                    data = await response.json() #data as a json object
                    services = data.get('services', [])
                    if services == None:
                        #print('No services found')
                        return None
                    service_list = [ # what we return
                        [
                            item.get('serviceUid', 'N/A'),
                            item['locationDetail'].get('gbttBookedDeparture', 'N/A'),
                            item['locationDetail'].get('realtimeDeparture', 'N/A'),
                            item['locationDetail']['destination'][0].get('tiploc', 'N/A')
                        ]
                        for item in services if 'locationDetail' in item and 'destination' in item['locationDetail'] and item['locationDetail']['destination'] and item.get('serviceType') == 'train' and item['locationDetail'].get('gbttBookedDeparture', 'N/A') >= time.strftime('%H%M')
                    ]
                    if time_limit:
                        service_list = [service for service in service_list if service[1] <= time_limit]
                    return service_list
            except aiohttp.ClientError as e:
                fails += 1
                print(f'Failed to retrieve board for {crs}. Error: {e}')
                asyncio.sleep(5) # to not overlad the server
                if fails < 3: # only attempt 3 times
                    return await Retrive().fetch_board(crs, time, fails=fails)
                else:
                    return None
                

    @staticmethod        
    async def fetch_service(serviceUid,date=datetime.datetime.today(),fails=0):
        '''
        inputs: uid, date, fails (optional)
        returns: list [[crs, arrival time, departure time], ....]
        '''
        username = rttapi_username #has been ommited due to api agreements, but an eqivilant can be sorced from api.rtt.io
        password = rttapi_pw #has been ommited due to api agreements, but an eqivilant can be sorced from api.rtt.io
        board_base_url = "https://api.rtt.io/api/v1/json/search/"
        service_base_url = "https://api.rtt.io/api/v1/json/service/"
        auth = base64.b64encode(f"{username}:{password}".encode()).decode()
        year,month,day = date.year, '%02d'%date.month, '%02d'%date.day
        url = f"{service_base_url}{serviceUid}/{year}/{month}/{day}" # the given sercvice on the given day
        #print(url)
        headers = {
            "Authorization": f"Basic {auth}"
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    data = await response.json() # data as a json object
                    stops = data.get('locations', [])
                    stop_list = [
                        [
                        item.get('crs', 'N/A'),
                        item.get('realtimeArrival', 'N/A'),
                        item.get('realtimeDeparture', 'N/A'),
                        ]
                        for item in stops
                    ]
            return stop_list
        except aiohttp.ClientError as e:
            print(f'Failed to retrieve service {serviceUid}. Error: {e}')
            if fails >= 3: # max 3 attempts
                return None
            asyncio.sleep(5) # to stop server spamming
            return await Retrive().fetch_service(serviceUid, date, fails=(fails+1))
    @staticmethod 
    async def fetch_service_info(serviceUid,date=datetime.datetime.today(),fails=0):
        '''
        inputs: uid, date, fails (optional)
        returns: list [trainid, atoc, origin tiploc, destination tiploc]
        '''
        username = rttapi_username #has been ommited due to api agreements, but an eqivilant can be sorced from api.rtt.io
        password = rttapi_pw #has been ommited due to api agreements, but an eqivilant can be sorced from api.rtt.io
        board_base_url = "https://api.rtt.io/api/v1/json/search/"
        service_base_url = "https://api.rtt.io/api/v1/json/service/"
        auth = base64.b64encode(f"{username}:{password}".encode()).decode() # the format required for the header
        year,month,day = date.year, '%02d'%date.month, '%02d'%date.day
        url = f"{service_base_url}{serviceUid}/{year}/{month}/{day}"
        #print(url)
        headers = {
            "Authorization": f"Basic {auth}"
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    data = await response.json() # data as a json object
                    info = [
                        data.get('trainIdentity', 'N/A'),
                        data.get('atocCode', 'N/A'),
                        data.get('origin', 'N/A')[0].get('tiploc', 'N/A'),
                        data.get('destination', 'N/A')[0].get('tiploc', 'N/A')
                    ]
            return info
        except aiohttp.ClientError as e:
            print(f'Failed to retrieve service {serviceUid}. Error: {e}')
            if fails >= 3: # only attempt 3 times
                return None
            asyncio.sleep(5) # to stop server spamming
            return await Retrive().fetch_service(serviceUid, date, fails=(fails+1))
    @staticmethod 
    async def get_service_delay(serviceUid, date=datetime.datetime.today(), fails=0):
        '''
        inputs: uid, date, fails (optional)
        returns: int delay
        '''
        username = rttapi_username #has been ommited due to api agreements, but an eqivilant can be sorced from api.rtt.io
        password = rttapi_pw #has been ommited due to api agreements, but an eqivilant can be sorced from api.rtt.io
        board_base_url = "https://api.rtt.io/api/v1/json/search/"
        service_base_url = "https://api.rtt.io/api/v1/json/service/"
        auth = base64.b64encode(f"{username}:{password}".encode()).decode()
        year,month,day = date.year, '%02d'%date.month, '%02d'%date.day
        url = f"{service_base_url}{serviceUid}/{year}/{month}/{day}"
        #print(url)
        headers = {
            "Authorization": f"Basic {auth}"
        }
        try:
            async with aiohttp.ClientSession() as session: #syntax outline as recommended by the aiohttp docs
                async with session.get(url, headers=headers) as response:
                    data = await response.json()
                    stops = data.get('locations', [])
                    stop_list = [
                        [
                        item.get('crs', 'N/A'),
                        item.get('realtimeArrival', 'N/A'),
                        item.get('gbttBookedArrival', 'N/A')
                        ]
                        for item in stops
                    ]
            for item in stop_list[::-1]:
                if item[1] < date.strftime('%H%M'):
                    return int(item[1]) - int(item[2])
        except aiohttp.ClientError as e:
            print(f'Failed to retrieve service {serviceUid}. Error: {e}')
            if fails >= 3:
                return None
            asyncio.sleep(5)
            return await Retrive().fetch_service(serviceUid, date, fails=(fails+1))
    @staticmethod
    async def fetch_map(session, style, z, x, y):
        subdomains = ['a', 'b', 'c']
        subdomain = subdomains[(z + x + y) % len(subdomains)] # to ensure even mix of subdomain

        url = f'http://{subdomain}.tiles.openrailwaymap.org/{style}/{z}/{x}/{y}.png' # the tile required at zoom level z
        #print(url)
        tile_dir = f'rail_tiles/{z}'
        os.makedirs(tile_dir, exist_ok=True)
        tile_path = os.path.join(tile_dir, f'tile_{x}_{y}.png')
        
        if not os.path.exists(tile_path):
            for attempt in range(3): # max 3 attemps
                try:
                    async with session.get(url) as response:
                        if response.status == 200: # good response
                            with open(tile_path, 'wb') as file:
                                file.write(await response.read())
                            #print(f'Tile {z}/{x}/{y} saved successfully.')
                            break
                        '''
                        else:
                            print(f'Failed to retrieve tile {z}/{x}/{y}. Status code: {response.status}')
                        '''
                except aiohttp.ClientError as e:
                    #print(f'Attempt {attempt + 1} failed for tile {z}/{x}/{y}. Error: {e}')
                    await asyncio.sleep(1)
    @staticmethod             
    async def get_trainline_id(crs): # just matches from table
        with open('stations-gb-id-name.csv', 'r') as file:
            rows= csv.reader(file, delimiter=';') 
            for row in rows:
                if row[1] == crs:
                    return row[0] # the trainline id column
            return None
    @staticmethod          
    async def get_stations_in_box(top_y, left_x, bottom_y, right_x): # finds stations on screen
        stations = []
        #print(top_y, left_x, bottom_y, right_x)
        with open('uk-train-stations.csv', 'r') as file:
            rows= csv.reader(file)
            for row in rows:
                if left_x <= float(row[3]) <= right_x and bottom_y <= float(row[2]) <= top_y: # if in box
                    stations.append(row[0])
        '''
        if len(stations) == 0:
            print('No stations found in box')
            '''
        return stations
    @staticmethod
    async def get_all_stations(): # returns all stations
        stations_and_coords = []
        with open('uk-train-stations.csv', 'r') as file:
            rows= csv.reader(file)
            for row in rows:
                stations_and_coords.append([row[0], float(row[2]), float(row[3])]) # station, (lat, long)
        return stations_and_coords

    @staticmethod         
    async def get_rail_line(crs_1, crs_2): # returns a evenly distibutes array of points along the line between said stations
        trainline_id_1 = await Retrive().get_trainline_id(crs_1)
        trainline_id_2 = await Retrive().get_trainline_id(crs_2)
        url = f'https://trainmap.ntag.fr/api/route?dep={trainline_id_1}&arr={trainline_id_2}'
        #print(url)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200: # good response
                    data = await response.json()
                    positions = data.get('geometry', {}).get('coordinates', [])
                    return positions[0] # returns the list of coordinates 
                return None
    @staticmethod
    async def main():
        print('wrong file bozo')
        #board_data = await Retrive().fetch_board("EXC")
        #print(board_data)
        #service_data= await Retrive().fetch_service("G45103", datetime.date(2024, 11, 22))
        #print(service_data)
        #await fetch_map(aiohttp.ClientSession(),'signals', 11, 512, 512)
        service_info = await Retrive().fetch_service_info("Y22177")
        print(service_info)