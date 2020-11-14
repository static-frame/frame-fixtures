
import numpy as np
import static_frame as sf
from frame_fixtures.frame_fixtures import Fixture


def get_str_to_type():
    mapping = {}
    mapping['F'] = sf.Frame



def test_parser_a() -> None:

    msg = 'f(Fg)|i(I,str)|c(IDg,dtD)|v(float)'
    msg = 'f(F)|i((I,I),(str,bool))|c((IN,I),(dtns,int))|v(str,bool,object)|s(10,10)'

    f1 = Fixture.to_frame(msg)


if __name__ == '__main__':
    test_parser_a()