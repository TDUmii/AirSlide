from src.core.slide_controller import SlideController


def test_controller_sends_only_configured_arrow_keys() -> None:
    pressed: list[str] = []
    controller = SlideController(press_function=pressed.append)
    assert controller.next_slide()
    assert controller.previous_slide()
    assert pressed == ["right", "left"]


def test_controller_contains_keyboard_error() -> None:
    def fail(_key: str) -> None:
        raise RuntimeError("synthetic failure")
    assert not SlideController(press_function=fail).next_slide()
