---
layout: default
title: Schema Validation
comments: true
date: 2024-12-22
categories:
---
# TIL: Constructing and Validating Nested Payloads from DB Config Tables

Constructing deeply nested payloads from database config tables can be tricky, especially when external APIs expect strict schema compliance. Here's how to handle it without losing your mind.

---

## Scenario:
Imagine you have a database table `config_parameters` with fields like:

| id  | category  | key                            | value   |
|-----|-----------|--------------------------------|---------|
| 1   | machine   | Max Output RPM                 | 3200    |
| 2   | machine   | Efficiency %                   | 92.5    |
| 3   | tank      | Max Capacity L                 | 1500    |
| 4   | tank      | Current Temp °C                | 87      |
| 5   | sensor    | Humidity %                     | 45.3    |
| 6   | sensor    | Pressure kPa                   | 101.3   |

**Goal:**
- Construct a nested payload from this table.
- Validate it against the API's expected schema before sending.

---

## Manual Payload Construction:
A manual, verbose approach often works best for clarity and debugging.

```javascript
let payload = { presets: { machine: {}, tank: {}, sensor: {} } };

// Manual assignments
payload.presets.machine["Max Output RPM"] = 3200;
payload.presets.machine["Efficiency %"] = 92.5;
payload.presets.tank["Max Capacity L"] = 1500;
payload.presets.tank["Current Temp °C"] = 87;
payload.presets.sensor["Humidity %"] = 45.3;
payload.presets.sensor["Pressure kPa"] = 101.3;
```

### Why This Works:
- **Explicit and readable** – No loops to decipher.
- **Manual validation** – Field errors are easy to spot.
- **Patchable** – Missing a value? Add a line.

---

## Automating with Loops (Safely):
Dynamic construction can work with small safeguards in place.

```javascript
let payload = { presets: { machine: {}, tank: {}, sensor: {} } };
let dbRows = [
  { category: 'machine', key: 'Max Output RPM', value: 3200 },
  { category: 'machine', key: 'Efficiency %', value: 92.5 },
  { category: 'tank', key: 'Max Capacity L', value: 1500 },
  { category: 'tank', key: 'Current Temp °C', value: 87 },
  { category: 'sensor', key: 'Humidity %', value: 45.3 },
  { category: 'sensor', key: 'Pressure kPa', value: 101.3 }
];

// Populate payload dynamically
for (let row of dbRows) {
  payload.presets[row.category][row.key] = row.value;
}
```

### Why Be Careful:
- **Unexpected DB values** can break the API.
- **Schema mismatches** happen without notice.

---

## Validating Against API Schema:
Suppose the API expects:

```json
{
  "machine": ["Max Output RPM", "Efficiency %"],
  "tank": ["Max Capacity L"],
  "sensor": ["Humidity %", "Pressure kPa"]
}
```

### Validation Example (JS):

```javascript
let apiSchema = {
  machine: ["Max Output RPM", "Efficiency %"],
  tank: ["Max Capacity L"],
  sensor: ["Humidity %", "Pressure kPa"]
};

function validatePayload(payload, schema) {
  let errors = [];

  for (let category in schema) {
    schema[category].forEach(key => {
      if (!(key in payload.presets[category])) {
        errors.push(`${category}: Missing ${key}`);
      }
    });
  }

  return errors.length ? errors : "Payload is valid!";
}

console.log(validatePayload(payload, apiSchema));
```

---

## Real-Life Example – Game Config:

```javascript
let gamePayload = { presets: { player: {}, weapons: {}, levels: {} } };

gamePayload.presets.player["Max Health"] = 100;
gamePayload.presets.player["Armor Level"] = 5;
gamePayload.presets.weapons["Laser Gun Damage"] = 150;
gamePayload.presets.weapons["Plasma Cannon Heat"] = 87;
gamePayload.presets.levels["Enemies in Level 1"] = 50;
```

### Validate Game Payload:

```javascript
let gameSchema = {
  player: ["Max Health", "Armor Level"],
  weapons: ["Laser Gun Damage"],
  levels: ["Enemies in Level 1"]
};
console.log(validatePayload(gamePayload, gameSchema));
```

---

## TL;DR:
- Building payloads manually avoids unnecessary complexity.
- Explicit assignments are easy to validate.
- Schema validation catches mismatches early.

