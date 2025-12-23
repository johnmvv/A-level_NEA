import math
class StaticMethods():
    @staticmethod #doesn't need a class to be called (note the lack of "self")
    def get_xy_from_latlong(zoom, lon, lat):
        x = (lon + 180)/360 * (2**zoom) * 512 #just ratios
        y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * (2 ** zoom) * 512 #as using macator projection
        return x, y
    
    @staticmethod#doesn't need a class to be called (note the lack of "self")
    def get_latlon_from_xy(zoom, x, y):
        lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / (2**zoom * 512))))) #as using mcator projection, just inverse of above
        lon = (x / (2**zoom * 512)) * 360 - 180
        return lat, lon
    
    @staticmethod#doesn't need a class to be called (note the lack of "self")
    def get_tile_range(width, height, x, y, zoom): #simply gats the ranges of tiles on screen
        start_x = int(max(0, -x // 512)) #leftmost, max to stop errors if screen contains outside of map
        end_x = int(min(2**zoom, (width - x) // 512 + 1)) #leftmost + number of tiles horizontally on screen, min to stop errors if screen contains outside of map
        start_y = int(max(0, -y // 512)) #topmost
        end_y = int(min(2**zoom, (height - y) // 512 + 1)) #topmost + number of tiles vertically on screen
        return range(start_x, end_x), range(start_y, end_y)