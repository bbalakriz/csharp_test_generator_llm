import os
from testgen.repo import find_cs_files

def test_find_cs_files(tmp_path):
    # create some .cs files and some excluded dirs
    src = tmp_path / "proj"
    (src / "bin").mkdir()
    (src / "Controllers").mkdir(parents=True)
    f1 = src / "Program.cs"
    f1.write_text("class C{}")
    f2 = src / "Controllers" / "HomeController.cs"
    f2.write_text("class HC{}")
    fs = list(find_cs_files(str(src)))
    # should find exactly two .cs files
    assert sorted(os.path.basename(p) for p in fs) == ["HomeController.cs", "Program.cs"]
