from decimal import Decimal
import unittest

from ...utils.parsers import strict_int, strict_real, ParsingError

class TestParsers(unittest.TestCase):

    def test_strict_int(self):
        # normal usage
        self.assertEqual(strict_int('420'), 420)
        self.assertEqual(strict_int('-69'), -69)
        self.assertEqual(strict_int('0'), 0)

        # big ints
        self.assertEqual(
            strict_int('-314159265358979323846264338327950288419716939937510'),
                        -314159265358979323846264338327950288419716939937510,
        )

        # empty, spaces
        with self.assertRaises(ParsingError): strict_int('')
        with self.assertRaises(ParsingError): strict_int(' ')
        with self.assertRaises(ParsingError): strict_int(' -420')
        with self.assertRaises(ParsingError): strict_int('69 ')
        with self.assertRaises(ParsingError): strict_int('  0  ')
        with self.assertRaises(ParsingError): strict_int('0 0')
        with self.assertRaises(ParsingError): strict_int('12 34')
        with self.assertRaises(ParsingError): strict_int('\t5')
        with self.assertRaises(ParsingError): strict_int('-6\n')

        # invalid characters
        with self.assertRaises(ParsingError): strict_int('bad')
        with self.assertRaises(ParsingError): strict_int('11bad')
        with self.assertRaises(ParsingError): strict_int('bad11')
        with self.assertRaises(ParsingError): strict_int('-11bad')
        with self.assertRaises(ParsingError): strict_int('bad-11')
        with self.assertRaises(ParsingError): strict_int('0bad')
        with self.assertRaises(ParsingError): strict_int('bad0')
        with self.assertRaises(ParsingError): strict_int('8x8')
        with self.assertRaises(ParsingError): strict_int('1.0')
        with self.assertRaises(ParsingError): strict_int('1.')
        with self.assertRaises(ParsingError): strict_int('.0')
        with self.assertRaises(ParsingError): strict_int('-1.0')
        with self.assertRaises(ParsingError): strict_int('-1.')
        with self.assertRaises(ParsingError): strict_int('-.0')
        with self.assertRaises(ParsingError): strict_int('7\0')
        with self.assertRaises(ParsingError): strict_int('0b1010\n')
        with self.assertRaises(ParsingError): strict_int('0o1010\n')
        with self.assertRaises(ParsingError): strict_int('0x1010\n')
        with self.assertRaises(ParsingError): strict_int('0xffff\n')
        with self.assertRaises(ParsingError): strict_int('ffff\n')

        # sign and leading zero problems
        with self.assertRaises(ParsingError): strict_int('+5')
        with self.assertRaises(ParsingError): strict_int('-0')
        with self.assertRaises(ParsingError): strict_int('-090')
        with self.assertRaises(ParsingError): strict_int('01')
        with self.assertRaises(ParsingError): strict_int('0000')

    # TODO test strict_int intervals

    def test_strict_real(self):
        # normal usage
        self.assertEqual(strict_real('123.45'), Decimal('123.450'))
        self.assertEqual(strict_real('-54.321'), -Decimal('54.3210'))
        self.assertEqual(strict_real('-0.123000'), Decimal('-0.12300'))
        self.assertEqual(strict_real('5.0'), Decimal('5'))
        self.assertEqual(strict_real('0.000'), Decimal('0'))
        self.assertEqual(strict_real('-5.0'), Decimal('-5'))
        self.assertEqual(strict_real('55'), Decimal('55'))
        self.assertEqual(strict_real('0'), Decimal('0'))
        self.assertEqual(strict_real('-55'), Decimal('-55'))

        # big decimals
        self.assertEqual(
            strict_real('-314159265358979323846264338327950288419716939937510'),
                Decimal('-314159265358979323846264338327950288419716939937510.000000'),
        )
        self.assertEqual(
            strict_real('3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679'),
                Decimal('3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679000000'),
        )

        # leading and trailing
        with self.assertRaises(ParsingError): strict_real('.1')
        with self.assertRaises(ParsingError): strict_real('1.')
        with self.assertRaises(ParsingError): strict_real('-.1')
        with self.assertRaises(ParsingError): strict_real('-1.')
        with self.assertRaises(ParsingError): strict_real('.0')
        with self.assertRaises(ParsingError): strict_real('0.')
        with self.assertRaises(ParsingError): strict_real('-.0')
        with self.assertRaises(ParsingError): strict_real('-0.')
        with self.assertRaises(ParsingError): strict_real('.')
        with self.assertRaises(ParsingError): strict_real('-')
        with self.assertRaises(ParsingError): strict_real('-.')

        # invalid characters
        with self.assertRaises(ParsingError): strict_real('bad')
        with self.assertRaises(ParsingError): strict_real('11.0bad')
        with self.assertRaises(ParsingError): strict_real('bad11.0')
        with self.assertRaises(ParsingError): strict_real('-11.0bad')
        with self.assertRaises(ParsingError): strict_real('bad-11.0')
        with self.assertRaises(ParsingError): strict_real('0.0bad')
        with self.assertRaises(ParsingError): strict_real('bad0.0')
        with self.assertRaises(ParsingError): strict_real('8x8')

        # empty, spaces
        with self.assertRaises(ParsingError): strict_real('')
        with self.assertRaises(ParsingError): strict_real(' ')
        with self.assertRaises(ParsingError): strict_real(' -420.0')
        with self.assertRaises(ParsingError): strict_real('69.0 ')
        with self.assertRaises(ParsingError): strict_real('  0.0  ')
        with self.assertRaises(ParsingError): strict_real('0.0 0.0')
        with self.assertRaises(ParsingError): strict_real('12.0 34.0')
        with self.assertRaises(ParsingError): strict_real('12 34.0')
        with self.assertRaises(ParsingError): strict_real('1 2.34')
        with self.assertRaises(ParsingError): strict_real('12. 34')
        with self.assertRaises(ParsingError): strict_real('12 .34')
        with self.assertRaises(ParsingError): strict_real('12.3 4')
        with self.assertRaises(ParsingError): strict_real('\t5.5')
        with self.assertRaises(ParsingError): strict_real('-6.6\n')

        # sign and leading zero problems
        with self.assertRaises(ParsingError): strict_real('+5')
        with self.assertRaises(ParsingError): strict_real('+5.5')
        with self.assertRaises(ParsingError): strict_real('+5.0')
        with self.assertRaises(ParsingError): strict_real('+0.5')
        with self.assertRaises(ParsingError): strict_real('+0.0')
        with self.assertRaises(ParsingError): strict_real('-0.0')
        with self.assertRaises(ParsingError): strict_real('05.1')
        with self.assertRaises(ParsingError): strict_real('-05.1')
        with self.assertRaises(ParsingError): strict_real('00.1')
        with self.assertRaises(ParsingError): strict_real('-00.1')
        with self.assertRaises(ParsingError): strict_real('-090.0')
        with self.assertRaises(ParsingError): strict_real('01.0')
        with self.assertRaises(ParsingError): strict_real('0000.0')

        # TODO more invalid usage

        # TODO more strict_real tests


    # TODO test strict_real params

    # TODO test strict_real intervals


if __name__ == '__main__':
    unittest.main()
