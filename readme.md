To run the application, just do `python run.py`. Python version used in my machine - 3.13.2. You’ll need to have:

- The .NET SDK installed (so dotnet is on your PATH).

- dotnet-reportgenerator-globaltool installed globally (dotnet tool install -g dotnet-reportgenerator-globaltool
)

# C# NUnit test generator

This project provides a simple Python driven solution to automatically generate NUnit unit tests for C# code. It uses a small .NET 8 Roslyn extractor tool to parse C# source, a local Ollama LLM to write rich test classes, and organizes everything into a clean, production-grade workflow.

## Overall solution

1. **Clone or update a C# repository**
   We fetch the target Git repo (or pull the latest changes) into a temporary directory.

2. **Scaffold and build a Roslyn extractor**
   A tiny .NET 8 console app (using Microsoft.CodeAnalysis.CSharp) parses each `.cs` file and emits JSON describing its public classes, constructors, and methods.

3. **Generate NUnit test classes with Ollama**
   For each public class, we assemble a prompt—including full source code and method signatures—and call the `ollama` CLI to produce a complete NUnit test class in C#.

4. **Cache generated tests**
   A SQLite database stores generated code keyed by file path, class name, source hash, and model name to avoid unnecessary regeneration.

5. **Write test files and run tests**
   We mirror the original folder structure under a `GeneratedTests` project, write out the test classes, then build and run `dotnet test` to verify everything.

## Design choices and why this is production grade

* **Separation of concerns**
  Each core responsibility lives in its own module (`repo`, `extractor`, `generator`, `cache`, `writer`), making the code easier to read, test, and maintain.

* **Robust caching**
  By hashing the full source of each class and the model name, we ensure test regeneration happens only when code actually changes, saving time and LLM cost.

* **Parallel processing**
  We use a thread pool to analyze and generate tests for multiple files simultaneously, speeding up large repositories.

* **Dry-run mode**
  You can preview file writes and skip test execution without modifying anything—a safe way to inspect outputs.

* **Basic LLM validation**
  We check for expected keywords (`[TestFixture]`, `[Test]`, correct test-class name) before accepting code, catching obvious generation errors early.

* **Automated test verification**
  The final `dotnet test` build & run step ensures generated tests actually compile and pass, giving confidence in the output.

* **Unit tests for core logic**
  We include pytest tests for repository discovery and caching, helping catch regressions as the tool evolves.

## Modules and logic

### `testgen/repo.py`

* **`get_repo`**: Clone or update a Git repo into a local directory.
* **`find_cs_files`**: Recursively yield `.cs` files, excluding common build and hidden folders.

### `testgen/extractor.py`

* **`ensure_extractor_tool`**:

  * Creates a .NET 8 console project if needed.
  * Overwrites `Program.cs` with a raw C# Roslyn extractor.
  * Adds the `Microsoft.CodeAnalysis.CSharp` NuGet package.
  * Builds the extractor in Release mode.

* **`extract_classes_info_from_cs_file`**:

  * Invokes the extractor DLL on a given `.cs` file.
  * Parses its JSON output into Python dictionaries describing each class (name, namespace, constructors, public methods, full source, using directives).

### `testgen/generator.py`

* **`generate_nunit_test_class`**:

  * Builds a detailed prompt with class metadata and full source code.
  * Runs `ollama run <model>` to produce a complete NUnit test class.
  * Strips Markdown fences and validates that the output contains the correct class name and NUnit attributes.

* **Prompt builder**:

  * You can optionally pass a few-shot example to guide the LLM.
  * Ensures the test class is named `MyClassTests` and uses `[TestFixture]`, `[Test]`, and the AAA pattern.

### `testgen/cache.py`

* **`init_cache`**:

  * Opens or creates an SQLite database with a `test_cache` table.
  * Optionally allows cross-thread access for parallel runs.

* **`compute_sha256_hash`**:

  * Hashes a string (the full source code) to detect changes.

* **`get_cached_test` / `cache_test`**:

  * Retrieve or store generated test code by `(key, source_hash, model_name)`.

### `testgen/writer.py`

* **`init_nunit_project`**:

  * Scaffolds a `dotnet new nunit` project under a given directory.
  * Enforces specific package versions for NUnit, the test adapter, the .NET test SDK, and Moq.

* **`write_test_file`**:

  * Mirrors the original `.cs` file’s subfolder structure under the test project.
  * In dry-run mode, only logs the intended file path and code preview.

* **`run_and_verify_tests`**:

  * Builds the test project and runs `dotnet test`.
  * Logs results, errors, and returns a boolean success status.
  * Skips execution entirely if dry-run is enabled.

### `run.py`

This is the simple driver script:

1. Configure constants (`REPO_URL`, `OUTPUT_DIR`, `OLLAMA_MODEL`, etc.) at the top.
2. Initialize logging and caching.
3. Clone/fetch the repo, build the extractor, and scaffold the test project.
4. Use a `ThreadPoolExecutor` to concurrently:

   * Extract class info from each `.cs` file.
   * Generate or fetch cached test code.
   * Write test files.
5. Build and run the generated tests, or skip if dry-run.

### `tests/`

* **`test_cache.py`**

  * Confirms that hashing is consistent and caching round-trips correctly.

* **`test_repo.py`**

  * Ensures `find_cs_files` only returns `.cs` files in the right directories, respecting exclusions.


with this modular layout, we get a clear, maintainable codebase that can be extended (few-shot examples, alternative extractors, different LLM backends) and integrated into any CI/CD pipeline.
