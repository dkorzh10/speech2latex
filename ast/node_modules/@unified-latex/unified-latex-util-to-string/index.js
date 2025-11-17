import Prettier from "prettier/standalone.js";
import { printLatexAst } from "@unified-latex/unified-latex-prettier";
import { printRaw } from "@unified-latex/unified-latex-util-print-raw";
import { unified } from "unified";
const unifiedLatexStringCompiler = function unifiedLatexStringCompiler2(options) {
  const {
    pretty = false,
    printWidth = 80,
    useTabs = true,
    forceNewlineEnding = false
  } = options || {};
  const prettyPrinter = (ast) => {
    let formatted = Prettier.format("_", {
      useTabs,
      printWidth,
      parser: "latex-dummy-parser",
      plugins: [
        {
          languages: [
            {
              name: "latex",
              extensions: [".tex"],
              parsers: ["latex-dummy-parser"]
            }
          ],
          parsers: {
            "latex-dummy-parser": {
              parse: () => ast,
              astFormat: "latex-ast",
              locStart: () => 0,
              locEnd: () => 1
            }
          },
          printers: {
            "latex-ast": {
              print: printLatexAst
            }
          }
        }
      ],
      ...options || {}
    });
    if (forceNewlineEnding && !formatted.endsWith("\n")) {
      formatted += "\n";
    }
    return formatted;
  };
  Object.assign(this, {
    Compiler: (ast) => {
      if (!pretty) {
        return printRaw(ast);
      }
      return prettyPrinter(ast);
    }
  });
};
const processor = unified().use(unifiedLatexStringCompiler, { pretty: true }).freeze();
function toString(ast) {
  if (Array.isArray(ast)) {
    ast = { type: "root", content: ast };
  }
  if (ast.type !== "root") {
    ast = { type: "root", content: [ast] };
  }
  return processor.stringify(ast);
}
export {
  toString,
  unifiedLatexStringCompiler
};
//# sourceMappingURL=index.js.map
