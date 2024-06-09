"""This is mostly taken from my previous 'cme' project."""

import time
from enum import IntEnum
from pathlib import Path
from typing import Any, Iterable, Optional, Union

import arcade
from arcade.hitbox import HitBoxAlgorithm, SimpleHitBoxAlgorithm
from arcade.texture import Texture, load_texture


class CustomPhysicsEnginePlatformer(arcade.PhysicsEnginePlatformer):
    def on_update(self, delta_time: float) -> arcade.SpriteList[arcade.Sprite]:
        """
        Allow updating taking delta_time into account. `.change_x` attrs now
        take pixels per second (not .change_y).

        :param delta_time: Time since last update
        :type delta_time: float
        :return: List of all collisions
        :rtype: arcade.SpriteList[arcade.Sprite]
        """
        self.player_sprite.change_x = self.player_sprite.change_x * delta_time
        # self.player_sprite.change_y = self.player_sprite.change_y * delta_time  # noqa
        out = self.update()
        self.player_sprite.change_x = self.player_sprite.change_x / delta_time
        # self.player_sprite.change_y = self.player_sprite.change_y / delta_time  # noqa
        return out


class AssetsPath(type(Path())):  # type: ignore
    """
    Provides the find_asset method to recursively retrieve the given asset.

    Subclass or instantiate this to create a hierarchie of assets folders
    (e.g. `ImagesPath`, `SoundsPath`, ...).
    """
    def __new__(cls, *pathsegments: str | Path) -> "AssetsPath":
        obj: AssetsPath = super().__new__(cls, *pathsegments)
        obj.get = obj.find_asset
        return obj

    # Avoiding using an __init__ because it doesn't work really well with the
    # pathlib Path system

    def find_asset(
        self,
        asset: str,
        preferences: Optional[list[str]] = None,
    ) -> Path:
        """
        Returns first occurrence of the provided filename.

        `assets` parameter may use glob syntax.
        `preferences` should be a tuple containing preferred extensions.
        Defaults to `.png` and `.svg`. If None, the first match will be picked.
        """
        if preferences is None:
            preferences = [".png", ".svg"]

        for item in self.rglob(asset):
            if not preferences or item.suffix in preferences:
                return Path(item)
        else:
            if preferences:
                # Nothing found matching preferences, trying again without any
                return self.find_asset(asset, preferences=[])

            if "." not in asset:
                # .find_asset("filename") without ext should also be allowed
                return self.find_asset(fr"{asset}.*")

            raise FileNotFoundError(
                f"Could not find an asset with glob `{asset}`"
            )


class Facing(IntEnum):
    """
    Holds enums for common facing directories.
    Subclass to add your own.
    """
    RIGHT = 0
    LEFT = 1
    FRONT = 2
    BACK = 3


def load_texture_series(
    dir: Union[Path, str],
    stem: str,
    range_: Iterable[Any],
    hit_box_algorithm: HitBoxAlgorithm = SimpleHitBoxAlgorithm(),  # type: ignore[no-untyped-call]  # noqa
) -> list[Texture]:
    """Load a series of textures following a name schema from a directory.

    Args:
        dir (Union[Path, str]): The directory containing the textures
        stem (str): The name schema of the textures. Should contain the
        number/unique identifier as `{i}` to be interpolated the the
        str.format() method. Example: `"player_idle_{i}.png"`.
        range_ (Iterable): Any iterable with interpolation values. Example:
        `range(1, 7)` or `["idle", "walking", "jumping"]`.
        hit_box_algorithm (Literal["None", "Simple", "Detailed"]): Hit box
        algorithm.

    Returns:
        list[Texture]: A list of loaded textures.
    """
    dir = Path(dir)
    textures = []
    for i in range_:
        textures.append(load_texture(
            dir / stem.format(i=i),
            hit_box_algorithm=hit_box_algorithm,
        ))
    return textures


def jump_vertical_position(yo: float, vo: float, t: float, a: float) -> float:
    """
    Calculate the jump vertical position from jump time.

    :param yo: Initial vertical position
    :type yo: float
    :param vo: Initial vertical acceleration
    :type vo: float
    :param t: Time in jump
    :type t: float
    :param a: Gravity constant
    :type a: float
    :return: Vertical position
    :rtype: float
    """
    return yo + vo * t + 0.5 * a * t ** 2


class Updater:
    def update(self, sprite: arcade.Sprite, delta_time: float) -> None:
        raise NotImplementedError("update() should be overridden by subclass")


class SimpleUpdater(Updater):
    """Just move, taking delta_time into account."""

    def update(self, sprite: arcade.Sprite, delta_time: float) -> None:
        sprite.center_x += sprite.change_x * delta_time
        sprite.center_y += sprite.change_y * delta_time
        sprite.angle += sprite.change_angle * delta_time


class SlimeUpdater(Updater):
    """
    Move taking delta_time into account. Allow jumping up to a specific height.
    """
    MAX_JUMP_HEIGHT = 200

    def update(self, sprite: "SlimePlayer", delta_time: float) -> None:
        sprite.center_x += sprite.change_x * delta_time
        if not sprite.jumping and sprite.jump_key_held and sprite.on_ground:
            # Initiate jump
            sprite.jumping = True
            sprite.jump_initial_pos = sprite.bottom
            sprite.jump_time = 0.0
            sprite.time_force_jump = 0.4
        if sprite.jumping or sprite.jump_key_held and sprite.on_ground:
            y = jump_vertical_position(
                sprite.jump_initial_pos,
                100,
                sprite.jump_time,
                -9.8,
            )
            sprite.bottom = y
            if sprite.time_force_jump <= 0 and (wall := sprite.on_ground):
                sprite.bottom = wall.top + 1
                sprite.jumping = False

                # Would immediate init next otherwise
                sprite.jump_key_held = False


class Sprite(arcade.Sprite):
    """
    Enhances change_x, change_y and change_angle by multiplying with
    timedelta. Should generally be taken over ArcadeSprite.
    """
    def update(self) -> None:
        """
        Overriding due to the fact that arcade's default behavior updates
        Sprite positions while not taking delta_time into account.
        This does nothing. Logic is now in `on_update()`.
        """
        pass

    def on_update(  # type: ignore[override]  # (Save because it only adds a default argument)  # noqa
        self,
        delta_time: float,
        updater: Updater = SimpleUpdater(),
    ) -> None:
        """
        This method moves the sprite based on its velocity and angle change.
        Takes delta_time into account by multiplying it with the change values.
        """
        updater.update(self, delta_time)

    @property
    def center(self) -> tuple[float, float]:
        return (self.center_x, self.center_y)

    @center.setter
    def center(self, point: tuple[float, float]) -> None:
        self.center_x = point[0]
        self.center_y = point[1]


class AnimatedSprite(Sprite):
    """
    Provides Support for category based animations.
    Designed for internal use.

    Textures are provided and saved as a list of tuples per category. The
    tuples contain a sprite for each required facing directory. If you just
    require left and right facing it might be best for you to flip the textures
    while loading. For that use the `load_texture_pair()` function from this
    module.
    """

    def __init__(
        self,
        path_or_texture: Optional[str | arcade.Texture] = None,
        scale: float = 1,
        center_x: float = 0,
        center_y: float = 0,
        angle: float = 0,
    ) -> None:
        """
        `arcade.Sprite` constructor.

        Add textures afterwards with `texture_*` methods.
        `path_or_texture` parameter will be used as default.
        """
        super().__init__(
            path_or_texture=path_or_texture,
            scale=scale,
            center_x=center_x,
            center_y=center_y,
            angle=angle,
        )

        self.initial_texture_set = bool(path_or_texture)

        self.all_textures: dict[
            str, list[tuple[arcade.Texture, ...]]
        ] = {}

        self._state: Optional[str] = None
        self._last_state: Optional[str] = None

        self._facing: Facing | int = Facing.RIGHT

        self._animation_speed: float = 1
        self._last_animation_update = time.time()

    @property
    def state(self) -> Optional[str]:
        return self._state

    @state.setter
    def state(self, value: str) -> None:
        if value not in self.all_textures:
            raise ValueError(f"No textures found for state `{value}`")
        self._last_state = self._state
        self._state = value
        self.cur_texture_index = 0

    @property
    def facing(self) -> Facing | int:
        return self._facing

    @facing.setter
    def facing(self, value: Facing | int) -> None:
        self._facing = value

    @property
    def animation_speed(self) -> float:
        """Time between animation updates in seconds."""
        return self._animation_speed

    @animation_speed.setter
    def animation_speed(self, value: int) -> None:
        self._animation_speed = value

    def update_animation(self, delta_time: float = 1 / 60) -> None:
        """
        Updates the current texture by taking the next texture of the current
        state.
        This will update based on the specified `animation_speed` attribute.
        """

        if not self.state:
            raise RuntimeError(
                "Tried to update animation of Sprite without state"
            )

        current_time = time.time()
        if (
            self.state != self._last_state or
            current_time - self._last_animation_update >= self.animation_speed
        ):
            self._last_state = self.state  # Immediately switch if new state

            self.cur_texture_index += 1
            self._last_animation_update = current_time

            try:
                differently_faced_textures = self.all_textures[self.state][
                    self.cur_texture_index
                ]
            except IndexError:
                self.cur_texture_index = 0
                differently_faced_textures = self.all_textures[self.state][
                    self.cur_texture_index
                ]
            try:
                self.texture = differently_faced_textures[
                    self.facing
                ]
            except IndexError:
                self.texture = differently_faced_textures[0]
                print(
                    "Tried to update animation on Sprite with unavailable "
                    "facing, falling back to index 0.",
                )

        self.sync_hit_box_to_texture()  # type: ignore[no-untyped-call]

    def add_texture(
        self,
        texture: arcade.Texture | tuple[arcade.Texture, ...],
        category: str,
    ) -> None:
        """
        Add a texture to the sprite. category is commonly a string like
        `idling`, `walking`, `jumping`, etc.
        If given a tuple of Textures, multiple facing directories are stored
        and can later be accessed using the Facing enum from the enums module.
        """
        # Prevent weird Texture before first animation tick
        if not self.initial_texture_set:
            if isinstance(texture, tuple):
                self.texture = texture[0]
            else:
                self.texture = texture
            self.initial_texture_set = True

        if isinstance(texture, tuple):
            try:
                self.all_textures[category].append(texture)
            except KeyError:
                self.all_textures[category] = [texture]
        else:
            try:
                self.all_textures[category].append((texture,))
            except KeyError:
                self.all_textures[category] = [(texture,)]

    def add_textures(
        self, textures: dict[str, list[tuple[arcade.Texture, ...]]]
    ) -> None:
        """
        Add multiple Textures to the sprite. `textures` parameter should be a
        dict with a str as key indicating the category and a list of Textures
        as value.
        """
        for category, texture_list in textures.items():
            for texture_tuple in texture_list:
                self.add_texture(texture_tuple, category)

    def clear_textures(self) -> None:
        """
        Clear all textures added to this sprite, excluding the default one.
        """
        self.all_textures.clear()


class SlimePlayer(AnimatedSprite):
    def __init__(
        self,
        walls: arcade.SpriteList[arcade.Sprite],
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.walls = walls
        self.jump_time = 0.0
        self.should_die = False
        self._jump_key_held = False
        self.jump_initial_pos = 0.0
        self.jumping = False

        # To prevent jump getting caught immediately as on_ground
        self.time_force_jump = 0.0

    @property
    def jump_key_held(self) -> bool:
        return self._jump_key_held

    @jump_key_held.setter
    def jump_key_held(self, value: bool) -> None:
        self._jump_key_held = value
        if not self.jumping:
            self.jump_initial_pos = self.bottom

    @property
    def on_ground(self) -> Optional[arcade.Sprite]:
        for wall in self.walls:
            if wall.left <= self.center_x <= wall.right:
                if wall.top <= self.bottom <= wall.top + 5:
                    return wall

    def on_update(
        self,
        delta_time: float,
        updater: Updater = SlimeUpdater(),
    ) -> None:
        if self.time_force_jump > 0:
            self.time_force_jump = max(0, self.time_force_jump - delta_time)
        if self.jumping:
            self.jump_time += delta_time
        return super().on_update(delta_time, updater)


class AnimatedWalkingSprite(AnimatedSprite):
    """
    Adds out of the box support for idling und walking textures.

    Textures are provided and saved as a list of tuples per category. The
    tuples contain a sprite for each required facing directory. If you just
    require left and right facing it might be best for you to flip the textures
    while loading. For that use the `load_texture_pair()` function from this
    module.
    """

    def __init__(
        self,
        path_or_texture: Optional[str] = None,
        scale: float = 1,
        center_x: float = 0,
        center_y: float = 0,
        angle: float = 0,
    ) -> None:
        """
        `arcade.Sprite` constructor.

        Add textures afterwards with `texture_*` methods.
        `texture` parameter will be used as default.
        """

        super().__init__(
            path_or_texture=path_or_texture,
            scale=scale,
            center_x=center_x,
            center_y=center_y,
            angle=angle,
        )

    def set_idling(self) -> None:
        self.state = "idling"

    def set_walking(self) -> None:
        self.state = "walking"

    def texture_add_idling(
        self,
        textures: list[tuple[arcade.Texture, ...]],
    ) -> None:
        """
        Adds a list containing tuples of Textures and assigns them as idling
        textures.

        Obtain the Structure by collecting left-right faced texture tuples from
        `load_texture_pair()` in a list.
        If you only need one Texture for all possible facings or aren't using
        different facing directions at all, simply pass one-item tuples to the
        function.
        """
        for texture in textures:
            self.add_texture(texture, "idling")

    def texture_add_walking(
        self,
        textures: list[tuple[arcade.Texture, ...]],
    ) -> None:
        """
        Adds a list containing tuples of Textures and assigns them as walking
        textures.

        Obtain the Structure by collecting left-right texture tuples from
        `load_texture_pair()` in a list.
        If you only need one Texture for all possible facings or aren't using
        different facing directions at all, simply pass one-item tuples to the
        function.
        """
        for texture in textures:
            self.add_texture(texture, "walking")


def load_texture_pair(
    file_name: str | Path,
    **kwargs: Any,
) -> tuple[arcade.Texture, arcade.Texture]:
    """
    All `**kwargs` are passed to the `load_texture()` function and
    therefore applied to both textures. Don't use any `flipped_*` kwargs
    as they are internally used to flip the second sprite.
    """

    return (
        texture := load_texture(file_name, **kwargs),
        texture.flip_horizontally(),
    )


class FadingView(arcade.View):
    """Implements logic to fade a view in and/or out."""
    def __init__(
        self, window: Optional[arcade.Window] = None,
        fade_rate: int = 200,
        next_view: Optional[type[arcade.View]] = None,
    ):
        """
        `fade_rate` is the increase/decrease rate of the views opacity per
        second. E.g. with a `fade_rate` of 255 the view takes 1 seconds to
        fade.
        """
        super().__init__(window)
        self.fade_rate = fade_rate
        self.next_view = next_view
        self._fade_out: Optional[float] = None
        self._fade_in: Optional[float] = None

    def start_fade_in(self) -> None:
        """
        Start the fading. Usually called right when the view was constructed
        and set up.
        """
        self._fade_in = 255.0

    def start_fade_out(self) -> None:
        """
        Start the fading. Usually called right when the view is about to
        change.
        """
        self._fade_out = 0.0

    def stop_fade_out(self) -> None:
        """
        Stop fading out. Useful when fading does not happen on transition but
        during the view is active. This will remove the fading, so you can fade
        back in again.
        """
        self._fade_out = None

    def on_update(self, delta_time: float) -> None:
        """Overridden to call the update_fade() method."""
        super().on_update(delta_time)
        self.update_fade(delta_time)

    def update_fade(self, delta_time: float) -> None:
        """
        Updates the fade while taking into account the `delta_time` value.
        """
        step = self.fade_rate * delta_time

        if self._fade_out is not None:
            self._fade_out += step
            if self._fade_out > 255:
                if self.next_view:
                    next_view = self.next_view()
                    next_view.setup()
                    self.window.show_view(next_view)
                else:
                    self._fade_out = 255

        if self._fade_in is not None:
            self._fade_in -= step
            if self._fade_in <= 0:
                self._fade_in = None

    def draw_fading(self) -> None:
        if self._fade_out is not None:
            rect = arcade.types.LBWH(
                left=0,
                bottom=0,
                width=self.window.width,
                height=self.window.height,
            )
            arcade.draw_rect_filled(
                rect,
                color=(0, 0, 0, int(self._fade_out)),
            )

        if self._fade_in is not None:
            rect = arcade.types.LBWH(
                left=0,
                bottom=0,
                width=self.window.width,
                height=self.window.height,
            )
            arcade.draw_rect_filled(
                rect,
                color=(0, 0, 0, int(self._fade_in)),
            )


def get_gradient(start_color, end_color, num_colors):
    """
    Generate a gradient between two colors as a list of RGB tuples.

    Args:
        start_color (tuple): The starting color in RGB format
        (e.g. (0, 0, 255) for blue).
        end_color (tuple): The ending color in RGB format.
        num_colors (int): The number of colors in the gradient.

    Returns:
        list: A list of RGB tuples representing the gradient.
    """
    # Unpack the start and end colors
    start_r, start_g, start_b = start_color
    end_r, end_g, end_b = end_color

    # Calculate the step size for each color channel
    r_step = (end_r - start_r) / (num_colors - 1)
    g_step = (end_g - start_g) / (num_colors - 1)
    b_step = (end_b - start_b) / (num_colors - 1)

    # Generate the gradient
    gradient = []
    for i in range(num_colors):
        r = int(start_r + i * r_step)
        g = int(start_g + i * g_step)
        b = int(start_b + i * b_step)
        gradient.append((r, g, b))

    return gradient
