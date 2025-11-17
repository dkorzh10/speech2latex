"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
const unifiedLatexUtilMatch = require("@unified-latex/unified-latex-util-match");
const unifiedLatexUtilVisit = require("@unified-latex/unified-latex-util-visit");
function trim(nodes) {
  if (!Array.isArray(nodes)) {
    console.warn("Trying to trim a non-array ast", nodes);
    return nodes;
  }
  const { trimmedStart } = trimStart(nodes);
  const { trimmedEnd } = trimEnd(nodes);
  return { trimmedStart, trimmedEnd };
}
function trimStart(nodes) {
  const { start } = amountOfLeadingAndTrailingWhitespace(nodes);
  nodes.splice(0, start);
  for (const leadingToken of nodes) {
    if (!unifiedLatexUtilMatch.match.comment(leadingToken)) {
      break;
    }
    if (leadingToken.leadingWhitespace || leadingToken.sameline) {
      leadingToken.leadingWhitespace = false;
    }
    if (start > 0 && leadingToken.sameline) {
      leadingToken.sameline = false;
    }
  }
  return { trimmedStart: start };
}
function trimEnd(nodes) {
  const { end } = amountOfLeadingAndTrailingWhitespace(nodes);
  nodes.splice(nodes.length - end, end);
  for (let i = nodes.length - 1; i >= 0; i--) {
    const trailingToken = nodes[i];
    if (!unifiedLatexUtilMatch.match.comment(trailingToken)) {
      break;
    }
    delete trailingToken.suffixParbreak;
    if (unifiedLatexUtilMatch.match.comment(trailingToken) && trailingToken.leadingWhitespace && !trailingToken.sameline) {
      trailingToken.leadingWhitespace = false;
    }
  }
  return { trimmedEnd: end };
}
function amountOfLeadingAndTrailingWhitespace(ast) {
  let start = 0;
  let end = 0;
  for (const node of ast) {
    if (unifiedLatexUtilMatch.match.whitespace(node) || unifiedLatexUtilMatch.match.parbreak(node)) {
      start++;
    } else {
      break;
    }
  }
  if (start === ast.length) {
    return { start, end: 0 };
  }
  for (let i = ast.length - 1; i >= 0; i--) {
    const node = ast[i];
    if (unifiedLatexUtilMatch.match.whitespace(node) || unifiedLatexUtilMatch.match.parbreak(node)) {
      end++;
    } else {
      break;
    }
  }
  return { start, end };
}
const unifiedLatexTrimEnvironmentContents = function unifiedLatexTrimEnvironmentContents2() {
  return (tree) => {
    unifiedLatexUtilVisit.visit(tree, (node) => {
      if (!(unifiedLatexUtilMatch.match.math(node) || unifiedLatexUtilMatch.match.anyEnvironment(node))) {
        return;
      }
      let firstNode = node.content[0];
      if (unifiedLatexUtilMatch.match.comment(firstNode) && firstNode.sameline) {
        firstNode.suffixParbreak = false;
        trimEnd(node.content);
        const { trimmedStart } = trimStart(node.content.slice(1));
        node.content.splice(1, trimmedStart);
      } else {
        trim(node.content);
      }
    });
  };
};
const unifiedLatexTrimRoot = function unifiedLatexTrimRoot2() {
  return (tree) => {
    trim(tree.content);
  };
};
function hasWhitespaceEquivalent(nodes) {
  let start = false;
  let end = false;
  for (let i = 0; i < nodes.length; i++) {
    const node = nodes[i];
    if (unifiedLatexUtilMatch.match.comment(node)) {
      if (node.leadingWhitespace) {
        start = true;
        break;
      }
      continue;
    }
    if (unifiedLatexUtilMatch.match.whitespace(node)) {
      start = true;
    }
    break;
  }
  for (let j = nodes.length - 1; j >= 0; j--) {
    const node = nodes[j];
    if (unifiedLatexUtilMatch.match.comment(node)) {
      if (node.leadingWhitespace) {
        end = true;
        break;
      }
      continue;
    }
    if (unifiedLatexUtilMatch.match.whitespace(node)) {
      end = true;
    }
    break;
  }
  return { start, end };
}
exports.hasWhitespaceEquivalent = hasWhitespaceEquivalent;
exports.trim = trim;
exports.trimEnd = trimEnd;
exports.trimStart = trimStart;
exports.unifiedLatexTrimEnvironmentContents = unifiedLatexTrimEnvironmentContents;
exports.unifiedLatexTrimRoot = unifiedLatexTrimRoot;
//# sourceMappingURL=index.cjs.map
