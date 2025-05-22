# run.py

import os
import logging
import shutil
import subprocess
from typing import Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

from testgen.repo import get_repo, find_cs_files
from testgen.cache import init_cache, compute_sha256_hash, get_cached_test, cache_test
from testgen.extractor import ensure_extractor_tool, extract_classes_info_from_cs_file
from testgen.generator import generate_nunit_test_class
from testgen.writer import init_nunit_project, write_test_file

# ------------- CONFIGURATION -------------
REPO_URL = "https://github.com/anuraj/MinimalApi"
BRANCH = "main"
OUTPUT_DIR = os.path.abspath("generated_tests_output")
SRC_SUBDIR = "src"                    # where we’ll clone the original repo
LL_MODEL = "qwen2.5:7b"
PROVIDER = "ollama"
# PROVIDER = "openai"
# LL_MODEL = "o4-mini"
TEST_PROJECT_NAME = "GeneratedTests"
FORCE_REGENERATE = False
DRY_RUN = False
MAX_WORKERS = 1
# ------------------------------------------------

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    # 1) Ensure our OUTPUT_DIR structure
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    src_dir = os.path.join(OUTPUT_DIR, SRC_SUBDIR)
    if os.path.isdir(src_dir):
        shutil.rmtree(src_dir)
    os.makedirs(src_dir, exist_ok=True)

    # 2) Clone the original repository into OUTPUT_DIR/src
    logger.info(f"Cloning {REPO_URL} into {src_dir}")
    get_repo(src_dir, REPO_URL, BRANCH)

    # 3) Locate the original .csproj (non-test) inside src_dir
    original_csproj = None
    for root, dirs, files in os.walk(src_dir):
        for f in files:
            if f.lower().endswith(".csproj") and "test" not in f.lower():
                original_csproj = os.path.join(root, f)
                break
        if original_csproj:
            break

    if not original_csproj:
        logger.error("Could not find a .csproj in the cloned source directory.")
        return

    # 4) Build the Roslyn extractor
    extractor_dll, _ = ensure_extractor_tool(OUTPUT_DIR)

    # 5) Initialize an empty NUnit test project under OUTPUT_DIR/GeneratedTests
    test_proj_dir = init_nunit_project(OUTPUT_DIR, TEST_PROJECT_NAME)
    test_csproj_path = os.path.join(test_proj_dir, f"{TEST_PROJECT_NAME}.csproj")

    # 6) Create (or overwrite) a solution in OUTPUT_DIR and add both projects
    sln_path = os.path.join(OUTPUT_DIR, f"{TEST_PROJECT_NAME}.sln")
    subprocess.run(
        ["dotnet", "new", "sln", "-n", TEST_PROJECT_NAME, "--force"],
        cwd=OUTPUT_DIR,
        check=True
    )

    # Add the original project (relative path from OUTPUT_DIR)
    rel_original_csproj = os.path.relpath(original_csproj, OUTPUT_DIR)
    subprocess.run(
        ["dotnet", "sln", sln_path, "add", rel_original_csproj],
        cwd=OUTPUT_DIR,
        check=True
    )

    # Add the test project
    rel_test_csproj = os.path.relpath(test_csproj_path, OUTPUT_DIR)
    subprocess.run(
        ["dotnet", "sln", sln_path, "add", rel_test_csproj],
        cwd=OUTPUT_DIR,
        check=True
    )

    # 7) Build a global type-definition map by scanning all .cs files in src_dir
    global_type_defs = {}
    for csf in find_cs_files(src_dir):
        classes = extract_classes_info_from_cs_file(csf, extractor_dll)
        for cls in classes:
            for fqcn, src in cls.get("ReferencedTypeDefinitions", {}).items():
                if fqcn not in global_type_defs:
                    global_type_defs[fqcn] = src

    # 8) Process each .cs file in parallel, generating tests under test_proj_dir
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as exe:
        futures = []
        for csf in find_cs_files(src_dir):
            futures.append(
                exe.submit(
                    process_file,
                    test_proj_dir,
                    csf,
                    src_dir,
                    extractor_dll,
                    global_type_defs
                )
            )
        for fut in as_completed(futures):
            success = fut.result()
            if not success:
                logger.warning("One file processing failed; see logs above.")

    # 9) Modify the test project .csproj to reference the original project
    add_project_reference(test_csproj_path, original_csproj)

    # 10) Restore & build the entire solution (pulling down NuGet dependencies)
    logger.info("Running `dotnet restore` on the solution...")
    proc_restore = subprocess.run(
        ["dotnet", "restore", sln_path], cwd=OUTPUT_DIR, capture_output=True, text=True
    )
    if proc_restore.returncode != 0:
        logger.error(f"`dotnet restore` failed:\n{proc_restore.stderr}")
        return

    logger.info("Building solution...")
    proc_build = subprocess.run(
        ["dotnet", "build", sln_path, "-c", "Release"], cwd=OUTPUT_DIR, capture_output=True, text=True
    )
    if proc_build.returncode != 0:
        logger.error(f"Solution build failed:\n{proc_build.stderr}")
        return

    logger.info("Solution built successfully.")

    # 11) Run tests with coverage and generate HTML report
    generate_coverage_and_report(sln_path)


def process_file(
    test_proj_dir: str,
    cs_file: str,
    repo_root: str,
    extractor_dll: str,
    global_type_defs: Dict[str, str]
) -> bool:
    """
    For each class in cs_file:
      - Extract ClassInfo (with per-method DependencyTypes & SourceCode)
      - Compute exactly which types that method actually uses
      - Pull only those definitions from global_type_defs
      - Scan for any additional missing types in the repo
      - Generate or retrieve cached NUnit tests
      - Write test file
    """
    wrote_any = False
    class_infos = extract_classes_info_from_cs_file(cs_file, extractor_dll)

    import re
    from testgen.repo import find_cs_files

    for cls in class_infos:
        # 0) Read & store entire .cs file contents
        with open(cs_file, encoding="utf-8") as f:
            cls["FullSourceCode"] = f.read()

        # 1) Build set of referenced type names from DependencyTypes & method source
        method_info = cls["Methods"][0]
        method_src = method_info.get("SourceCode", "")
        referenced = set(method_info.get("DependencyTypes", []))

        for token in re.findall(r"\b[A-Z]\w*(?:<[^>]+>)?", method_src):
            base = token.split("<")[0]
            referenced.add(base)
            for arg in re.findall(r"<([^>]+)>", token):
                for sub in arg.split(","):
                    referenced.add(sub.strip())

        for ctor in cls.get("Constructors", []):
            for param in ctor.get("Parameters", []):
                referenced.add(param.split()[0])

        # 2) Filter global_type_defs down to only what’s referenced
        used_from_global = {
            name: src
            for name, src in global_type_defs.items()
            if name in referenced
        }
        cls["ReferencedTypeDefinitions"].clear()
        cls["ReferencedTypeDefinitions"].update(used_from_global)

        # 3) For any still-missing types, search all .cs files in repo_root
        missing = referenced - set(cls["ReferencedTypeDefinitions"])
        for t in missing:
            pattern = rf"\b(class|interface)\s+{t}\b"
            for other_cs in find_cs_files(repo_root):
                try:
                    content = open(other_cs, encoding="utf-8").read()
                except Exception:
                    continue
                if re.search(pattern, content):
                    cls["ReferencedTypeDefinitions"][t] = content
                    break

        # 4) Generate or fetch cached tests
        key = f"{os.path.relpath(cs_file, repo_root)}::{cls['ClassName']}"
        src_hash = compute_sha256_hash(
            cls.get("SourceCode", cls.get("FullSourceCode", ""))
        )

        code = None
        if not FORCE_REGENERATE:
            code = get_cached_test(conn=None, key=key, source_hash=src_hash, model_name=LL_MODEL)
        if not code:
            code = generate_nunit_test_class(
                class_info=cls,
                model_name=LL_MODEL,
                test_project_namespace=TEST_PROJECT_NAME,
                provider=PROVIDER
            )
            if code:
                cache_test(cache_conn=None, key=key, src_hash=src_hash, model_name=LL_MODEL, code=code)

        # 5) Write out the test file under test_proj_dir/Source/
        if code:
            write_test_file(
                test_proj_dir,
                cs_file,
                repo_root,
                code,
                dry_run=DRY_RUN
            )
            wrote_any = True

    return wrote_any


def add_project_reference(test_csproj_path: str, original_csproj_path: str):
    """
    Inject a <ProjectReference> into the test project's .csproj
    so it references the original project (which now lives under OUTPUT_DIR/src).
    """
    import xml.etree.ElementTree as ET

    ET.register_namespace("", "http://schemas.microsoft.com/developer/msbuild/2003")
    tree = ET.parse(test_csproj_path)
    root = tree.getroot()

    # Find or create an <ItemGroup> to hold ProjectReference
    item_group = None
    for ig in root.findall("ItemGroup"):
        if ig.find("ProjectReference") is not None:
            item_group = ig
            break
    if item_group is None:
        item_group = ET.SubElement(root, "ItemGroup")

    # Compute relative path from test_csproj to original_csproj
    rel_path = os.path.relpath(original_csproj_path, os.path.dirname(test_csproj_path))

    # Add the ProjectReference node
    ET.SubElement(item_group, "ProjectReference", Include=rel_path)

    tree.write(test_csproj_path, xml_declaration=True, encoding="utf-8")
    logger.info(f"Added ProjectReference to {original_csproj_path} in {test_csproj_path}")


def generate_coverage_and_report(solution_path: str):
    """
    Given a .sln path, run all tests with coverage and produce an HTML report.
    """
    logger.info("Running tests with coverage collection...")

    coverage_results_dir = os.path.join(OUTPUT_DIR, "coverage_results")
    os.makedirs(coverage_results_dir, exist_ok=True)

    test_cmd = [
        "dotnet", "test", solution_path,
        "--collect:XPlat Code Coverage",
        "--results-directory", coverage_results_dir,
        "-c", "Release"
    ]
    proc = subprocess.run(test_cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        logger.error(f"`dotnet test` failed:\n{proc.stderr}")
        return

    logger.info("Tests completed. Generating HTML coverage report...")

    cobertura_path = None
    for root, _, files in os.walk(coverage_results_dir):
        for f in files:
            if f.endswith(".coverage.cobertura.xml"):
                cobertura_path = os.path.join(root, f)
                break
        if cobertura_path:
            break

    if not cobertura_path:
        logger.error("Could not locate 'coverage.cobertura.xml'")
        return

    coverage_report_dir = os.path.join(OUTPUT_DIR, "coverage-report")
    os.makedirs(coverage_report_dir, exist_ok=True)

    report_cmd = [
        "reportgenerator",
        f"-reports:{cobertura_path}",
        f"-targetdir:{coverage_report_dir}",
        "-reporttypes:Html"
    ]
    proc2 = subprocess.run(report_cmd, capture_output=True, text=True)
    if proc2.returncode != 0:
        logger.error(f"ReportGenerator failed:\n{proc2.stderr}")
        return

    logger.info(f"HTML coverage report generated: {coverage_report_dir}")


if __name__ == "__main__":
    main()
