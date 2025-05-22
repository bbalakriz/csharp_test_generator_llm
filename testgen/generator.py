import subprocess
import logging
import re
from typing import Dict, Optional, Any
import openai, os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

EXPECTED_KEYWORDS = ["[TestFixture]", "[Test]"]

def run_llm(
    prompt: str,
    model_name: str,
    provider: str = "ollama",
    timeout_sec: int = 300
) -> Optional[str]:
    """
    Abstracted LLM call. Supports two providers:
      - "ollama": runs `ollama run <model_name> <prompt>`
      - "openai": calls openai.ChatCompletion with model <model_name>
    Returns the raw string output (with fences stripped), or None on failure.
    """
    if provider == "ollama":
        # Use subprocess.Popen to stream and collect output
        try:
            proc = subprocess.Popen(
                ["ollama", "run", model_name, prompt],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        except FileNotFoundError:
            logger.error("`ollama` CLI not found in PATH.")
            return None

        lines = []
        if proc.stdout is not None:
            for line in proc.stdout:
                lines.append(line)
        proc.wait()  # wait indefinitely

        stderr = proc.stderr.read().strip() if proc.stderr else ""
        if proc.returncode != 0:
            logger.error(f"Ollama failed (exit {proc.returncode}): {stderr}")
            return None

        output = "".join(lines).strip()

    elif provider == "openai":
        # Ensure API key is set
        if not openai.api_key:
            print("API Key...." + os.getenv("OPENAI_API_KEY"))
            openai.api_key = os.getenv("OPENAI_API_KEY", "")
        if not openai.api_key:
            logger.error(
                "OpenAI API key not set. Please set the OPENAI_API_KEY environment variable."
            )
            return None
            
        try:
            response = openai.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a C# NUnit test generator."},
                    {"role": "user", "content": prompt}
                ]
            )
            output = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI call failed: {e}")
            return None

    else:
        logger.error(f"Unknown LLM provider: {provider}")
        return None

    # strip markdown fences if present
    print(f"Raw LLM response... {output}")
    match = re.search(r"```csharp\s*(.*?)\s*```", output, re.DOTALL)
    if match:
        output = match.group(1).strip()
    else:
        logger.warning("No fenced csharp code block found; using full output.")

    return output


def generate_nunit_test_class(
    class_info: Dict[str, Any],
    model_name: str,
    test_project_namespace: str,
    few_shot_example: Optional[str] = None,
    provider: str = "ollama",
    timeout_sec: int = 300
) -> Optional[str]:
    """
    Generate a full NUnit test class for `class_info`:
      - Builds prompt with _build_prompt()
      - Calls run_llm() using either Ollama or OpenAI
      - Validates that output contains [TestFixture] and [Test] attributes
    """
    class_name = class_info["ClassName"]
    prompt = _build_prompt(class_info, test_project_namespace, few_shot_example)
    print(prompt)  # for debugging

    logger.debug(f"LLM prompt (truncated): {prompt[:500]}…")

    code = run_llm(
        prompt=prompt,
        model_name=model_name,
        provider=provider,
        timeout_sec=timeout_sec
    )
    if code is None:
        return None

    # validation checks
    if f"class {class_name}Tests" not in code:
        logger.error("LLM output missing expected test-class name.")
        return None
    if not all(kw in code for kw in EXPECTED_KEYWORDS):
        logger.error("LLM output missing NUnit attributes.")
        return None

    return code

def _build_prompt(
    class_info: Dict[str, Any],
    root_namespace: str,
    few_shot: Optional[str]
) -> str:
    type_defs: Dict[str, str] = class_info.get("ReferencedTypeDefinitions", {})
    parts = []

    if few_shot:
        parts.append(few_shot)
        parts.append("\n---\n")

    # Add all methods under test
    # parts.append("## Methods to Test\n")
    # for method in class_info.get("Methods", []):
    #     method_src = method.get("SourceCode", method.get("Signature", ""))
    #     parts.append("```csharp\n")
    #     parts.append(method_src)
    #     parts.append("\n```\n")

    # Full class for context
    parts.append("## Class Source\n")
    parts.append("```csharp\n")
    parts.append(class_info.get("FullSourceCode", ""))
    parts.append("\n```\n\n")

    # Dependent type definitions
    if type_defs:
        parts.append("\n## Dependent Class Definitions\n")
        for fqcn, code in type_defs.items():
            simple = fqcn.split('.')[-1]
            parts.append(f"### {simple}\n")
            parts.append("```csharp\n")
            parts.append(code)
            parts.append("\n```\n")

    parts.append(
        f"\nGenerate a complete NUnit test class named {class_info['ClassName']}Tests "
        f"in namespace {root_namespace}. Use [TestFixture], [Test], the Arrange–Act–Assert pattern, "
        f"mock interfaces with Moq, and cover all branches and exception paths."
    )

    return ''.join(parts)
