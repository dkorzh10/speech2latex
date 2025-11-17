"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
const unifiedLatexBuilder = require("@unified-latex/unified-latex-builder");
const unifiedLatexUtilArgspec = require("@unified-latex/unified-latex-util-argspec");
const unifiedLatexUtilMatch = require("@unified-latex/unified-latex-util-match");
const unifiedLatexUtilScan = require("@unified-latex/unified-latex-util-scan");
const unifiedLatexUtilRenderInfo = require("@unified-latex/unified-latex-util-render-info");
const unifiedLatexUtilVisit = require("@unified-latex/unified-latex-util-visit");
function gobbleSingleArgument(nodes, argSpec, startPos = 0) {
  if (typeof argSpec === "string" || !argSpec.type) {
    throw new Error(
      `argSpec must be an already-parsed argument specification, not "${JSON.stringify(
        argSpec
      )}"`
    );
  }
  let argument = null;
  let currPos = startPos;
  const gobbleWhitespace = argSpec.noLeadingWhitespace ? () => {
  } : () => {
    while (currPos < nodes.length) {
      if (!unifiedLatexUtilMatch.match.whitespace(nodes[currPos])) {
        break;
      }
      currPos++;
    }
  };
  const openMark = argSpec.openBrace || "";
  const closeMark = argSpec.closeBrace || "";
  const acceptGroup = (argSpec.type === "mandatory" || argSpec.type === "optional") && openMark === "{" && closeMark === "}";
  gobbleWhitespace();
  const currNode = nodes[currPos];
  if (currNode == null || unifiedLatexUtilMatch.match.comment(currNode) || unifiedLatexUtilMatch.match.parbreak(currNode)) {
    const ret = {
      argument,
      nodesRemoved: 0
    };
    return ret;
  }
  switch (argSpec.type) {
    case "mandatory":
      if (acceptGroup) {
        let content = [currNode];
        if (unifiedLatexUtilMatch.match.group(currNode)) {
          content = currNode.content;
        }
        argument = unifiedLatexBuilder.arg(content, {
          openMark,
          closeMark
        });
        currPos++;
        break;
      } else {
        const bracePos2 = findBracePositions(
          nodes,
          currPos,
          openMark,
          closeMark
        );
        if (bracePos2) {
          argument = unifiedLatexBuilder.arg(nodes.slice(bracePos2[0] + 1, bracePos2[1]), {
            openMark,
            closeMark
          });
          currPos = bracePos2[1] + 1;
          break;
        }
      }
    // NOTE: Fallthrough is on purpose.
    // Matching a mandatory argument and an optional argument is the same for our purposes
    // because we're not going to fail to parse because of a missing argument.
    case "optional":
      if (acceptGroup && unifiedLatexUtilMatch.match.group(currNode)) {
        argument = unifiedLatexBuilder.arg(currNode.content, {
          openMark,
          closeMark
        });
        currPos++;
        break;
      }
      const bracePos = findBracePositions(
        nodes,
        currPos,
        openMark,
        closeMark
      );
      if (bracePos) {
        argument = unifiedLatexBuilder.arg(nodes.slice(bracePos[0] + 1, bracePos[1]), {
          openMark,
          closeMark
        });
        currPos = bracePos[1] + 1;
        break;
      }
      break;
    case "optionalStar":
    case "optionalToken": {
      const bracePos2 = findBracePositions(
        nodes,
        currPos,
        argSpec.type === "optionalStar" ? "*" : argSpec.token
      );
      if (bracePos2) {
        argument = unifiedLatexBuilder.arg(currNode, { openMark: "", closeMark: "" });
        currPos = bracePos2[0] + 1;
      }
      break;
    }
    case "until": {
      if (argSpec.stopTokens.length > 1) {
        console.warn(
          `"until" matches with multi-token stop conditions are not yet implemented`
        );
        break;
      }
      const rawToken = argSpec.stopTokens[0];
      const stopToken = rawToken === " " ? { type: "whitespace" } : rawToken;
      let bracePos2 = findBracePositions(
        nodes,
        startPos,
        void 0,
        stopToken
      );
      if (!bracePos2) {
        break;
      }
      argument = unifiedLatexBuilder.arg(nodes.slice(startPos, bracePos2[1]), {
        openMark: "",
        closeMark: rawToken
      });
      currPos = bracePos2[1];
      if (currPos < nodes.length) {
        currPos++;
      }
      break;
    }
    case "embellishment": {
      for (const token of argSpec.embellishmentTokens) {
        const bracePos2 = findBracePositions(nodes, currPos, token);
        if (!bracePos2) {
          continue;
        }
        let argNode = nodes[bracePos2[0] + 1];
        argument = unifiedLatexBuilder.arg(
          unifiedLatexUtilMatch.match.group(argNode) ? argNode.content : argNode,
          {
            openMark: token,
            closeMark: ""
          }
        );
        currPos = bracePos2[1] + 1;
        break;
      }
      break;
    }
    default:
      console.warn(
        `Don't know how to find an argument of argspec type "${argSpec.type}"`
      );
  }
  const nodesRemoved = argument ? currPos - startPos : 0;
  nodes.splice(startPos, nodesRemoved);
  return { argument, nodesRemoved };
}
function cloneStringNode(node, content) {
  return Object.assign({}, node, { content });
}
function findBracePositions(nodes, startPos, openMark, closeMark) {
  const currNode = nodes[startPos];
  let openMarkPos = startPos;
  let closeMarkPos = startPos;
  if (openMark) {
    if (!unifiedLatexUtilMatch.match.anyString(currNode)) {
      return;
    }
    const nodeContent = currNode.content;
    if (!nodeContent.startsWith(openMark)) {
      return;
    }
    openMarkPos = startPos;
    if (currNode.content.length > openMark.length) {
      const nodeContent2 = currNode.content;
      currNode.content = openMark;
      nodes.splice(
        openMarkPos + 1,
        0,
        cloneStringNode(currNode, nodeContent2.slice(openMark.length))
      );
    }
    closeMarkPos = openMarkPos + 1;
  }
  if (!closeMark) {
    const argNode = nodes[closeMarkPos];
    if (!argNode) {
      return;
    }
    if (unifiedLatexUtilMatch.match.anyString(argNode) && argNode.content.length > 1) {
      const argContent = argNode.content;
      argNode.content = argContent[0];
      nodes.splice(
        closeMarkPos + 1,
        0,
        cloneStringNode(argNode, argContent.slice(1))
      );
    }
    return [openMarkPos, closeMarkPos];
  }
  closeMarkPos = unifiedLatexUtilScan.scan(nodes, closeMark, {
    startIndex: closeMarkPos,
    allowSubstringMatches: true
  });
  if (closeMarkPos === null) {
    return;
  }
  const closingNode = nodes[closeMarkPos];
  if (unifiedLatexUtilMatch.match.anyString(closingNode) && typeof closeMark === "string") {
    const closingNodeContent = closingNode.content;
    let closeMarkIndex = closingNodeContent.indexOf(closeMark);
    if (closingNodeContent.length > closeMark.length) {
      closingNode.content = closeMark;
      const prev = closingNodeContent.slice(0, closeMarkIndex);
      const next = closingNodeContent.slice(
        closeMarkIndex + closeMark.length
      );
      if (prev) {
        nodes.splice(
          closeMarkPos,
          0,
          cloneStringNode(closingNode, prev)
        );
        closeMarkPos++;
      }
      if (next) {
        nodes.splice(
          closeMarkPos + 1,
          0,
          cloneStringNode(closingNode, next)
        );
      }
    }
  }
  return [openMarkPos, closeMarkPos];
}
function gobbleArguments(nodes, argSpec, startPos = 0) {
  if (typeof argSpec === "function") {
    return argSpec(nodes, startPos);
  }
  if (typeof argSpec === "string") {
    argSpec = unifiedLatexUtilArgspec.parse(argSpec);
  }
  const args = [];
  let nodesRemoved = 0;
  for (const spec of argSpec) {
    if (spec.type === "embellishment") {
      const remainingTokens = new Set(spec.embellishmentTokens);
      const argForToken = Object.fromEntries(
        spec.embellishmentTokens.map((t, i) => {
          var _a;
          const defaultArg = "defaultArg" in spec ? (_a = spec.defaultArg) == null ? void 0 : _a[i] : void 0;
          return [t, emptyArg(defaultArg)];
        })
      );
      let { argument, nodesRemoved: removed } = gobbleSingleArgument(
        nodes,
        embellishmentSpec(remainingTokens),
        startPos
      );
      while (argument) {
        const token = argument.openMark;
        remainingTokens.delete(token);
        argForToken[token] = argument;
        nodesRemoved += removed;
        const newSpec = embellishmentSpec(remainingTokens);
        ({ argument, nodesRemoved: removed } = gobbleSingleArgument(
          nodes,
          newSpec,
          startPos
        ));
      }
      args.push(...spec.embellishmentTokens.map((t) => argForToken[t]));
    } else {
      const { argument, nodesRemoved: removed } = gobbleSingleArgument(
        nodes,
        spec,
        startPos
      );
      const defaultArg = "defaultArg" in spec ? spec.defaultArg : void 0;
      args.push(argument || emptyArg(defaultArg));
      nodesRemoved += removed;
    }
  }
  return { args, nodesRemoved };
}
function embellishmentSpec(tokens) {
  return {
    type: "embellishment",
    embellishmentTokens: [...tokens]
  };
}
function emptyArg(defaultArg) {
  const ret = unifiedLatexBuilder.arg([], { openMark: "", closeMark: "" });
  if (defaultArg != null) {
    unifiedLatexUtilRenderInfo.updateRenderInfo(ret, { defaultArg });
  }
  return ret;
}
function attachMacroArgsInArray(nodes, macros) {
  let currIndex;
  const isRelevantMacro = unifiedLatexUtilMatch.match.createMacroMatcher(macros);
  function gobbleUntilMacro() {
    while (currIndex >= 0 && !isRelevantMacro(nodes[currIndex])) {
      currIndex--;
    }
  }
  currIndex = nodes.length - 1;
  while (currIndex >= 0) {
    gobbleUntilMacro();
    if (currIndex < 0) {
      return;
    }
    const macroIndex = currIndex;
    const macro = nodes[macroIndex];
    const macroName = macro.content;
    const macroInfo = macros[macroName];
    unifiedLatexUtilRenderInfo.updateRenderInfo(macro, macroInfo.renderInfo);
    const signatureOrParser = macroInfo.argumentParser || macroInfo.signature;
    if (signatureOrParser == null) {
      currIndex--;
      continue;
    }
    if (macro.args != null) {
      currIndex = macroIndex - 1;
      continue;
    }
    currIndex++;
    const { args } = gobbleArguments(nodes, signatureOrParser, currIndex);
    macro.args = args;
    currIndex = macroIndex - 1;
  }
}
function attachMacroArgs(tree, macros) {
  unifiedLatexUtilVisit.visit(
    tree,
    (nodes) => {
      attachMacroArgsInArray(nodes, macros);
    },
    { includeArrays: true, test: Array.isArray }
  );
}
const unifiedLatexAttachMacroArguments = function unifiedLatexAttachMacroArguments2(options) {
  return (tree) => {
    const { macros = {} } = options || {};
    if (Object.keys(macros).length === 0) {
      console.warn(
        "Attempting to attach macro arguments but no macros are specified."
      );
    }
    unifiedLatexUtilVisit.visit(
      tree,
      (nodes) => {
        attachMacroArgsInArray(nodes, macros);
      },
      { includeArrays: true, test: Array.isArray }
    );
  };
};
function getArgsContent(node) {
  if (!Array.isArray(node.args)) {
    return [];
  }
  return node.args.map((arg) => {
    if (arg.openMark === "" && arg.content.length === 0) {
      return null;
    }
    return arg.content;
  });
}
function getNamedArgsContent(node, namedArgumentsFallback = []) {
  var _a;
  const names = ((_a = node._renderInfo) == null ? void 0 : _a.namedArguments) || namedArgumentsFallback;
  if (!Array.isArray(node.args) || !Array.isArray(names) || names.length === 0) {
    return {};
  }
  const ret = {};
  node.args.forEach((arg, i) => {
    const name = names[i];
    if (name == null) {
      return;
    }
    let val = arg.content;
    if (arg.openMark === "" && arg.content.length === 0) {
      val = null;
    }
    ret[name] = val;
  });
  return ret;
}
exports.attachMacroArgs = attachMacroArgs;
exports.attachMacroArgsInArray = attachMacroArgsInArray;
exports.getArgsContent = getArgsContent;
exports.getNamedArgsContent = getNamedArgsContent;
exports.gobbleArguments = gobbleArguments;
exports.gobbleSingleArgument = gobbleSingleArgument;
exports.unifiedLatexAttachMacroArguments = unifiedLatexAttachMacroArguments;
//# sourceMappingURL=index.cjs.map
