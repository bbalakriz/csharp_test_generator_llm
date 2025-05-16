import os
import subprocess
import logging
from typing import Optional

logger = logging.getLogger(__name__)

NUNIT_VERSION = "4.1.0"
TEST_ADAPTER_VERSION = "4.5.0"
TEST_SDK_VERSION = "17.9.0"
MOQ_VERSION = "4.20.70"

def init_nunit_project(base_dir: str, project_name: str) -> str:
    """
    scaffold a new `dotnet new nunit` project under base_dir.
    Returns the project directory.
    """
    proj_dir = os.path.join(base_dir, project_name)
    csproj = os.path.join(proj_dir, f"{project_name}.csproj")
    if not os.path.isfile(csproj):
        os.makedirs(proj_dir, exist_ok=True)
        subprocess.run(
            ["dotnet", "new", "nunit", "-n", project_name, "-f", "net8.0", "-o", proj_dir],
            check=True
        )
        # enforce versions
        for pkg, ver in [
            ("NUnit", NUNIT_VERSION),
            ("NUnit3TestAdapter", TEST_ADAPTER_VERSION),
            ("Microsoft.NET.Test.Sdk", TEST_SDK_VERSION),
            ("Moq", MOQ_VERSION),
        ]:
            subprocess.run(
                ["dotnet", "add", csproj, "package", pkg, "--version", ver],
                check=True
            )
    return proj_dir

def write_test_file(
    project_dir: str,
    original_cs: str,
    repo_root: str,
    test_code: str,
    dry_run: bool = False
) -> Optional[str]:
    """
    just write `test_code` to an appropriately named .cs file, mirroring original_cs path.
    If dry_run, only print path + preview.
    """
    rel = os.path.relpath(original_cs, start=repo_root)
    dest_dir = os.path.join(project_dir, os.path.dirname(rel))
    os.makedirs(dest_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(original_cs))[0] + "Tests.cs"
    dest = os.path.join(dest_dir, base)

    if dry_run:
        logger.info(f"[DRY RUN] Would write {len(test_code)} chars to {dest}")
        logger.info(f"[DRY RUN] Preview:\n{test_code[:200].rstrip()}…")
        return dest

    with open(dest, "w", encoding="utf-8") as f:
        f.write(test_code)
    logger.info(f"Wrote test file at {dest}")
    return dest

def run_and_verify_tests(project_dir: str, dry_run: bool = False) -> bool:
    """
    dotnet build & test. If dry_run, skip execution.
    """
    if dry_run:
        logger.info("[DRY RUN] Skipping build & test execution")
        return True

    build = subprocess.run(
        ["dotnet", "build", project_dir, "-c", "Release", "--nologo"],
        capture_output=True, text=True
    )
    if build.returncode != 0:
        logger.error(f"Build failed:\n{build.stdout}\n{build.stderr}")
        return False

    test = subprocess.run(
        ["dotnet", "test", project_dir, "--no-build", "--logger", "console;verbosity=minimal"],
        capture_output=True, text=True
    )
    logger.info(test.stdout)
    if test.returncode != 0:
        logger.error("Some tests failed.")
        return False

    logger.info("All tests passed!")
    return True
