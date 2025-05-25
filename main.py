import pyautogui
from datetime import datetime
from ursina import *
import json
import os
import math

app = Ursina()
from ursina.prefabs.hot_reloader import HotReloader
HotReloader.enabled = False

block_textures = {
    1: 'grass.png',
    2: 'dirt.png',
    3: 'stone.png'
}

current_block = 1
world_data = {}

class Voxel(Button):
    def __init__(self, position=(0,0,0), block_type=1):
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            origin_y=0.5,
            texture=block_textures.get(block_type, 'white_cube'),
            color=color.white,
            highlight_color=color.lime,
            scale=1
        )
        self.block_type = block_type
        world_data[str(self.position)] = block_type

    def input(self, key):
        if self.hovered:
            if key == 'left mouse down':
                pos = str(self.position)
                destroy(self)
                world_data.pop(pos, None)
            elif key == 'right mouse down':
                pos = self.position + mouse.normal
                if str(pos) not in world_data:
                    Voxel(position=pos, block_type=current_block)

def create_ground(size=30):
    for x in range(size):
        for z in range(size):
            Voxel(position=(x, 0, z), block_type=1)

def save_world():
    with open('save.json', 'w') as f:
        json.dump(world_data, f)
    print("Monde sauvegardé !")

def load_world():
    if not os.path.exists('save.json'):
        print("Aucune sauvegarde trouvée, création d’un sol basique.")
        create_ground()
        return
    with open('save.json', 'r') as f:
        data = json.load(f)
    for pos_str, block_type in data.items():
        pos = eval(pos_str)
        Voxel(position=pos, block_type=block_type)
    print("Monde chargé !")

def create_hotbar():
    for i in range(3):
        icon = Entity(
            model='quad',
            texture=block_textures[i+1],
            scale=(0.07, 0.07),
            position=window.bottom_left + Vec2(0.07 * i + 0.05, 0.05),
            parent=camera.ui
        )
        def on_click(i=i+1):
            global current_block
            current_block = i
        icon.on_click = on_click

def input(key):
    global current_block
    if key == '1': current_block = 1
    if key == '2': current_block = 2
    if key == '3': current_block = 3
    if key == 'f5': save_world()
    if key == 'f9': load_world()
    if key == 'escape': application.quit()          # Quitte le jeu
    if key == 'f1':
       now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
       pyautogui.screenshot(f'screenshot_{now}.png')



class Player(Entity):
    def __init__(self):
        super().__init__()
        self.speed = 5
        self.gravity = 9.81
        self.jump_height = 1.5
        self.velocity_y = 0
        self.grounded = False

        self.position = (5, 3, 5)

        self.camera_pivot = Entity(parent=self, y=1.5)
        camera.parent = self.camera_pivot
        camera.position = (0, 0, 0)
        camera.rotation = (0, 0, 0)
        camera.fov = 90

        mouse.locked = True

        self.rotation_y = 0

    def update(self):
        # Rotation souris
        self.camera_pivot.rotation_x -= mouse.velocity[1] * 40
        self.camera_pivot.rotation_x = clamp(self.camera_pivot.rotation_x, -90, 90)

        self.rotation_y += mouse.velocity[0] * 40
        self.rotation = (0, self.rotation_y, 0)

        # Mouvement clavier
        direction = Vec3(
            self.forward * (held_keys['w'] - held_keys['s']) +
            self.right * (held_keys['d'] - held_keys['a'])
        )
        if direction.length() > 0:
            direction = direction.normalized()
        move_amount = direction * time.dt * self.speed

        # Collision X
        new_pos = self.position + Vec3(move_amount.x, 0, 0)
        if not self.collides_with_block(new_pos):
            self.position = Vec3(new_pos.x, self.position.y, self.position.z)

        # Collision Z
        new_pos = self.position + Vec3(0, 0, move_amount.z)
        if not self.collides_with_block(new_pos):
            self.position = Vec3(self.position.x, self.position.y, new_pos.z)

        # Gravité & sol
        ray = raycast(self.position + Vec3(0,0.1,0), Vec3(0,-1,0), distance=0.2, ignore=[self])
        if ray.hit:
            self.grounded = True
            self.velocity_y = 0
            self.position = Vec3(self.position.x, ray.world_point.y + 0.1, self.position.z)
        else:
            self.grounded = False
            self.velocity_y -= self.gravity * time.dt

        # Mouvement vertical avec collision
        new_pos = self.position + Vec3(0, self.velocity_y * time.dt, 0)
        if not self.collides_with_block(new_pos):
            self.position = new_pos
        else:
            if self.velocity_y < 0:
                self.grounded = True
            self.velocity_y = 0

        # Saut
        if self.grounded and held_keys['space']:
            self.velocity_y = math.sqrt(2 * self.gravity * self.jump_height)
            self.grounded = False

    def collides_with_block(self, pos):
        for x in range(math.floor(pos.x - 0.25), math.ceil(pos.x + 0.25) + 1):
            for y in range(math.floor(pos.y), math.ceil(pos.y + 1.8) + 1):
                for z in range(math.floor(pos.z - 0.25), math.ceil(pos.z + 0.25) + 1):
                    if str(Vec3(x,y,z)) in world_data:
                        return True
        return False

Sky()
player = Player()

create_hotbar()
load_world()

app.run()

create_hotbar()
load_world()

app.run()
