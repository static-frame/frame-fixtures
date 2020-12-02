
.. image:: https://img.shields.io/pypi/pyversions/static-frame.svg
  :target: https://pypi.org/project/static-frame

.. image:: https://img.shields.io/pypi/v/frame-fixtures.svg
  :target: https://pypi.org/project/frame-fixtures

.. image:: https://img.shields.io/codecov/c/github/InvestmentSystems/frame-fixtures.svg
  :target: https://codecov.io/gh/InvestmentSystems/frame-fixtures


.. image:: https://img.shields.io/github/workflow/status/InvestmentSystems/frame-fixtures/Test?label=test&logo=Github
  :target: https://github.com/InvestmentSystems/frame-fixtures/actions?query=workflow%3ATest

.. image:: https://img.shields.io/github/workflow/status/InvestmentSystems/frame-fixtures/Quality?label=quality&logo=Github
  :target: https://github.com/InvestmentSystems/frame-fixtures/actions?query=workflow%3AQuality



frame-fixtures
===============

The FrameFixtures library defines a tiny domain-specific language that permits using compact expressions to create diverse, deterministic DataFrame fixtures with StaticFrame. The resulting ``Frame`` can be used for test, performance studies, or documentation examples, and can easily be converted to Pandas DataFrames or other representations available via StaticFrame.


Code: https://github.com/InvestmentSystems/frame-fixtures

Packages: https://pypi.org/project/frame-fixtures



Installation
-------------------------------

Install FrameFixtures via PIP::

    pip install frame-fixtures [extras]


The ``[extras]`` configuration includes StaticFrame as a requirement. As StaticFrame uses FrameFixtures, installation without ``[extras]`` assumes the availability of StaticFrame::

    pip install frame-fixtures


Examples
------------------------------

Import FrameFixtures with the following convention:

>>> import frame_fixtures as ff


Create a 4 by 8 ``Frame`` of string, Booleans, and floats.

>>> ff.parse('v(str,str,bool,float)|s(4,8)')
<Frame>
<Index> 0     1     2      3         4     5     6      7         <int64>
<Index>
0       zjZQ  zaji  True   1080.4    zDVQ  zEdH  True   647.9
1       zO5l  zJnC  False  2580.34   z5hI  zB7E  True   2755.18
2       zEdH  zDdR  False  700.42    zyT8  zwIp  False  -1259.28
3       zB7E  zuVU  True   3338.48   zS6w  zDVQ  False  3442.84
<int64> <<U4> <<U4> <bool> <float64> <<U4> <<U4> <bool> <float64>


The same ``Frame`` can be converted to Pandas:

>>> ff.parse('v(str,str,bool,float)|s(4,8)').to_pandas()
      0     1      2        3     4     5      6        7
0  zjZQ  zaji   True  1080.40  zDVQ  zEdH   True   647.90
1  zO5l  zJnC  False  2580.34  z5hI  zB7E   True  2755.18
2  zEdH  zDdR  False   700.42  zyT8  zwIp  False -1259.28
3  zB7E  zuVU   True  3338.48  zS6w  zDVQ  False  3442.84


Create a 4 by 4 ``Frame`` of Booleans with three-level index and columns.

>>> ff.parse('v(bool)|i(IH,(str,int,str))|c(IH,(str,int,str))|s(4,4)')
<Frame>
<IndexHierarchy>               zZbu   zZbu   zZbu   zZbu   <<U4>
                               105269 105269 119909 119909 <int64>
                               zDVQ   z5hI   zyT8   zS6w   <<U4>
<IndexHierarchy>
zZbu             105269  zDVQ  False  False  True   False
zZbu             105269  z5hI  False  False  False  False
zZbu             119909  zyT8  False  False  False  True
zZbu             119909  zS6w  True   False  True   True
<<U4>            <int64> <<U4> <bool> <bool> <bool> <bool>


The same ``Frame`` can be converted to Pandas:

>>> ff.parse('v(bool)|i(IH,(str,int,str))|c(IH,(str,int,str))|s(4,4)').to_pandas()
__index0__                         zZbu
__index1__                       105269        119909
__index2__                         zDVQ   z5hI   zyT8   zS6w
__index0__ __index1__ __index2__
zZbu       105269     zDVQ        False  False   True  False
                      z5hI        False  False  False  False
           119909     zyT8        False  False  False   True
                      zS6w         True  False   True   True


FrameFixtures support defining features unique to StaticFrame, such as specifying a grow-only ``FrameGO``, ``Index`` types within ``IndexHierarchy``, and usage of ``np.datetime64`` types other than nanoseconds. These specifications are not directly convertible to Pandas.

>>> ff.parse('f(Fg)|v(int,bool,str)|i((IY,ID),(dtY,dtD))|c(ISg,dts)|s(6,2)')
<FrameGO>
<IndexSecondGO>                  1970-01-01T09:38:35 1970-01-01T01:00:48 <datetime64[s]>
<IndexHierarchy>
36685            2258-03-21      -88017              False
36685            2298-04-20      92867               False
5618             2501-10-08      84967               False
5618             2441-04-14      13448               False
93271            2234-04-07      175579              False
93271            2210-12-26      58768               False
<datetime64[Y]>  <datetime64[D]> <int64>             <bool>




Grammar
------------------------------

Container Components
.............................

A FrameFixture is defined by specifying one or more container components using symbols such as `s` for shape and ``i`` for index. Container components (CCs) are given arguments using Python function call syntax, and multiple CCs are delimited with ``|``. The shape CC takes ints as arguments; all other CCs take Constructor Specifiers (CS) and/or Dtype Specifiers (DS) as arguments. So a 100 by 20 ``Frame`` with an index of ``str`` is specified as ``s(100,20)|i(I,str)``, where 100 and 20 define the row and column counts, and `I` is the CC and `str` is the DS. Component symbols, whether components are required, and the number of required arguments, is summarized below.

+-------+----------+---------+----------+----------------------------------+
|Symbol |Component |Required |Arguments |Signature                         |
+=======+==========+=========+==========+==================================+
|f      |Frame     |False    |1         |(CS,)                             |
+-------+----------+---------+----------+----------------------------------+
|i      |Index     |False    |2         |(CS, DS) or ((CS, ...), (DS, ...))|
+-------+----------+---------+----------+----------------------------------+
|c      |Columns   |False    |2         |(CS, DS) or ((CS, ...), (DS, ...))|
+-------+----------+---------+----------+----------------------------------+
|v      |Values    |False    |unbound   |(DS, ...)                         |
+-------+----------+---------+----------+----------------------------------+
|s      |Shape     |True     |2         |(int, int)                        |
+-------+----------+---------+----------+----------------------------------+


Constructor Specifiers
.............................

CSs are given to the ``f`` CC; the ``i`` and ``c`` CC take one or many CSs as their first argument.

+-------+-----------------+
|Symbol |Class            |
+=======+=================+
|F      |Frame            |
+-------+-----------------+
|Fg     |FrameGO          |
+-------+-----------------+
|I      |Index            |
+-------+-----------------+
|Ig     |IndexGO          |
+-------+-----------------+
|IH     |IndexHierarchy   |
+-------+-----------------+
|IHg    |IndexHierarchyGO |
+-------+-----------------+
|IY     |IndexYear        |
+-------+-----------------+
|IYg    |IndexYearGO      |
+-------+-----------------+
|IYM    |IndexYearMonth   |
+-------+-----------------+
|IYMg   |IndexYearMonthGO |
+-------+-----------------+
|ID     |IndexDate        |
+-------+-----------------+
|IDg    |IndexDateGO      |
+-------+-----------------+
|IS     |IndexSecond      |
+-------+-----------------+
|ISg    |IndexSecondGO    |
+-------+-----------------+
|IN     |IndexNanosecond  |
+-------+-----------------+
|INg    |IndexNanosecondGO|
+-------+-----------------+




Dtype Specifiers
.............................

DSs are given to the ``v`` CC, and are used repeatedly to fill all columns; the ``i`` and ``c`` CC take one or many DSs as their second argument.


+-----------+--------------------------+
|Symbol     |Class                     |
+===========+==========================+
|dtY        |dtype('<M8[Y]')           |
+-----------+--------------------------+
|dtM        |dtype('<M8[M]')           |
+-----------+--------------------------+
|dtD        |dtype('<M8[D]')           |
+-----------+--------------------------+
|dts        |dtype('<M8[s]')           |
+-----------+--------------------------+
|dtns       |dtype('<M8[ns]')          |
+-----------+--------------------------+
|tdY        |dtype('<m8[Y]')           |
+-----------+--------------------------+
|tdM        |dtype('<m8[M]')           |
+-----------+--------------------------+
|tdD        |dtype('<m8[D]')           |
+-----------+--------------------------+
|tds        |dtype('<m8[s]')           |
+-----------+--------------------------+
|tdns       |dtype('<m8[ns]')          |
+-----------+--------------------------+
|int        |<class 'int'>             |
+-----------+--------------------------+
|str        |<class 'str'>             |
+-----------+--------------------------+
|float      |<class 'float'>           |
+-----------+--------------------------+
|bool       |<class 'bool'>            |
+-----------+--------------------------+
|complex    |<class 'complex'>         |
+-----------+--------------------------+
|object     |<class 'object'>          |
+-----------+--------------------------+
|int8       |<class 'numpy.int8'>      |
+-----------+--------------------------+
|int16      |<class 'numpy.int16'>     |
+-----------+--------------------------+
|int32      |<class 'numpy.int32'>     |
+-----------+--------------------------+
|int64      |<class 'numpy.int64'>     |
+-----------+--------------------------+
|float16    |<class 'numpy.float16'>   |
+-----------+--------------------------+
|float32    |<class 'numpy.float32'>   |
+-----------+--------------------------+
|float64    |<class 'numpy.float64'>   |
+-----------+--------------------------+
|complex64  |<class 'numpy.complex64'> |
+-----------+--------------------------+
|complex128 |<class 'numpy.complex128'>|
+-----------+--------------------------+



