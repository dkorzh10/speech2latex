"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
const unifiedLatexUtilMatch = require("@unified-latex/unified-latex-util-match");
const unifiedLatexUtilVisit = require("@unified-latex/unified-latex-util-visit");
function findRegionInArray(tree, start, end) {
  const ret = [];
  let currRegion = { start: void 0, end: tree.length };
  for (let i = 0; i < tree.length; i++) {
    const node = tree[i];
    if (start(node)) {
      currRegion.start = i;
    }
    if (end(node)) {
      currRegion.end = i + 1;
      ret.push(currRegion);
      currRegion = { start: void 0, end: tree.length };
    }
  }
  if (currRegion.start != null) {
    ret.push(currRegion);
  }
  return ret;
}
function refineRegions(regions) {
  const _regions = [...regions];
  _regions.sort((a, b) => a.start - b.start);
  const cutPointsSet = new Set(_regions.flatMap((r) => [r.start, r.end]));
  const cutPoints = Array.from(cutPointsSet);
  cutPoints.sort((a, b) => a - b);
  const retRegions = [];
  const retRegionsContainedIn = [];
  let seekIndex = 0;
  for (let i = 0; i < cutPoints.length - 1; i++) {
    const start = cutPoints[i];
    const end = cutPoints[i + 1];
    const region = { start, end };
    const regionContainedIn = /* @__PURE__ */ new Set();
    let encounteredEndPastStart = false;
    for (let j = seekIndex; j < _regions.length; j++) {
      const superRegion = _regions[j];
      if (superRegion.end >= region.start) {
        encounteredEndPastStart = true;
      }
      if (!encounteredEndPastStart && superRegion.end < region.start) {
        seekIndex = j + 1;
        continue;
      }
      if (superRegion.start > end) {
        break;
      }
      if (superRegion.start <= region.start && superRegion.end >= region.end) {
        encounteredEndPastStart = true;
        regionContainedIn.add(superRegion);
      }
    }
    if (regionContainedIn.size > 0) {
      retRegions.push(region);
      retRegionsContainedIn.push(regionContainedIn);
    }
  }
  return { regions: retRegions, regionsContainedIn: retRegionsContainedIn };
}
function splitByRegions(array, regionsRecord) {
  const ret = [];
  const indices = [0, array.length];
  const reverseMap = {};
  for (const [key, records] of Object.entries(regionsRecord)) {
    indices.push(
      ...records.flatMap((r) => {
        reverseMap["" + [r.start, r.end]] = key;
        return [r.start, r.end];
      })
    );
  }
  indices.sort((a, b) => a - b);
  for (let i = 0; i < indices.length - 1; i++) {
    const start = indices[i];
    const end = indices[i + 1];
    if (start === end) {
      continue;
    }
    const regionKey = reverseMap["" + [start, end]];
    ret.push([regionKey || null, array.slice(start, end)]);
  }
  return ret;
}
function escapeRegExp(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
function buildWordRegex(allowedSet) {
  const regexpStr = `^(${["\\p{L}"].concat(Array.from(allowedSet).map(escapeRegExp)).join("|")})*`;
  return new RegExp(regexpStr, "u");
}
function hasReparsableMacroNamesInArray(tree, allowedTokens) {
  for (let i = 0; i < tree.length; i++) {
    const macro = tree[i];
    const string = tree[i + 1];
    if (unifiedLatexUtilMatch.match.anyMacro(macro) && unifiedLatexUtilMatch.match.anyString(string)) {
      if (allowedTokens.has(
        macro.content.charAt(macro.content.length - 1)
      ) || allowedTokens.has(string.content.charAt(0))) {
        return true;
      }
    }
  }
  return false;
}
function hasReparsableMacroNames(tree, allowedTokens) {
  if (typeof allowedTokens === "string") {
    allowedTokens = new Set(allowedTokens.split(""));
  }
  const _allowedTokens = allowedTokens;
  for (const v of _allowedTokens) {
    if (v.length > 1) {
      throw new Error(
        `Only single characters are allowed as \`allowedTokens\` when reparsing macro names, not \`${v}\`.`
      );
    }
  }
  let ret = false;
  unifiedLatexUtilVisit.visit(
    tree,
    (nodes) => {
      if (hasReparsableMacroNamesInArray(nodes, _allowedTokens)) {
        ret = true;
        return unifiedLatexUtilVisit.EXIT;
      }
    },
    { includeArrays: true, test: Array.isArray }
  );
  return ret;
}
function reparseMacroNamesInArray(tree, allowedTokens) {
  var _a, _b, _c;
  const regex = buildWordRegex(allowedTokens);
  let i = 0;
  while (i < tree.length) {
    const macro = tree[i];
    const string = tree[i + 1];
    if (unifiedLatexUtilMatch.match.anyMacro(macro) && // The _^ macros in math mode should not be extended no-matter what;
    // So we check to make sure that the macro we're dealing with has the default escape token.
    (macro.escapeToken == null || macro.escapeToken === "\\") && unifiedLatexUtilMatch.match.anyString(string) && // There are two options. Either the macro ends with the special character,
    // e.g. `\@foo` or the special character starts the next string, e.g. `\foo@`.
    (allowedTokens.has(
      macro.content.charAt(macro.content.length - 1)
    ) || allowedTokens.has(string.content.charAt(0)))) {
      const match2 = string.content.match(regex);
      const takeable = match2 ? match2[0] : "";
      if (takeable.length > 0) {
        if (takeable.length === string.content.length) {
          macro.content += string.content;
          tree.splice(i + 1, 1);
          if (macro.position && ((_a = string.position) == null ? void 0 : _a.end)) {
            macro.position.end = string.position.end;
          }
        } else {
          macro.content += takeable;
          string.content = string.content.slice(takeable.length);
          if ((_b = macro.position) == null ? void 0 : _b.end) {
            macro.position.end.offset += takeable.length;
            macro.position.end.column += takeable.length;
          }
          if ((_c = string.position) == null ? void 0 : _c.start) {
            string.position.start.offset += takeable.length;
            string.position.start.column += takeable.length;
          }
        }
      } else {
        i++;
      }
    } else {
      ++i;
    }
  }
}
function reparseMacroNames(tree, allowedTokens) {
  if (typeof allowedTokens === "string") {
    allowedTokens = new Set(allowedTokens.split(""));
  }
  const _allowedTokens = allowedTokens;
  for (const v of _allowedTokens) {
    if (v.length > 1) {
      throw new Error(
        `Only single characters are allowed as \`allowedTokens\` when reparsing macro names, not \`${v}\`.`
      );
    }
  }
  unifiedLatexUtilVisit.visit(
    tree,
    (nodes) => {
      reparseMacroNamesInArray(nodes, _allowedTokens);
    },
    { includeArrays: true, test: Array.isArray }
  );
}
const expl3Find = {
  start: unifiedLatexUtilMatch.match.createMacroMatcher(["ExplSyntaxOn"]),
  end: unifiedLatexUtilMatch.match.createMacroMatcher(["ExplSyntaxOff"])
};
const atLetterFind = {
  start: unifiedLatexUtilMatch.match.createMacroMatcher(["makeatletter"]),
  end: unifiedLatexUtilMatch.match.createMacroMatcher(["makeatother"])
};
function findExpl3AndAtLetterRegionsInArray(tree) {
  const expl3 = findRegionInArray(tree, expl3Find.start, expl3Find.end);
  const atLetter = findRegionInArray(
    tree,
    atLetterFind.start,
    atLetterFind.end
  );
  const regionMap = new Map([
    ...expl3.map((x) => [x, "expl"]),
    ...atLetter.map((x) => [x, "atLetter"])
  ]);
  const all = refineRegions([...expl3, ...atLetter]);
  const ret = {
    explOnly: [],
    atLetterOnly: [],
    both: []
  };
  for (let i = 0; i < all.regions.length; i++) {
    const region = all.regions[i];
    const containedIn = all.regionsContainedIn[i];
    if (containedIn.size === 2) {
      ret.both.push(region);
      continue;
    }
    for (const v of containedIn.values()) {
      if (regionMap.get(v) === "expl") {
        ret.explOnly.push(region);
      }
      if (regionMap.get(v) === "atLetter") {
        ret.atLetterOnly.push(region);
      }
    }
  }
  ret.explOnly = ret.explOnly.filter((r) => r.end - r.start > 1);
  ret.atLetterOnly = ret.atLetterOnly.filter((r) => r.end - r.start > 1);
  ret.both = ret.both.filter((r) => r.end - r.start > 1);
  return ret;
}
const atLetterSet = /* @__PURE__ */ new Set(["@"]);
const explSet = /* @__PURE__ */ new Set(["_", ":"]);
const bothSet = /* @__PURE__ */ new Set(["_", ":", "@"]);
function reparseExpl3AndAtLetterRegions(tree) {
  unifiedLatexUtilVisit.visit(
    tree,
    {
      leave: (nodes) => {
        const regions = findExpl3AndAtLetterRegionsInArray(nodes);
        const totalNumRegions = regions.both.length + regions.atLetterOnly.length + regions.explOnly.length;
        if (totalNumRegions === 0) {
          return;
        }
        const splits = splitByRegions(nodes, regions);
        const processed = [];
        for (const [key, slice] of splits) {
          switch (key) {
            case null:
              processed.push(...slice);
              continue;
            case "atLetterOnly":
              reparseMacroNames(slice, atLetterSet);
              processed.push(...slice);
              continue;
            case "explOnly":
              reparseMacroNames(slice, explSet);
              processed.push(...slice);
              continue;
            case "both":
              reparseMacroNames(slice, bothSet);
              processed.push(...slice);
              continue;
            default:
              throw new Error(
                `Unexpected case when splitting ${key}`
              );
          }
        }
        nodes.length = 0;
        nodes.push(...processed);
        return unifiedLatexUtilVisit.SKIP;
      }
    },
    { includeArrays: true, test: Array.isArray }
  );
}
exports.findExpl3AndAtLetterRegionsInArray = findExpl3AndAtLetterRegionsInArray;
exports.findRegionInArray = findRegionInArray;
exports.hasReparsableMacroNames = hasReparsableMacroNames;
exports.hasReparsableMacroNamesInArray = hasReparsableMacroNamesInArray;
exports.reparseExpl3AndAtLetterRegions = reparseExpl3AndAtLetterRegions;
exports.reparseMacroNames = reparseMacroNames;
exports.reparseMacroNamesInArray = reparseMacroNamesInArray;
//# sourceMappingURL=index.cjs.map
