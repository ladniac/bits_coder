import unittest

from fields import Int, Uint, Float, Ufloat, Bool, Unicode
from coder import BitsCoder


class TestFileds(unittest.TestCase):
    def test_bool_field(self):
        self.assertEqual(Bool(1, value=True).enc_value, 1)
        self.assertEqual(Bool(3).decode('true'), True)
        for val in [True, False, 1, 56, 0, '', 'true']:
            self.assertEqual(
                bool(val),
                Bool(1).decode(Bool(1, value=val).enc_value),
            )

    def test_int_filed(self):
        self.assertEqual(Int(3, value=2).enc_value, 2)
        self.assertEqual(Int(5).decode(19), -13)
        for n, val in enumerate(range(-2, 1, -11)):
            self.assertEqual(
                val,
                Int(2).decode(Int(n + 3, value=val).enc_value),
            )

    def test_uint_field(self):
        for val in range(2, 1):
            self.assertEqual(
                val,
                Uint(2).decode(Uint(2, value=val).enc_value),
            )

    def test_float_field(self):
        fields_params = [
            (7, 1, 5.1), (15, 2, -23.34), (32, 3, -23.45599)
        ]
        for n, field_params in enumerate(fields_params):
            enc_field = Float(*field_params[:2], value=field_params[2])
            dec_field = Float(*field_params[:2])
            self.assertAlmostEqual(
                field_params[2],
                dec_field.decode(enc_field.enc_value),
                n + 1
            )

    def test_ufloat_field(self):
        fields_params = [
            (7, 1, 5.1), (15, 2, 23.34), (32, 3, 23.45513)
        ]
        for n, field_params in enumerate(fields_params):
            enc_field = Ufloat(*field_params[:2], value=field_params[2])
            dec_field = Ufloat(*field_params[:2])
            self.assertAlmostEqual(
                field_params[2],
                dec_field.decode(enc_field.enc_value),
                n + 1
            )

    def test_unicode_field(self):
        value = 'ćwie®ć'
        field = Unicode(256 * 14, value=value)
        self.assertEqual(
            value,
            field.decode(field.enc_value),
        )

    def test_encoder(self):
        fields_to_encode = [
            Int(3, value=1),
            Int(8, value=9),
            Int(5, value=3),
        ]
        coder = BitsCoder(fields_to_encode)
        enc = coder.encode()
        proper_value = 0b001_00001001_00011
        self.assertEqual(enc, proper_value.to_bytes(2, 'big'))

        coder = BitsCoder(fields_to_encode, byteorder='little')
        enc = coder.encode()
        self.assertEqual(enc, proper_value.to_bytes(2, 'little'))

        fields_to_encode = [
            Float(7, 1, value=-1.3),
            Bool(1, value=True),
            Int(8, value=-3),
        ]
        coder = BitsCoder(fields_to_encode)
        enc = coder.encode()
        proper_value = 0b1110011_1_0000000011111101.to_bytes(3, 'big')
        self.assertEqual(enc, proper_value)

        # empty fill
        fields_to_encode = [
            Ufloat(5, 1, value=1.3),
            Uint(8, value=9),
            Int(4, value=-3),
        ]
        coder = BitsCoder(fields_to_encode)
        enc = coder.encode()
        proper_value = 0b01101_00001001_1101_0000000.to_bytes(3, 'big')
        self.assertEqual(enc, proper_value)

    def test_decoder(self):
        proper_map = {'a': -12, 'b': 2.11, 'c': True, 'd': 12, '___1': 0}
        pld = 'e9a7003000'
        fields = [
            Int(7, name='a'),
            Ufloat(8, 2, name='b'),
            Bool(1, name='c'),
            Int(6, name='d')
        ]
        coder = BitsCoder(fields)
        coder.decode(pld)
        self.assertEqual(proper_map, coder.map)


if __name__ == '__main__':
    unittest.main()
