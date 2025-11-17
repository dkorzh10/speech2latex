(function() {
  if (typeof globalThis === "object") {
    return;
  }
  Object.defineProperty(Object.prototype, "__magic__", {
    get: function() {
      return this;
    },
    configurable: true
    // This makes it possible to `delete` the getter later.
  });
  __magic__.globalThis = __magic__;
  delete Object.prototype.__magic__;
})();
const clone = typeof globalThis.structuredClone === "function" ? globalThis.structuredClone : (obj) => JSON.parse(JSON.stringify(obj));
function structuredClone(obj) {
  return clone(obj);
}
export {
  structuredClone as s
};
//# sourceMappingURL=index-NHd3tQDq.js.map
