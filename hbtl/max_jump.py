from . import model


def calc_max_jump_change_ys(
    gravity: float,
    initial_velocity: float,
    fps: float = 1000,
) -> dict[float, float]:
    """
    Calculate a jump 'path' of change_y of a sprite until it starts dropping
    down again (does not include dropping down, last value is highest point).

    :param gravity: Gravity as expected by model.CustomPhysicsEnginePlatformer
    :type gravity: float
    :param initial_velocity: Initial velocity as expected by engine.jump()
    (per second)
    :type initial_velocity: float
    :param fps: FPS to calculate the jump curve, defaults to 1000
    :type fps: float, optional
    :return: Dict of time in jump to change_y value
    :rtype: dict[float, float]
    """
    vel_per_frame = initial_velocity / fps
    player = model.Sprite()
    engine = model.CustomPhysicsEnginePlatformer(
        player_sprite=player,
        gravity_constant=gravity,
    )
    change_ys: dict[float, float] = {}
    engine.jump(vel_per_frame)
    change_ys[0.0] = player.change_y
    time = 0.0
    while change_ys[list(change_ys)[-1]] > 0:
        engine.on_update(1 / fps)
        time += 1 / fps
        change_ys[time] = player.change_y
    change_ys.popitem()
    return change_ys
