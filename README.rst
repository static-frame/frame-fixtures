
.. image:: https://img.shields.io/pypi/pyversions/static-frame.svg?style=flat-square
  :target: https://pypi.org/project/static-frame

.. image:: https://img.shields.io/pypi/v/frame-fixtures.svg?style=flat-square
  :target: https://pypi.org/project/frame-fixtures

.. image:: https://github.com/InvestmentSystems/frame-fixtures/workflows/Test/badge.svg
  :target: https://github.com/InvestmentSystems/frame-fixtures/actions?query=workflow%3ATest

.. image:: https://github.com/InvestmentSystems/frame-fixtures/workflows/Quality/badge.svg
  :target: https://github.com/InvestmentSystems/frame-fixtures/actions?query=workflow%3AQuality


frame-fixtures
===============

The FrameFixtures library defines a tiny domain-specific language that permits using compact expressions to create diverse, deterministic DataFrame fixtures with StaticFrame. The resulting ``Frame`` can be used for test, performance studies, or documentation examples, and can easily be converted to Pandas DataFrames or other representations available via StaticFrame.


Code: https://github.com/InvestmentSystems/frame-fixtures

Packages: https://pypi.org/project/frame-fixtures



Installation
-------------------------------

Install FrameFixtures via PIP:

    pip install frame-fixtures [extras]


The ``[extras]`` configuration includes StaticFrame as a requirement. As StaticFrame uses FrameFixtures, installation without ``[extras]`` assumes the availability of StaticFrame.

    pip install frame-fixtures


Examples
---------------------

Import FrameFixtures with the following convention:

>>> import frame_fixtures as ff


Create a 4 by 8 ``Frame`` of string, Booleans, and floats.

>>> ff.Fixture.to_frame('v(str,str,bool,float)|s(4,8)')
<Frame>
<Index> 0     1     2      3         4     5     6      7         <int64>
<Index>
0       zjZQ  zaji  True   1080.4    zDVQ  zEdH  True   647.9
1       zO5l  zJnC  False  2580.34   z5hI  zB7E  True   2755.18
2       zEdH  zDdR  False  700.42    zyT8  zwIp  False  -1259.28
3       zB7E  zuVU  True   3338.48   zS6w  zDVQ  False  3442.84
<int64> <<U4> <<U4> <bool> <float64> <<U4> <<U4> <bool> <float64>


The same ``Frame`` can be converted to Pandas:

>>> ff.Fixture.to_frame('v(str,str,bool,float)|s(4,8)').to_pandas()
      0     1      2        3     4     5      6        7
0  zjZQ  zaji   True  1080.40  zDVQ  zEdH   True   647.90
1  zO5l  zJnC  False  2580.34  z5hI  zB7E   True  2755.18
2  zEdH  zDdR  False   700.42  zyT8  zwIp  False -1259.28
3  zB7E  zuVU   True  3338.48  zS6w  zDVQ  False  3442.84


Create a 10 by 4 ``Frame`` of objects and complex numbers with two-level index of string, date and a one-level column of strings.

>>> ff.Fixture.to_frame('v(object,complex)|i(IH,(str,dtD))|c(I,str)|s(10,4)')
<Frame>
<Index>                          zZbu     ztsv                zUvW     zkuW               <<U4>
<IndexHierarchy>
zZbu             2258-03-21      96520    (-610.8-2859.36j)   True     (1080.4-646.86j)
zZbu             2298-04-20      -88017   (3243.94+3740.6j)   False    (2580.34-314.34j)
ztsv             2501-10-08      92867    (-823.14+3261.32j)  105269   (700.42-2882.58j)
ztsv             2441-04-14      3884.98  (114.58-626.64j)    119909   (3338.48+2377.6j)
zUvW             2234-04-07      -646.86  (-3367.74+3793.88j) 194224   (2444.92-2574.48j)
zUvW             2210-12-26      -314.34  (2812.54-142.38j)   -2981.64 (3944.56-2077.98j)
zkuW             2224-04-06      zDdR     (1325.38-3512.22j)  3565.34  (2105.38+627.1j)
zkuW             2202-08-20      zuVU     (-3424.62-1404.42j) 3770.2   (2398.18+2890.4j)
zmVj             2006-10-27      zKka     (-779.94+837.08j)   zMmd     (3884.48+80.72j)
zmVj             2450-09-20      84967    (353.96-1107.72j)   zRKC     (3442.66+2873j)
<<U4>            <datetime64[D]> <object> <complex128>        <object> <complex128>

