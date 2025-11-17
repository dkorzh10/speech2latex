"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
const unifiedLatexUtilVisit = require("@unified-latex/unified-latex-util-visit");
const unifiedLatexUtilMatch = require("@unified-latex/unified-latex-util-match");
const unifiedLatexUtilTrim = require("@unified-latex/unified-latex-util-trim");
const unifiedLatexUtilSplit = require("@unified-latex/unified-latex-util-split");
function replaceNode(ast, visitor) {
  unifiedLatexUtilVisit.visit(ast, {
    leave: (node, info) => {
      let replacement = visitor(node, info);
      if (typeof replacement === "undefined" || replacement === node) {
        return;
      }
      if (!info.containingArray || info.index == null) {
        throw new Error(
          "Trying to replace node, but cannot find containing array"
        );
      }
      if (replacement === null || Array.isArray(replacement) && replacement.length === 0) {
        info.containingArray.splice(info.index, 1);
        return info.index;
      }
      if (!Array.isArray(replacement)) {
        replacement = [replacement];
      }
      info.containingArray.splice(info.index, 1, ...replacement);
      return info.index + replacement.length;
    }
  });
}
function firstSignificantNode(nodes, parbreaksAreInsignificant) {
  const index = firstSignificantNodeIndex(nodes, parbreaksAreInsignificant);
  if (index == null) {
    return null;
  }
  return nodes[index];
}
function lastSignificantNode(nodes, parbreaksAreInsignificant) {
  const index = lastSignificantNodeIndex(nodes, parbreaksAreInsignificant);
  if (index == null) {
    return null;
  }
  return nodes[index];
}
function lastSignificantNodeIndex(nodes, parbreaksAreInsignificant) {
  for (let i = nodes.length - 1; i >= 0; i--) {
    const node = nodes[i];
    if (unifiedLatexUtilMatch.match.whitespace(node) || unifiedLatexUtilMatch.match.comment(node) || parbreaksAreInsignificant && unifiedLatexUtilMatch.match.parbreak(node)) {
      continue;
    }
    return i;
  }
  return void 0;
}
function firstSignificantNodeIndex(nodes, parbreaksAreInsignificant) {
  for (let i = 0; i < nodes.length; i++) {
    const node = nodes[i];
    if (unifiedLatexUtilMatch.match.whitespace(node) || unifiedLatexUtilMatch.match.comment(node) || parbreaksAreInsignificant && unifiedLatexUtilMatch.match.parbreak(node)) {
      continue;
    }
    return i;
  }
  return void 0;
}
function isSpaceLike(node) {
  return unifiedLatexUtilMatch.match.whitespace(node) || unifiedLatexUtilMatch.match.comment(node) && Boolean(node.leadingWhitespace);
}
function joinWithoutExcessWhitespace(head, tail) {
  if (tail.length === 0) {
    return;
  }
  if (head.length === 0) {
    head.push(...tail);
    return;
  }
  const headEnd = head[head.length - 1];
  const tailStart = tail[0];
  if (unifiedLatexUtilMatch.match.whitespace(headEnd) && unifiedLatexUtilMatch.match.whitespace(tailStart)) {
    head.push(...tail.slice(1));
    return;
  }
  if (!isSpaceLike(headEnd) || !isSpaceLike(tailStart)) {
    if (unifiedLatexUtilMatch.match.whitespace(headEnd) && unifiedLatexUtilMatch.match.comment(tailStart)) {
      const comment2 = {
        type: "comment",
        content: tailStart.content,
        sameline: true,
        leadingWhitespace: true
      };
      tail = tail.slice(1);
      unifiedLatexUtilTrim.trimStart(tail);
      head.pop();
      head.push(comment2, ...tail);
      return;
    }
    head.push(...tail);
    return;
  }
  if (unifiedLatexUtilMatch.match.comment(headEnd) && unifiedLatexUtilMatch.match.comment(tailStart)) {
    if (tailStart.leadingWhitespace || tailStart.sameline) {
      head.push(
        { type: "comment", content: tailStart.content },
        ...tail.slice(1)
      );
      return;
    }
    head.push(...tail);
    return;
  }
  let comment = unifiedLatexUtilMatch.match.comment(headEnd) ? headEnd : tailStart;
  if (!unifiedLatexUtilMatch.match.comment(comment)) {
    throw new Error(
      `Expected a comment but found ${JSON.stringify(comment)}`
    );
  }
  if (!comment.leadingWhitespace || !comment.sameline) {
    comment = {
      type: "comment",
      content: comment.content,
      leadingWhitespace: true,
      sameline: true
    };
  }
  head.pop();
  head.push(comment, ...tail.slice(1));
}
function wrapSignificantContent(content, wrapper) {
  let hoistUntil = 0;
  let hoistAfter = content.length;
  for (let i = 0; i < content.length; i++) {
    if (unifiedLatexUtilMatch.match.whitespace(content[i]) || unifiedLatexUtilMatch.match.comment(content[i])) {
      hoistUntil = i + 1;
      continue;
    }
    break;
  }
  for (let j = content.length - 1; j >= 0; j--) {
    if (unifiedLatexUtilMatch.match.whitespace(content[j]) || unifiedLatexUtilMatch.match.comment(content[j])) {
      hoistAfter = j;
      continue;
    }
    break;
  }
  if (hoistUntil === 0 && hoistAfter === content.length) {
    return ensureArray(wrapper(content));
  }
  const frontMatter = content.slice(0, hoistUntil);
  const middle = content.slice(hoistUntil, hoistAfter);
  const backMatter = content.slice(hoistAfter, content.length);
  return frontMatter.concat(wrapper(middle), backMatter);
}
function ensureArray(x) {
  if (!Array.isArray(x)) {
    return [x];
  }
  return x;
}
function replaceStreamingCommandInArray(nodes, isStreamingCommand, replacer) {
  while (nodes.length > 0 && isStreamingCommand(nodes[nodes.length - 1])) {
    nodes.pop();
    unifiedLatexUtilTrim.trimEnd(nodes);
  }
  const foundStreamingCommands = [];
  for (let i = nodes.length - 1; i >= 0; i--) {
    const node = nodes[i];
    if (isStreamingCommand(node)) {
      const wrapper = (content) => replacer(content, node);
      let tail = nodes.slice(i + 1);
      unifiedLatexUtilTrim.trimStart(tail);
      tail = wrapSignificantContent(tail, wrapper);
      foundStreamingCommands.push(node);
      nodes.splice(i);
      joinWithoutExcessWhitespace(nodes, tail);
    }
  }
  return { foundStreamingCommands };
}
function replaceStreamingCommandInGroup(group, isStreamingCommand, replacer, options) {
  const content = group.content;
  let popFromGroup = isStreamingCommand(firstSignificantNode(content));
  let innerProcessed = replaceStreamingCommand(
    content,
    isStreamingCommand,
    replacer,
    options
  );
  if (innerProcessed.length === 0) {
    return [];
  }
  if (popFromGroup) {
    return innerProcessed;
  } else {
    return [{ type: "group", content: innerProcessed }];
  }
}
function replaceStreamingCommand(ast, isStreamingCommand, replacer, options) {
  if (typeof isStreamingCommand !== "function") {
    throw new Error(
      `'isStreamingCommand' must be a function, not '${typeof isStreamingCommand}'`
    );
  }
  const {
    macrosThatBreakPars = [
      "part",
      "chapter",
      "section",
      "subsection",
      "subsubsection",
      "vspace",
      "smallskip",
      "medskip",
      "bigskip",
      "hfill"
    ],
    environmentsThatDontBreakPars = []
  } = options || {};
  let processedContent = [];
  if (unifiedLatexUtilMatch.match.group(ast)) {
    processedContent = replaceStreamingCommandInGroup(
      ast,
      isStreamingCommand,
      replacer
    );
  }
  if (Array.isArray(ast)) {
    const nodes = ast;
    let scanIndex = nodes.length;
    let sliceIndex = scanIndex;
    while (scanIndex > 0 && (isStreamingCommand(nodes[scanIndex - 1]) || unifiedLatexUtilMatch.match.whitespace(nodes[scanIndex - 1]))) {
      scanIndex--;
      if (isStreamingCommand(nodes[scanIndex])) {
        sliceIndex = scanIndex;
      }
    }
    if (sliceIndex !== nodes.length) {
      nodes.splice(sliceIndex);
    }
    const macroThatBreaks = unifiedLatexUtilMatch.match.createMacroMatcher(macrosThatBreakPars);
    const envThatDoesntBreak = unifiedLatexUtilMatch.match.createEnvironmentMatcher(
      environmentsThatDontBreakPars
    );
    const isPar = (node) => unifiedLatexUtilMatch.match.parbreak(node) || unifiedLatexUtilMatch.match.macro(node, "par") || macroThatBreaks(node) || unifiedLatexUtilMatch.match.environment(node) && !envThatDoesntBreak(node) || node.type === "displaymath";
    const splitByPar = unifiedLatexUtilSplit.splitOnCondition(nodes, isPar);
    splitByPar.separators = splitByPar.separators.map(
      (sep) => unifiedLatexUtilMatch.match.macro(sep, "par") ? { type: "parbreak" } : sep
    );
    const replacers = [];
    let segments = splitByPar.segments.map((segment) => {
      if (segment.length === 0) {
        return segment;
      }
      function applyAccumulatedReplacers(nodes2) {
        if (replacers.length === 0) {
          return nodes2;
        }
        return wrapSignificantContent(
          nodes2,
          composeReplacers(replacers)
        );
      }
      const { foundStreamingCommands } = replaceStreamingCommandInArray(
        segment,
        isStreamingCommand,
        replacer
      );
      const ret = applyAccumulatedReplacers(segment);
      foundStreamingCommands.forEach((macro) => {
        replacers.push((nodes2) => {
          const ret2 = replacer(nodes2, macro);
          if (!Array.isArray(ret2)) {
            return [ret2];
          }
          return ret2;
        });
      });
      return ret;
    });
    if (segments.length > 1) {
      segments.forEach((segment, i) => {
        if (i === 0) {
          unifiedLatexUtilTrim.trimEnd(segment);
        } else if (i === segments.length - 1) {
          unifiedLatexUtilTrim.trimStart(segment);
        } else {
          unifiedLatexUtilTrim.trim(segment);
        }
      });
    }
    processedContent = unifiedLatexUtilSplit.unsplitOnMacro({
      segments,
      macros: splitByPar.separators
    });
  }
  return processedContent;
}
function composeReplacers(replacers) {
  if (replacers.length === 0) {
    throw new Error("Cannot compose zero replacement functions");
  }
  return (nodes) => {
    let ret = nodes;
    for (let i = 0; i < replacers.length; i++) {
      const func = replacers[i];
      ret = func(ret);
    }
    return ret;
  };
}
function replaceNodeDuringVisit(replacement, info) {
  const parent = info.parents[0];
  if (!parent) {
    throw new Error(`Cannot replace node: parent not found`);
  }
  const container = parent[info.key];
  if (!Array.isArray(container)) {
    throw new Error(`Cannot replace node: containing array not found`);
  }
  if (info.index == null) {
    throw new Error(`Cannot replace node: node index undefined`);
  }
  if (!Array.isArray(replacement)) {
    container[info.index] = replacement;
  } else {
    container.splice(info.index, 1, ...replacement);
  }
}
const unifiedLatexReplaceStreamingCommands = function unifiedLatexReplaceStreamingCommands2(options) {
  const { replacers = {} } = options || {};
  const isReplaceable = unifiedLatexUtilMatch.match.createMacroMatcher(replacers);
  return (tree) => {
    unifiedLatexUtilVisit.visit(
      tree,
      (group, info) => {
        if (info.context.hasMathModeAncestor || !group.content.some(isReplaceable)) {
          return;
        }
        let fixed = replaceStreamingCommand(
          group,
          isReplaceable,
          (content, command) => {
            return replacers[command.content](content, command);
          }
        );
        if (!info.containingArray || info.index == null) {
          return;
        }
        const prevToken = info.containingArray[info.index - 1];
        const nextToken = info.containingArray[info.index + 1];
        if (unifiedLatexUtilMatch.match.whitespaceLike(prevToken) && unifiedLatexUtilMatch.match.whitespaceLike(fixed[0])) {
          unifiedLatexUtilTrim.trimStart(fixed);
        }
        if (unifiedLatexUtilMatch.match.whitespaceLike(nextToken) && unifiedLatexUtilMatch.match.whitespaceLike(fixed[fixed.length - 1])) {
          unifiedLatexUtilTrim.trimEnd(fixed);
        }
        replaceNodeDuringVisit(fixed, info);
      },
      { test: unifiedLatexUtilMatch.match.group }
    );
    unifiedLatexUtilVisit.visit(
      tree,
      (nodes, info) => {
        if (info.context.hasMathModeAncestor || !nodes.some(isReplaceable)) {
          return;
        }
        const replaced = replaceStreamingCommand(
          nodes,
          isReplaceable,
          (content, command) => {
            return replacers[command.content](content, command);
          }
        );
        if (replaced !== nodes) {
          nodes.length = 0;
          nodes.push(...replaced);
        }
      },
      { includeArrays: true, test: Array.isArray }
    );
  };
};
exports.firstSignificantNode = firstSignificantNode;
exports.firstSignificantNodeIndex = firstSignificantNodeIndex;
exports.lastSignificantNode = lastSignificantNode;
exports.lastSignificantNodeIndex = lastSignificantNodeIndex;
exports.replaceNode = replaceNode;
exports.replaceNodeDuringVisit = replaceNodeDuringVisit;
exports.replaceStreamingCommand = replaceStreamingCommand;
exports.replaceStreamingCommandInGroup = replaceStreamingCommandInGroup;
exports.unifiedLatexReplaceStreamingCommands = unifiedLatexReplaceStreamingCommands;
//# sourceMappingURL=index.cjs.map
