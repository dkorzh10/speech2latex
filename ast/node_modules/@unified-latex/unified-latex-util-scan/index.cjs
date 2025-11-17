"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
const unifiedLatexUtilMatch = require("@unified-latex/unified-latex-util-match");
const unifiedLatexUtilPrintRaw = require("@unified-latex/unified-latex-util-print-raw");
const Trie = require("trie-prefix-tree");
function scan(nodes, token, options) {
  const { startIndex, onlySkipWhitespaceAndComments, allowSubstringMatches } = options || {};
  if (typeof token === "string") {
    token = { type: "string", content: token };
  }
  for (let i = startIndex || 0; i < nodes.length; i++) {
    const node = nodes[i];
    if (node.type === token.type) {
      switch (node.type) {
        case "comment":
        case "displaymath":
        case "inlinemath":
        case "root":
        case "parbreak":
        case "whitespace":
        case "verb":
        case "verbatim":
        case "group":
          return i;
        case "macro":
          if (node.content === token.content) {
            return i;
          }
          break;
        case "environment":
        case "mathenv":
          if (unifiedLatexUtilPrintRaw.printRaw(node.env) === unifiedLatexUtilPrintRaw.printRaw(token.env)) {
            return i;
          }
          break;
        case "string":
          if (node.content === token.content) {
            return i;
          }
          if (allowSubstringMatches && node.content.indexOf(token.content) >= 0) {
            return i;
          }
          break;
      }
    }
    if (onlySkipWhitespaceAndComments && !unifiedLatexUtilMatch.match.whitespace(node) && !unifiedLatexUtilMatch.match.comment(node)) {
      return null;
    }
  }
  return null;
}
function prefixMatch(nodes, prefixes, options) {
  const {
    startIndex = 0,
    matchSubstrings = false,
    assumeOneCharStrings = false
  } = options || {};
  if (typeof prefixes === "string") {
    prefixes = [prefixes];
  }
  if (Array.isArray(prefixes)) {
    prefixes = Trie(prefixes);
  }
  const prefixTree = prefixes;
  const history = {
    lastPrefix: "",
    lastWord: "",
    index: startIndex,
    partialMatch: ""
  };
  function tryToMatchNextChar(char, index) {
    let ret = false;
    if (prefixTree.isPrefix(history.lastPrefix + char)) {
      history.lastPrefix += char;
      history.index = index;
      ret = true;
    }
    if (prefixTree.hasWord(history.lastPrefix)) {
      history.lastWord = history.lastPrefix;
    }
    return ret;
  }
  for (let i = 0; startIndex + i < nodes.length; i++) {
    const node = nodes[startIndex + i];
    if (!unifiedLatexUtilMatch.match.string(node)) {
      break;
    }
    if (assumeOneCharStrings && node.content.length !== 1) {
      break;
    }
    if (matchSubstrings) {
      let fullMatch = true;
      history.partialMatch = "";
      for (let j = 0; j < node.content.length; j++) {
        const char = node.content[j];
        if (tryToMatchNextChar(char, startIndex + i)) {
          history.partialMatch += char;
        } else {
          fullMatch = false;
          break;
        }
      }
      if (fullMatch) {
        history.partialMatch = "";
      } else {
        break;
      }
    } else {
      if (!tryToMatchNextChar(node.content, startIndex + i)) {
        break;
      }
    }
  }
  return history.lastWord ? {
    match: history.lastWord,
    endNodeIndex: history.index,
    endNodePartialMatch: history.partialMatch ? history.partialMatch : null
  } : null;
}
exports.Trie = Trie;
exports.prefixMatch = prefixMatch;
exports.scan = scan;
//# sourceMappingURL=index.cjs.map
