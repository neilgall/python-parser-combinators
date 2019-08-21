from parsers import *

def test_result_ok():
	r = Result.ok(123, "xx")
	assert r.is_ok()


def test_result_err():
	r = Result.err("foo", "bar")
	assert r.is_err()


def test_the_letter_a():
	assert the_letter_a("a") == Result.ok((), "")
	assert the_letter_a("aaa") == Result.ok((), "aa")
	assert the_letter_a("baa") == Result.err("'a'", "baa")


def test_string():
	assert string("foo")("foo") == Result.ok((), "")
	assert string("foo")("foobar") == Result.ok((), "bar")
	assert string("foo")("barfoo") == Result.err("'foo'", "barfoo")


def test_integer():
	assert integer("123") == Result.ok(123, "")
	assert integer("123foo") == Result.ok(123, "foo")
	assert integer("bar") == Result.err("an integer", "bar")
	assert integer("") == Result.err("an integer", "")


def test_mul():
	p = the_letter_a * the_letter_a
	assert p("aa") == Result.ok(((), ()), "")
	assert p("aab") == Result.ok(((), ()), "b")
	assert p("ba") == Result.err("'a'", "ba")
	assert p("ab") == Result.err("'a'", "b")


def test_or():
	p1 = the_letter_a.retn(1)
	p2 = string("b").retn(2)
	p = p1 | p2
	assert p("aa") == Result.ok(1, "a")
	assert p("ba") == Result.ok(2, "a")
	assert p("ca") == Result.err("'a' or 'b'", "ca")


def test_before():
	p = the_letter_a.before(integer)
	assert p("a123") == Result.ok(123, "")
	assert p("b123") == Result.err("'a'", "b123")
	assert p("ab") == Result.err("an integer", "b")


def test_then():
	p = the_letter_a.then(integer)
	assert p("a123b") == Result.ok((), "b")
	assert p("b123a") == Result.err("'a'", "b123a")
	assert p("ab") == Result.err("an integer", "b")
