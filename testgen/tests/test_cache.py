import os
import tempfile
import pytest
from testgen.cache import init_cache, compute_sha256_hash, get_cached_test, cache_test

@pytest.fixture
def cache_conn():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    conn = init_cache(path, allow_threads=False)
    yield conn
    conn.close()
    os.remove(path)

def test_hash_consistency():
    h1 = compute_sha256_hash("hello")
    h2 = compute_sha256_hash("hello")
    assert h1 == h2
    assert len(h1) == 64

def test_cache_roundtrip(cache_conn):
    key = "k1"
    src_hash = "h1"
    model = "m1"
    code = "some code"
    assert get_cached_test(cache_conn, key, src_hash, model) is None
    cache_test(cache_conn, key, src_hash, model, code)
    retrieved = get_cached_test(cache_conn, key, src_hash, model)
    assert retrieved == code
