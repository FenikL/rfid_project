# content of test_sample.py
import model

def test_probability():
    assert model.get_probability(1, 1).probability == 1