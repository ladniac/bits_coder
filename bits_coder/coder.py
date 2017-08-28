from fields import NBITS_AUTO, Uint


class BitsCoder:
    """
    Tool to encode/decode binary data.

    BitsCoder specifies format of data stored in binary format
    using fields.Fields. When the format is specified you can either
    decode from binary or encode data to binary format.

    Parameters
    ----------
    fields: list
        List of fields which inherit from `fields.Field`
    byteorder: unicode
        Byte order, choices are: 'big' or 'little'

    """

    def __init__(self, fields, byteorder='big'):
        assert byteorder in ['big', 'little'], \
            "byteorder must be either 'little' or 'big'"
        self.byteorder = byteorder
        self._fields = fields
        self._add_field_for_remaining_bits()
        self._map = {}
        self._create_fields_map()

    def _add_field_for_remaining_bits(self):
        bits_count = sum(
            field.nbits
            for field in self._fields
            if field.nbits != NBITS_AUTO
        )
        remaining_bits = bits_count % 8
        if remaining_bits:
            self._fields.append(Uint(nbits=remaining_bits, value=0))

    def _create_fields_map(self):
        underscore_counter = 1
        for field in self._fields:
            if not field.name:
                field.name = '___{}'.format(underscore_counter)
                underscore_counter += 1
            self._map[field.name] = field.value

    def validate_fields_for_encoding(self):
        if not all(field.enc_value is not None for field in self._fields):
            raise ValueError('All fields need to have a value for encoding')

    @property
    def map(self):
        """Filed name to field value map."""
        self._create_fields_map()
        return self._map

    @property
    def list(self):
        """List of field's values."""
        if not hasattr(self, '_list'):
            self._list = [field.value for field in self._fields]
        return self._list

    def encode(self):
        """Encode all fields to bytearray."""
        self.validate_fields_for_encoding()
        byte_array = bytearray()
        last_byte = 0
        free_bits_left = 8

        for field in self._fields:
            shift = free_bits_left - field.nbits
            if shift >= 0:
                last_byte |= (field.enc_value << shift)
                free_bits_left = shift
                if shift == 0:
                    byte_array.append(last_byte)
                    last_byte = 0
            else:
                shift = abs(shift)
                last_byte |= (field.enc_value >> shift)
                byte_array.append(last_byte)
                full_bytes, remaining_bits = divmod(shift, 8)
                if full_bytes:
                    remaining_full_bytes_value = (
                        (field.enc_value >> remaining_bits) &
                        (2 ** (8 * full_bytes) - 1)
                    )
                    byte_array.extend(
                        remaining_full_bytes_value.to_bytes(
                            full_bytes, byteorder='big')
                    )
                if remaining_bits:
                    free_bits_left = 8 - remaining_bits
                    last_byte = (
                        (field.enc_value & (2 ** remaining_bits - 1)) <<
                        (8 - remaining_bits)
                    )
                else:
                    free_bits_left = 8
                    last_byte = 0
        if 0 < free_bits_left < 8:
            byte_array.append(last_byte)
        if self.byteorder == 'little':
            byte_array = byte_array[::-1]

        return byte_array

    def decode(self, pld):
        """Decode values from bytearray

        Parameters
        ----------
        pld: bytearray, str(hex)
            Payload to be decoded.

        """
        if isinstance(pld, str):
            pld = bytearray.fromhex(pld)
        byte_number = 0
        bits_on_byte_left = 8
        if self.byteorder == 'little':
            pld = pld[::-1]
        for field in self._fields:
            bytes_to_decode = bytearray([pld[byte_number]])
            if field.nbits > bits_on_byte_left:
                add_bytes, last_bits_used = divmod(
                    field.nbits - bits_on_byte_left, 8)
                end_byte_n = byte_number + add_bytes + (last_bits_used != 0)
                bytes_to_decode = pld[byte_number:end_byte_n + 1]
                bits_on_byte_left = 8 - last_bits_used
                byte_number += add_bytes + 1
            else:
                bits_on_byte_left -= field.nbits
            if not bits_on_byte_left:
                byte_number += 1
            value = (
                (
                    int.from_bytes(bytes_to_decode, byteorder='big') >>
                    (bits_on_byte_left % 8)
                ) &
                (2 ** field.nbits - 1)
            )
            field.decode(value)
