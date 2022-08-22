from github_scripts import utils


def test_get_top_perm_admin():
    expected = "privadmin"
    input1 = "privpull,privpush,privadmin"
    assert utils.get_top_perm(input1) == expected


def test_get_top_perm_push():
    expected = "privpush"
    input1 = "privpush,privpull"
    assert utils.get_top_perm(input1) == expected


def test_get_top_perm_pull():
    expected = "privpull"
    input1 = "privpull"
    assert utils.get_top_perm(input1) == expected
