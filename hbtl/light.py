from __future__ import annotations

import math
import arcade
from arcade.draw_commands import draw_lbwh_rectangle_textured
from arcade.experimental.lights import Light, LightLayer

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Lighting Demo (Experimental)"


class MyGame(arcade.Window):

    def __init__(self, width, height, title):
        """
        Set up the application.
        """
        super().__init__(width, height, title, resizable=True)
        self.time = 0
        self.background_color = arcade.color.AERO_BLUE
        # self.background = arcade.load_texture(":resources:images/backgrounds/abstract_1.jpg")

        self.light_layer = LightLayer(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.moving_light = Light(400, 300, radius=300, mode='soft')
        self.light_layer.add(self.moving_light)

    def on_draw(self):
        self.clear()

        with self.light_layer:
            arcade.draw_rect_filled(arcade.types.LBWH(0, 0, self.width, self.height), arcade.color.AERO_BLUE)
            # draw_lbwh_rectangle_textured(
            #     0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, self.background)

        self.light_layer.draw(ambient_color=arcade.types.Color(255, 255, 255, 255))

    def on_update(self, dt):
        self.time += dt
        self.moving_light.position = (
            400 + math.sin(self.time) * 300,
            300 + math.cos(self.time) * 50
        )
        self.moving_light.radius = 300 + math.sin(self.time * 2.34) * 150

    def on_resize(self, width, height):
        self.default_camera.use()
        # self.light_layer.resize(width, height)


if __name__ == "__main__":
    MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    arcade.run()
