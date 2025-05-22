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
    Ensure the Roslyn-based extractor is built and return paths to the DLL and .csproj.
    The extractor now emits additional JSON fields:
      - MethodInfo.SourceCode: full implementation text
      - ReferencedTypeDefinitions: map of custom type names to source code    """
    
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
    Invoke the Roslyn extractor on a .cs file and parse its JSON output.
    Returns a list of ClassInfo dicts, each containing:
      - FilePath, NamespaceName, ClassName
      - Constructors, Methods (with SourceCode), Properties
      - UsingDirectives
      - ReferencedTypeDefinitions: dict of typeName -> code
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
        classes = json.loads(out)
        for cls in classes:
            # DEBUG: report counts of methods and dependencies
            logger.debug(
                f"[Extractor] {cls['ClassName']} -> "
                f"{len(cls.get('Methods', []))} methods, "
                f"{len(cls.get('ReferencedTypeDefinitions', {}))} dependencies"
            )
        return classes
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
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;

public class ClassInfo
{
    public string FilePath { get; set; } = "";
    public string NamespaceName { get; set; } = "";
    public string ClassName { get; set; } = "";
    public List<ConstructorInfo> Constructors { get; set; } = new();
    public List<MethodInfo> Methods { get; set; } = new();
    public List<PropertyInfo> Properties { get; set; } = new();
    public List<string> UsingDirectives { get; set; } = new();
    public Dictionary<string, string> ReferencedTypeDefinitions { get; set; } = new();
}

public class ConstructorInfo
{
    public string Signature { get; set; } = "";
    public List<string> Parameters { get; set; } = new();
    public List<ExceptionCondition> ExceptionConditions { get; set; } = new();
}

public class MethodInfo
{
    public string Name { get; set; } = "";
    public string Signature { get; set; } = "";
    public string ReturnType { get; set; } = "";
    public List<string> Parameters { get; set; } = new();
    public List<ExceptionCondition> ExceptionConditions { get; set; } = new();
    public List<string> DependencyTypes { get; set; } = new();
    public string SourceCode { get; set; } = "";
}

public class PropertyInfo
{
    public string Name { get; set; } = "";
    public string Type { get; set; } = "";
}

public class ExceptionCondition
{
    public string ConditionExpression { get; set; } = "";
    public string ExceptionType { get; set; } = "";
}

class Program
{
    static void Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.Error.WriteLine("Usage: extractor <cs-file>");
            return;
        }

        var filePath = args[0];
        if (!File.Exists(filePath))
        {
            Console.Error.WriteLine("File not found: " + filePath);
            return;
        }

        var code = File.ReadAllText(filePath);
        var tree = CSharpSyntaxTree.ParseText(code, new CSharpParseOptions(LanguageVersion.Latest));
        var root = tree.GetCompilationUnitRoot();
        
        var mscorlib = MetadataReference.CreateFromFile(typeof(object).Assembly.Location);
        var compilation = CSharpCompilation.Create("ExtractorAssembly")
            .AddReferences(mscorlib)
            .AddSyntaxTrees(tree);
        var semanticModel = compilation.GetSemanticModel(tree);

        var result = new List<ClassInfo>();
        var usings = root.Usings.Select(u => u.ToString().Trim()).ToList();

        foreach (var classDecl in root.DescendantNodes().OfType<ClassDeclarationSyntax>())
        {
            var classSymbol = semanticModel.GetDeclaredSymbol(classDecl);
            if (classSymbol == null) continue;

            // Move collectedTypes inside the loop, so it's declared before use:
            var collectedTypes = new Dictionary<string, string>();

            // Recursive collector now fully implemented:
            void CollectType(INamedTypeSymbol typeSymbol)
            {
                var key = typeSymbol.ToDisplayString();
                if (collectedTypes.ContainsKey(key)) return;

                var declRef = typeSymbol.DeclaringSyntaxReferences.FirstOrDefault();
                if (declRef == null) return;
                var decl = declRef.GetSyntax() as TypeDeclarationSyntax;
                if (decl == null) return;

                collectedTypes[key] = decl.NormalizeWhitespace().ToFullString();

                // 1) Properties
                foreach (var prop in decl.Members.OfType<PropertyDeclarationSyntax>())
                {
                    var pt = semanticModel.GetTypeInfo(prop.Type).Type as INamedTypeSymbol;
                    if (pt != null && pt.Locations.Any(l => l.IsInSource))
                        CollectType(pt);
                }
                // 2) Fields
                foreach (var field in decl.Members.OfType<FieldDeclarationSyntax>())
                {
                    var ft = semanticModel.GetTypeInfo(field.Declaration.Type).Type as INamedTypeSymbol;
                    if (ft != null && ft.Locations.Any(l => l.IsInSource))
                        CollectType(ft);
                }
                // 3) Constructor parameters
                foreach (var ctor in decl.Members.OfType<ConstructorDeclarationSyntax>())
                {
                    foreach (var param in ctor.ParameterList.Parameters)
                    {
                        var pt = semanticModel.GetTypeInfo(param.Type).Type as INamedTypeSymbol;
                        if (pt != null && pt.Locations.Any(l => l.IsInSource))
                            CollectType(pt);
                    }
                }
                // 4) Base type
                if (typeSymbol.BaseType != null && typeSymbol.BaseType.Locations.Any(l => l.IsInSource))
                    CollectType(typeSymbol.BaseType);
                // 5) Interfaces
                foreach (var iface in typeSymbol.Interfaces)
                    if (iface.Locations.Any(l => l.IsInSource))
                        CollectType(iface);
            }

            // Build ClassInfo
            var info = new ClassInfo
            {
                FilePath = filePath,
                NamespaceName = classSymbol.ContainingNamespace?.ToDisplayString() ?? "",
                ClassName = classDecl.Identifier.Text,
                UsingDirectives = usings,
                ReferencedTypeDefinitions = collectedTypes
            };

            // Constructors
            foreach (var ctor in classDecl.Members.OfType<ConstructorDeclarationSyntax>())
            {
                if (!ctor.Modifiers.Any(m => m.IsKind(SyntaxKind.PublicKeyword))) continue;
                var ci = new ConstructorInfo
                {
                    Signature = ctor.NormalizeWhitespace().ToString().Split('{')[0].Trim(),
                    Parameters = ctor.ParameterList.Parameters.Select(p => p.ToString()).ToList(),
                    ExceptionConditions = ctor.DescendantNodes()
                        .OfType<IfStatementSyntax>()
                        .SelectMany(ifNode => ifNode.DescendantNodes()
                            .OfType<ThrowStatementSyntax>()
                            .Select(ts => new ExceptionCondition
                            {
                                ConditionExpression = ifNode.Condition.ToString(),
                                ExceptionType = (ts.Expression as ObjectCreationExpressionSyntax)?.Type.ToString() ?? "Exception"
                            }))
                        .ToList()
                };
                info.Constructors.Add(ci);
            }

            // Methods
            foreach (var method in classDecl.Members.OfType<MethodDeclarationSyntax>())
            {
                // if (!method.Modifiers.Any(m => m.IsKind(SyntaxKind.PublicKeyword))) continue;
                var sym = semanticModel.GetDeclaredSymbol(method);
                // capture full method source, including leading comments/trivia
                var leadingTrivia = method.GetLeadingTrivia().ToFullString();
                var normalized    = method.NormalizeWhitespace().ToFullString();

                var mi = new MethodInfo
                {
                    Name = method.Identifier.Text,
                    Signature = method.NormalizeWhitespace().ToString().Split('{')[0].Trim(),
                    ReturnType = sym.ReturnType.ToDisplayString(),
                    Parameters = method.ParameterList.Parameters.Select(p => p.ToString()).ToList(),
                    ExceptionConditions = method.DescendantNodes()
                        .OfType<IfStatementSyntax>()
                        .SelectMany(ifNode => ifNode.DescendantNodes()
                            .OfType<ThrowStatementSyntax>()
                            .Select(ts => new ExceptionCondition
                            {
                                ConditionExpression = ifNode.Condition.ToString(),
                                ExceptionType = (ts.Expression as ObjectCreationExpressionSyntax)?.Type.ToString() ?? "Exception"
                            }))
                        .ToList(),
                    DependencyTypes = new List<string>(),                    
                    SourceCode = leadingTrivia + normalized
                };

                // Detect locals for dependencies
                var dataFlow = semanticModel.AnalyzeDataFlow(method.Body);
                foreach (var local in dataFlow.VariablesDeclared.OfType<ILocalSymbol>())
                {
                    if (local.Type is INamedTypeSymbol nt && nt.Locations.Any(l => l.IsInSource))
                    {
                        mi.DependencyTypes.Add(nt.ToDisplayString());
                        CollectType(nt);
                    }
                }
                info.Methods.Add(mi);
            }

            // Properties
            foreach (var prop in classDecl.Members.OfType<PropertyDeclarationSyntax>())
            {
                var pi = new PropertyInfo
                {
                    Name = prop.Identifier.Text,
                    Type = (semanticModel.GetTypeInfo(prop.Type).Type as INamedTypeSymbol)
                           ?.ToDisplayString() ?? prop.Type.ToString()
                };
                info.Properties.Add(pi);
                var pt = semanticModel.GetTypeInfo(prop.Type).Type as INamedTypeSymbol;
                if (pt != null && pt.Locations.Any(l => l.IsInSource))
                    CollectType(pt);
            }

            result.Add(info);
        }

        Console.WriteLine(JsonSerializer.Serialize(result));
    }
}
"""
