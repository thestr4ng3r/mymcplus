
import mymc


def md5(fn):
    import hashlib
    return hashlib.md5(open(fn, "rb").read()).hexdigest()


def patch_fixed_time(monkeypatch, mod):
    def tod_now():
        return 42, 37, 22, 20, 4, 2018
    monkeypatch.setattr(mod, "tod_now", tod_now)


def patch_localtime(monkeypatch):
    import time
    def localtime(secs=None):
        return time.gmtime(secs)
    monkeypatch.setattr(time, "localtime", localtime)


def test_ls(monkeypatch, capsys, data):
    patch_localtime(monkeypatch)
    mymc.main(["mymc",
               "-i", data.join("mc01.ps2").strpath,
               "ls"])

    output = capsys.readouterr()
    assert output.err == ""
    assert output.out == ("rwx--d----+----       4 2018-04-21 14:53:07 .\n"
                          "-wx--d----+--H-       0 2018-04-21 14:53:00 ..\n"
                          "rwx--d-------H-       4 2018-04-21 14:53:01 BEDATA-SYSTEM\n"
                          "rwx--d----+----       5 2018-04-21 14:53:09 BESCES-50501REZ\n")


def test_extract(capsys, data, tmpdir):
    out_file = tmpdir.join("BESCES-50501REZ").strpath

    mymc.main(["mymc",
               "-i", data.join("mc01.ps2").strpath,
               "extract", "-o", out_file, "BESCES-50501REZ/BESCES-50501REZ"])

    output = capsys.readouterr()
    assert output.err == ""
    assert output.out == ""

    assert md5(out_file) == "5388344a2d4bb429b9a18ff683a8a691"


def test_add(monkeypatch, capsys, mc01_copy, tmpdir):
    import ps2mc
    patch_fixed_time(monkeypatch, ps2mc)
    patch_localtime(monkeypatch)

    file = tmpdir.join("helloworld.txt").strpath
    with open(file, "w") as f:
         f.write("Hello World!\n")

    mc_file = mc01_copy.join("mc01.ps2").strpath

    mymc.main(["mymc",
               "-i", mc_file,
               "add", file])

    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""

    mymc.main(["mymc",
               "-i", mc_file,
               "ls"])

    output = capsys.readouterr()
    assert output.out == ("rwx--d----+----       5 2018-04-20 13:37:42 .\n"
                          "-wx--d----+--H-       0 2018-04-21 14:53:00 ..\n"
                          "rwx--d-------H-       4 2018-04-21 14:53:01 BEDATA-SYSTEM\n"
                          "rwx--d----+----       5 2018-04-21 14:53:09 BESCES-50501REZ\n"
                          "rwx-f-----+----      13 2018-04-20 13:37:42 helloworld.txt\n")
    assert output.err == ""

    assert md5(mc_file) == "faa75353a97328c7d8fe38756c38fdd9"


def test_check_ok(capsys, data):
    mymc.main(["mymc",
               "-i", data.join("mc01.ps2").strpath,
               "check"])

    output = capsys.readouterr()
    assert output.out == "No errors found.\n"
    assert output.err == ""


def test_check_root_directory(capsys, mc01_copy):
    mc_file = mc01_copy.join("mc01.ps2").strpath
    with open(mc_file, "r+b") as f:
        f.seek(0x200)
        f.write("\x13\x37")

    assert md5(mc_file) == "bec7e8c3884806024b9eb9599dc4315f"

    mymc.main(["mymc",
               "-i", mc_file,
               "check"])

    output = capsys.readouterr()
    assert output.err == mc_file + ": Root directory damaged.\n"
    assert output.out == ""
