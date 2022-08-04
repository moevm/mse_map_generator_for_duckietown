from dt_map_generator.advancedMap import advancedMap, Pose, add_new_obj

from dt_maps import MapLayer
from dt_map_generator.generator import Generator

class DuckietownMap(object):
    DEFAULT_TILE_SIZE = 0.585

    NEW_CELLS = {  # type, yaw
        0: ['floor', 0],
        5: ['straight', 0],
        10: ['straight', 90],
        3: ['curve', 0],
        6: ['curve', 90],
        12: ['curve', 180],
        9: ['curve', 270],
        7: ['3way', 0],
        11: ['3way', 270],
        14: ['3way', 90],
        13: ['3way', 180],
        15: ['4way', 0]
    }

    def __init__(self, generator=None):
        self._map = list()
        self._data = {}
        self._objects = []
        self._generator = generator

    def set_generator(self, generator):
        self._generator = generator

    def new(self):
        self._generator.create()
        state = self._generator.get_state()

        self._map = [[''] * state.width for _ in range(state.height)]

        for i in range(state.height):
            for j in range(state.width):
                self._map[i][j] = self.NEW_CELLS[state.map[i][j]]

        self._data = {
            'tiles': self._map,
            'objects': self._objects,
            'tile_size': self.DEFAULT_TILE_SIZE
        }
        return self

    def print_map(self, state):
        old_map = state.map
        # old_map =tuple(zip(*old_map[::-1])) #rotate to 90 degree
        print("map=", old_map)
        for i in range(state.height):
            for j in range(state.width):
                if old_map[i][j] != 0:
                    print("#", end=' ')
                else:
                    print("0", end=' ')
            print('\n', end='')

    def is_near_road(self, state, cells: list):
        old_map = state.map
        near_road_floor = []
        wt_list = []
        for i in range(0, len(cells)):
            cell = cells[i]
            a = cell[0]
            b = cell[1]
            road_cells = (5, 10, 7, 11, 13, 14)

            if old_map[a + 1][b] in road_cells:
                near_road_floor.append(cell)
                wt_list.append([a, b, 90])  # сверху

            if old_map[a - 1][b] in road_cells:
                near_road_floor.append(cell)
                wt_list.append([a, b, 270])  # снизу

            if old_map[a][b + 1] in road_cells:
                near_road_floor.append(cell)
                wt_list.append([a, b, 0])  # слева

            if old_map[a][b - 1] in road_cells:
                near_road_floor.append(cell)
                wt_list.append([a, b, 180])  # справа

        list1 = near_road_floor
        list2 = []
        for item in list1:
            if item not in list2:
                list2.append(item)

        near_road_floor = list2
        return near_road_floor, wt_list

    def get_watchtowers_place(self, state):
        old_map = state.map
        width = state.width
        height = state.height

        floor_list = []
        for i in range(1, height - 1):
            for j in range(1, width - 1):
                if old_map[i][j] == 0:
                    floor_list.append([i, j])

        flor_near_road, watchtowers_list = self.is_near_road(state, floor_list)
        return watchtowers_list

    def connect_layers(self, a_map:advancedMap, layer_name:str, layers: dict):
        a_map.map.layers.__dict__[layer_name] = layers[layer_name]

    def save_new_architecture(self):

        state = self._generator.get_state()
        save_path = self._generator.get_save_path()
        old_map = state.map
        a_map = advancedMap(width=state.width, height=state.height, storage_location=save_path)

        frames_layer = MapLayer(a_map.map, "frames")
        tiles_layer = MapLayer(a_map.map, "tiles")
        tile_maps_layer = MapLayer(a_map.map, "tile_maps", a_map.createTileMaps())
        traffic_signs_layer = MapLayer(a_map.map, "traffic_signs")
        ground_tags_layer = MapLayer(a_map, "ground_tags")
        citizens_layer = MapLayer(a_map, "citizens")
        vehicles_layer = MapLayer(a_map, "vehicles")

        add_new_obj(a_map.map, frames_layer, "frames", f'{a_map.map_name}', {'relative_to': None, 'pose': None})
        frames_layer[f'{a_map.map_name}']['pose'] = Pose(1.0, 2.0).get_pose()

        for height in range(0, state.width):
            for width in range(0, state.height):
                old_cell = old_map[width][height]
                new_cell = self.NEW_CELLS[old_cell]
                pose = Pose(x=width * self.DEFAULT_TILE_SIZE, y=height * self.DEFAULT_TILE_SIZE, yaw=new_cell[1])
                a_map.createMapTileBlock(a_map.map, frames_layer, width, height, None, pose)
                add_new_obj(a_map.map, tiles_layer, "tiles", f'{a_map.map_name}/tile_{width}_{height}',
                            {'i': width, 'j': height, 'type': new_cell[0]})

        watchtower_layer = MapLayer(a_map.map, "watchtowers")
        watchtowers_list = self.get_watchtowers_place(state)
        a_map.createWatchtowers(a_map.map, frames_layer, watchtower_layer, watchtowers_list)
        a_map.createTrafficSigns(a_map.map, frames_layer, traffic_signs_layer, 1)
        a_map.createGroundTags(a_map.map, frames_layer, ground_tags_layer, 1)
        a_map.createCitizens(a_map.map, frames_layer, citizens_layer, 1)
        a_map.createVehicles(a_map.map, frames_layer, vehicles_layer, 1)

        layers ={
            "watchtowers": watchtower_layer,
            "frames": frames_layer,
            "tiles": tiles_layer,
            "tile_maps": tile_maps_layer,
            "traffic_signs": traffic_signs_layer,
            "ground_tags": ground_tags_layer,
            "citizens": citizens_layer,
            "vehicles": vehicles_layer,
        }

        for layer in layers:
            self.connect_layers(a_map, layer, layers)

        a_map.map.to_disk()

    def save(self):
        self.save_new_architecture()  # reload to new arch map

    def generateNewMap(self, info):
        state = self._generator.get_state()
        save_path = self._generator.get_save_path()
        old_map = state.map
        a_map = advancedMap(width=state.width, height=state.height, storage_location=save_path)

        frames_layer = MapLayer(a_map.map, "frames")
        tiles_layer = MapLayer(a_map.map, "tiles")
        tile_maps_layer = MapLayer(a_map.map, "tile_maps", a_map.createTileMaps())
        traffic_signs_layer = MapLayer(a_map.map, "traffic_signs")
        ground_tags_layer = MapLayer(a_map, "ground_tags")
        citizens_layer = MapLayer(a_map, "citizens")
        vehicles_layer = MapLayer(a_map, "vehicles")

        add_new_obj(a_map.map, frames_layer, "frames", f'{a_map.map_name}', {'relative_to': None, 'pose': None})
        frames_layer[f'{a_map.map_name}']['pose'] = Pose(1.0, 2.0).get_pose()

        for height in range(0, state.width):
            for width in range(0, state.height):
                old_cell = old_map[width][height]
                new_cell = self.NEW_CELLS[old_cell]
                pose = Pose(x=width * self.DEFAULT_TILE_SIZE, y=height * self.DEFAULT_TILE_SIZE, yaw=new_cell[1])
                a_map.createMapTileBlock(a_map.map, frames_layer, width, height, None, pose)
                add_new_obj(a_map.map, tiles_layer, "tiles", f'{a_map.map_name}/tile_{width}_{height}',
                            {'i': width, 'j': height, 'type': new_cell[0]})

        watchtower_layer = MapLayer(a_map.map, "watchtowers")
        watchtowers_list = list()
        if (info['watchtowers'] == True):
            watchtowers_list = self.get_watchtowers_place(state)
        a_map.createWatchtowers(a_map.map, frames_layer, watchtower_layer, watchtowers_list)
        a_map.createTrafficSigns(a_map.map, frames_layer, traffic_signs_layer, info['traffic_signs'])
        a_map.createGroundTags(a_map.map, frames_layer, ground_tags_layer, info['ground_tags'])
        a_map.createCitizens(a_map.map, frames_layer, citizens_layer, info['citizens'])
        a_map.createVehicles(a_map.map, frames_layer, vehicles_layer, info['vehicles'])

        layers = {
            "watchtowers": watchtower_layer,
            "frames": frames_layer,
            "tiles": tiles_layer,
            "tile_maps": tile_maps_layer,
            "traffic_signs": traffic_signs_layer,
            "ground_tags": ground_tags_layer,
            "citizens": citizens_layer,
            "vehicles": vehicles_layer,
        }

        for layer in layers:
            self.connect_layers(a_map, layer, layers)

        a_map.map.to_disk()

if __name__ == '__main__':
    info = {
        'x': 6,
        'y': 5,
        'width': 6,
        'height': 5,
        'length': 10,
        'path': '../maps',
        'crossroads_data': {
            'triple': 2,
            'quad': 0
        },
        'tile_width': 0.585,
        'tile_height': 0.585,
        'dir_name': '../maps',
        'traffic_signs': 1,
        'ground_tags': 1,
        'citizens': 1,
        'vehicles': 1,
        'watchtowers': True,
    }
    DuckietownMap(Generator(info)).new().generateNewMap(info)