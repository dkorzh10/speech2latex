"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
function normalizeNode(node) {
  if (typeof node === "string") {
    return s(node);
  }
  return node;
}
function normalizeArgument(arg2, openMark = "{", closeMark = "}") {
  if (arg2 == null) {
    return { type: "argument", content: [], openMark: "", closeMark: "" };
  }
  if (typeof arg2 === "string") {
    return {
      type: "argument",
      openMark,
      closeMark,
      content: [s(arg2)]
    };
  }
  if (arg2.type === "argument") {
    return arg2;
  }
  return { type: "argument", openMark, closeMark, content: [arg2] };
}
function normalizeArgumentsList(args2, openMark = "{", closeMark = "}") {
  if (args2 == null) {
    return [];
  }
  if (Array.isArray(args2)) {
    return args2.map((arg2) => normalizeArgument(arg2, openMark, closeMark));
  }
  return [normalizeArgument(args2, openMark, closeMark)];
}
const BRACES_MAP = {
  "*": { openMark: "", closeMark: "" },
  "{": { openMark: "{", closeMark: "}" },
  "[": { openMark: "[", closeMark: "]" },
  "(": { openMark: "(", closeMark: ")" },
  "<": { openMark: "<", closeMark: ">" }
};
const CLOSE_BRACES = new Set(
  Object.values(BRACES_MAP).map((x) => x.closeMark).filter((x) => x)
);
function bracesToOpenAndCloseMarks(braces) {
  const ret = [];
  for (const char of braces.split("")) {
    if (CLOSE_BRACES.has(char)) {
      continue;
    }
    const braces2 = BRACES_MAP[char];
    if (braces2 == null) {
      throw new Error(`Unknown open/close mark type "${char}"`);
    }
    ret.push(braces2);
  }
  return ret;
}
function args(args2, special) {
  if (!Array.isArray(args2)) {
    args2 = [args2];
  }
  if (special == null ? void 0 : special.braces) {
    const braces = bracesToOpenAndCloseMarks(special.braces);
    if (braces.length !== args2.length) {
      throw new Error(
        `There is a difference between the number of supplied braces and the number of supplied arguments. ${args2.length} supplied with braces signature ${special.braces}`
      );
    }
    return args2.map(
      (arg2, i) => normalizeArgument(arg2, braces[i].openMark, braces[i].closeMark)
    );
  }
  const openMark = (special == null ? void 0 : special.defaultOpenMark) ?? "{";
  const closeMark = (special == null ? void 0 : special.defaultCloseMark) ?? "}";
  return normalizeArgumentsList(args2, openMark, closeMark);
}
function arg(args2, special) {
  if (args2 == null) {
    return { type: "argument", content: [], openMark: "", closeMark: "" };
  }
  if (typeof args2 === "string") {
    args2 = s(args2);
  }
  if (!Array.isArray(args2) && args2.type === "argument") {
    return args2;
  }
  let openMark = (special == null ? void 0 : special.openMark) ?? "{";
  let closeMark = (special == null ? void 0 : special.closeMark) ?? "}";
  if (special == null ? void 0 : special.braces) {
    const braces = bracesToOpenAndCloseMarks(special.braces);
    if (braces[0]) {
      openMark = braces[0].openMark;
      closeMark = braces[0].closeMark;
    }
  }
  if (!Array.isArray(args2)) {
    args2 = [args2];
  }
  return { type: "argument", content: args2, openMark, closeMark };
}
function m(name, marcoArgs, special) {
  const args2 = normalizeArgumentsList(marcoArgs);
  const escapeToken = special == null ? void 0 : special.escapeToken;
  const ret = { type: "macro", content: name };
  if (args2.length > 0) {
    ret.args = args2;
  }
  if (escapeToken != null) {
    ret.escapeToken = escapeToken;
  }
  return ret;
}
function s(value) {
  if (typeof value === "string") {
    return { type: "string", content: value };
  }
  return value;
}
function env(name, body, envArgs, special) {
  if (!Array.isArray(body)) {
    body = [body];
  }
  const args2 = normalizeArgumentsList(envArgs, "[", "]");
  const ret = {
    type: "environment",
    env: name,
    content: body.map(normalizeNode)
  };
  if (args2.length > 0) {
    ret.args = args2;
  }
  return ret;
}
const SP = { type: "whitespace" };
exports.SP = SP;
exports.arg = arg;
exports.args = args;
exports.env = env;
exports.m = m;
exports.s = s;
//# sourceMappingURL=index.cjs.map
