import random
from pathlib import Path

import arcade
import arcade.experimental.lights
import pyglet.graphics
from pyglet.math import Vec2

try:
    from . import model
except ImportError:
    # Nuitka does not allow invoking via -m
    import model

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
SPEED_PENALTY_VERTICAL_PLUS = -0.05
SPECTRE_SPEED_CAP = 5
GRAVITY = 1
JUMP_VELOCITY = 23

MAPS_PER_BIOME = 10
BACKGROUND_GRADIENT_STEPS = 30

# Dripstones above this height will fall down eventually
ICE_DRIPSTONE_FALL_HEIGHT = 1050


class Window(arcade.Window):
    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.F11:
            self.set_fullscreen(not self.fullscreen)


def main() -> None:
    win = Window(
        title="Haunted by the Light",
        resizable=True,
        vsync=True,
        fullscreen=True
    )
    win.set_min_size(1200, 800)
    intro_view = IntroView1()
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


class OutroView(model.FadingView):
    def setup(self) -> None:
        self.window.background_color = arcade.color.EERIE_BLACK
        self.sprites = arcade.SpriteList()
        self.text = model.Sprite(
            path_or_texture=TEXTURES_PATH.get("dark_mode_unlocked"),
            scale=5,
        )
        self.sprites.append(self.text)

        self.next_view = GameView
        arcade.schedule_once(lambda _: self.start_fade_out(), 4)
        self.start_fade_in()
        self.on_resize(self.window.width, self.window.height)

    def on_resize(self, width: int, height: int):
        self.text.center = width / 2, height / 2

    def on_draw(self) -> None:
        self.clear()
        self.sprites.draw(pixelated=True)
        self.draw_fading()


class CreditsView(arcade.View):
    def setup(self) -> None:
        self.window.background_color = arcade.color.BLACK
        self.camera = arcade.Camera2D()

        self.text_batch = pyglet.graphics.Batch()
        self.texts: list[arcade.Text] = []

        text_dict = {
            "Haunted by the Light": (48, 80),
            "by TheCheese": (24, 600),
            "Credits": (36, 100),
            "Music (Grass) - 'Example' by Someone 1": (24, 60),
            "Music (Ice) - 'Example' by Someone 2": (24, 60),
            "Music (Obsidian) -  'Example' by Someone 2": (24, 400),
            "And a special Thanks to:": (36, 100),
            "The Python Arcade Library": (24, 60),
        }

        cur_y = -50
        for text, (size, space) in text_dict.items():
            self.texts.append(arcade.Text(
                text,
                x=0,
                y=cur_y,
                font_size=size,
                batch=self.text_batch,
            ))
            cur_y -= space
        self.last_y = cur_y

        self.on_resize(self.window.width, self.window.height)

    def on_resize(self, width: int, height: int):
        self.camera.match_screen()
        for text in self.texts:
            text.x = width / 2 - text.content_width / 2

    def on_update(self, delta_time: float) -> None:
        self.camera.projection = self.camera.projection.move(
            dy=-100 * delta_time
        )
        if self.camera.projection.top + 800 < self.last_y:
            view = GameView()
            view.setup()
            self.window.show_view(view)

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol in (arcade.key.SPACE, arcade.key.ESCAPE):
            view = GameView()
            view.setup()
            self.window.show_view(view)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_LEFT:
            view = GameView()
            view.setup()
            self.window.show_view(view)

    def on_draw(self) -> None:
        self.clear()
        self.camera.use()
        self.text_batch.draw()


class GameView(model.FadingView):
    def __init__(self) -> None:
        super().__init__()

    def setup(self) -> None:
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
        self.light_layer = arcade.experimental.lights.LightLayer(
            self.window.width,
            self.window.height,
        )
        self.spectre_light = arcade.experimental.lights.Light(
            self.spectre.center_x, self.spectre.center_y - 50,
            radius=300,
            mode="soft",
        )
        self.light_layer.add(self.spectre_light)
        self.prepared_ice_stars = arcade.SpriteList()
        self.prepared_obs_stars = arcade.SpriteList()
        self.setup_background_gradient_switch()
        self.paused = False

        self.window.background_color = arcade.color.FRESH_AIR
        self.on_resize(self.window.width, self.window.height)
        self.start_fade_in()

    def setup_background_gradient_switch(self) -> None:
        self.background_gradient_to_ice = model.get_gradient(
            arcade.color.FRESH_AIR[:3], (0, 51, 96),
            BACKGROUND_GRADIENT_STEPS,
        )[::-1]
        self.background_gradient_to_obs = model.get_gradient(
            (0, 51, 96), (20, 20, 20), BACKGROUND_GRADIENT_STEPS,
        )[::-1]
        for _ in range(100):
            star = arcade.Sprite(
                path_or_texture=TEXTURES_PATH.get("star"),
                scale=random.randint(1, 3),
                center_x=random.randint(10, self.window.width - 10),
                center_y=random.randint(10, self.window.height - 10),
            )
            self.prepared_ice_stars.append(star)
        for _ in range(20):
            scale = random.randint(1, 2)
            stem = (
                "blinking_star_{i}.png"
                if scale == 1
                else "blinking_star_big_{i}.png"
            )
            star = model.AnimatedSprite(
                scale=scale,
                center_x=random.randint(10, self.window.width - 10),
                center_y=random.randint(10, self.window.height - 10),
            )
            star.add_textures({
                "blinking": model.load_texture_series(
                    TEXTURES_PATH / "obsidian",
                    stem,
                    range(1, 3),
                )
            })
            star.state = "blinking"
            self.prepared_obs_stars.append(star)

    def start_background_gradient_to_ice(self) -> None:
        def change_color(dt: float) -> None:
            if not self.background_gradient_to_ice:
                arcade.unschedule(change_color)
                return
            color = self.background_gradient_to_ice.pop()
            self.window.background_color = color

        arcade.schedule(change_color, 1 / BACKGROUND_GRADIENT_STEPS)

        self.scene["ambient"].clear()

    def start_background_gradient_to_obs(self) -> None:
        def change_color(dt: float) -> None:
            if not self.background_gradient_to_obs:
                arcade.unschedule(change_color)
                return
            color = self.background_gradient_to_obs.pop()
            self.window.background_color = color

        arcade.schedule(change_color, 1 / BACKGROUND_GRADIENT_STEPS)

        self.spectre_light.radius = 500.0

        self.scene["ambient"].clear()

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

    def place_butterfly(self, dt: float) -> None:
        if (
            self.player.center_x
            < MAP_WIDTH * TILE_SIZE * TILE_SCALING * MAPS_PER_BIOME
        ):
            butterfly = model.AnimatedSprite(scale=2)
            i = random.randint(1, 3)
            butterfly.add_textures({
                "moving": model.load_texture_series(
                    TEXTURES_PATH / "grass",
                    f"butterfly_small{i}_{{i}}.png",
                    range(1, 4),
                )
            })
            butterfly.state = "moving"
            butterfly.left = self.window.width
            butterfly.change_x = -35
            butterfly.center_y = self.window.height - random.randint(350, 500)
            self.scene["ambient"].append(butterfly)
        else:
            arcade.unschedule(self.place_butterfly)

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
        arcade.schedule(self.place_butterfly, 10.0)
        self.place_cloud(0)

        self.player.center_x = 30000

    def on_resize(self, width: int, height: int):
        self.title.center_x = width / 2
        self.title.center_y = height * 0.85

        self.click_to_play.center_x = width * 0.6
        self.click_to_play.center_y = height * 0.45

        self.show_credits.right = width - 20
        self.show_credits.top = height - 20

        self.quit_game.left = 20
        self.quit_game.bottom = 20

        self.tip_speed.center_x = width * 0.8
        self.tip_speed.center_y = height * 0.65

        self.pause_continue.center_x = width / 2
        self.pause_continue.center_y = height / 2 + 40
        self.pause_quit.center_x = width / 2
        self.pause_quit.top = self.pause_continue.bottom - 40

        self.light_layer.resize(width, height)

        for i, heart in enumerate(self.hearts):
            heart.top = height - 30
            heart.left = (i + 1) * 14 + i * heart.width + 16

        self.camera.match_screen()
        self.ui_camera.match_screen(False)

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
        layer_options = {
            "obstacles": {
                "custom_class": model.Sprite,
            }
        }
        init_map = arcade.tilemap.load_tilemap(
            map_file=MAPS_PATH.get("init_map.tmj"),
            scaling=TILE_SCALING,
            layer_options=layer_options,
        )
        self.maps.append(init_map)
        self.scene = arcade.Scene.from_tilemap(init_map)
        self.scene.add_sprite_list("obstacles", use_spatial_hash=True)
        self.scene.add_sprite_list("obsidian_obstacles", use_spatial_hash=True)
        self.scene.add_sprite_list("ambient")

        for i in range(1, MAPS_PER_BIOME + 1):
            map_num = random.randint(1, 6)
            map = arcade.tilemap.load_tilemap(
                map_file=MAPS_PATH.get(f"grass_{map_num}.tmj"),
                scaling=TILE_SCALING,
                layer_options=layer_options,
                offset=Vec2(
                    round((i * MAP_WIDTH) * TILE_SIZE * TILE_SCALING), 0
                ),
            )
            scene = arcade.Scene.from_tilemap(map)
            self.scene["walls"].extend(scene["walls"])
            self.maps.append(map)

        for i in range(1, MAPS_PER_BIOME + 1):
            map_num = random.randint(1, 3)
            map = arcade.tilemap.load_tilemap(
                map_file=MAPS_PATH.get(f"ice_{map_num}.tmj"),
                scaling=TILE_SCALING,
                layer_options=layer_options,
                offset=Vec2(
                    round(
                        ((MAPS_PER_BIOME + i) * MAP_WIDTH)
                        * TILE_SIZE * TILE_SCALING
                    ), 0
                ),
            )
            scene = arcade.Scene.from_tilemap(map)
            self.scene["walls"].extend(scene["walls"])
            self.scene["obstacles"].extend(scene["obstacles"])
            self.maps.append(map)

        for i in range(1, MAPS_PER_BIOME + 1):
            map_num = random.randint(1, 3)
            map = arcade.tilemap.load_tilemap(
                map_file=MAPS_PATH.get(f"obsidian_{map_num}.tmj"),
                scaling=TILE_SCALING,
                layer_options=layer_options,
                offset=Vec2(
                    round(
                        ((2 * MAPS_PER_BIOME + i) * MAP_WIDTH)
                        * TILE_SIZE * TILE_SCALING
                    ), 0
                )
            )
            scene = arcade.Scene.from_tilemap(map)
            self.scene["walls"].extend(scene["walls"])
            self.scene["obsidian_obstacles"].extend(
                scene["obsidian_obstacles"]
            )
            self.maps.append(map)

        dark_map = arcade.tilemap.load_tilemap(
            map_file=MAPS_PATH.get("darkness.tmj"),
            scaling=TILE_SCALING,
            layer_options=layer_options,
            offset=Vec2(
                round(
                    ((3 * MAPS_PER_BIOME + 1) * MAP_WIDTH)
                    * TILE_SIZE * TILE_SCALING
                ), 0
            )
        )
        dark_scene = arcade.Scene.from_tilemap(dark_map)
        self.scene["walls"].extend(dark_scene["walls"])
        self.scene["ambient"].extend(dark_scene["ambient"])
        self.maps.append(map)

        # Add checkpoints
        for wall in self.scene["walls"]:
            wall: model.Sprite
            if wall.properties.get("checkable"):
                if wall.center_x <= MAP_WIDTH * TILE_SCALING * TILE_SIZE:
                    continue  # Not on init map
                if random.random() < 0.02:
                    checkpoint = model.Sprite(
                        path_or_texture=TEXTURES_PATH.get("checkpoint"),
                        scale=TILE_SCALING,
                        center_x=wall.center_x,
                        center_y=wall.center_y + TILE_SIZE * TILE_SCALING,
                    )
                    if not arcade.check_for_collision_with_lists(
                        checkpoint,
                        [self.scene["obstacles"],
                         self.scene["obsidian_obstacles"]],
                    ):
                        self.scene["checkpoints"].append(checkpoint)

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

        self.show_credits = model.Sprite(
            path_or_texture=TEXTURES_PATH.get("show_credits"),
            scale=3,
        )
        self.ui_sprites.append(self.show_credits)

        self.quit_game = model.Sprite(
            path_or_texture=TEXTURES_PATH.get("quit_game"),
            scale=3,
        )
        self.ui_sprites.append(self.quit_game)

        self.tip_speed = model.Sprite(
            path_or_texture=TEXTURES_PATH.get("tip_speed"),
            scale=1,
            angle=0,
        )
        self.ui_sprites.append(self.tip_speed)

        self.hearts = arcade.SpriteList()
        for _ in range(3):
            self.hearts.append(model.Sprite(
                path_or_texture=TEXTURES_PATH.get("heart"),
                scale=4,)
            )

        self.pause_sprites = arcade.SpriteList()
        self.pause_continue = model.Sprite(
            path_or_texture=TEXTURES_PATH.get("continue"),
            scale=3,
        )
        self.pause_quit = model.Sprite(
            path_or_texture=TEXTURES_PATH.get("quit"),
            scale=3,
        )
        self.pause_sprites.extend([self.pause_continue, self.pause_quit])

    def on_update(self, delta_time: float) -> None:
        super().on_update(delta_time)

        if self.started and not self.ended and not self.paused:
            if not self.player.change_y > 0 and self.player.state == "moving":
                # Only gain if not jumping or going up
                self.player.change_x += SPEED_GAIN_PER_SECOND * delta_time
            elif self.player.center_x > MAP_WIDTH * TILE_SIZE * TILE_SCALING:
                # Even reduce speed to spice things up (not on init_map)
                self.player.change_x += SPEED_PENALTY_VERTICAL_PLUS
            self.spectre.change_x += SPEED_GAIN_PER_SECOND_SPECTRE * delta_time
            self.spectre.change_x = max(
                self.spectre.change_x, self.player.change_x - 10
            )
            self.spectre.change_x = max(
                self.spectre.change_x, self.player.change_x - SPECTRE_SPEED_CAP
            )
            self.engine.on_update(delta_time)
            self.scene.on_update(
                delta_time, ["ambient", "spectre", "obstacles"]
            )
            if self.spectre.state == "moving":
                self.spectre.center_y = self.player.center_y
                light_pos = (
                    self.spectre.center_x - 20, self.spectre.center_y - 20
                )
                self.spectre_light.position = light_pos

            for dripstone in self.scene["obstacles"]:
                dripstone: arcade.Sprite
                if dripstone.top < -500:
                    dripstone.remove_from_sprite_lists()
                elif not dripstone.change_y:
                    if dripstone.center_y > ICE_DRIPSTONE_FALL_HEIGHT:
                        if self.player.right + 140 > dripstone.left:
                            dripstone.change_y = -1000

            for checkpoint in self.scene["checkpoints"]:
                checkpoint: model.Sprite
                if not checkpoint.properties.get("active"):
                    if (
                        checkpoint.bottom < self.player.top
                        and checkpoint.left <= self.player.center_x
                        <= checkpoint.right
                    ):
                        checkpoint.properties["active"] = True
                        checkpoint.texture = arcade.load_texture(
                            file_path=TEXTURES_PATH.get("checkpoint_active"),
                        )

            if len(
                self.background_gradient_to_ice
            ) == BACKGROUND_GRADIENT_STEPS:
                if self.player.center_x >= (
                    MAPS_PER_BIOME + 1
                ) * MAP_WIDTH * TILE_SIZE * TILE_SCALING:
                    self.start_background_gradient_to_ice()
                    self.background_gradient_to_ice.pop()
            elif len(
                self.background_gradient_to_obs
            ) == BACKGROUND_GRADIENT_STEPS:
                if self.player.center_x >= (
                    2 * MAPS_PER_BIOME + 1
                ) * MAP_WIDTH * TILE_SIZE * TILE_SCALING:
                    self.start_background_gradient_to_obs()
                    self.background_gradient_to_obs.pop()

            if self.spectre.center_x + 500 > (
                3 * MAPS_PER_BIOME + 1
            ) * MAP_WIDTH * TILE_SIZE * TILE_SCALING:
                self.spectre.change_y = 0
            if self.player.center_x - 800 > (
                3 * MAPS_PER_BIOME + 1
            ) * MAP_WIDTH * TILE_SIZE * TILE_SCALING:
                self.end("victory")

            # Add stars
            if (
                (MAPS_PER_BIOME + 1) * MAP_WIDTH * TILE_SIZE * TILE_SCALING
            ) <= self.player.center_x <= (
                (2 * MAPS_PER_BIOME + 1) * MAP_WIDTH * TILE_SIZE * TILE_SCALING
            ):
                try:
                    self.scene["ambient"].append(self.prepared_ice_stars.pop())
                    self.scene["ambient"].append(self.prepared_ice_stars.pop())
                except (IndexError, ValueError):
                    pass
            elif self.player.center_x >= (
                2 * MAPS_PER_BIOME + 1
            ) * MAP_WIDTH * TILE_SIZE * TILE_SCALING:
                try:
                    self.scene["ambient"].append(self.prepared_obs_stars.pop())
                    self.scene["ambient"].append(self.prepared_obs_stars.pop())
                except (IndexError, ValueError):
                    pass

        self.scene.update_animation(delta_time)

        self.camera.match_screen()
        self.camera.position = (
            self.player.center_x,
            self.player.center_y + self.window.height / 8,
        )

        if not self.ended and self.player.center_y <= -200:
            self.try_res()
        elif not self.ended and self.spectre.right - 30 > self.player.left:
            self.try_res()
        elif arcade.check_for_collision_with_lists(
            self.player, [
                self.scene["obstacles"], self.scene["obsidian_obstacles"]
            ],
        ):
            self.try_res()

    def try_res(self) -> None:
        right_most_checkpoint = None
        for checkpoint in self.scene["checkpoints"]:
            checkpoint: model.Sprite
            if checkpoint.properties.get("active"):
                if (
                    not right_most_checkpoint
                    or checkpoint.center_x > right_most_checkpoint.center_x
                ):
                    right_most_checkpoint = checkpoint
        if not right_most_checkpoint:
            self.end()
            return

        try:
            self.hearts.pop()
        except (IndexError, ValueError):  # BUG SpriteList raises ValueError for some reason  # noqa
            self.end()
            return

        self.ended = True

        self.fade_rate = 200
        self.start_fade_out()

        def fade_back_in(dt: float) -> None:
            self.fade_rate = 100
            self.stop_fade_out()
            self.start_fade_in()

        arcade.schedule_once(fade_back_in, 1.0)
        arcade.schedule_once(lambda _: setattr(self, "fade_rate", 200), 1.5)

        def set_to_checkpoint(dt: float) -> None:
            self.player.state = "idling"
            self.player.update_animation(0)
            self.player.center_x = right_most_checkpoint.center_x
            self.player.bottom = right_most_checkpoint.bottom
            self.spectre.center_x = self.player.center_x - 320
            self.spectre.center_y = self.player.center_y
            self.spectre_light.position = self.spectre.center
            self.spectre.change_x = self.player.change_x + 2

        arcade.schedule_once(set_to_checkpoint, 1.0)

        def start_from_checkpoint(dt: float) -> None:
            self.ended = False
            self.player.state = "moving"

        arcade.schedule_once(start_from_checkpoint, 5.0)

    def end(self, state: str = "dead") -> None:
        self.ended = True
        self.player.state = state
        self.player.update_animation(0)
        self.next_view = OutroView if state == "victory" else GameView
        time = 3.0 if state == "victory" else 1.0
        arcade.schedule_once(lambda _: self.start_fade_out(), time)

    def on_draw(self) -> None:
        self.clear()

        with self.light_layer:
            arcade.draw_rect_filled(
                arcade.types.LBWH(0, 0, self.window.width, self.window.height),
                self.window.background_color,
            )
            self.ui_camera.use()
            self.scene.draw(["ambient"], pixelated=True)
            self.camera.use()
            self.scene.draw(
                ["walls", "obstacles", "obsidian_obstacles",
                 "checkpoints", "spectre", "player"],
                pixelated=True,
            )

        self.light_layer.draw(ambient_color=arcade.color.WHITE)

        if not self.started:
            self.ui_camera.use()
            self.ui_sprites.draw(pixelated=True)
        self.ui_camera.use()
        self.hearts.draw(pixelated=True)

        if self.paused:
            arcade.draw_rect_filled(
                arcade.types.LBWH(0, 0, self.window.width, self.window.height),
                arcade.types.Color(0, 0, 0, 100),
            )
            self.pause_sprites.draw(pixelated=True)

        self.draw_fading()

    @property
    def stop_jump_value(self) -> float:
        return -0.8 * self.player.change_y + JUMP_VELOCITY

    def on_key_press(self, symbol: int, modifiers: int):
        if self.started:
            if symbol == arcade.key.SPACE and self.engine.can_jump():
                self.engine.jump(JUMP_VELOCITY)
            elif symbol == arcade.key.ESCAPE:
                self.paused = not self.paused
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
            if self.paused:
                if button == arcade.MOUSE_BUTTON_LEFT:
                    if self.pause_continue.rect.point_in_rect((x, y)):
                        self.paused = False
                    elif self.pause_quit.rect.point_in_rect((x, y)):
                        self.paused = False
                        self.end()
            elif button == arcade.MOUSE_BUTTON_LEFT and self.engine.can_jump():
                self.engine.jump(JUMP_VELOCITY)
        else:
            if button == arcade.MOUSE_BUTTON_LEFT:
                if self.show_credits.rect.point_in_rect((x, y)):
                    self.next_view = CreditsView
                    self.fade_rate = 500
                    self.start_fade_out()
                elif self.quit_game.rect.point_in_rect((x, y)):
                    self.window.close()
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
