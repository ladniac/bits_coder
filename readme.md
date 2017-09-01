# BitsCoder

Tool for encoding/decoding binary messages

## Installation

Clone repository:

    $ git clone https://github.com/ladniac/bits_coder.git
    
Install package in your virtualenv:

    $ pip setup.py install
    
    
## Basic usage

### Encoding messages

Let's say we want to endode a following message:

    data = {
        'temperature': 21,
		 'is_nice': True,
		 'lat': 78.234,
		 'lon': -33.111
    }
    
And we want to use a following format:
[5b temperature][1b is_nice][18b lat][18b lon][5b empty]

    >>> from bits_coder.fields import Int, Bool, Float
    >>> from bits_coder.coder import BitsCoder
    >>> coder = BitsCoder(
    	[
    		Int(6, name='temperature', value=data['temperature']),
    		Bool(1, name='is_nice', value=data['is_nice']),
    		Float(18, frac=3, name='lat', value=data['lat']),
    		Float(18, frac=3, name='lon',  value=data['lon'])
    	]
    )


    >>> encoded_msg = coder.encode()
    >>> print(encoded_msg.hex())
    5698cd6fd520

You can use the same BitsCoder instance to decode messages (fields without names will be named as ___n):

    >>> coder.decode('FA123155A100')
    >>> print(coder.map)
    {'temperature': -2, 'is_nice': True, 'lat': 9.314, 'lon': -86.776, '___1': 0}

