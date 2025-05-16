# run.py
import os
import logging
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

from testgen.repo import get_repo, find_cs_files
from testgen.cache import init_cache, compute_sha256_hash, get_cached_test, cache_test
from testgen.extractor import ensure_extractor_tool, extract_classes_info_from_cs_file
from testgen.generator import generate_nunit_test_class
from testgen.writer import init_nunit_project, write_test_file, run_and_verify_tests

# ------------- CONFIGURATION -------------
REPO_URL = "https://github.com/anuraj/MinimalApi"
BRANCH    = "main"
OUTPUT_DIR= os.path.abspath("generated_tests_output")
OLLAMA_MODEL = "qwen2.5:7b"
TEST_PROJECT_NAME = "GeneratedTests"
FORCE_REGENERATE = False
DRY_RUN = False          # <── set True to preview but not write or run
MAX_WORKERS = 1 # setting to test 1 for initial tetsing to process one .cs file creation at a time
# ------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def main():
    # inintal preparation
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    cache_db = os.path.join(OUTPUT_DIR, "test_cache.db")
    cache_conn = init_cache(cache_db, allow_threads=True)

    tmp_repo = tempfile.mkdtemp(prefix="testgen_repo_")
    try:
        # 1 clone
        get_repo(tmp_repo, REPO_URL, BRANCH)
        # 2 build extractor
        extractor_dll, _ = ensure_extractor_tool(OUTPUT_DIR)
        # 3 init test project
        test_proj_dir = init_nunit_project(OUTPUT_DIR, TEST_PROJECT_NAME)

        # 4 process all .cs files in parallel
        futures = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as exe:
            for csf in find_cs_files(tmp_repo):
                futures.append(exe.submit(process_file, test_proj_dir, csf, tmp_repo, extractor_dll, cache_conn))

            for fut in as_completed(futures):
                success = fut.result()
                if not success:
                    logger.warning("One file processing failed; see logs above.")

        # 5 run tests
        run_and_verify_tests(test_proj_dir, dry_run=DRY_RUN)

    finally:
        cache_conn.close()
        logger.info("cleaning up repo clone")
        import shutil
        shutil.rmtree(tmp_repo, ignore_errors=True)

def process_file(test_proj_dir, cs_file, repo_root, extractor_dll, cache_conn) -> bool:
    """
    extract classes --> then generate or fetch from cache --> write test file
    returns True if at least one test was written
    """
    wrote_any = False
    infos = extract_classes_info_from_cs_file(cs_file, extractor_dll)
    for cls in infos:
        key = f"{os.path.relpath(cs_file, repo_root)}::{cls['ClassName']}"
        src_hash = compute_sha256_hash(cls["FullSourceCode"])

        code = None
        if not FORCE_REGENERATE:
            code = get_cached_test(cache_conn, key, src_hash, OLLAMA_MODEL)
        if code:
            logger.info(f"cache hit for {cls['ClassName']}")
        else:
            logger.info(f"generating test for {cls['ClassName']}")
            code = generate_nunit_test_class(cls, OLLAMA_MODEL, TEST_PROJECT_NAME)
            if code:
                cache_test(cache_conn, key, src_hash, OLLAMA_MODEL, code)
        if code:
            write_test_file(test_proj_dir, cs_file, repo_root, code, dry_run=DRY_RUN)
            wrote_any = True
    return wrote_any

if __name__ == "__main__":
    main()
