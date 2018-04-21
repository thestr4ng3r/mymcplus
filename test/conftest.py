
import sys, os
import pytest
import tarfile
import shutil

test_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(test_dir, "..", "mymc")))

@pytest.fixture(scope="session")
def data(tmpdir_factory):
    data_dir = tmpdir_factory.mktemp("data")
    path = os.path.join(test_dir, "data.tar.gz")
    tar = tarfile.open(path)
    tar.extractall(data_dir.strpath)
    return data_dir

@pytest.fixture
def mc01_copy(data, tmpdir):
    shutil.copy(data.join("mc01.ps2").strpath, tmpdir.strpath)
    return tmpdir