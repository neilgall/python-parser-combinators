
from typing import Callable, Generic, Tuple, TypeVar

T = TypeVar('T')
U = TypeVar('U')
V = TypeVar('V')
Unit = Tuple[()]

class Result(Generic[T]):
	@classmethod
	def ok(self, value: T, remaining: str) -> "Result[T]":
		"""Construct a successful result"""
		r = self()
		r._tag = self.ok
		r._value = value
		r._remaining = remaining
		return r


	@classmethod
	def err(self, expected: str, actual: str) -> "Result[T]":
		"""Construct a failed result"""
		r = self()
		r._tag = self.err
		r._expected = expected
		r._actual = actual
		return r


	def __repr__(self) -> str:
		if self._tag == Result.ok:
			return f"ok({self._value}, {self._remaining})"
		else:
			return f"err({self._expected}, {self._actual})"


	def __eq__(self, other) -> bool:
		if self.is_ok() and other.is_ok():
			return self._value == other._value and self._remaining == other._remaining
		elif self.is_err() and other.is_err():
			return self._expected == other._expected and self._actual == other._actual
		else:
			return False


	def is_ok(self) -> bool:
		return self._tag == Result.ok


	def is_err(self) -> bool:
		return self._tag == Result.err


	def map(self, f: Callable[[T], U]) -> "Result[U]":
		"""
		Apply f to the value in this result, if successful
		"""
		if self.is_ok():
			return Result.ok(f(self._value), self._remaining)
		else:
			return self


	def flat_map(self, f: Callable[[T], "Parser[U]"]) -> "Result[U]":
		"""
		Apply f to the value and remaining text in this result, if successful
		"""
		if self.is_ok():
			return f(self._value, self._remaining)
		else:
			return self


	def map_expected(self, f: Callable[[str], str]) -> "Result[T]":
		"""
		Map f over the 'expected' message in this result, if not successful
		"""
		if self.is_ok():
			return self
		else:
			return Result.err(f(self._expected), self._actual)


class Parser(Generic[T]):
	"""
	Decorator for functions from str -> Result[T] providing
	combinator methods
	"""
	def __init__(self, parse: Callable[[str], Result[T]]):
		self._parse = parse


	def __call__(self, input: str) -> Result[T]:
		return self._parse(input)


	def map(self, f: Callable[[T], U]) -> "Parser[U]":
		"""
		Map 'f' over the result of this parser
		"""
		@Parser
		def _mapped(input: str) -> Result[U]:
			return self(input).map(f)
		return _mapped


	def flat_map(self, f: Callable[[T, str], "Parser[U]"]) -> "Parser[U]":
		"""
		Apply 'f' to the result and remaining text of this parser
		"""
		@Parser
		def _mapped(input: str) -> "Parser[U]":
			return self(input).flat_map(f)
		return mapped


	def retn(self, v: U) -> "Parser[U]":
		"""
		Replace the result of this parser with the constant 'v'
		"""
		@Parser
		def _mapped(input: str) -> Result[U]:
			return self(input).map(lambda _: v)
		return _mapped


	def __mul__(self, p2: "Parser[U]") -> "Parser[Tuple[T, U]]":
		"""
		A parser for the product of T and U where (as a tuple) where
		the source text for U immediately follows that for T
		"""
		def _step2(v1: T, r1: str) -> Result[Tuple[T, U]]:
			return p2(r1).map(lambda v2: (v1, v2))

		@Parser
		def _seq(input: str) -> Result[Tuple[T, U]]:
			return self(input).flat_map(_step2)

		return _seq


	def __or__(self, p2: "Parser[T]") -> "Parser[T]":
		"""
		A parser for T which tries this parser first, and 'p2' second
		if this parser fails
		"""
		@Parser
		def _or(input: str) -> Result[T]:
			r1 = self(input)
			if r1.is_ok():
				return r1
			else: 
				def _expect(e2: str) -> str:
					return f'{r1._expected} or {e2}'
				return p2(input).map_expected(_expect)
		return _or


	def before(self, p2: "Parser[U]") -> "Parser[U]":
		"""
		A parser for U which only succeeds if immediately preceeded
		by a successful match by this parser
		"""
		def _second(t: Tuple[T, U]) -> U:
			return t[1]

		return (self * p2).map(_second)


	def then(self, p2: "Parser[U]") -> "Parser[T]":
		"""
		A parser for T which only succeeds if immediately followed
		by a successful match by 'p2'. Both this and p2's input text
		are consumed
		"""
		def _first(t: Tuple[T, U]) -> T:
			return t[0]

		return (self * p2).map(_first)


class ParserRef(Generic[T]):
	def set(self, p: Parser[T]):
		self._p = p

	def __call__(self, input: str) -> Result[T]:
		return self._p(input)

	def get(self) -> Parser[T]:
		return Parser(self)


@Parser
def the_letter_a(input: str) -> Result[Unit]:
	"""
	A parser which returns Unit if the input text begins with 'a'
	"""
	if input[0] == 'a':
		return Result.ok((), input[1:])
	else:
		return Result.err("'a'", input)


def string(expected: str) -> Parser[str]:
	"""
	A parser which returns Unit if the input text begins with 'expected'
	"""
	@Parser
	def _parse(input):
		if input.startswith(expected):
			return Result.ok((), input[len(expected):])
		else:
			return Result.err(f"'{expected}'", input)
	return _parse


@Parser
def skip_whitespace(input: str) -> Result[Unit]:
	"""
	A parser which skips initial whitespace in the input
	"""
	return Result.ok((), input.lstrip(" \n\r\t"))

@Parser
def integer(input: str) -> Result[int]:
	"""
	A Parser which reads integers
	"""
	if not input or not input[0].isdigit():
		return Result.err("an integer", input)

	value = 0
	pos = 0
	while pos < len(input) and input[pos].isdigit():
		value = (value * 10) + (ord(input[pos]) - ord('0'))
		pos += 1

	return Result.ok(value, input[pos:])


