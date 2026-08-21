from src.core.gesture_state_machine import GestureState, GestureStateMachine


def test_ready_tracking_trigger_cooldown_and_rearm() -> None:
    machine = GestureStateMachine(cooldown_ms=800)
    assert machine.update(0.0, hand_present=True, open_palm=True) is GestureState.READY
    machine.mark_tracking()
    assert machine.state is GestureState.TRACKING
    machine.trigger(0.1)
    assert not machine.can_detect
    assert machine.update(0.7, hand_present=True, open_palm=True, motion_speed=1.0) is GestureState.COOLDOWN
    assert machine.update(0.91, hand_present=True, open_palm=True, motion_speed=1.0) is GestureState.WAIT_FOR_REARM
    machine.update(1.0, hand_present=True, open_palm=False)
    assert machine.update(1.2, hand_present=True, open_palm=False) is GestureState.NO_HAND
    assert machine.update(1.3, hand_present=True, open_palm=True) is GestureState.READY


def test_stationary_hand_rearms_only_after_hold() -> None:
    machine = GestureStateMachine(cooldown_ms=300)
    machine.update(0.0, hand_present=True, open_palm=True)
    machine.trigger(0.1)
    machine.update(0.4, hand_present=True, open_palm=True, motion_speed=0.01)
    assert not machine.can_detect
    machine.update(0.73, hand_present=True, open_palm=True, motion_speed=0.01)
    assert machine.can_detect


def test_return_to_center_during_cooldown_rearms_at_cooldown_end() -> None:
    machine = GestureStateMachine(cooldown_ms=800)
    machine.update(0.0, hand_present=True, open_palm=True)
    machine.trigger(0.1)
    assert (
        machine.update(
            0.5,
            hand_present=True,
            open_palm=True,
            motion_speed=0.8,
            near_center=True,
        )
        is GestureState.COOLDOWN
    )
    assert (
        machine.update(
            0.91,
            hand_present=True,
            open_palm=True,
            motion_speed=0.8,
            near_center=False,
        )
        is GestureState.READY
    )
