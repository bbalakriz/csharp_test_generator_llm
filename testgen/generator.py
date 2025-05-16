import subprocess
import logging
import re
from typing import Dict, Optional

logger = logging.getLogger(__name__)

EXPECTED_KEYWORDS = ["[TestFixture]", "[Test]"]

def generate_nunit_test_class(
    class_info: Dict[str, any],
    model_name: str,
    test_project_namespace: str,
    few_shot_example: Optional[str] = None,
    timeout_sec: int = 300
) -> Optional[str]:
    """
    call the local Ollama on my machine to generate a full NUnit test class.
    this performs simple keyword validation to ensure that nunit tests are generated and; returns None on failure.
    """
    class_name = class_info["ClassName"]
    namespace = class_info.get("NamespaceName", "")
    prompt = _build_prompt(class_info, test_project_namespace, few_shot_example)
    print(prompt)
    
    logger.debug(f"LLM prompt (truncated): {prompt[:500]}…")
    try:
        proc = subprocess.run(
            ["ollama", "run", model_name, prompt],
            capture_output=True, text=True, timeout=timeout_sec, check=True
        )
        code = proc.stdout.strip()
    except FileNotFoundError:
        logger.error("`ollama` CLI not found in PATH.")
        return None
    except subprocess.CalledProcessError as e:
        logger.error(f"Ollama failed: {e.stderr}")
        return None
    except subprocess.TimeoutExpired:
        logger.error(f"Ollama timed out after {timeout_sec}s")
        return None

    # strip the language markers out
    code = re.sub(r"^```(?:csharp)?\s*|\s*```$", "", code)

    # basic validation
    if f"class {class_name}Tests" not in code:
        logger.error("LLM output missing expected test-class name.")
        return None
    if not all(kw in code for kw in EXPECTED_KEYWORDS):
        logger.error("LLM output missing NUnit attributes.")
        return None

    return code

def _build_prompt(class_info, root_namespace: str, few_shot: Optional[str]) -> str:
    # more elaborate prompt to be built here; better to insert few_shot examples here rather than a simple prompt like this
    core = f"""
You are a C# NUnit expert. Generate a complete, runnable NUnit test CLASS for the following C# class:
ClassName: {class_info['ClassName']}
Namespace: {class_info.get('NamespaceName','Global')}
FullSource:
```\n{class_info['FullSourceCode']}\n```
Your test class must be named {class_info['ClassName']}Tests in namespace {root_namespace}.
Use [TestFixture], [Test], Arrange, Act and Assert pattern, include setup if needed, meaningful test cases.
"""
    if few_shot:
        return few_shot + "\n---\n" + core
    return core
