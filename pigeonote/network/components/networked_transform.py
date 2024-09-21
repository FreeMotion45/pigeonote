import pygame
from pigeonote import Vector2
from pigeonote.network import NetworkedComponent, rpc


class NetworkedTransform(NetworkedComponent):
    interpolation_time: float = 0.1

    def init(self):
        self._previous_pos = self.position
        self._current_pos = self.position

        self._previous_rot = self.rotation
        self._current_rot = self.rotation

        self._time_since_last_update = 0

        if self.is_owner:
            self.schedule(self._periodic_update_transform, self.interpolation_time)

    def _periodic_update_transform(self):
        self._set_transform(self.position, self.rotation)
        self.schedule(self._periodic_update_transform, self.interpolation_time)

    @rpc()
    def _set_transform(self, new_position: Vector2, angle: float):
        if self.is_owner:
            return

        self._previous_pos = self._current_pos
        self._current_pos = new_position

        self._previous_rot = self._current_rot
        self._current_rot = angle

        self._time_since_last_update = 0

    def update(self):
        if self.is_owner:
            return

        interpolation_value = self._time_since_last_update / self.interpolation_time

        self.rotation = pygame.math.lerp(self._previous_rot, self._current_rot, interpolation_value)
        self.position = self._previous_pos.lerp(self._current_pos, interpolation_value)

        self._time_since_last_update += self.dt
