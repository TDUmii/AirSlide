from src.core.gesture_state_machine import GestureState, GestureStateMachine


def test_default_cooldown_is_one_second() -> None:
    machine = GestureStateMachine()
    machine.update(0.0, hand_present=True, open_palm=True)
    machine.trigger(0.1)
    assert machine.update(1.09, hand_present=True, open_palm=True) is GestureState.COOLDOWN
    assert machine.update(1.10, hand_present=True, open_palm=True) is GestureState.READY


def test_ready_tracking_trigger_and_automatic_cooldown_recovery() -> None:
    machine = GestureStateMachine(cooldown_ms=500)
    assert machine.update(0.0, hand_present=True, open_palm=True) is GestureState.READY
    machine.mark_tracking()
    assert machine.state is GestureState.TRACKING
    machine.trigger(0.1)
    assert not machine.can_detect
    assert machine.update(0.59, hand_present=True, open_palm=True) is GestureState.COOLDOWN
    assert machine.update(0.60, hand_present=True, open_palm=True) is GestureState.READY


def test_no_hand_at_cooldown_end_returns_to_no_hand() -> None:
    machine = GestureStateMachine(cooldown_ms=500)
    machine.update(0.0, hand_present=True, open_palm=True)
    machine.trigger(0.1)
    assert machine.update(0.6, hand_present=False, open_palm=False) is GestureState.NO_HAND


def test_hand_position_does_not_affect_cooldown_recovery() -> None:
    machine = GestureStateMachine(cooldown_ms=500)
    machine.update(0.0, hand_present=True, open_palm=True)
    machine.trigger(0.1)
    assert machine.update(0.4, hand_present=True, open_palm=True) is GestureState.COOLDOWN
    assert machine.update(0.6, hand_present=True, open_palm=True) is GestureState.READY
