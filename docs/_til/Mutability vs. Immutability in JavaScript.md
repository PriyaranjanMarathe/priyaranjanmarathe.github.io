---
layout: default
title: Mutability vs. Immutability in JavaScript
comments: true
date: 2024-12-22
categories: tils
---
# TIL: Mutability vs. Immutability in JavaScript 

## Understanding the Problem of Mutability

In JavaScript, objects are mutable by default. When you copy an object, you're often just copying the reference, not the actual data. This leads to situations where changes to one object inadvertently affect another.

### Example: Mutating Shared Data
```javascript
const account = {
  owner: "Bob",
  balance: { amount: 100 }
};

const clonedAccount = account;  // Not a copy, just a reference!
clonedAccount.balance.amount = 50;

console.log(account.balance.amount);  // 50 (Oops! Unexpected mutation)
```
- **Why it happens**: `clonedAccount` points to the same memory location as `account`.
- **Why it matters**: Changing one object changes the other unintentionally.

---

## How Immutability Solves This

Immutability ensures that data cannot be directly changed. Instead, when modifications are needed, a new object is created.

### Example: Immutable Copy
```javascript
const account = {
  owner: "Bob",
  balance: { amount: 100 }
};

const newAccount = structuredClone(account);
newAccount.balance.amount = 50;

console.log(account.balance.amount);  // 100 (No mutation!)
```
- **Why it works**: `structuredClone` creates a deep copy, ensuring that `newAccount` and `account` are separate objects.

---

## Techniques to Achieve Immutability

### 1. Shallow Copy (Doesn't Prevent Deep Mutation)
```javascript
const shallowCopy = { ...account };
shallowCopy.balance.amount = 50;
console.log(account.balance.amount);  // 50 (Oops, shallow copy!)
```

### 2. Deep Copy with `structuredClone`
```javascript
const deepCopy = structuredClone(account);
deepCopy.balance.amount = 50;
console.log(account.balance.amount);  // 100 (Deep copy prevents mutation)
```

- **Takeaway**: Shallow copies copy only the top level. Deep copies ensure nested objects are also cloned.

---

## Real-World Scenario: Loan Records
Imagine managing a loan system where modifying one user's loan record could accidentally change others.

```javascript
const defaultLoan = {
  amount: 1000,
  history: { lastPayment: "01-01-2024" }
};

function updateLoan(userLoan) {
  const loan = structuredClone(defaultLoan);
  return { ...loan, ...userLoan };
}

const updatedLoan = updateLoan({ amount: 750 });
console.log(updatedLoan.amount);  // 750
console.log(defaultLoan.amount);  // 1000 (Unchanged)
```
- **Without `structuredClone`**: Modifying the loan record directly mutates the original.
- **With `structuredClone`**: The original data remains unchanged.

---

## Why Immutability Matters

### Prevents Unintended Side Effects
- **Mutable**: One small change can ripple across your application.
- **Immutable**: Changes are predictable and isolated.

### Supports Functional Programming
- Functions that don't modify outside variables are easier to debug and reason about.

---

## Common Pitfalls with Cloning

1. **Non-Serializable Values**:
```javascript
const obj = { compute: () => 42 };
structuredClone(obj);  // DataCloneError
```
- **Why**: Functions and DOM elements cannot be cloned.
- **Fix**: Exclude or handle non-serializable properties before cloning.

2. **Circular References**:
```javascript
const obj = {};
obj.self = obj;
const copy = structuredClone(obj);
console.log(copy.self === copy);  // true
```
- **Benefit**: `structuredClone` can handle circular references, unlike `JSON.stringify`.

3. **Performance Costs**:
- Deep cloning large objects can be expensive. Use shallow copies for simple data structures.

---

## Hands-On Practice
- Try these examples in your browser's console.
- Experiment with `structuredClone` on [JSFiddle](https://jsfiddle.net/) or [CodeSandbox](https://codesandbox.io/).
- Read more at [MDN structuredClone Docs](https://developer.mozilla.org/en-US/docs/Web/API/structuredClone).

---

## When to Use Immutability
- **State Management**: Ensures React or Redux states remain pure.
- **Data Integrity**: Prevents accidental mutations in financial apps or databases.
- **Concurrency**: Immutable data is thread-safe, making it ideal for parallel programming.

### When NOT to Use Immutability
- Performance-sensitive code (deep cloning can slow things down).
- Temporary or simple objects that don't require strict state control.

---

## Conclusion
Mutability introduces hidden bugs. Embracing immutability through techniques like `structuredClone` leads to cleaner, safer, and more predictable code. Understanding when to use deep vs. shallow copies can prevent unnecessary headaches and ensure data integrity across your application.

