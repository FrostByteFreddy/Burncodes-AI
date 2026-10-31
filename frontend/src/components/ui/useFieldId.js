// Stable ids for label/input pairs
let next = 0;
export const useFieldId = (prefix) => `${prefix}-${++next}`;
