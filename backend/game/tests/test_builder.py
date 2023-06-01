from game.actions.common import MessageBuilder


def test_simple():
    m = MessageBuilder()

    m.add("Hello!")
    m.add("World!")

    assert m.message == "Hello!\n\nWorld!"


def test_simple_op():
    m = MessageBuilder()

    m += "Hello!"
    m += "World!"

    assert m.message == "Hello!\n\nWorld!"


def test_list1():
    m = MessageBuilder()
    m.addList(["a", "b"])
    assert m.message == "- a\n- b"


def test_list2():
    m1 = MessageBuilder()

    with m1.startList("Hello!") as report:
        pass
    assert m1.message == ""

    m2 = MessageBuilder()
    with m2.startList("Hello!") as report:
        report("a")
        report("b")
    assert m2.message == "Hello!\n\n- a\n- b"
