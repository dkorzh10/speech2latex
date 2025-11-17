import { match } from "@unified-latex/unified-latex-util-match";
function splitOnCondition(nodes, splitFunc = () => false, options) {
  if (!Array.isArray(nodes)) {
    throw new Error(`Can only split an Array, not ${nodes}`);
  }
  const { onlySplitOnFirstOccurrence = false } = options || {};
  const splitIndices = [];
  for (let i = 0; i < nodes.length; i++) {
    if (splitFunc(nodes[i])) {
      splitIndices.push(i);
      if (onlySplitOnFirstOccurrence) {
        break;
      }
    }
  }
  if (splitIndices.length === 0) {
    return { segments: [nodes], separators: [] };
  }
  let separators = splitIndices.map((i) => nodes[i]);
  let segments = splitIndices.map((splitEnd, i) => {
    const splitStart = i === 0 ? 0 : splitIndices[i - 1] + 1;
    return nodes.slice(splitStart, splitEnd);
  });
  segments.push(
    nodes.slice(splitIndices[splitIndices.length - 1] + 1, nodes.length)
  );
  return { segments, separators };
}
function splitOnMacro(ast, macroName) {
  if (typeof macroName === "string") {
    macroName = [macroName];
  }
  if (!Array.isArray(macroName)) {
    throw new Error("Type coercion failed");
  }
  const isSeparator = match.createMacroMatcher(macroName);
  const { segments, separators } = splitOnCondition(ast, isSeparator);
  return { segments, macros: separators };
}
function unsplitOnMacro({
  segments,
  macros
}) {
  if (segments.length === 0) {
    console.warn("Trying to join zero segments");
    return [];
  }
  if (segments.length !== macros.length + 1) {
    console.warn(
      "Mismatch between lengths of macros and segments when trying to unsplit"
    );
  }
  let ret = segments[0];
  for (let i = 0; i < macros.length; i++) {
    ret = ret.concat(macros[i]).concat(segments[i + 1]);
  }
  return ret;
}
function arrayJoin(array, sep) {
  return array.flatMap((item, i) => {
    if (i === 0) {
      return item;
    }
    if (Array.isArray(sep)) {
      return [...sep, ...item];
    } else {
      return [sep, ...item];
    }
  });
}
export {
  arrayJoin,
  splitOnCondition,
  splitOnMacro,
  unsplitOnMacro
};
//# sourceMappingURL=index.js.map
