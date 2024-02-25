from typing import Generic, Literal, TypeVar

T_co = TypeVar("T_co", covariant=True)  # Success type
E_co = TypeVar("E_co", covariant=True)  # Error type


class Ok(Generic[T_co]):
    def __init__(self, value: T_co):
        self._value = value

    @staticmethod
    def is_ok() -> Literal[True]:
        return True

    @staticmethod
    def is_err() -> Literal[False]:
        return False

    @property
    def ok_value(self):
        return self._value


class Err(Generic[E_co]):
    def __init__(self, value: E_co):
        self._value = value

    @staticmethod
    def is_ok() -> Literal[False]:
        return False

    @staticmethod
    def is_err() -> Literal[True]:
        return True

    @property
    def err_value(self):
        return self._value


Result = Ok[T_co] | Err[E_co]
