# testgen/extractor.py
import os
import subprocess
import json
import logging
from typing import List, Dict, Any, Tuple

from .repo import find_cs_files  # for possible future expansion

logger = logging.getLogger(__name__)

EXTRACTOR_DIR_NAME = "RoslynExtractor"
EXTRACTOR_PROJECT_NAME = "CodeStructureExtractor"
ROSLYN_CSHARP_VERSION = "4.9.2"

def ensure_extractor_tool(base_dir: str) -> Tuple[str, str]:
    """
    just a simple scaffolding to build a .NET 8 console tool that uses Roslyn to dump JSON
    of all public classes & methods from a .cs file. # TODO: expand this implementation to suit the needs of IndiGo
    Returns (path_to_dll, path_to_csproj).
    """
    
    proj_parent = os.path.join(base_dir, EXTRACTOR_DIR_NAME)
    proj_dir = os.path.join(proj_parent, EXTRACTOR_PROJECT_NAME)
    csproj = os.path.join(proj_dir, f"{EXTRACTOR_PROJECT_NAME}.csproj")
    dll = os.path.join(proj_dir, "bin", "Release", "net8.0", f"{EXTRACTOR_PROJECT_NAME}.dll")

    if not os.path.isfile(dll):
        os.makedirs(proj_dir, exist_ok=True)
        # 1 dotnet new console ...
        subprocess.run([
            "dotnet", "new", "console", 
            "--force", "-n", EXTRACTOR_PROJECT_NAME,
            "-f", "net8.0", "-o", proj_dir
        ], check=True)
        # 2 overwrite Program.cs
        with open(os.path.join(proj_dir, "Program.cs"), "w", encoding="utf-8") as f:
            f.write(_roslyn_extractor_cs())
        # 3 add Roslyn
        subprocess.run([
            "dotnet","add", csproj, "package",
            "Microsoft.CodeAnalysis.CSharp",
            "--version", ROSLYN_CSHARP_VERSION
        ], check=True)
        # 4) build
        subprocess.run(["dotnet","build", csproj, "-c","Release"], check=True)

    return dll, csproj

def extract_classes_info_from_cs_file(cs_file: str, extractor_dll: str) -> List[Dict[str, Any]]:
    """
    call the extractor DLL on a single .cs file, parse JSON output.
    """
    if not os.path.isfile(cs_file):
        logger.warning(f"File not found: {cs_file}")
        return []
    proc = subprocess.run(
        ["dotnet", extractor_dll, cs_file],
        capture_output=True, text=True
    )
    if proc.returncode != 0:
        logger.error(f"Extractor error ({cs_file}): {proc.stderr.strip()}")
        return []
    out = proc.stdout.strip()
    if not out:
        return []
    try:
        return json.loads(out)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed for {cs_file}: {e}")
        return []

def _roslyn_extractor_cs() -> str:
    # simple c# AST extractor based on Rolsyln. found that Roslyn provides better 
    # AST extraction capabilities when compared to that of python tree_sitter AST 
    # parser. generated this implementation using openai models.. this needs to be 
    # updated to include the semantic model based data structure extraction for handling nested data types
    return """
// full Roslyn extractor source...
using System;
using System.IO;
using System.Text.Json;
using System.Collections.Generic;
using System.Linq;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;

// Data structures for JSON output
public class ClassInfo
{
    public string FilePath { get; set; } = "";
    public string ClassName { get; set; } = "";
    public string NamespaceName { get; set; } = ""; // Namespace of the class itself
    public List<MethodInfo> PublicMethods { get; set; } = new List<MethodInfo>();
    public string FullSourceCode { get; set; } = ""; // Full content of the .cs file
    public List<string> UsingDirectivesInFile { get; set; } = new List<string>(); // All 'using' in the file
    public bool IsStatic { get; set; } = false;
    public bool IsAbstract { get; set; } = false;
    public List<ConstructorInfo> Constructors { get; set; } = new List<ConstructorInfo>();
}

public class MethodInfo
{
    public string Name { get; set; } = "";
    public string ReturnType { get; set; } = "";
    public List<string> Parameters { get; set; } = new List<string>(); // e.g., "string name", "int count"
    public string Signature { get; set; } = ""; // e.g., "public string GetName(int id)"
    public bool IsStatic { get; set; } = false;
    public bool IsAbstract { get; set; } = false;
    public bool IsAsync { get; set; } = false;
}

public class ConstructorInfo
{
    public string Signature { get; set; } = "";
    public List<string> Parameters { get; set; } = new List<string>();
}

public class Extractor
{
    public static void Main(string[] args)
    {
        var filePath = args.Length > 0 ? args[0] : Console.In.ReadToEnd().Trim();
        if (string.IsNullOrEmpty(filePath) || !File.Exists(filePath))
        {
            Console.Error.WriteLine($"Error: File not found or path is empty. Path: '{filePath}'");
            Environment.ExitCode = 1; // Indicate error
            return;
        }

        var results = new List<ClassInfo>();
        try
        {
            string code = File.ReadAllText(filePath);
            SyntaxTree tree = CSharpSyntaxTree.ParseText(code, CSharpParseOptions.Default.WithLanguageVersion(LanguageVersion.Latest));
            CompilationUnitSyntax root = tree.GetCompilationUnitRoot();

            // Attempt to create a compilation for semantic analysis (helps resolve types more accurately)
            // This is a minimal compilation, might need more references for complex projects
            var compilation = CSharpCompilation.Create("ExtractorAssembly")
                .AddReferences(MetadataReference.CreateFromFile(typeof(object).Assembly.Location)) 
                .AddSyntaxTrees(tree);
            SemanticModel semanticModel = compilation.GetSemanticModel(tree);

            var usingDirectivesInFile = root.Usings.Select(u => u.ToString().Trim()).ToList();

            foreach (var typeDeclaration in root.DescendantNodes().OfType<TypeDeclarationSyntax>())
            {
                // We are interested in classes, structs, and interfaces for potential test generation context
                // but primarily focus on generating tests for non-abstract classes.
                if (!(typeDeclaration is ClassDeclarationSyntax || 
                      typeDeclaration is StructDeclarationSyntax /*|| 
                      typeDeclaration is InterfaceDeclarationSyntax*/)) // For now, only classes/structs
                {
                    continue;
                }

                var declaredSymbol = semanticModel.GetDeclaredSymbol(typeDeclaration);
                if (declaredSymbol == null) continue;

                string namespaceName = declaredSymbol.ContainingNamespace?.ToDisplayString() ?? "Global";
                if (declaredSymbol.ContainingNamespace != null && declaredSymbol.ContainingNamespace.IsGlobalNamespace)
                {
                     namespaceName = "Global"; // Explicitly "Global" for clarity
                }


                var classInfo = new ClassInfo
                {
                    FilePath = Path.GetFullPath(filePath),
                    ClassName = typeDeclaration.Identifier.Text,
                    NamespaceName = namespaceName,
                    FullSourceCode = code,
                    UsingDirectivesInFile = new List<string>(usingDirectivesInFile),
                    IsStatic = declaredSymbol.IsStatic,
                    IsAbstract = declaredSymbol.IsAbstract
                };

                // Get Constructors
                foreach (var ctorNode in typeDeclaration.Members.OfType<ConstructorDeclarationSyntax>())
                {
                    if (ctorNode.Modifiers.Any(m => m.IsKind(SyntaxKind.PublicKeyword))) // Consider public constructors
                    {
                        var ctorParams = ctorNode.ParameterList.Parameters
                            .Select(p => $"{p.Type?.ToString() ?? "unknown"} {p.Identifier.ValueText}")
                            .ToList();
                        classInfo.Constructors.Add(new ConstructorInfo
                        {
                            Parameters = ctorParams,
                            Signature = $"public {classInfo.ClassName}({string.Join(", ", ctorParams)})"
                        });
                    }
                }


                // Get Public Methods
                foreach (var methodNode in typeDeclaration.Members.OfType<MethodDeclarationSyntax>())
                {
                    if (methodNode.Modifiers.Any(m => m.IsKind(SyntaxKind.PublicKeyword)))
                    {
                        var methodSymbol = semanticModel.GetDeclaredSymbol(methodNode);
                        if (methodSymbol == null) continue;

                        var parameters = methodNode.ParameterList.Parameters
                            .Select(p => $"{p.Type?.ToString() ?? "unknown_type"} {p.Identifier.ValueText}")
                            .ToList();
                        
                        string returnType = methodSymbol.ReturnType.ToDisplayString(SymbolDisplayFormat.FullyQualifiedFormat);
                        string methodName = methodNode.Identifier.ValueText;
                        
                        var modifiers = string.Join(" ", methodNode.Modifiers.Select(m => m.Text));
                        if (!string.IsNullOrWhiteSpace(modifiers)) modifiers += " ";

                        classInfo.PublicMethods.Add(new MethodInfo
                        {
                            Name = methodName,
                            ReturnType = returnType,
                            Parameters = parameters,
                            Signature = $"{modifiers}{returnType} {methodName}({string.Join(", ", parameters)})",
                            IsStatic = methodSymbol.IsStatic,
                            IsAbstract = methodSymbol.IsAbstract,
                            IsAsync = methodSymbol.IsAsync
                        });
                    }
                }
                
                // Add class if it's not abstract (abstract classes cannot be instantiated directly for testing)
                // Or if it's static (static classes are tested via their static members)
                if (!classInfo.IsAbstract || classInfo.IsStatic) 
                {
                    results.Add(classInfo);
                }
            }
            var jsonOptions = new JsonSerializerOptions { WriteIndented = false, Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping };
            Console.WriteLine(JsonSerializer.Serialize(results, jsonOptions));
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"Error processing file {filePath}: {ex.ToString()}");
            Environment.ExitCode = 2; // Indicate processing error
        }
    }
}
"""
