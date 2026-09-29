from qvc.normalize import normalize_pair


def test_normalize_pair_mg_g():
    c, e = normalize_pair("500 mg daily", "0.5 g daily")
    assert "500 mg" in c and "500 mg" in e
