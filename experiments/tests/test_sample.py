# content of test_sample.py
import model

def test_probability():
    assert model.run_model(1, 1).probability == 1