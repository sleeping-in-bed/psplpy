import image_util


def test_image_util():
    ltwh = (100, 200, 300, 400)
    ltrb = ((100, 200), (400, 600))
    four_vertexes = ((100, 200), (400, 200), (400, 600), (100, 600))

    assert image_util.get_box_center(ltrb) == (250, 400)

    assert image_util.trans_to_ltwh(ltrb) == ltwh
    assert image_util.trans_to_ltwh(ltwh) == ltwh
    assert image_util.trans_to_ltwh(four_vertexes) == ltwh

    assert image_util.trans_to_ltrb(ltrb) == ltrb
    assert image_util.trans_to_ltrb(ltwh) == ltrb
    assert image_util.trans_to_ltrb(four_vertexes) == ltrb

