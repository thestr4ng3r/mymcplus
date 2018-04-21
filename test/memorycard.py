
import mymc

def md5(fn):
    import hashlib
    return hashlib.md5(open(fn, "rb").read()).hexdigest()

def test_ls(capsys, data):
    mymc.main(["mymc",
               "-i", data.join("mc01.ps2").strpath,
               "ls"])

    output = capsys.readouterr()
    assert output.err == ""
    assert output.out == ("rwx--d----+----       4 2018-04-21 16:53:07 .\n"
                          "-wx--d----+--H-       0 2018-04-21 16:53:00 ..\n"
                          "rwx--d-------H-       4 2018-04-21 16:53:01 BEDATA-SYSTEM\n"
                          "rwx--d----+----       5 2018-04-21 16:53:09 BESCES-50501REZ\n")


def test_extract(capsys, data, tmpdir):
    out_file = tmpdir.join("BESCES-50501REZ").strpath

    mymc.main(["mymc",
               "-i", data.join("mc01.ps2").strpath,
               "extract", "-o", out_file, "BESCES-50501REZ/BESCES-50501REZ"])

    output = capsys.readouterr()
    assert output.err == ""
    assert output.out == ""

    assert md5(out_file) == "5388344a2d4bb429b9a18ff683a8a691"

