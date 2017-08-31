bit_overfl_exc_txt = '{0} cannot fit in {1} bits'
NBITS_AUTO = float('inf')


class Field:
    """Abstract field base class."""

    def __init__(self, nbits, name=None, value=None,
                 bsum=None, allow_auto_nbits=False):
        self.enc_value = None
        self.name = self._validate_name(name)
        self._nbits = self._validate_nbits(nbits, allow_auto_nbits)
        self._value = value
        if value is not None:
            self.encode()

    def __repr__(self):
        return f'{self.__class__.__name__}({self.value})'

    @classmethod
    def check_capacity(self, enc_value, nbits, value):
        """
        Check if a given value fits in bits limit.

        Parameters
        ----------
        enc_value : field type
            Encoded value
        nbits: int
            Bits limit
        value: int
            Decoded value

        Returns
        -------
        bool
            Raises OverflowError error if value doesn't fit

        """
        raise NotImplementedError

    def encode(self):
        """Convert value to bytes."""
        raise NotImplementedError

    def decode(self, value):
        """
        Decode value.

        Parameters
        ----------
        value : field type
            Value to be decoded

        Returns
        -------
            Decoded value

        """
        raise NotImplementedError

    def _validate_name(self, name):
        if name and name.startswith('___'):
            raise ValueError('Field name cannot start with `___`')
        return name

    def _validate_nbits(self, nbits, allow_auto_nbits):
        if not (isinstance(nbits, int) or nbits == NBITS_AUTO):
            raise ValueError(
                'First argument must be either '
                'integer or NBITS_AUTO')
        if nbits == NBITS_AUTO and not allow_auto_nbits:
            raise ValueError('NBITS_AUTO not allowed for this field')
        return nbits

    def _force_nbits(self, nbits):
        if nbits == NBITS_AUTO:
            raise ValueError(
                f'{self.__class__.__name__} '
                'field requires fixed number of bits'
            )

    @property
    def value(self):
        """Field value"""
        return self._value

    @value.setter
    def value(self, value):
        self.encode()
        self._value = value

    @property
    def nbits(self):
        """Bits limit"""
        return self._nbits

    @nbits.setter
    def nbits(self, nbits):
        self.check_capacity(self.enc_value, nbits, self.value)
        self._nbits = nbits


class SignedDecimal(Field):
    """Abstract field for Decimals"""

    def __init__(self, nbits, name=None, value=None):
        super().__init__(nbits, name, value)

    @classmethod
    def check_capacity(cls, enc_value, nbits, value):
        if enc_value > 2 ** nbits - 1:
            raise OverflowError(bit_overfl_exc_txt.format(value, nbits))
        return True


class Bool(Field):
    """
    Boolean field.

    Value is always encoded to 0 or 1
    based on the same rules as standard library bool.

    Parameters
    ----------
    nbits: int
        Bits limit.
        When used in encoder value will be representeb by `nbits` bits.
    name: str
        (optional) Filed name.
    value: type
        (optional) Value which will be transformed to bits.

    """
    def __init__(self, nbits, name=None, value=None):
        super().__init__(nbits, name, value)

    def encode(self):
        if self._nbits == NBITS_AUTO:
            self._nbits = 1
        enc_value = int(bool(self.value))
        self.check_capacity(enc_value, self.nbits, self.value)
        self.enc_value = enc_value

    def decode(self, value):
        self._value = bool(value)
        return self._value

    @classmethod
    def check_capacity(cls, enc_value, nbits, value):
        if enc_value and nbits < 1:
            raise OverflowError(bit_overfl_exc_txt.format(value, nbits))
        return True


class Int(SignedDecimal):
    """
    Signed integer field.

    Accepts signed integers and encodes them using two's complement system.

    Parameters
    ----------
    nbits: int
        Bits limit.
        When used in encoder value will be representeb by `nbits` bits.
    name: str
        (optional) Filed name.
    value: int
        (optional) Value which will be transformed to bits.

    """
    def __init__(self, nbits, name=None, value=None):
        super().__init__(nbits, name, value)

    def encode(self):
        enc_value = self.value
        if enc_value < 0:
            enc_value += 2 ** self.nbits
        self.check_capacity(enc_value, self.nbits, self.value)
        self.enc_value = enc_value

    def decode(self, value):
        org_value = value
        if value >= (2 ** self.nbits) / 2:
            value -= 2 ** self.nbits
            if value >= 0:
                raise OverflowError(
                    bit_overfl_exc_txt.format(org_value, self.nbits))
        self._value = value
        return self._value


class Float(SignedDecimal):
    """
    Signed float field.

    Accepts signed floats and encodes them using two's complement system.

    Parameters
    ----------
    nbits: int
        Bits limit.
        When used in encoder value will be representeb by `nbits` bits.
    frac: int
        Number of decimal places.
    name: str
        (optional) Filed name.
    value: float
        (optional) Value which will be transformed to bits.

    """
    def __init__(self, nbits, frac, name=None, value=None):
        self.frac = frac
        super().__init__(nbits, name, value)

    def encode(self):
        enc_value = int(round(self.value * (10 ** self.frac), 0))
        if enc_value < 0:
            enc_value += 2 ** self.nbits
        self.check_capacity(enc_value, self.nbits, self.value)
        self.enc_value = enc_value

    def decode(self, value):
        org_value = value
        if value >= (2 ** self.nbits) / 2:
            value -= 2 ** self.nbits
            if value >= 0:
                raise OverflowError(
                    bit_overfl_exc_txt.format(org_value, self.nbits))
        self._value = value / (10 ** self.frac)
        return self._value


class Uint(Field):
    """
    Unsigned integer field.

    Accepts unsigned integers and encodes them to bits.

    Parameters
    ----------
    nbits: int
        Bits limit.
        When used in encoder value will be representeb by `nbits` bits.
    name: str
        (optional) Filed name.
    value: float
        (optional) Value which will be transformed to bits.

    """
    def __init__(self, nbits, name=None, value=None):
        super().__init__(nbits, name, value)

    def encode(self):
        assert self.value >= 0, 'Uint value needs to be positive'
        self.check_capacity(self.value, self.nbits, self.value)
        self.enc_value = self.value

    def decode(self, value):
        self._value = value
        return self._value

    @classmethod
    def check_capacity(cls, enc_value, nbits, value):
        if enc_value > 2 ** nbits - 1:
            raise OverflowError(bit_overfl_exc_txt.format(value, nbits))


class Ufloat(Field):
    """
    Unsigned float field.

    Accepts unsigned floats and encodes them to bits.

    Parameters
    ----------
    nbits: int
        Bits limit.
        When used in encoder value will be representeb by `nbits` bits.
    frac: int
        Number of decimal places.
    name: str
        (optional) Filed name.
    value: float
        (optional) Value which will be transformed to bits.

    """
    def __init__(self, nbits, frac, name=None, value=None):
        self.frac = frac
        super().__init__(nbits, name, value)

    def encode(self):
        assert self.value >= 0, 'Ufloat value must be positive'
        enc_value = int(round(self.value * (10 ** self.frac), 0))
        self.check_capacity(enc_value, self.nbits, self.value)
        self.enc_value = enc_value

    def decode(self, value):
        self._value = value / (10 ** self.frac)
        return self._value

    @classmethod
    def check_capacity(cls, enc_value, nbits, value):
        if enc_value > 2 ** nbits - 1:
            raise OverflowError(bit_overfl_exc_txt.format(value, nbits))


class Unicode(Field):
    """
    Unicode field.

    Encodes str to bytes.

    Parameters
    ----------
    nbits: int
        Bits limit.
        When used in encoder value will be representeb by `nbits` bits.
    name: str
        (optional) Filed name.
    value: str
        (optional) Value which will be transformed to bits.
    fill_type: str
        The way of filling remaining bytes.
        Possible choices are: 'prefix' or 'suffix'
        defualt: 'prefix'
    fill_char: str
        Character used to fill remaining bytes. Max 1B.
        default '\0'
    encoding: str
        Encoding used. Choices are: 'UTF-8', 'UTF-16'
        default: 'UTF-16'

    """
    supported_encodings = {
        'UTF-8': 8,
        'UTF-16': 16
    }

    def __init__(self, nbits, name=None, value=None,
                 fill_type='prefix', fill_char='\0',
                 encoding='UTF-16'):
        self._validate_fill(fill_type, fill_char)
        self._validate_encoding(encoding)
        self.fill_type = fill_type
        self.fill_char = fill_char
        self.encoding = encoding
        super().__init__(nbits, name, value)

    @classmethod
    def check_capacity(cls, enc_value, nbits, value):
        if len(enc_value) * 256 > nbits:
            raise OverflowError(bit_overfl_exc_txt.format(value, nbits))
        return True

    def _validate_fill(self, fill_type, fill_char):
        if not len(fill_char.encode()) == 1:
            raise ValueError('Invalid null_prefix field')
        if fill_type not in ('prefix', 'suffix'):
            raise ValueError(
                'fill_type must be either `suffix` or `prefix`')

    def _validate_encoding(self, encoding):
        if encoding not in self.supported_encodings:
            raise ValueError('Encoding {encoding} is not supported')

    def _fill_gap(self, value):
        if (self.nbits / 8 - len(value)) > 0:
            fill = bytearray(
                self.fill_char * int(self.nbits / 8 - len(value)),
                'utf8'
            )
            if self.fill_type == 'prefix':
                value = fill + value
            else:
                value = value + fill
        return value

    def _trim_fill(self, value):
        null = ord(self.fill_char)
        if self.fill_type == 'prefix':
            start_byte = next(
                num for num, i in enumerate(value) if i != null
            )
            value = value[start_byte:]
        else:
            end_byte = next(
                num for num, i in enumerate(reversed(value))
                if i != null
            )
            value = value[:-end_byte - 1]
        return value

    def encode(self):
        rval = self.value.encode(self.encoding)
        if self.nbits != NBITS_AUTO:
            self.check_capacity(rval, self.nbits, self.value)
            rval = self._fill_gap(rval)
        self.enc_value = rval
        if self.nbits == NBITS_AUTO:
            self.nbits = 2 ** len(rval) * 8

    def decode(self, value):
        try:
            value = self._trim_fill(value)
        except StopIteration:
            pass
        self._value = value.decode(self.encoding)
        return self._value
