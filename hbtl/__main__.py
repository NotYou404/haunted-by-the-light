import random
from pathlib import Path

import arcade
import pyglet.display
from pyglet.math import Vec2

from . import model

ASSETS_PATH = model.AssetsPath(Path(__file__).parent / "assets")
TEXTURES_PATH = ASSETS_PATH / "textures"
MUSIC_PATH = ASSETS_PATH / "music"
SOUNDS_PATH = ASSETS_PATH / "sounds"
MAPS_PATH = ASSETS_PATH / "maps"

TILE_SIZE = 16
MAP_WIDTH = 30

TILE_SCALING = 4
PLAYER_SCALING = 3

INITIAL_SPEED = 300
INITIAL_SPEED_SPECTRE = 310
SPEED_GAIN_PER_SECOND = 4
SPEED_GAIN_PER_SECOND_SPECTRE = 2
GRAVITY = 1
JUMP_VELOCITY = 23

MAPS_PER_BIOME = 10


def main() -> None:
    display = pyglet.display.get_display()
    screen = display.get_default_screen()
    width = screen.width
    height = screen.height
    win = arcade.Window(
        resizable=True,
        vsync=True,
        width=width,
        height=height,
    )
    win.set_min_size(1200, 800)
    intro_view = GameView()  # TODO IntroView1()
    intro_view.setup()
    win.show_view(intro_view)
    arcade.run()


class IntroView1(model.FadingView):
    def setup(self) -> None:
        self.window.background_color = arcade.color.WHITE
        self.sprites = arcade.SpriteList()
        self.text1 = model.Sprite(
            path_or_texture=TEXTURES_PATH.get("there_were_times"),
            scale=5,
        )
        self.sprites.append(self.text1)

        self.next_view = IntroView2
        arcade.schedule_once(lambda _: self.start_fade_out(), 3)
        self.start_fade_in()
        self.on_resize(self.window.width, self.window.height)

    def on_resize(self, width: int, height: int):
        self.text1.center = width / 2, height / 2

    def on_draw(self) -> None:
        self.clear()
        self.sprites.draw(pixelated=True)
        self.draw_fading()


class IntroView2(model.FadingView):
    def setup(self) -> None:
        self.window.background_color = arcade.color.WHITE
        self.sprites = arcade.SpriteList()
        self.text2 = model.Sprite(
            path_or_texture=TEXTURES_PATH.get("when_there_was_no_dark_mode"),
            scale=5,
        )
        self.sprites.append(self.text2)

        self.next_view = GameView
        arcade.schedule_once(lambda _: self.start_fade_out(), 4)
        self.start_fade_in()
        self.on_resize(self.window.width, self.window.height)

    def on_resize(self, width: int, height: int):
        self.text2.center = width / 2, height / 2

    def on_draw(self) -> None:
        self.clear()
        self.sprites.draw(pixelated=True)
        self.draw_fading()


class GameView(model.FadingView):
    def __init__(self) -> None:
        super().__init__()

    def setup(self) -> None:
        self.window.maximize()

        self.started = False
        self.ended = False

        self.shapes = pyglet.shapes.Batch()
        self.setup_map()
        self.setup_player()
        self.setup_spectre()
        self.camera = arcade.camera.Camera2D()
        self.ui_camera = arcade.camera.Camera2D()
        self.engine = model.CustomPhysicsEnginePlatformer(
            player_sprite=self.player,
            gravity_constant=GRAVITY,
            walls=self.scene["walls"],
        )
        self.setup_ui()

        self.window.background_color = arcade.color.FRESH_AIR
        self.on_resize(self.window.width, self.window.height)
        self.start_fade_in()

    def place_cloud(self, dt: float) -> None:
        if (
            self.player.center_x
            < MAP_WIDTH * TILE_SIZE * TILE_SCALING * MAPS_PER_BIOME
        ):
            cloud = model.Sprite(
                path_or_texture=TEXTURES_PATH.get(
                    f"cloud{random.randint(1, 3)}"
                ),
                scale=8,
                center_y=self.window.height - 200,
            )
            cloud.left = self.window.width
            cloud.change_x = -20
            self.scene["ambient"].append(cloud)
        else:
            arcade.unschedule(self.place_cloud)

    def start(self) -> None:

        def start_movement_slime(dt: float) -> None:
            self.player.state = "moving"
            self.player.change_x = INITIAL_SPEED

        def start_movement_spectre(dt: float) -> None:
            self.spectre.state = "moving"
            self.spectre.change_x = INITIAL_SPEED_SPECTRE

        self.started = True
        self.spectre.state = "awake"
        arcade.schedule_once(lambda _: self.engine.jump(JUMP_VELOCITY), 0.8)
        arcade.schedule_once(start_movement_spectre, 1.4)
        arcade.schedule_once(start_movement_slime, 2.0)

        arcade.schedule(self.place_cloud, 20.0)
        self.place_cloud(0)

    def on_resize(self, width: int, height: int):
        self.title.center_x = width / 2
        self.title.center_y = height * 0.85

        self.click_to_play.center_x = width * 0.6
        self.click_to_play.center_y = height * 0.45

        self.options_icon.right = width - 20
        self.options_icon.top = height - 20

    def setup_player(self) -> None:
        self.player = model.AnimatedSprite(
            scale=PLAYER_SCALING,
        )
        idling = model.load_texture_series(
            TEXTURES_PATH / "slime",
            "slime_idle_{i}.png",
            range(1, 5),
        )
        moving = model.load_texture_series(
            TEXTURES_PATH / "slime",
            "slime_moving_{i}.png",
            range(1, 5),
        )
        dead = model.load_texture(
            TEXTURES_PATH / "slime" / "slime_dead.png",
        )
        victory = model.load_texture(
            TEXTURES_PATH / "slime" / "slime_victory.png",
        )
        self.player.add_textures({
            "idling": idling,
            "moving": moving,
            "dead": [dead],
            "victory": [victory],
        })
        self.player.state = "idling"
        self.player.center = (
            self.scene["spawn"][0].center_x,
            self.scene["spawn"][0].center_y - 16,
        )
        self.scene["spawn"].visible = False
        self.scene.add_sprite("player", self.player)

    def setup_spectre(self) -> None:
        self.spectre = model.AnimatedSprite(scale=4)
        idling = model.load_texture_series(
            TEXTURES_PATH / "spectre",
            "spectre_idle_{i}.png",
            range(1, 3),
        )
        moving = model.load_texture_series(
            TEXTURES_PATH / "spectre",
            "spectre_moving_{i}.png",
            range(1, 3),
        )
        awake = model.load_texture(
            TEXTURES_PATH / "spectre" / "spectre_awake.png"
        )
        self.spectre.add_textures({
            "idling": idling,
            "moving": moving,
            "awake": [awake],
        })
        self.spectre.state = "idling"
        self.spectre.center = (
            self.scene["spectre_spawn"][0].center_x,
            self.scene["spectre_spawn"][0].center_y,
        )
        self.scene["spectre_spawn"].visible = False
        self.scene.add_sprite("spectre", self.spectre)

    def setup_map(self) -> None:
        self.maps = []
        init_map = arcade.tilemap.load_tilemap(
            map_file=MAPS_PATH.get("init_map.tmj"),
            scaling=TILE_SCALING,
        )
        self.maps.append(init_map)
        self.scene = arcade.Scene.from_tilemap(init_map)
        self.scene.add_sprite_list("obstacles", use_spatial_hash=True)
        self.scene.add_sprite_list("ambient")
        for i in range(1, MAPS_PER_BIOME + 1):
            map_num = random.randint(1, 6)
            map = arcade.tilemap.load_tilemap(
                map_file=MAPS_PATH.get(f"grass_{map_num}.tmj"),
                scaling=TILE_SCALING,
                offset=Vec2(
                    round(((i) * MAP_WIDTH) * TILE_SIZE * TILE_SCALING), 0
                ),
            )
            scene = arcade.Scene.from_tilemap(map)
            self.scene["walls"].extend(scene["walls"])
            self.maps.append(map)

    def setup_ui(self) -> None:
        self.ui_sprites = arcade.SpriteList()
        self.title = model.Sprite(
            path_or_texture=TEXTURES_PATH.get("haunted_by_the_light"),
            scale=8,
            angle=-10,
        )
        self.ui_sprites.append(self.title)

        self.click_to_play_angle = 0
        self.click_to_play = model.Sprite(
            path_or_texture=TEXTURES_PATH.get("click_to_play"),
            scale=3,
            angle=25,
        )

        def update_click_to_play_angle(dt: float) -> None:
            self.click_to_play.angle = self.click_to_play_angle * 5 + 20
            self.click_to_play_angle = not self.click_to_play_angle

        arcade.schedule(update_click_to_play_angle, 1)
        self.ui_sprites.append(self.click_to_play)

        self.options_icon = model.Sprite(
            path_or_texture=TEXTURES_PATH.get("options_icon"),
            scale=2,
        )
        self.ui_sprites.append(self.options_icon)

    def on_update(self, delta_time: float) -> None:
        super().on_update(delta_time)

        if self.started and not self.ended:
            if not self.player.change_y > 0:
                self.player.change_x += SPEED_GAIN_PER_SECOND * delta_time
            self.spectre.change_x += SPEED_GAIN_PER_SECOND_SPECTRE * delta_time
            self.engine.on_update(delta_time)
            self.scene.on_update(
                delta_time, ["spectre", "obstacles", "ambient"]
            )
            if self.spectre.state == "moving":
                self.spectre.center_y = self.player.center_y

        self.scene.update_animation(delta_time)

        self.camera.match_screen()
        self.camera.position = (
            self.player.center_x,
            self.player.center_y + self.window.height / 8,
        )

        if not self.ended and self.player.center_y <= -200:
            self.end()
        elif self.spectre.right - 30 > self.player.left:
            self.end()

    def end(self, state: str = "dead") -> None:
        self.ended = True
        self.player.state = state
        self.player.update_animation(0)
        self.next_view = GameView
        arcade.schedule_once(lambda _: self.start_fade_out(), 1.0)

    def on_draw(self) -> None:
        self.clear()
        self.ui_camera.use()
        self.scene.draw(["ambient"], pixelated=True)
        self.camera.use()
        self.scene.draw(
            ["player", "spectre", "obstacles", "walls", "checkpoints"],
            pixelated=True,
        )
        if not self.started:
            self.ui_camera.use()
            self.ui_sprites.draw(pixelated=True)
        self.ui_camera.use()
        self.draw_fading()

    @property
    def stop_jump_value(self) -> float:
        return -0.8 * self.player.change_y + JUMP_VELOCITY

    def on_key_press(self, symbol: int, modifiers: int):
        if self.started:
            if symbol == arcade.key.SPACE and self.engine.can_jump():
                self.engine.jump(JUMP_VELOCITY)
        else:
            if symbol == arcade.key.SPACE:
                self.start()

    def on_key_release(self, symbol: int, modifiers: int):
        if self.started:
            if (
                symbol == arcade.key.SPACE
                and self.player.change_y > self.stop_jump_value
            ):
                self.player.change_y = self.stop_jump_value

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        if self.started:
            if button == arcade.MOUSE_BUTTON_LEFT and self.engine.can_jump():
                self.engine.jump(JUMP_VELOCITY)
        else:
            if button == arcade.MOUSE_BUTTON_LEFT:
                if False:  # Options and stats
                    ...  # TODO
                else:
                    self.start()

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        if self.started:
            if (
                button == arcade.MOUSE_BUTTON_LEFT
                and self.player.change_y > self.stop_jump_value
            ):
                self.player.change_y = self.stop_jump_value


if __name__ == "__main__":
    main()
